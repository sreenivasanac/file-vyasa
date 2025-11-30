"""Media extractor for audio and video files.

Contains:
- MediaExtractor: extracts metadata using ffprobe
- MediaTranscriber: transcribes audio/video using OpenAI Whisper
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor
from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


# Shared constants for supported media extensions
AUDIO_EXTENSIONS: List[str] = ["mp3", "wav", "m4a", "flac", "aac", "ogg", "wma"]
VIDEO_EXTENSIONS: List[str] = ["mp4", "mov", "avi", "mkv", "wmv", "flv", "m4v", "webm"]


class MediaExtractor(BaseExtractor):
    """Extractor for audio and video files - extracts metadata using ffprobe.

    Transcription is handled separately by MediaTranscriber.
    """

    AUDIO_EXTENSIONS: List[str] = AUDIO_EXTENSIONS
    VIDEO_EXTENSIONS: List[str] = VIDEO_EXTENSIONS

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


class MediaTranscriber:
    """Transcribe audio/video files using OpenAI Whisper.

    Extracts the first 10 minutes of audio and transcribes using the 'base' Whisper model.
    This is content extraction, not LLM-based processing.
    """

    MODEL_SIZE = "base"
    MAX_DURATION_SECONDS = 600  # 10 minutes

    def __init__(self, model_size: str = "base", max_duration: int = 600):
        self.model_size = model_size
        self.max_duration = max_duration
        self._whisper = None
        self._model = None

    def _get_whisper(self):
        """Lazy load whisper and the model."""
        if self._whisper is None:
            import whisper
            self._whisper = whisper
            logger.info("loading_whisper_model", model=self.model_size)
            self._model = whisper.load_model(self.model_size)
        return self._whisper, self._model

    def _get_file_duration(self, file_path: Path) -> Optional[float]:
        """Get duration of media file in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception as e:
            logger.debug("duration_check_failed", path=str(file_path), error=str(e))

        return None

    def _extract_audio_segment(
        self,
        input_file: Path,
        output_file: Path,
        max_duration: int
    ) -> bool:
        """Extract audio segment from file using ffmpeg.

        Args:
            input_file: Path to input audio/video file
            output_file: Path to output audio file
            max_duration: Maximum duration in seconds

        Returns:
            True if extraction succeeded
        """
        try:
            command = [
                "ffmpeg",
                "-i", str(input_file),
                "-ss", "0",
                "-t", str(max_duration),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # Convert to WAV for Whisper compatibility
                "-ar", "16000",  # 16kHz sample rate (Whisper's native rate)
                "-ac", "1",  # Mono
                "-loglevel", "error",
                "-y",  # Overwrite output
                str(output_file)
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.warning("ffmpeg_extraction_failed",
                             error=result.stderr[:500] if result.stderr else "Unknown error")
                return False

            return output_file.exists() and output_file.stat().st_size > 0

        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg_timeout", path=str(input_file))
            return False
        except FileNotFoundError:
            logger.error("ffmpeg_not_found")
            return False
        except Exception as e:
            logger.error("audio_extraction_failed", path=str(input_file), error=str(e))
            return False

    def transcribe(self, file_obj: FileObject) -> FileObject:
        """Transcribe audio/video file.

        Extracts first 10 minutes of audio and transcribes using Whisper.
        Updates file_obj with transcription and related metadata.

        Args:
            file_obj: FileObject representing audio/video file

        Returns:
            FileObject with transcription populated
        """
        file_path = Path(file_obj.path)

        if not file_path.exists():
            logger.warning("media_file_not_found", path=str(file_path))
            file_obj.transcription = None
            file_obj.extraction_error = "Media file not found"
            return file_obj

        ext = file_path.suffix.lower().lstrip(".")
        if ext not in AUDIO_EXTENSIONS + VIDEO_EXTENSIONS:
            logger.debug("unsupported_media_format", extension=ext)
            file_obj.transcription = None
            return file_obj

        # Check file duration
        file_duration = self._get_file_duration(file_path)
        if file_duration is not None and file_duration < 1:
            logger.debug("file_too_short", path=str(file_path), duration=file_duration)
            file_obj.transcription = "[Audio too short to transcribe]"
            file_obj.transcription_duration = file_duration
            return file_obj

        # Determine actual duration to transcribe
        if file_duration:
            transcribe_duration = min(self.max_duration, file_duration)
        else:
            transcribe_duration = self.max_duration

        temp_audio_path = None
        try:
            # Create temp file for extracted audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_audio_path = Path(tmp.name)

            # Extract audio segment
            logger.info("extracting_audio",
                       filename=file_obj.filename,
                       duration=transcribe_duration)

            extract_ok = self._extract_audio_segment(
                file_path, temp_audio_path, int(transcribe_duration)
            )
            if not extract_ok:
                file_obj.transcription = None
                file_obj.extraction_error = "Audio extraction failed"
                return file_obj

            # Transcribe with Whisper
            logger.info("transcribing", filename=file_obj.filename)
            whisper, model = self._get_whisper()

            result = model.transcribe(
                str(temp_audio_path),
                language=None,  # Auto-detect language
                task="transcribe"
            )

            transcription_text = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")

            if transcription_text:
                file_obj.transcription = transcription_text
                file_obj.transcription_duration = transcribe_duration
                file_obj.content_preview = self._truncate_for_preview(transcription_text)

                # Store language in metadata
                if file_obj.metadata is None:
                    file_obj.metadata = {}
                file_obj.metadata["transcription_language"] = detected_language
                file_obj.metadata["transcription_model"] = f"whisper-{self.model_size}"

                logger.info("transcription_complete",
                           filename=file_obj.filename,
                           language=detected_language,
                           chars=len(transcription_text))
            else:
                file_obj.transcription = "[No speech detected in audio]"
                file_obj.transcription_duration = transcribe_duration
                file_obj.content_preview = file_obj.transcription

        except Exception as e:
            logger.error("transcription_failed", filename=file_obj.filename, error=str(e))
            file_obj.transcription = None
            file_obj.extraction_error = f"Transcription failed: {str(e)[:200]}"

        finally:
            # Cleanup temp file
            if temp_audio_path and temp_audio_path.exists():
                try:
                    os.unlink(temp_audio_path)
                except Exception:
                    pass

        return file_obj

    def _truncate_for_preview(self, text: str, max_lines: int = 50) -> str:
        """Truncate transcription to first N lines for content preview."""
        lines = text.split('\n')
        if len(lines) <= max_lines:
            return text

        truncated = '\n'.join(lines[:max_lines])
        return truncated + f"\n... [truncated, {len(lines) - max_lines} more lines]"
