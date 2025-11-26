"""Media extractor for audio and video files - extracts metadata using ffprobe."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor

logger = structlog.get_logger()


class MediaExtractor(BaseExtractor):
    """Extractor for audio and video files - extracts metadata without transcription.

    Transcription is handled separately by the Transcriber LLM module.
    """

    AUDIO_EXTENSIONS: List[str] = [
        "mp3", "wav", "m4a", "flac", "aac", "ogg", "wma"
    ]
    VIDEO_EXTENSIONS: List[str] = [
        "mp4", "mov", "avi", "mkv", "wmv", "flv", "m4v", "webm"
    ]

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return cls.AUDIO_EXTENSIONS + cls.VIDEO_EXTENSIONS

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract metadata from audio/video files using ffprobe."""
        metadata = {}
        content_parts = []

        ext = file_path.suffix.lower().lstrip(".")
        is_video = ext in self.VIDEO_EXTENSIONS
        file_type = "Video" if is_video else "Audio"

        try:
            probe_data = self._get_ffprobe_data(file_path)
            if probe_data:
                format_info = probe_data.get("format", {})

                # Duration
                duration_secs = float(format_info.get("duration", 0))
                if duration_secs > 0:
                    duration_str = self._format_duration(duration_secs)
                    metadata["duration"] = duration_secs
                    metadata["duration_formatted"] = duration_str
                    content_parts.append(f"{file_type}: {duration_str}")

                # Format
                format_name = format_info.get("format_long_name", "")
                if format_name:
                    metadata["format"] = format_name
                    content_parts.append(f"Format: {format_name}")

                # Bitrate
                bitrate = format_info.get("bit_rate")
                if bitrate:
                    bitrate_kbps = int(bitrate) // 1000
                    metadata["bitrate_kbps"] = bitrate_kbps
                    content_parts.append(f"Bitrate: {bitrate_kbps} kbps")

                # Stream info
                streams = probe_data.get("streams", [])
                for stream in streams:
                    codec_type = stream.get("codec_type")

                    if codec_type == "video":
                        width = stream.get("width")
                        height = stream.get("height")
                        if width and height:
                            metadata["resolution"] = f"{width}x{height}"
                            content_parts.append(f"Resolution: {width}x{height}")

                        fps = stream.get("r_frame_rate", "")
                        if fps and "/" in fps:
                            num, den = fps.split("/")
                            if int(den) > 0:
                                fps_val = round(int(num) / int(den), 2)
                                metadata["fps"] = fps_val

                        codec_name = stream.get("codec_name")
                        if codec_name:
                            metadata["video_codec"] = codec_name

                    elif codec_type == "audio":
                        codec_name = stream.get("codec_name")
                        if codec_name:
                            metadata["audio_codec"] = codec_name

                        sample_rate = stream.get("sample_rate")
                        if sample_rate:
                            metadata["sample_rate"] = int(sample_rate)

                        channels = stream.get("channels")
                        if channels:
                            metadata["channels"] = channels
                            if channels == 2:
                                channel_str = "Stereo"
                            elif channels == 1:
                                channel_str = "Mono"
                            else:
                                channel_str = f"{channels} channels"
                            content_parts.append(f"Audio: {channel_str}")

                # Tags (title, artist, etc.)
                tags = format_info.get("tags", {})
                for tag_key in ["title", "artist", "album", "date", "comment"]:
                    tag_value = tags.get(tag_key) or tags.get(tag_key.upper())
                    if tag_value:
                        metadata[tag_key] = tag_value
                        if tag_key in ["title", "artist"]:
                            content_parts.append(f"{tag_key.capitalize()}: {tag_value}")

        except Exception as e:
            logger.debug("ffprobe_failed", path=str(file_path), error=str(e))
            content_parts.append(f"[{file_type} file - metadata extraction failed]")

        if not content_parts:
            content_parts.append(f"[{file_type} file]")

        content = "\n".join(content_parts)
        return content, metadata

    def _get_ffprobe_data(self, file_path: Path) -> Dict[str, Any]:
        """Run ffprobe to get file metadata."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            logger.warning("ffprobe_timeout", path=str(file_path))
        except json.JSONDecodeError:
            logger.warning("ffprobe_json_error", path=str(file_path))
        except FileNotFoundError:
            logger.warning("ffprobe_not_found")
        except Exception as e:
            logger.debug("ffprobe_error", path=str(file_path), error=str(e))

        return {}

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
