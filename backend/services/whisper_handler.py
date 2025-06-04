"""
Whisper voice-to-text integration service for the Voice Agent backend.
"""

import os
import io
import tempfile
import logging
from typing import Optional, Iterator
from openai import OpenAI
from pydub import AudioSegment


class WhisperHandler:
    """Handles OpenAI Whisper voice-to-text transcription."""

    def __init__(self, logger=None):
        """Initialize the Whisper handler."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=self.api_key)
        self.logger = logger or logging.getLogger(__name__)

        # Whisper configuration
        self.model = "whisper-1"
        self.language = "en"  # Can be made configurable
        self.response_format = "text"  # or "json" for detailed response

        # Audio processing settings
        self.target_sample_rate = 16000  # Whisper optimal sample rate
        self.max_file_size = 25 * 1024 * 1024  # 25MB limit for Whisper API
        self.supported_formats = ["wav", "mp3", "m4a", "flac", "ogg", "webm"]

    def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: Optional[str] = None,
    ) -> str:
        """
        Transcribe audio data using OpenAI Whisper.

        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (wav, mp3, etc.)
            language: Language code (optional, auto-detect if None)

        Returns:
            Transcribed text string

        Raises:
            ValueError: If audio format is unsupported or data is invalid
            Exception: If transcription fails
        """
        try:
            self.logger.info(
                f"Starting transcription of {len(audio_data)} bytes ({audio_format})"
            )

            # Validate input
            if not audio_data:
                raise ValueError("Empty audio data provided")

            if audio_format.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported audio format: {audio_format}")

            if len(audio_data) > self.max_file_size:
                raise ValueError(
                    f"Audio file too large: {len(audio_data)} bytes (max: {self.max_file_size})"
                )

            # Process audio if needed
            processed_audio = self._preprocess_audio(audio_data, audio_format)

            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}", delete=False
            ) as temp_file:
                temp_file.write(processed_audio)
                temp_file_path = temp_file.name

            try:
                # Transcribe using OpenAI Whisper
                with open(temp_file_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language or self.language,
                        response_format=self.response_format,
                    )

                # Extract text from response
                if isinstance(transcript, str):
                    transcribed_text = transcript
                else:
                    transcribed_text = (
                        transcript.text
                        if hasattr(transcript, "text")
                        else str(transcript)
                    )

                self.logger.info(
                    f"Transcription successful: '{transcribed_text[:100]}...'"
                )
                return transcribed_text.strip()

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}", exc_info=True)
            raise

    def transcribe_audio_chunks(
        self, audio_chunks: Iterator[bytes], audio_format: str = "wav"
    ) -> Iterator[str]:
        """
        Transcribe audio chunks for streaming/real-time processing.

        Args:
            audio_chunks: Iterator of audio byte chunks
            audio_format: Audio format

        Yields:
            Transcribed text for each chunk
        """
        chunk_count = 0

        for chunk in audio_chunks:
            try:
                chunk_count += 1
                self.logger.debug(
                    f"Processing audio chunk {chunk_count}: {len(chunk)} bytes"
                )

                if len(chunk) < 1024:  # Skip very small chunks
                    self.logger.debug(f"Skipping small chunk {chunk_count}")
                    continue

                transcription = self.transcribe_audio(chunk, audio_format)

                if transcription:
                    self.logger.info(
                        f"Chunk {chunk_count} transcription: '{transcription}'"
                    )
                    yield transcription

            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk_count}: {e}")
                # Continue with next chunk instead of failing completely
                continue

    def _preprocess_audio(self, audio_data: bytes, audio_format: str) -> bytes:
        """
        Preprocess audio for optimal Whisper performance.

        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format

        Returns:
            Processed audio bytes
        """
        try:
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)

            # Convert to optimal format for Whisper
            # - Mono channel
            # - 16kHz sample rate
            # - WAV format
            if audio.channels > 1:
                audio = audio.set_channels(1)
                self.logger.debug("Converted to mono")

            if audio.frame_rate != self.target_sample_rate:
                audio = audio.set_frame_rate(self.target_sample_rate)
                self.logger.debug(f"Resampled to {self.target_sample_rate}Hz")

            # Export as WAV
            output_buffer = io.BytesIO()
            audio.export(output_buffer, format="wav")
            processed_data = output_buffer.getvalue()

            self.logger.debug(
                f"Preprocessed audio: {len(audio_data)} -> {len(processed_data)} bytes"
            )
            return processed_data

        except Exception as e:
            self.logger.warning(f"Audio preprocessing failed, using original: {e}")
            return audio_data

    def validate_audio_format(self, audio_data: bytes) -> bool:
        """
        Validate if audio data is in a supported format.

        Args:
            audio_data: Raw audio bytes

        Returns:
            True if format is valid and supported
        """
        try:
            # Try to load with pydub to validate format
            AudioSegment.from_file(io.BytesIO(audio_data))
            return True
        except Exception as e:
            self.logger.debug(f"Audio format validation failed: {e}")
            return False

    def get_audio_info(self, audio_data: bytes, audio_format: str) -> dict:
        """
        Get information about audio data.

        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format

        Returns:
            Dictionary with audio information
        """
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)

            return {
                "duration_seconds": len(audio) / 1000.0,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "frame_count": audio.frame_count(),
                "size_bytes": len(audio_data),
                "format": audio_format,
            }
        except Exception as e:
            self.logger.error(f"Failed to get audio info: {e}")
            return {"error": str(e)}


# Factory function for easy instantiation
def create_whisper_handler(logger=None) -> WhisperHandler:
    """Create a WhisperHandler instance with error handling."""
    try:
        return WhisperHandler(logger)
    except ValueError as e:
        if logger:
            logger.error(f"Failed to create WhisperHandler: {e}")
        raise


# For standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)

    try:
        # Test the whisper handler
        handler = create_whisper_handler(logger)

        # Test with a simple WAV file (you would need to provide actual audio data)
        logger.info("WhisperHandler created successfully")
        logger.info("To test transcription, provide actual audio data")

        # Example of how to use:
        # with open('test_audio.wav', 'rb') as f:
        #     audio_data = f.read()
        #     transcription = handler.transcribe_audio(audio_data, 'wav')
        #     print(f"Transcription: {transcription}")

    except Exception as e:
        logger.error(f"Error in standalone test: {e}", exc_info=True)
