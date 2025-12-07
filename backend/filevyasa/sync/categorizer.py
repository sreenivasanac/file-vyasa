"""Helpers for categorizing files for sync processing.

Extracted from :mod:`filevyasa.sync.service` to keep the main service orchestration
focused and make the decision logic easier to test independently.
"""

from typing import Dict, List, Optional, Tuple

from filevyasa.db.tables import FileObjectTable
from filevyasa.models.file_object import FileObject

from .db_ops import create_file_record
from .processor import SyncProgress


def categorize_files(
  session,
  fs_files: List[FileObject],
  existing_by_inode: Dict[Optional[int], FileObjectTable],
  existing_by_path: Dict[str, FileObjectTable],
  folder,
  progress: SyncProgress,
  generate_document_summaries: bool,
  generate_image_descriptions: bool,
  extract_media_transcriptions: bool,
  folder_id: str,
) -> Tuple[List[Tuple[FileObject, Optional[FileObjectTable], str]], Dict[str, FileObjectTable]]:
  """Categorize files into work queues based on timestamps and pending state.

  Rules:
  - Always process new files.
  - Process pending files left from prior run.
  - Re-process if file changed since last extraction.
  - Re-run AI if enabled and stale vs. last AI run.
  - Otherwise mark unchanged and count it as processed for this run.
  """
  files_to_process: List[Tuple[FileObject, Optional[FileObjectTable], str]] = []
  new_db_files: Dict[str, FileObjectTable] = {}

  ai_enabled = (
    generate_document_summaries
    or generate_image_descriptions
    or extract_media_transcriptions
  )

  for file_obj in fs_files:
    db_file = existing_by_inode.get(file_obj.inode) or existing_by_path.get(file_obj.path)

    if db_file is None:
      pending_record = create_file_record(file_obj, folder_id)
      pending_record.extraction_status = 'pending'
      pending_record.last_extracted_at = None
      pending_record.last_ai_processed_at = None
      session.add(pending_record)
      new_db_files[file_obj.path] = pending_record
      files_to_process.append((file_obj, pending_record, 'new'))
      continue

    if db_file.path != file_obj.path:
      db_file.path = file_obj.path
      db_file.filename = file_obj.filename

    is_pending = db_file.extraction_status == 'pending'
    modified_since_db = (
      file_obj.modified_at
      and db_file.modified_at
      and file_obj.modified_at > db_file.modified_at
    )

    needs_extraction = is_pending or db_file.extraction_status != 'success'
    last_extracted_at = getattr(db_file, 'last_extracted_at', None)
    if last_extracted_at is None:
      needs_extraction = True
    elif file_obj.modified_at and file_obj.modified_at > last_extracted_at:
      needs_extraction = True
    elif modified_since_db:
      needs_extraction = True

    last_ai_processed_at = getattr(db_file, 'last_ai_processed_at', None)
    needs_ai = False
    if ai_enabled:
      if last_ai_processed_at is None:
        needs_ai = True
      elif file_obj.modified_at and file_obj.modified_at > last_ai_processed_at:
        needs_ai = True

    if is_pending or needs_extraction or needs_ai:
      action = 'pending' if is_pending else 'modified'
      files_to_process.append((file_obj, db_file, action))
    else:
      progress.increment('unchanged_count')
      progress.increment('processed')

  return files_to_process, new_db_files
