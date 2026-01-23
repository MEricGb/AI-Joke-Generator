# Partea ta: TTS Engine + STT Engine

Tu ești responsabil de cele două **motoare audio** ale aplicației:
- **tts_engine.py** — Text-to-Speech (convertește text în voce)
- **stt_engine.py** — Speech-to-Text (convertește voce în text)

Aceste fișiere sunt **self-contained** (funcționează independent) și sunt apelate din GUI.

---

## Concepte cheie

### Threading (fire de execuție)

Operațiile audio (înregistrare, redare) sunt lente. Dacă ar rula pe thread-ul principal, interfața s-ar bloca. De aceea rulează pe **thread-uri daemon**:

```python
threading.Thread(target=play_audio, daemon=True).start()
```

- `target` = funcția care rulează pe thread-ul nou
- `daemon=True` = thread-ul se oprește automat la închiderea aplicației
- `.start()` = pornește execuția

### Subprocess

TTS-ul generează un fișier MP3, apoi folosește un **program extern** (afplay, mpg123) pentru redare:

```python
self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
self._process.wait()  # Așteaptă să se termine redarea
```

- `Popen` = pornește un proces extern
- `DEVNULL` = ignoră output-ul procesului
- `.wait()` = blochează thread-ul curent până se termină procesul
- `.terminate()` = oprește procesul forțat

### Callbacks

Funcții transmise ca parametri, apelate când o operație se termină:

```python
# Redarea s-a terminat → apelează on_complete
if not self._stop_flag and on_complete:
    on_complete()
```

---

## Fișierul 1: tts_engine.py (91 linii)

Convertește text în vorbire folosind Google gTTS.

### Fluxul complet

```
text → gTTS generează MP3 → salvat în fișier temporar → player audio → sunet
```

### Importuri (liniile 1-7)

```python
import os           # Operații cu fișiere (exists, remove)
import sys          # Detectare platformă (darwin/win32/linux)
import tempfile     # Fișiere temporare
import threading    # Thread-uri
import subprocess   # Pornire procese externe (afplay, mpg123)
from gtts import gTTS   # Google Text-to-Speech
import config       # Setări (limbile suportate)
```

### Clasa TTSEngineError (linia 10)

```python
class TTSEngineError(Exception):
    pass
```

Excepție custom. GUI-ul o prinde cu `try/except TTSEngineError`.

### __init__() (liniile 16-21)

```python
def __init__(self):
    self.language = "en"        # Limba implicită
    self.is_playing = False     # Se redă audio acum?
    self.temp_file = None       # Calea fișierului MP3 temporar
    self._process = None        # Procesul audio (subprocess)
    self._stop_flag = False     # Flag pentru oprire manuală
```

**Nu face validări** — dacă gTTS nu e instalat, `from gtts import gTTS` eșuează la import, iar GUI-ul prinde eroarea la `_init_services()`.

### set_language() (liniile 23-24)

```python
def set_language(self, language: str):
    # "English" → "en", "Romanian" → "ro"
    self.language = config.TTS_LANGUAGES.get(language, "en")
```

Simplu: convertește numele limbii în cod ISO.

### play() — Metoda principală (liniile 26-60)

```python
def play(self, text: str, on_complete=None) -> bool:
    self.stop()  # Oprește orice redare anterioară

    if not text or not text.strip():
        raise TTSEngineError("Cannot convert empty text.")

    try:
        # 1. Generare audio
        tts = gTTS(text=text, lang=self.language, slow=False)

        # 2. Salvare în fișier temporar
        self._cleanup_temp()  # Șterge fișierul anterior
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        tts.save(self.temp_file)

        # 3. Redare în background
        self._stop_flag = False
        self.is_playing = True

        def play_audio():
            try:
                cmd = self._get_player_cmd()  # Comandă specifică OS-ului
                self._process = subprocess.Popen(cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
                self._process.wait()  # Blochează ACEST thread până se termină
            except Exception:
                pass
            finally:
                self.is_playing = False
                self._process = None
                # Apelează callback-ul DOAR dacă nu a fost oprit manual
                if not self._stop_flag and on_complete:
                    on_complete()

        threading.Thread(target=play_audio, daemon=True).start()
        return True

    except Exception as e:
        raise TTSEngineError(f"TTS failed: {e}")
```

**Pas cu pas:**
1. `stop()` — oprește orice redare în curs
2. `gTTS(text, lang)` — trimite textul la Google și primește audio
3. `NamedTemporaryFile(suffix=".mp3", delete=False)` — creează fișier temporar care NU se șterge automat
4. `tts.save(self.temp_file)` — salvează audio-ul în fișier
5. Pornește thread nou care:
   - Detectează comanda audio a platformei
   - Pornește procesul extern
   - Așteaptă să se termine
   - Apelează `on_complete` când e gata

**`delete=False`** — Fișierul temporar nu se șterge singur. Noi îl ștergem manual cu `_cleanup_temp()`.

**`self._stop_flag`** — Dacă utilizatorul apasă "Stop", flag-ul devine True. La final, `on_complete` NU se apelează (pentru că utilizatorul a oprit intenționat).

### _get_player_cmd() (liniile 62-67)

```python
def _get_player_cmd(self) -> list:
    if sys.platform == "darwin":       # macOS
        return ["afplay", self.temp_file]
    elif sys.platform == "win32":      # Windows
        return ["powershell", "-c",
                f"(New-Object Media.SoundPlayer '{self.temp_file}').PlaySync()"]
    return ["mpg123", "-q", self.temp_file]  # Linux (necesită mpg123 instalat)
```

Fiecare OS are alt player audio. `afplay` e preinstalat pe macOS, `mpg123` trebuie instalat pe Linux.

### stop() (liniile 69-78)

```python
def stop(self):
    self._stop_flag = True  # Semnalizează că a fost oprit manual

    if self._process and self._process.poll() is None:  # Procesul încă rulează?
        self._process.terminate()  # Trimite SIGTERM
        try:
            self._process.wait(timeout=1)  # Așteaptă max 1 sec
        except subprocess.TimeoutExpired:
            self._process.kill()  # Forțează oprirea (SIGKILL)

    self.is_playing = False
    self._process = None
```

**`poll()`** — Returnează None dacă procesul încă rulează, sau exit code-ul dacă s-a terminat.

**`terminate()` vs `kill()`** — terminate trimite semnal politicos (procesul poate face cleanup). kill oprește imediat, fără posibilitate de intervenție.

### _cleanup_temp() și cleanup() (liniile 80-90)

```python
def _cleanup_temp(self):
    if self.temp_file and os.path.exists(self.temp_file):
        try:
            os.remove(self.temp_file)  # Șterge fișierul MP3
        except OSError:
            pass  # Ignoră dacă nu poate șterge (ex: fișier încă folosit)
        self.temp_file = None

def cleanup(self):
    self.stop()            # Oprește redarea
    self._cleanup_temp()   # Șterge fișierul temporar
```

`cleanup()` e apelat de GUI la închiderea aplicației (`_on_close()`).

---

## Fișierul 2: stt_engine.py (84 linii)

Convertește vorbire (microfon) în text folosind SpeechRecognition + Google Speech API.

### Fluxul complet

```
microfon → calibrare zgomot → înregistrare → Google Speech API → text
```

### Importuri cu verificare (liniile 1-16)

```python
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
```

**De ce try/except la import?** Aceste biblioteci sunt opționale. Dacă nu sunt instalate, aplicația funcționează fără voice input (butonul e dezactivat).

**`SR_AVAILABLE` / `PYAUDIO_AVAILABLE`** — Flag-uri booleene verificate în `__init__()`.

### __init__() — Validare completă (liniile 25-48)

```python
def __init__(self):
    # Verificare 1: SpeechRecognition instalat?
    if not SR_AVAILABLE:
        raise STTEngineError("SpeechRecognition not installed. Run: pip install SpeechRecognition")

    # Verificare 2: PyAudio instalat?
    if not PYAUDIO_AVAILABLE:
        raise STTEngineError(
            "PyAudio not installed.\n"
            "macOS: brew install portaudio && pip install pyaudio\n"
            "Linux: sudo apt install portaudio19-dev && pip install pyaudio\n"
            "Windows: pip install pyaudio")

    # Configurare recognizer
    self.recognizer = sr.Recognizer()
    self.recognizer.energy_threshold = 300          # Nivel minim sunet (sub = ignorat)
    self.recognizer.dynamic_energy_threshold = True  # Se adaptează la zgomot
    self.recognizer.pause_threshold = 0.8            # 0.8 sec tăcere = sfârșit frază
    self.is_listening = False

    # Verificare 3: Microfonul funcționează?
    try:
        with sr.Microphone():
            pass  # Doar testăm că se poate deschide
    except OSError as e:
        raise STTEngineError(f"No microphone found: {e}")
```

**`energy_threshold = 300`** — Sunetele cu energie sub 300 sunt considerate tăcere. Previne detectarea zgomotului de fundal ca vorbire.

**`dynamic_energy_threshold = True`** — Ajustează threshold-ul automat bazat pe zgomotul ambiant. Util în medii zgomotoase.

**`pause_threshold = 0.8`** — Dacă 0.8 secunde trec fără vorbire, consideră că fraza s-a terminat.

### listen() — Înregistrare și recunoaștere (liniile 50-80)

```python
def listen(self, timeout=5.0, phrase_time_limit=10.0, on_result=None, on_error=None):
    if self.is_listening:
        return  # Nu permite ascultare multiplă simultană

    def _listen():
        self.is_listening = True
        try:
            with sr.Microphone() as source:
                # Calibrare: "ascultă" 0.5 sec de zgomot ambiant
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Înregistrare
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,               # Max sec așteptare pentru vorbire
                    phrase_time_limit=phrase_time_limit)  # Max sec de înregistrare

            # Trimite audio-ul la Google Speech API
            text = self.recognizer.recognize_google(audio)

            if on_result and text:
                on_result(text)  # Callback cu textul recunoscut

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
            self.is_listening = False  # MEREU resetează la final

    threading.Thread(target=_listen, daemon=True).start()
```

**Parametrii:**
- `timeout=5.0` — Așteaptă maxim 5 secunde ca utilizatorul să înceapă să vorbească. Dacă nu detectează sunet → `WaitTimeoutError`.
- `phrase_time_limit=10.0` — Înregistrează maxim 10 secunde. Previne înregistrări infinite.
- `on_result` — Funcție apelată cu textul recunoscut (la succes)
- `on_error` — Funcție apelată cu mesajul de eroare (la eșec)

**`adjust_for_ambient_noise(source, duration=0.5)`** — Ascultă 0.5 secunde de "tăcere" pentru a calibra threshold-ul. De asta GUI-ul afișează "Calibrating..." înainte de "Speak now".

**`recognize_google(audio)`** — Trimite audio-ul la Google Speech-to-Text API (gratuit, fără cheie API, dar necesită internet).

**Erorile posibile:**
- `WaitTimeoutError` — Nu s-a detectat sunet în `timeout` secunde
- `UnknownValueError` — S-a detectat sunet dar nu s-a putut transcrie (vorbire neclară, altă limbă)
- `RequestError` — Eroare de rețea / API Google indisponibil

### stop() (liniile 82-83)

```python
def stop(self):
    self.is_listening = False
```

Simplu: setează flag-ul. Thread-ul `_listen()` verifică acest flag prin `finally:`.

---

## Cum sunt apelate din GUI

### TTS (citit cu voce):

```python
# gui.py → _speak_jokes()
text = utils.format_jokes_for_tts(self.current_jokes)  # Formatează pentru voce
self.tts_engine.set_language(self.current_language)      # Setează limba
self.tts_engine.play(text, on_complete=lambda: self.root.after(0, self._on_speech_complete))
```

### STT (input vocal):

```python
# gui.py → _start_recording()
self.stt_engine.listen(
    timeout=8.0,
    phrase_time_limit=15.0,
    on_result=lambda text: self.root.after(0, lambda: self._on_stt_result(text)),
    on_error=lambda err: self.root.after(0, lambda: self._on_stt_error(err))
)
```

---

## Diagrama interacțiunii

```
┌──────────────────────────────────────────────────────┐
│                      GUI                             │
│                                                      │
│  [Read Aloud] ──► tts_engine.play(text, callback)    │
│                       │                              │
│                       ▼                              │
│                  gTTS → MP3 → afplay/mpg123          │
│                       │                              │
│                       ▼                              │
│               callback → UI update                   │
│                                                      │
│  [Voice Input] ──► stt_engine.listen(callbacks)      │
│                       │                              │
│                       ▼                              │
│               Microphone → Google API → text         │
│                       │                              │
│                       ▼                              │
│               on_result(text) → UI update            │
│                                                      │
│  [Stop] ──► tts_engine.stop()                        │
│                  └─► process.terminate()             │
└──────────────────────────────────────────────────────┘
```

---

## Întrebări de verificare

1. De ce `play()` apelează `self.stop()` la început?
2. Ce se întâmplă dacă utilizatorul apasă "Stop" în timpul redării? Urmărește flag-ul `_stop_flag`.
3. De ce `_cleanup_temp()` are `try/except OSError`?
4. Care e diferența dintre `terminate()` și `kill()` pentru un subprocess?
5. Ce face `adjust_for_ambient_noise()` și de ce durează 0.5 secunde?
6. Ce se întâmplă dacă utilizatorul nu vorbește deloc în timpul `listen()`?
7. De ce callback-urile `on_result`/`on_error` folosesc `root.after(0, ...)` în GUI?
8. Ce e un "daemon thread" și de ce e important aici?
