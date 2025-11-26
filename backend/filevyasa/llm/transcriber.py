"""Audio/Video transcription using OpenAI Whisper."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import structlog

from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


class Transcriber:
    """Transcribe audio/video files using OpenAI Whisper.

    Extracts the first 10 minutes of audio and transcribes using the 'base' Whisper model.
    """

    MODEL_SIZE = "base"
    MAX_DURATION_SECONDS = 600  # 10 minutes

    AUDIO_EXTENSIONS = ["mp3", "wav", "m4a", "flac", "aac", "ogg", "wma"]
    VIDEO_EXTENSIONS = ["mp4", "mov", "avi", "mkv", "wmv", "flv", "m4v", "webm"]

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
        if ext not in self.AUDIO_EXTENSIONS + self.VIDEO_EXTENSIONS:
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
