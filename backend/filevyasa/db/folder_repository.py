"""Database operations for monitored folders.

This module centralizes all direct database access for monitored folders so
that API routes can focus on HTTP concerns only.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from uuid import uuid4

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import MonitoredFolderTable
from filevyasa.models.enums import FolderStatus
from filevyasa.models.folder import FolderSyncRequest, MonitoredFolderResponse


class FolderNotFoundError(Exception):
    """Raised when a monitored folder cannot be found in the database."""


class FolderAlreadyMonitoredError(Exception):
    """Raised when attempting to create a folder that is already monitored."""


class FolderSyncAlreadyRunningError(Exception):
    """Raised when attempting to start a sync while one is already running."""


@contextmanager
def db_session():
    """Context manager for database sessions.

    Provides a small convenience wrapper around :func:`get_session` that
    ensures sessions are always closed.
    """

    session = get_session()
    try:
        yield session
    finally:
        session.close()


def _folder_to_response(folder: MonitoredFolderTable) -> MonitoredFolderResponse:
    """Convert a :class:`MonitoredFolderTable` row to API response model."""

    return MonitoredFolderResponse(
        id=folder.id,
        root_path=folder.root_path,
        name=folder.name,
        status=FolderStatus(folder.status),
        last_synced_at=folder.last_synced_at,
        last_llm_model=folder.last_llm_model,
        last_sync_started_at=getattr(folder, "last_sync_started_at", None),
        total_files=folder.total_files,
        processed_files=folder.processed_files,
        failed_files=folder.failed_files,
        skipped_files=getattr(folder, "skipped_files", 0),
        generate_document_summaries=folder.generate_document_summaries,
        generate_image_descriptions=folder.generate_image_descriptions,
        extract_media_transcriptions=folder.extract_media_transcriptions,
        ignore_patterns=folder.ignore_patterns or [],
        created_at=folder.created_at,
    )


def check_folder_conflicts(
    root_path: str, *, exclude_folder_id: Optional[str] = None
) -> Optional[str]:
    """Return the conflicting folder's root_path if there's a conflict.

    A conflict occurs when the new folder path is a subfolder of an existing
    monitored folder or vice versa. Optionally an existing folder ID can be
    excluded from the conflict check (useful for updates).
    """

    new_path = Path(root_path).resolve()

    with db_session() as session:
        folders: Iterable[MonitoredFolderTable] = session.query(MonitoredFolderTable).all()

        for folder in folders:
            if exclude_folder_id and folder.id == exclude_folder_id:
                continue

            existing_path = Path(folder.root_path).resolve()

            # Check if one is subfolder of the other
            try:
                new_path.relative_to(existing_path)
                return folder.root_path
            except ValueError:
                pass

            try:
                existing_path.relative_to(new_path)
                return folder.root_path
            except ValueError:
                pass

    return None


def get_folder_by_root_path(root_path: str) -> Optional[MonitoredFolderTable]:
    """Return folder row for an exact root_path match, if any."""

    with db_session() as session:
        return (
            session.query(MonitoredFolderTable)
            .filter_by(root_path=root_path)
            .first()
        )


def create_monitored_folder(
    *,
    root_path: str,
    generate_document_summaries: bool,
    generate_image_descriptions: bool,
    extract_media_transcriptions: bool,
    ignore_patterns: Optional[List[str]] = None,
) -> MonitoredFolderResponse:
    """Create and persist a new monitored folder.

    Raises :class:`FolderAlreadyMonitoredError` if a folder with the same
    root_path already exists.
    """

    combined_ignore_patterns: List[str] = list(settings.default_ignore_patterns)
    if ignore_patterns:
        combined_ignore_patterns.extend(ignore_patterns)

    with db_session() as session:
        existing = (
            session.query(MonitoredFolderTable)
            .filter_by(root_path=root_path)
            .first()
        )
        if existing:
            raise FolderAlreadyMonitoredError(root_path)

        folder_id = str(uuid4())
        folder_name = Path(root_path).name or root_path

        folder = MonitoredFolderTable(
            id=folder_id,
            root_path=root_path,
            name=folder_name,
            status=FolderStatus.IDLE.value,
            generate_document_summaries=generate_document_summaries,
            generate_image_descriptions=generate_image_descriptions,
            extract_media_transcriptions=extract_media_transcriptions,
            ignore_patterns=combined_ignore_patterns,
            created_at=datetime.now(),
        )

        session.add(folder)
        session.commit()

        return _folder_to_response(folder)


def list_folders() -> List[MonitoredFolderResponse]:
    """Return all monitored folders ordered by creation time (newest first)."""

    with db_session() as session:
        folders = (
            session.query(MonitoredFolderTable)
            .order_by(MonitoredFolderTable.created_at.desc())
            .all()
        )
        return [_folder_to_response(f) for f in folders]


def get_folder(folder_id: str) -> Optional[MonitoredFolderResponse]:
    """Return a single monitored folder by ID, or ``None`` if not found."""

    with db_session() as session:
        folder = (
            session.query(MonitoredFolderTable)
            .filter_by(id=folder_id)
            .first()
        )
        if not folder:
            return None
        return _folder_to_response(folder)


def delete_folder(folder_id: str) -> bool:
    """Delete a monitored folder.

    Returns ``True`` if the folder existed and was deleted, ``False`` if it
    did not exist.
    """

    with db_session() as session:
        folder = (
            session.query(MonitoredFolderTable)
            .filter_by(id=folder_id)
            .first()
        )
        if not folder:
            return False

        session.delete(folder)
        session.commit()
        return True


def prepare_folder_sync(
    folder_id: str,
    request: Optional[FolderSyncRequest] = None,
) -> Tuple[MonitoredFolderResponse, bool, bool, bool]:
    """Prepare a folder for sync and return its state and AI options.

    The folder's status and progress counters are reset, and the sync start
    timestamp is recorded. Returns the updated folder response together with
    the effective AI processing flags to be used by the sync service.
    """

    with db_session() as session:
        folder = (
            session.query(MonitoredFolderTable)
            .filter_by(id=folder_id)
            .first()
        )

        if not folder:
            raise FolderNotFoundError(folder_id)

        if folder.status == FolderStatus.SYNCING.value:
            raise FolderSyncAlreadyRunningError(folder_id)

        generate_document_summaries = folder.generate_document_summaries
        generate_image_descriptions = folder.generate_image_descriptions
        extract_media_transcriptions = folder.extract_media_transcriptions

        if request:
            if request.generate_document_summaries is not None:
                generate_document_summaries = request.generate_document_summaries
            if request.generate_image_descriptions is not None:
                generate_image_descriptions = request.generate_image_descriptions
            if request.extract_media_transcriptions is not None:
                extract_media_transcriptions = request.extract_media_transcriptions

        folder.processed_files = 0
        folder.failed_files = 0
        folder.status = FolderStatus.SYNCING.value
        folder.last_sync_started_at = datetime.now()
        session.commit()

        response = _folder_to_response(folder)

    return (
        response,
        generate_document_summaries,
        generate_image_descriptions,
        extract_media_transcriptions,
    )


def cancel_folder_sync(folder_id: str) -> bool:
    """Mark a folder's sync as cancelled if it is currently syncing.

    Returns ``True`` if the folder exists (status may or may not change),
    and ``False`` if the folder does not exist.
    """

    with db_session() as session:
        folder = (
            session.query(MonitoredFolderTable)
            .filter_by(id=folder_id)
            .first()
        )
        if not folder:
            return False

        if folder.status == FolderStatus.SYNCING.value:
            folder.status = FolderStatus.CANCELLED.value
            session.commit()

        return True


def folder_exists(folder_id: str) -> bool:
    """Return ``True`` if a folder with the given ID exists."""

    with db_session() as session:
        return (
            session.query(MonitoredFolderTable)
            .filter_by(id=folder_id)
            .first()
            is not None
        )
