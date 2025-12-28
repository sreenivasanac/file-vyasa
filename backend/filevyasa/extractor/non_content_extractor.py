"""Non-content extractors for file types that don't need content extraction.

These extractors generate simple descriptions without reading file contents,
avoiding LLM calls for files where content extraction isn't meaningful.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from filevyasa.extractor.base import BaseExtractor


class NonContentExtractor(BaseExtractor):
    """Base class for extractors that don't extract file content.

    Used for file types where content extraction isn't meaningful or supported.
    Generates a simple description based on file type and name.
    """

    @classmethod
    def supported_extensions(cls) -> List[str]:
        """Override in subclasses to specify supported extensions."""
        return []

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Return simple description without extracting content."""
        ext = file_path.suffix.lower().lstrip(".") or "no extension"
        filename = file_path.name
        type_label = self._get_type_label(ext)
        description = f"{type_label} file with name {filename}"

        return description, {
            "extraction_method": "skipped",
            "reason": "non_content_file_type",
            "file_type": ext
        }

    def _get_type_label(self, ext: str) -> str:
        """Get human-readable label for the file type. Override for custom labels."""
        return ext.upper() if ext else "Unknown"


class CodeExtractor(NonContentExtractor):
    """Extractor for code/script and code-related files. Skips content extraction."""

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [
            # Core languages
            "py", "js", "ts", "jsx", "tsx",
            "css", "scss", "less", "sass",
            "php", "rb", "go", "rs", "java",
            "c", "cpp", "h", "hpp", "cs",
            "swift", "kt", "kts", "scala",
            "sh", "bash", "zsh", "fish",
            "sql", "r", "lua", "pl", "pm",
            "vue", "svelte",
            "json",
            # Config/data formats
            "yaml", "yml", "env", "jsonl",
            "toml", "ini", "conf", "cfg", "log",
            # JS/TS ecosystem variants
            "cjs", "cts", "mjs", "mts", "flow",
            # C/C++ variants
            "cc", "cxx", "hxx",
            # Python ecosystem
            "pyi", "pyx", "pxd", "pxi",
            # Scientific/HPC
            "f", "f90", "f95", "cu", "cuh", "m",
            # Build/schema files
            "proto", "cmake", "makefile", "mk", "prisma", "g4", "gbnf",
            # Other languages
            "coffee", "nix", "applescript",
            # Windows scripts
            "bat", "ps1", "cmd",
            # Code packages
            "jar", "whl", "egg", "deb",
            # Compiled/binary code artifacts
            "pyc", "pyo", "so", "dylib", "node", "wasm",
            # ML model files
            "onnx", "pt", "pth", "pb",
            # Data formats used in code
            "parquet", "feather", "joblib", "arff", "mat", "fig",
            # Translation files
            "mo", "po",
            # Dev artifacts
            "map", "sample", "dat", "bin", "bak", "snap",
            # GIS/Geospatial
            "shp", "shx", "dbf", "las", "laz", "gpx", "kml", "kmz", "pcd",
            # CAD/3D models
            "stl", "obj", "ply", "3ds", "ipt", "iam",
            # Certificates/keys
            "pem", "crt", "cer", "p12", "pfx",
        ]


class ArchiveExtractor(NonContentExtractor):
    """Extractor for archive/compressed files. Skips content extraction."""

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [
            "zip", "tar", "gz", "tgz", "bz2",
            "rar", "7z", "xz", "lz", "lzma",
            "dmg", "iso", "img",
        ]

    def _get_type_label(self, ext: str) -> str:
        labels = {
            "zip": "ZIP archive",
            "tar": "TAR archive",
            "gz": "GZIP compressed",
            "rar": "RAR archive",
            "7z": "7-Zip archive",
            "dmg": "macOS disk image",
            "iso": "ISO disk image",
        }
        return labels.get(ext, f"{ext.upper()} archive")


class UnhandledExtractor(NonContentExtractor):
    """Extractor for miscellaneous unhandled file types.

    Catches file types that don't fit other categories and generates
    a simple description without content extraction.
    """

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return [
            # Database files
            "db", "sqlite", "sqlite3", "mdb", "accdb",
            # Font files
            "woff", "woff2", "ttf", "otf", "eot",
            # Apple iWork formats
            "numbers", "pages", "key",
            # Data/binary files
            "pkl", "pickle", "npy", "npz", "h5", "hdf5",
            # Config/lock files
            "lock",
            # macOS specific
            "scpt", "workflow",
            # Mobile/app files
            "pkpass", "ipa", "apk",
            # Service files
            "service", "plist",
        ]

    def _get_type_label(self, ext: str) -> str:
        labels = {
            "db": "Database",
            "sqlite": "SQLite database",
            "woff": "Web font",
            "woff2": "Web font",
            "ttf": "TrueType font",
            "otf": "OpenType font",
            "numbers": "Apple Numbers",
            "pages": "Apple Pages",
            "key": "Apple Keynote",
            "pkl": "Python pickle",
            "scpt": "AppleScript",
            "pkpass": "Apple Wallet pass",
            "plist": "Property list",
        }
        return labels.get(ext, ext.upper())


class NoExtensionExtractor(NonContentExtractor):
    """Extractor for files without extensions.

    This is used as a fallback when a file has no extension.
    """

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return []  # Special case - handled explicitly in factory

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Return description for files without extension."""
        filename = file_path.name
        description = f"File without extension: {filename}"

        return description, {
            "extraction_method": "skipped",
            "reason": "no_extension",
            "file_type": "unknown"
        }
