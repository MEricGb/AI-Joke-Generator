"""
Speech-to-Text Engine Module.

Handles microphone input and speech recognition using SpeechRecognition library.

Requirements:
- macOS: brew install portaudio && pip install pyaudio
- Linux: sudo apt-get install portaudio19-dev && pip install pyaudio
- Windows: pip install pyaudio (usually works directly)
"""

import threading
from typing import Optional, Callable

# Check for required dependencies
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class STTEngineError(Exception):
    """Custom exception for STT errors."""
    pass


class STTEngine:
    """
    Speech-to-Text engine using SpeechRecognition.

    Attributes:
        recognizer: SpeechRecognition Recognizer instance
        microphone: Microphone instance
        is_listening: Whether currently recording
    """

    def __init__(self):
        """Initialize the STT engine."""
        # Check dependencies first
        if not SPEECH_RECOGNITION_AVAILABLE:
            raise STTEngineError(
                "SpeechRecognition not installed.\n"
                "Install with: pip install SpeechRecognition"
            )

        if not PYAUDIO_AVAILABLE:
            raise STTEngineError(
                "PyAudio not installed (required for microphone).\n"
                "Install with:\n"
                "  macOS: brew install portaudio && pip install pyaudio\n"
                "  Linux: sudo apt-get install portaudio19-dev && pip install pyaudio\n"
                "  Windows: pip install pyaudio"
            )

        self.recognizer = sr.Recognizer()
        self.microphone: Optional[sr.Microphone] = None
        self.is_listening = False
        self._stop_listening = None

        # Adjust for ambient noise sensitivity
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        self._check_microphone()

    def _check_microphone(self) -> None:
        """Check if microphone is available."""
        try:
            with sr.Microphone() as mic:
                # Quick test
                pass
            self.microphone = True
        except OSError as e:
            raise STTEngineError(
                f"No microphone found: {e}\n"
                "Make sure a microphone is connected."
            )
        except Exception as e:
            raise STTEngineError(f"Microphone error: {e}")

    def listen(
        self,
        timeout: float = 5.0,
        phrase_time_limit: float = 10.0,
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Listen for speech and transcribe it.

        Args:
            timeout: Max seconds to wait for speech to start
            phrase_time_limit: Max seconds for the phrase
            on_result: Callback with transcribed text
            on_error: Callback with error message
        """
        if self.is_listening:
            return

        def _listen_thread():
            self.is_listening = True
            try:
                with sr.Microphone() as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                    # Listen for audio
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )

                # Transcribe using Google's free API
                text = self.recognizer.recognize_google(audio)

                if on_result and text:
                    on_result(text)

            except sr.WaitTimeoutError:
                if on_error:
                    on_error("No speech detected. Try again.")
            except sr.UnknownValueError:
                if on_error:
                    on_error("Could not understand audio. Speak clearly.")
            except sr.RequestError as e:
                if on_error:
                    on_error(f"Speech service error: {e}")
            except Exception as e:
                if on_error:
                    on_error(f"Error: {str(e)}")
            finally:
                self.is_listening = False

        thread = threading.Thread(target=_listen_thread, daemon=True)
        thread.start()

    def stop(self) -> None:
        """Stop listening."""
        self.is_listening = False


def create_stt_engine() -> Optional[STTEngine]:
    """Factory function to create an STT engine instance."""
    try:
        return STTEngine()
    except STTEngineError as e:
        print(f"Warning: {e}")
        return None
