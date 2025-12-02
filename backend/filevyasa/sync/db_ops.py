"""Database operations for file sync.

Uses automatic field mapping from Pydantic models to SQLAlchemy tables.
When adding new fields, just add them to both FileObject and FileObjectTable -
the mapping happens automatically via model_dump().
"""

from datetime import datetime
from enum import Enum
from typing import Any, Union, get_args, get_origin

from filevyasa.db.tables import FileObjectTable
from filevyasa.models.file_object import FileObject

# Field name differences between Pydantic model and SQLAlchemy table
FIELD_MAPPING = {
    'metadata': 'file_metadata',  # Pydantic 'metadata' -> SQLAlchemy 'file_metadata'
}

# Fields to exclude from automatic mapping (computed fields, relationships)
EXCLUDE_FIELDS = {'folder_id', 'size_human', 'parent_dir'}

# Fields that should not be updated (immutable after creation)
UPDATE_EXCLUDE = {'id', 'folder_id', 'inode', 'created_at', 'size_human', 'parent_dir'}


def _is_enum_type(annotation) -> bool:
    """Check if a type annotation is an Enum or Optional[Enum]."""
    # Handle Optional[EnumType] (which is Union[EnumType, None])
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        return any(
            isinstance(arg, type) and issubclass(arg, Enum)
            for arg in args if arg is not type(None)
        )
    # Handle direct enum type
    return isinstance(annotation, type) and issubclass(annotation, Enum)


def _get_enum_fields(model_class: type) -> set[str]:
    """Get all field names that have Enum types from a Pydantic model."""
    enum_fields = set()
    for field_name, field_info in model_class.model_fields.items():
        if _is_enum_type(field_info.annotation):
            enum_fields.add(field_name)
    return enum_fields


def _prepare_data(file_obj: FileObject) -> dict[str, Any]:
    """Convert FileObject to dict with proper field names and enum values."""
    data = file_obj.model_dump(exclude=EXCLUDE_FIELDS)

    # Rename fields that differ between Pydantic and SQLAlchemy
    for pydantic_name, db_name in FIELD_MAPPING.items():
        if pydantic_name in data:
            data[db_name] = data.pop(pydantic_name)

    # Convert enums to their string values (detect enum fields dynamically)
    enum_fields = _get_enum_fields(FileObject)
    for field in enum_fields:
        if field in data and data[field] is not None:
            value = data[field]
            data[field] = value.value if hasattr(value, 'value') else str(value)

    return data


def create_file_record(file_obj: FileObject, folder_id: str) -> FileObjectTable:
    """Create FileObjectTable from FileObject using automatic field mapping."""
    data = _prepare_data(file_obj)
    return FileObjectTable(folder_id=folder_id, **data)


def update_file_record(db_file: FileObjectTable, file_obj: FileObject):
    """Update existing db_file with new file_obj data."""
    data = _prepare_data(file_obj)

    # Update only mutable fields
    for field, value in data.items():
        if field not in UPDATE_EXCLUDE:
            setattr(db_file, field, value)

    db_file.scanned_at = datetime.now()
