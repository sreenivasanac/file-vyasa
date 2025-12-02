"""Sync service - orchestrates folder synchronization."""

from datetime import datetime
from typing import List, Optional, Tuple

import structlog

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import FileObjectTable, MonitoredFolderTable
from filevyasa.extractor.media_extractor import MediaTranscriber
from filevyasa.llm import ImageDescriber, Summarizer
from filevyasa.models.enums import FolderStatus
from filevyasa.models.file_object import FileObject
from filevyasa.scanner import Scanner

from .db_ops import create_file_record, update_file_record
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

    def run(self):
        """Execute folder sync. Call this from a background task."""
        # Reset cancellation flag at the start of sync
        CancellationManager.reset(self.folder_id)

        session = get_session()

        try:
            folder = session.query(MonitoredFolderTable).filter_by(id=self.folder_id).first()
            if not folder:
                return

            folder.status = FolderStatus.SYNCING.value
            session.commit()

            # Initialize AI processors based on settings
            summarizer = Summarizer() if self.generate_document_summaries else None
            image_describer = ImageDescriber() if self.generate_image_descriptions else None
            transcriber = MediaTranscriber() if self.extract_media_transcriptions else None

            processor = FileProcessor(
                summarizer=summarizer,
                image_describer=image_describer,
                transcriber=transcriber,
                generate_document_summaries=self.generate_document_summaries,
            )

            # Load existing files from DB
            all_db_files = session.query(FileObjectTable).filter_by(folder_id=self.folder_id).all()
            existing_by_inode = {f.inode: f for f in all_db_files if f.inode}
            existing_by_path = {f.path: f for f in all_db_files}

            # Scan filesystem
            ignore_patterns = (
                list(folder.ignore_patterns or []) + list(settings.default_ignore_patterns)
            )
            scanner = Scanner(ignore_patterns=ignore_patterns, folder_id=self.folder_id)
            fs_files = scanner.scan_to_list(folder.root_path, recursive=True)
            fs_inodes = {f.inode for f in fs_files if f.inode}
            fs_paths = {f.path for f in fs_files}

            folder.total_files = len(fs_files)
            session.commit()

            # Categorize files
            files_to_process = self._categorize_files(fs_files, existing_by_inode, existing_by_path)

            # Commit path updates for unchanged files
            session.commit()
            folder.processed_files = self.progress.processed
            session.commit()

            # Process new/modified files
            if files_to_process:
                workers = self._get_worker_count(len(files_to_process))
                batch_pending = []

                def on_file_complete(file_obj: FileObject, db_file, action: str):
                    if action == 'new':
                        self.progress.increment('new_count')
                        session.add(create_file_record(file_obj, self.folder_id))
                    else:
                        self.progress.increment('modified_count')
                        update_file_record(db_file, file_obj)
                    self.progress.increment('processed')
                    batch_pending.append(file_obj)

                    # Commit in batches for UI responsiveness
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

                # Final batch commit
                if batch_pending and folder.status != FolderStatus.CANCELLED.value:
                    session.commit()
                    folder.processed_files = self.progress.processed
                    folder.failed_files = self.progress.failed
                    session.commit()

            # Delete files no longer on disk
            deleted_count = self._delete_removed_files(session, all_db_files, fs_inodes, fs_paths)

            # Update folder status
            session.refresh(folder)
            if folder.status != FolderStatus.CANCELLED.value:
                folder.status = FolderStatus.IDLE.value
                folder.last_synced_at = datetime.now()
                if self.generate_document_summaries or self.generate_image_descriptions:
                    folder.last_llm_model = f"{settings.llm_provider}/{settings.llm_model}"

            folder.total_files = len(fs_paths) - deleted_count
            folder.processed_files = self.progress.processed
            folder.failed_files = self.progress.failed
            session.commit()

            # Clean up processing tracker and cancellation flag
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

        except Exception as e:
            import traceback
            print(f"Sync error for folder {self.folder_id}: {e}")
            traceback.print_exc()
            folder = session.query(MonitoredFolderTable).filter_by(id=self.folder_id).first()
            if folder:
                folder.status = FolderStatus.ERROR.value
                session.commit()
            # Clean up processing tracker and cancellation flag on error
            ProcessingTracker.remove(self.folder_id)
            CancellationManager.cleanup(self.folder_id)
        finally:
            session.close()

    def _categorize_files(
        self,
        fs_files: List[FileObject],
        existing_by_inode: dict,
        existing_by_path: dict,
    ) -> List[Tuple[FileObject, Optional[any], str]]:
        """Categorize files into new, modified, or unchanged."""
        files_to_process = []

        for file_obj in fs_files:
            db_file = existing_by_inode.get(file_obj.inode) or existing_by_path.get(file_obj.path)

            if db_file is None:
                files_to_process.append((file_obj, None, 'new'))
            elif (
                file_obj.modified_at
                and db_file.modified_at
                and file_obj.modified_at > db_file.modified_at
            ):
                files_to_process.append((file_obj, db_file, 'modified'))
            else:
                # Unchanged - just update path if moved
                if db_file.path != file_obj.path:
                    db_file.path = file_obj.path
                    db_file.filename = file_obj.filename
                self.progress.increment('unchanged_count')
                self.progress.increment('processed')

        return files_to_process

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
