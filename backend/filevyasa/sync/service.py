"""Sync service - orchestrates folder synchronization."""

from datetime import datetime
from typing import List

import structlog

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import FileObjectTable, MonitoredFolderTable
from filevyasa.extractor.media_extractor import MediaTranscriber
from filevyasa.llm import ImageDescriber, Summarizer
from filevyasa.models.enums import FolderStatus
from filevyasa.models.file_object import FileObject
from filevyasa.scanner import Scanner

from .categorizer import categorize_files
from .db_ops import update_file_record
from .processor import (
    CancellationManager,
    FileProcessor,
    ProcessingTracker,
    SyncProgress,
    process_files_parallel,
)

logger = structlog.get_logger()


class SyncService:
    """Orchestrates folder synchronization with parallel processing."""

    def __init__(
        self,
        folder_id: str,
        generate_document_summaries: bool = False,
        generate_image_descriptions: bool = False,
        extract_media_transcriptions: bool = False,
    ):
        self.folder_id = folder_id
        self.generate_document_summaries = generate_document_summaries
        self.generate_image_descriptions = generate_image_descriptions
        self.extract_media_transcriptions = extract_media_transcriptions
        self.progress = SyncProgress()

    def _create_processor(self) -> FileProcessor:
        """Initialize AI processors based on settings."""
        summarizer = Summarizer() if self.generate_document_summaries else None
        image_describer = ImageDescriber() if self.generate_image_descriptions else None
        transcriber = MediaTranscriber() if self.extract_media_transcriptions else None

        return FileProcessor(
            summarizer=summarizer,
            image_describer=image_describer,
            transcriber=transcriber,
            generate_document_summaries=self.generate_document_summaries,
        )

    def _scan_filesystem(self, folder) -> tuple[List[FileObject], int]:
        """Scan filesystem and return list of files with skipped count."""
        # Combine default patterns with any folder-specific patterns
        file_patterns = list(settings.ignore_file_patterns)
        folder_names = list(settings.ignore_folder_names)
        excluded_paths = list(folder.excluded_paths or [])
        
        # Add any legacy ignore_patterns to file patterns for backward compatibility
        if folder.ignore_patterns:
            file_patterns.extend(folder.ignore_patterns)
        
        scanner = Scanner(
            file_patterns=file_patterns,
            folder_names=folder_names,
            excluded_paths=excluded_paths,
            folder_id=self.folder_id,
        )
        return scanner.scan_to_list(folder.root_path, recursive=True)

    def _process_files(
        self,
        session,
        folder,
        files_to_process: List,
        processor: FileProcessor,
    ):
        """Process new/modified files with parallel workers."""
        if not files_to_process:
            return

        workers = self._get_worker_count(len(files_to_process))
        batch_pending = []

        def on_file_complete(file_obj: FileObject, db_file, action: str):
            if action == 'new':
                self.progress.increment('new_count')
            else:
                self.progress.increment('modified_count')

            now = datetime.now()
            file_obj.last_extracted_at = now
            if (
                self.generate_document_summaries
                or self.generate_image_descriptions
                or self.extract_media_transcriptions
            ):
                file_obj.last_ai_processed_at = now
            file_obj.extraction_status = 'success'
            update_file_record(db_file, file_obj)
            self.progress.increment('processed')
            batch_pending.append(file_obj)

            if len(batch_pending) >= settings.sync_db_batch_size:
                session.commit()
                folder.processed_files = self.progress.processed
                folder.failed_files = self.progress.failed
                session.commit()
                batch_pending.clear()

        def is_cancelled() -> bool:
            session.refresh(folder)
            return folder.status == FolderStatus.CANCELLED.value

        process_files_parallel(
            files_to_process, processor, self.progress,
            on_file_complete, is_cancelled, workers,
            folder_id=self.folder_id
        )

        if batch_pending:
            session.commit()
            folder.processed_files = self.progress.processed
            folder.failed_files = self.progress.failed
            session.commit()

    def _finalize_sync(self, session, folder, fs_paths_count: int, deleted_count: int):
        """Update folder status after sync completes."""
        session.refresh(folder)
        if folder.status != FolderStatus.CANCELLED.value:
            folder.status = FolderStatus.IDLE.value
            folder.last_synced_at = datetime.now()
            if self.generate_document_summaries or self.generate_image_descriptions:
                folder.last_llm_model = f"{settings.llm_provider}/{settings.llm_model}"

        folder.total_files = fs_paths_count - deleted_count
        folder.processed_files = self.progress.processed
        folder.failed_files = self.progress.failed
        session.commit()

        ProcessingTracker.remove(self.folder_id)
        CancellationManager.cleanup(self.folder_id)

        logger.info(
            "sync_complete",
            folder_id=self.folder_id,
            new=self.progress.new_count,
            modified=self.progress.modified_count,
            unchanged=self.progress.unchanged_count,
            failed=self.progress.failed,
        )

    def run(self):
        """Execute folder sync. Call this from a background task."""
        CancellationManager.reset(self.folder_id)
        session = get_session()

        try:
            folder = session.query(MonitoredFolderTable).filter_by(id=self.folder_id).first()
            if not folder:
                return

            folder.status = FolderStatus.SYNCING.value
            folder.last_sync_started_at = datetime.now()
            session.commit()

            # Track per-run progress starting from zero; folder fields are updated from this
            self.progress = SyncProgress()

            processor = self._create_processor()

            # Load existing files from DB
            all_db_files = session.query(FileObjectTable).filter_by(folder_id=self.folder_id).all()
            existing_by_inode = {f.inode: f for f in all_db_files if f.inode}
            existing_by_path = {f.path: f for f in all_db_files}

            # Scan filesystem
            fs_files, skipped_count = self._scan_filesystem(folder)
            fs_inodes = {f.inode for f in fs_files if f.inode}
            fs_paths = {f.path for f in fs_files}

            folder.total_files = len(fs_files)
            folder.skipped_files = skipped_count
            session.commit()

            # Categorize files and create pending records for new files
            files_to_process, _ = categorize_files(
                session=session,
                fs_files=fs_files,
                existing_by_inode=existing_by_inode,
                existing_by_path=existing_by_path,
                folder=folder,
                progress=self.progress,
                generate_document_summaries=self.generate_document_summaries,
                generate_image_descriptions=self.generate_image_descriptions,
                extract_media_transcriptions=self.extract_media_transcriptions,
                folder_id=self.folder_id,
            )

            session.commit()
            folder.processed_files = self.progress.processed
            session.commit()

            # Process new/modified files
            self._process_files(session, folder, files_to_process, processor)

            # Delete files no longer on disk
            deleted_count = self._delete_removed_files(session, all_db_files, fs_inodes, fs_paths)

            # Finalize
            self._finalize_sync(session, folder, len(fs_paths), deleted_count)

        except Exception as e:
            import traceback
            print(f"Sync error for folder {self.folder_id}: {e}")
            traceback.print_exc()
            folder = session.query(MonitoredFolderTable).filter_by(id=self.folder_id).first()
            if folder:
                folder.status = FolderStatus.ERROR.value
                session.commit()
            ProcessingTracker.remove(self.folder_id)
            CancellationManager.cleanup(self.folder_id)
        finally:
            session.close()

    def _get_worker_count(self, file_count: int) -> int:
        """Determine number of workers based on settings and file count."""
        if not settings.sync_enable_parallel or file_count < 3:
            return 1
        return settings.sync_extraction_workers

    def _delete_removed_files(
        self, session, all_db_files: List[FileObjectTable], fs_inodes: set, fs_paths: set
    ) -> int:
        """Delete DB records for files no longer on disk."""
        deleted_count = 0
        for db_file in all_db_files:
            if db_file.inode and db_file.inode not in fs_inodes:
                session.delete(db_file)
                deleted_count += 1
            elif not db_file.inode and db_file.path not in fs_paths:
                session.delete(db_file)
                deleted_count += 1
        return deleted_count
