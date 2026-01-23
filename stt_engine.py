# Speech-to-Text using SpeechRecognition (requires pyaudio)

import threading

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    sr = None

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class STTEngineError(Exception):
    pass


class STTEngine:

    def __init__(self):
        if not SR_AVAILABLE:
            raise STTEngineError("SpeechRecognition not installed. Run: pip install SpeechRecognition")

        if not PYAUDIO_AVAILABLE:
            raise STTEngineError(
                "PyAudio not installed.\n"
                "macOS: brew install portaudio && pip install pyaudio\n"
                "Linux: sudo apt install portaudio19-dev && pip install pyaudio\n"
                "Windows: pip install pyaudio"
            )

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.is_listening = False

        # Test microphone access
        try:
            with sr.Microphone():
                pass
        except OSError as e:
            raise STTEngineError(f"No microphone found: {e}")

    def listen(self, timeout=5.0, phrase_time_limit=10.0, on_result=None, on_error=None):
        if self.is_listening:
            return

        def _listen():
            self.is_listening = True
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

                text = self.recognizer.recognize_google(audio)
                if on_result and text:
                    on_result(text)

            except sr.WaitTimeoutError:
                if on_error:
                    on_error("No speech detected. Try again.")
            except sr.UnknownValueError:
                if on_error:
                    on_error("Could not understand audio.")
            except sr.RequestError as e:
                if on_error:
                    on_error(f"Speech service error: {e}")
            except Exception as e:
                if on_error:
                    on_error(str(e))
            finally:
                self.is_listening = False

        threading.Thread(target=_listen, daemon=True).start()

    def stop(self):
        self.is_listening = False
