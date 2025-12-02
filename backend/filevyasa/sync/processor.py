"""File processing for sync operations."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, List, Optional, Tuple

import structlog

from filevyasa.extractor import enrich_file_object
from filevyasa.extractor.media_extractor import MediaTranscriber
from filevyasa.llm import ImageDescriber, Summarizer
from filevyasa.models.enums import FileCategory
from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


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
        is_non_content = (
            file_obj.content_preview and
            file_obj.metadata.get("extraction_method") == "skipped"
        )

        category = file_obj.category
        category_value = category.value if hasattr(category, 'value') else str(category)

        # Image files - use vision model
        if category_value == FileCategory.IMAGE.value:
            if self.image_describer:
                return self.image_describer.describe(file_obj)
            elif is_non_content:
                return self._set_summary_from_preview(file_obj)

        # Audio/Video files - transcribe and optionally summarize
        elif category_value in [FileCategory.AUDIO.value, FileCategory.VIDEO.value]:
            if self.transcriber:
                file_obj = self.transcriber.transcribe(file_obj)
                # Check if transcription was successful (has actual text, not error)
                has_transcription = (
                    file_obj.content_preview
                    and not file_obj.content_preview.startswith("[")
                )
                if self.summarizer and has_transcription and self.generate_document_summaries:
                    file_obj = self.summarizer.summarize(file_obj)
                return file_obj
            elif is_non_content:
                return self._set_summary_from_preview(file_obj)

        # Document/Text files - use summarizer
        elif category_value in [
            FileCategory.DOCUMENT.value, FileCategory.TEXT.value,
            FileCategory.SPREADSHEET.value, FileCategory.PRESENTATION.value
        ]:
            if is_non_content:
                return self._set_summary_from_preview(file_obj, clear_model=True)
            elif self.summarizer and file_obj.content_preview:
                return self.summarizer.summarize(file_obj)

        # Other file types
        else:
            if is_non_content:
                return self._set_summary_from_preview(file_obj, clear_model=True)
            elif self.summarizer and file_obj.content_preview:
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
):
    """Process files with configurable parallelism.

    Args:
        files_to_process: List of (file_obj, db_file, action) tuples
        processor: FileProcessor instance
        progress: SyncProgress to track counts
        on_file_complete: Callback(file_obj, db_file, action) called after each file
        is_cancelled: Callable returning True if sync was cancelled
        max_workers: Number of parallel workers
    """
    logger.info("starting_file_processing", files=len(files_to_process), workers=max_workers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all files
        futures = {
            executor.submit(processor.process_single_file, file_obj): (file_obj, db_file, action)
            for file_obj, db_file, action in files_to_process
        }

        for future in as_completed(futures):
            if is_cancelled():
                executor.shutdown(wait=False, cancel_futures=True)
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
