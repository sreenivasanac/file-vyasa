"""File processing for sync operations."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import structlog

from filevyasa.extractor import enrich_file_object
from filevyasa.extractor.media_extractor import MediaTranscriber
from filevyasa.llm import ImageDescriber, Summarizer
from filevyasa.models.enums import FileCategory
from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


class CancellationManager:
    """Thread-safe manager for sync cancellation signals.

    Uses in-memory flags for immediate cancellation response,
    avoiding SQLite session isolation delays.
    """

    _cancelled: Dict[str, bool] = {}
    _lock = threading.Lock()

    @classmethod
    def cancel(cls, folder_id: str):
        """Signal cancellation for a folder."""
        with cls._lock:
            cls._cancelled[folder_id] = True
        logger.info("cancellation_signalled", folder_id=folder_id)

    @classmethod
    def is_cancelled(cls, folder_id: str) -> bool:
        """Check if a folder sync has been cancelled."""
        with cls._lock:
            return cls._cancelled.get(folder_id, False)

    @classmethod
    def reset(cls, folder_id: str):
        """Reset cancellation flag when starting a new sync."""
        with cls._lock:
            cls._cancelled[folder_id] = False

    @classmethod
    def cleanup(cls, folder_id: str):
        """Remove cancellation flag when sync is done."""
        with cls._lock:
            cls._cancelled.pop(folder_id, None)


class ProcessingTracker:
    """Thread-safe tracker for files currently being processed.

    This allows the UI to show which files are actively being worked on.
    """

    # Class-level storage for tracking across folder syncs
    _instances: Dict[str, "ProcessingTracker"] = {}
    _lock = threading.Lock()

    def __init__(self, folder_id: str):
        self.folder_id = folder_id
        self._processing: Dict[str, str] = {}  # path -> filename
        self._processing_lock = threading.Lock()

    @classmethod
    def get_or_create(cls, folder_id: str) -> "ProcessingTracker":
        """Get or create a tracker for the given folder."""
        with cls._lock:
            if folder_id not in cls._instances:
                cls._instances[folder_id] = cls(folder_id)
            return cls._instances[folder_id]

    @classmethod
    def remove(cls, folder_id: str):
        """Remove tracker for folder when sync is complete."""
        with cls._lock:
            cls._instances.pop(folder_id, None)

    @classmethod
    def get_processing_files(cls, folder_id: str) -> List[Dict[str, str]]:
        """Get list of files currently being processed for a folder."""
        with cls._lock:
            tracker = cls._instances.get(folder_id)
            if not tracker:
                return []
        with tracker._processing_lock:
            return [{"path": p, "filename": f} for p, f in tracker._processing.items()]

    def add_file(self, path: str, filename: str):
        """Mark a file as currently being processed."""
        with self._processing_lock:
            self._processing[path] = filename

    def remove_file(self, path: str):
        """Mark a file as done processing."""
        with self._processing_lock:
            self._processing.pop(path, None)

    def clear(self):
        """Clear all processing files."""
        with self._processing_lock:
            self._processing.clear()


class SyncProgress:
    """Thread-safe progress tracking for parallel sync."""

    def __init__(self):
        self._lock = threading.Lock()
        self.processed = 0
        self.failed = 0
        self.new_count = 0
        self.modified_count = 0
        self.unchanged_count = 0

    def increment(self, field: str, count: int = 1):
        """Thread-safe increment of any counter field."""
        with self._lock:
            setattr(self, field, getattr(self, field) + count)


class FileProcessor:
    """Processes files with parallel extraction and AI processing."""

    def __init__(
        self,
        summarizer: Optional[Summarizer] = None,
        image_describer: Optional[ImageDescriber] = None,
        transcriber: Optional[MediaTranscriber] = None,
        generate_document_summaries: bool = False,
    ):
        self.summarizer = summarizer
        self.image_describer = image_describer
        self.transcriber = transcriber
        self.generate_document_summaries = generate_document_summaries

    def process_single_file(self, file_obj: FileObject) -> Tuple[FileObject, Optional[str]]:
        """Process a single file: extract content then apply AI processing.

        Returns: (processed_file_obj, error_or_none)
        """
        try:
            file_obj = enrich_file_object(file_obj)
            file_obj = self._route_to_ai_processor(file_obj)
            return (file_obj, None)
        except Exception as e:
            logger.error("file_processing_failed", filename=file_obj.filename, error=str(e))
            return (file_obj, str(e))

    def _route_to_ai_processor(self, file_obj: FileObject) -> FileObject:
        """Route file to appropriate AI processor based on category."""
        category = file_obj.category
        category_value = category.value if hasattr(category, 'value') else str(category)

        if category_value == FileCategory.IMAGE.value:
            return self._process_image(file_obj)
        elif category_value in [FileCategory.AUDIO.value, FileCategory.VIDEO.value]:
            return self._process_media(file_obj)
        else:
            return self._process_document(file_obj)

    def _is_non_content_file(self, file_obj: FileObject) -> bool:
        """Check if file was skipped during extraction (no real content)."""
        return (
            file_obj.content_preview
            and file_obj.metadata.get("extraction_method") == "skipped"
        )

    def _process_image(self, file_obj: FileObject) -> FileObject:
        """Process image files with vision model."""
        if self.image_describer:
            return self.image_describer.describe(file_obj)
        if self._is_non_content_file(file_obj):
            return self._set_summary_from_preview(file_obj)
        return file_obj

    def _process_media(self, file_obj: FileObject) -> FileObject:
        """Process audio/video files with transcription."""
        if self.transcriber:
            file_obj = self.transcriber.transcribe(file_obj)
            has_transcription = (
                file_obj.content_preview
                and not file_obj.content_preview.startswith("[")
            )
            if self.summarizer and has_transcription and self.generate_document_summaries:
                file_obj = self.summarizer.summarize(file_obj)
            return file_obj
        if self._is_non_content_file(file_obj):
            return self._set_summary_from_preview(file_obj)
        return file_obj

    def _process_document(self, file_obj: FileObject) -> FileObject:
        """Process document/text files with summarizer."""
        if self._is_non_content_file(file_obj):
            return self._set_summary_from_preview(file_obj, clear_model=True)
        if self.summarizer and file_obj.content_preview:
            return self.summarizer.summarize(file_obj)
        return file_obj

    def _set_summary_from_preview(
        self, file_obj: FileObject, clear_model: bool = False
    ) -> FileObject:
        """Set AI summary fields from content preview for non-content files."""
        file_obj.ai_brief_summary = file_obj.content_preview
        file_obj.ai_summary = file_obj.content_preview
        file_obj.summarized_at = datetime.now()
        if clear_model:
            file_obj.llm_model = None
        return file_obj


def process_files_parallel(
    files_to_process: List[Tuple[FileObject, Optional[any], str]],
    processor: FileProcessor,
    progress: SyncProgress,
    on_file_complete: Callable[[FileObject, Optional[any], str], None],
    is_cancelled: Callable[[], bool],
    max_workers: int,
    folder_id: Optional[str] = None,
):
    """Process files with configurable parallelism.

    Args:
        files_to_process: List of (file_obj, db_file, action) tuples
        processor: FileProcessor instance
        progress: SyncProgress to track counts
        on_file_complete: Callback(file_obj, db_file, action) called after each file
        is_cancelled: Callable returning True if sync was cancelled
        max_workers: Number of parallel workers
        folder_id: Optional folder ID for tracking currently processing files
    """
    logger.info("starting_file_processing", files=len(files_to_process), workers=max_workers)

    tracker = ProcessingTracker.get_or_create(folder_id) if folder_id else None

    def check_cancelled() -> bool:
        """Check both in-memory flag and callback for cancellation."""
        if folder_id and CancellationManager.is_cancelled(folder_id):
            return True
        return is_cancelled()

    def process_with_tracking(file_obj: FileObject) -> Tuple[FileObject, Optional[str]]:
        """Wrapper to track file processing."""
        if tracker:
            tracker.add_file(file_obj.path, file_obj.filename)
        try:
            return processor.process_single_file(file_obj)
        finally:
            if tracker:
                tracker.remove_file(file_obj.path)

    # Check cancellation before starting
    if check_cancelled():
        logger.info("sync_cancelled_before_processing", folder_id=folder_id)
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all files at once - executor manages the queue
        futures = {
            executor.submit(process_with_tracking, file_obj): (file_obj, db_file, action)
            for file_obj, db_file, action in files_to_process
        }

        for future in as_completed(futures):
            # Check cancellation after each file completes
            if check_cancelled():
                logger.info("sync_cancelled_during_processing", folder_id=folder_id)
                executor.shutdown(wait=False, cancel_futures=True)
                if tracker:
                    tracker.clear()
                break

            original_file, db_file, action = futures[future]
            try:
                processed_file, error = future.result()
                if error:
                    progress.increment('failed')
                else:
                    on_file_complete(processed_file, db_file, action)
            except Exception as e:
                logger.error("worker_failed", filename=original_file.filename, error=str(e))
                progress.increment('failed')
