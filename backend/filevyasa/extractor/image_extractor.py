"""Image extractor for EXIF metadata and basic image info."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor

logger = structlog.get_logger()


class ImageExtractor(BaseExtractor):
    """Extractor for image files - extracts EXIF and basic metadata."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return [
            "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif",
            "webp", "heic", "heif", "ico", "svg"
        ]

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract metadata from images."""
        metadata = {}
        content_parts = []

        # Get basic image info using Pillow
        try:
            from PIL import Image
            with Image.open(str(file_path)) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["format"] = img.format
                metadata["mode"] = img.mode
                content_parts.append(f"Image: {img.width}x{img.height} {img.format}")
        except Exception as e:
            logger.debug("pillow_failed", path=str(file_path), error=str(e))

        # Get EXIF data
        exif_data = self._extract_exif(file_path)
        if exif_data:
            metadata["exif"] = exif_data

            # Add useful EXIF fields to content
            if "DateTimeOriginal" in exif_data:
                content_parts.append(f"Date taken: {exif_data['DateTimeOriginal']}")
            if "Make" in exif_data and "Model" in exif_data:
                content_parts.append(f"Camera: {exif_data['Make']} {exif_data['Model']}")
            if "GPSInfo" in exif_data:
                content_parts.append("GPS: Location data available")

        content = "\n".join(content_parts) if content_parts else "[Image file - no text content]"
        return content, metadata

    def _extract_exif(self, file_path: Path) -> Dict[str, Any]:
        """Extract EXIF metadata from an image.

        Uses Pillow for WebP files (better handling, no warnings for missing EXIF)
        and exifread for other formats (broader EXIF tag support).
        """
        exif_data = {}
        ext = file_path.suffix.lower()

        # Use Pillow for WebP files - exifread logs warnings for WebP without EXIF
        if ext == ".webp":
            return self._extract_exif_pillow(file_path)

        # Use exifread for other formats (better EXIF tag coverage)
        try:
            import exifread
            with open(str(file_path), "rb") as f:
                tags = exifread.process_file(f, details=False)

                # Convert to serializable dict
                for tag, value in tags.items():
                    if tag.startswith("Thumbnail"):
                        continue
                    # Convert value to string for JSON serialization
                    exif_data[tag.replace("EXIF ", "").replace("Image ", "")] = str(value)

        except Exception as e:
            logger.debug("exifread_failed", path=str(file_path), error=str(e))

        return exif_data

    def _extract_exif_pillow(self, file_path: Path) -> Dict[str, Any]:
        """Extract EXIF using Pillow - handles missing EXIF gracefully without warnings."""
        exif_data = {}
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(str(file_path)) as img:
                exif_raw = img.getexif()
                if exif_raw:
                    for tag_id, value in exif_raw.items():
                        tag_name = TAGS.get(tag_id, str(tag_id))
                        # Convert value to string for JSON serialization
                        try:
                            exif_data[tag_name] = str(value)
                        except Exception:
                            pass
        except Exception as e:
            logger.debug("pillow_exif_failed", path=str(file_path), error=str(e))

        return exif_data
