import os
import sys
import tempfile
import threading
import subprocess
from gtts import gTTS
from . import config


class TTSEngineError(Exception):
    pass


class TTSEngine:

    def __init__(self):
        self.language = "en"
        self.is_playing = False
        self.temp_file = None
        self._process = None
        self._stop_flag = False

    def set_language(self, language: str):
        self.language = config.TTS_LANGUAGES.get(language, "en")

    def play(self, text: str, on_complete=None) -> bool:
        self.stop()

        if not text or not text.strip():
            raise TTSEngineError("Cannot convert empty text.")

        try:
            # Generate audio
            tts = gTTS(text=text, lang=self.language, slow=False)
            self._cleanup_temp()
            self.temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
            tts.save(self.temp_file)

            # Play in background
            self._stop_flag = False
            self.is_playing = True

            def play_audio():
                try:
                    cmd = self._get_player_cmd()
                    self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._process.wait()
                except Exception:
                    pass
                finally:
                    self.is_playing = False
                    self._process = None
                    if not self._stop_flag and on_complete:
                        on_complete()

            threading.Thread(target=play_audio, daemon=True).start()
            return True

        except Exception as e:
            raise TTSEngineError(f"TTS failed: {e}")

    def _get_player_cmd(self) -> list:
        if sys.platform == "darwin":
            return ["afplay", self.temp_file]
        elif sys.platform == "win32":
            return ["powershell", "-c", f"(New-Object Media.SoundPlayer '{self.temp_file}').PlaySync()"]
        return ["mpg123", "-q", self.temp_file]

    def stop(self):
        self._stop_flag = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self.is_playing = False
        self._process = None

    def _cleanup_temp(self):
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except OSError:
                pass
            self.temp_file = None

    def cleanup(self):
        self.stop()
        self._cleanup_temp()
