import os
import sys
import tempfile
import threading
import subprocess
import time
from typing import Optional, Callable
from gtts import gTTS
import config


class TTSEngineError(Exception):
    """Custom exception for TTS engine errors."""
    pass


class TTSEngine:
    """
    Text-to-Speech engine using gTTS.

    Converts text to speech and manages audio playback using system player.

    Attributes:
        current_language: Current language code for TTS
        is_playing: Whether audio is currently playing
        temp_file: Path to temporary audio file
    """

    def __init__(self):
        """Initialize the TTS engine."""
        self.current_language = "en"
        self.is_playing = False
        self.temp_file = None
        self._playback_thread = None
        self._stop_flag = False
        self._process: Optional[subprocess.Popen] = None

    def set_language(self, language: str) -> None:
        """
        Set the TTS language.

        Args:
            language: Language name ("English" or "Romanian")
        """
        if language in config.TTS_LANGUAGES:
            self.current_language = config.TTS_LANGUAGES[language]
        else:
            self.current_language = "en"

    def text_to_speech(
        self,
        text: str,
        language: Optional[str] = None
    ) -> str:
        """
        Convert text to speech and save to a temporary file.

        Args:
            text: Text to convert to speech
            language: Optional language override (language name, not code)

        Returns:
            Path to the generated audio file

        Raises:
            TTSEngineError: If conversion fails
        """
        if not text or not text.strip():
            raise TTSEngineError("Cannot convert empty text to speech.")

        # Use provided language or current language
        lang_code = self.current_language
        if language and language in config.TTS_LANGUAGES:
            lang_code = config.TTS_LANGUAGES[language]

        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=lang_code, slow=False)

            # Create temporary file
            self._cleanup_temp_file()
            self.temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            ).name

            # Save audio to file
            tts.save(self.temp_file)

            return self.temp_file

        except Exception as e:
            raise TTSEngineError(f"Failed to convert text to speech: {e}")

    def _get_player_command(self, filepath: str) -> list:
        """
        Get the appropriate audio player command for the current OS.

        Args:
            filepath: Path to the audio file

        Returns:
            Command list for subprocess
        """
        if sys.platform == "darwin":  # macOS
            return ["afplay", filepath]
        elif sys.platform == "win32":  # Windows
            return ["powershell", "-c", f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"]
        else:  # Linux
            # Try mpg123 first, fallback to ffplay
            return ["mpg123", "-q", filepath]

    def play(
        self,
        text: Optional[str] = None,
        language: Optional[str] = None,
        on_complete: Optional[Callable] = None
    ) -> bool:
        """
        Play text as speech.

        If text is provided, converts it first. Otherwise plays the last
        converted audio file.

        Args:
            text: Optional text to convert and play
            language: Optional language for conversion
            on_complete: Optional callback when playback completes

        Returns:
            True if playback started successfully
        """
        # Stop any current playback
        self.stop()

        try:
            # Convert text if provided
            if text:
                self.text_to_speech(text, language)

            if not self.temp_file or not os.path.exists(self.temp_file):
                raise TTSEngineError("No audio file to play. Convert text first.")

            # Get player command
            cmd = self._get_player_command(self.temp_file)

            # Start playback in background
            self._stop_flag = False
            self.is_playing = True

            def play_audio():
                try:
                    self._process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self._process.wait()
                except Exception:
                    pass
                finally:
                    self.is_playing = False
                    self._process = None
                    if not self._stop_flag and on_complete:
                        on_complete()

            self._playback_thread = threading.Thread(target=play_audio, daemon=True)
            self._playback_thread.start()

            return True

        except TTSEngineError:
            raise
        except Exception as e:
            raise TTSEngineError(f"Failed to play audio: {e}")

    def stop(self) -> None:
        """Stop current playback."""
        self._stop_flag = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self.is_playing = False
        self._process = None

    def is_busy(self) -> bool:
        """Check if audio is currently playing."""
        return self.is_playing and self._process is not None and self._process.poll() is None

    def _cleanup_temp_file(self) -> None:
        """Remove temporary audio file if it exists."""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except OSError:
                pass
            self.temp_file = None

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        self._cleanup_temp_file()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Global TTS engine instance
_engine_instance: Optional[TTSEngine] = None


def get_engine() -> TTSEngine:
    """
    Get the global TTS engine instance.

    Creates a new instance if one doesn't exist.

    Returns:
        TTSEngine instance
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TTSEngine()
    return _engine_instance


def speak(text: str, language: str = "English") -> bool:
    """
    Convenience function to speak text.

    Args:
        text: Text to speak
        language: Language name ("English" or "Romanian")

    Returns:
        True if started successfully
    """
    engine = get_engine()
    engine.set_language(language)
    return engine.play(text)


def stop_speaking() -> None:
    """Stop any current speech."""
    global _engine_instance
    if _engine_instance:
        _engine_instance.stop()


def is_speaking() -> bool:
    """Check if currently speaking."""
    global _engine_instance
    if _engine_instance:
        return _engine_instance.is_busy()
    return False


def cleanup_tts() -> None:
    """Clean up TTS resources."""
    global _engine_instance
    if _engine_instance:
        _engine_instance.cleanup()
        _engine_instance = None
