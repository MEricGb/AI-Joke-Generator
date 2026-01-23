# AI Joke Generator

O aplicație desktop care generează glume folosind un LLM local (Ollama), cu suport pentru text-to-speech (citit cu voce) și voice input (dictare vocală). Interfața este construită cu Tkinter într-un dark theme modern.

## Cerințe

- Python 3.9+
- [Ollama](https://ollama.ai) rulând local
- Un model descărcat (implicit: `llama3.2`)

## Instalare și rulare

```bash
# Creează un virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalează dependențele
pip install requests gtts python-dotenv SpeechRecognition pyaudio

# Descarcă modelul Ollama
ollama pull llama3.2

# Pornește Ollama (dacă nu rulează deja)
ollama serve

# Rulează aplicația
python main.py
```

### Voice Input pe macOS

Pentru a folosi input-ul vocal pe macOS:
```bash
brew install portaudio
pip install pyaudio
```
Acordă permisiune pentru microfon: System Settings → Privacy & Security → Microphone → Terminal.

### Voice Input pe Linux

```bash
sudo apt install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### Voice Input pe Windows

```bash
pip install pyaudio
```
PyAudio se instalează direct; nu necesită dependențe suplimentare.

---

## Structura proiectului

```
.
├── main.py              # Punct de intrare - verificări și lansare
├── gui.py               # Interfața grafică Tkinter (dark theme)
├── config.py            # Setări centralizate (URL, model, limbi, tonuri)
├── prompts.py           # Template-uri de prompt pentru LLM
├── joke_generator.py    # Integrare cu API-ul Ollama
├── text_processing.py   # Analiză text (limbă, keywords, statistici)
├── tts_engine.py        # Text-to-Speech cu gTTS
├── stt_engine.py        # Speech-to-Text cu SpeechRecognition
├── utils.py             # Funcții utilitare (validare, formatare, salvare)
└── pyproject.toml       # Configurare pachet și dependențe
```

---

## Fluxul de date al aplicației

```
Utilizatorul introduce un context (text sau voce)
    │
    ▼
Validare input (utils.validate_context)
    │  - verifică lungime 2-500 caractere
    │  - verifică că textul conține litere/cifre
    ▼
Analiză text (text_processing.analyze_input)
    │  - detectează limba (en/ro)
    │  - extrage cuvinte cheie
    │  - calculează statistici
    ▼
Construire prompt (prompts.build)
    │  - asamblează system prompt + ton + exemplu + context
    │  - instrucțiuni stricte de formatare
    ▼
Generare via Ollama API (joke_generator.generate_jokes)
    │  - POST la /api/generate cu model + prompt + parametri
    │  - parsare răspuns în glume individuale
    ▼
Afișare în interfață (gui.py - output_text widget)
    │
    ├──► Opțional: Citit cu voce (tts_engine.play)
    │       - generează MP3 cu gTTS
    │       - redă cu player-ul platformei
    │
    └──► Opțional: Salvare în fișier (utils.save_jokes_to_file)
            - fișier .txt cu header (timestamp, limbă, context)
```

---

## Descriere detaliată a fișierelor

---

### main.py — Punct de intrare

Fișierul care pornește aplicația. Efectuează verificări înainte de a lansa interfața grafică.

| Funcție | Parametri | Returnează | Ce face |
|---------|-----------|------------|---------|
| `check_deps()` | - | `bool` | Încearcă să importe `requests`, `gtts`, `dotenv`. Dacă vreunul lipsește, afișează comanda `pip install` necesară și returnează `False`. |
| `check_ollama()` | - | `bool` | Face un GET la `http://localhost:11434/api/tags`. Dacă primește răspuns, Ollama rulează. Dacă nu, afișează warning dar returnează `True` (aplicația pornește oricum). |
| `main()` | - | `int` (exit code) | 1) Apelează `check_deps()` — dacă eșuează, returnează 1. 2) Apelează `check_ollama()` — doar avertizare. 3) Importă `run_app()` din `gui.py` și o rulează. 4) Prinde `KeyboardInterrupt` pentru ieșire curată. |

**Cum funcționează:** Utilizatorul rulează `python main.py`. Scriptul verifică dependențele, verifică Ollama, apoi lansează fereastra GUI. Dacă dependențele lipsesc, se oprește cu instrucțiuni. Dacă Ollama nu e pornit, permite lansarea dar utilizatorul trebuie să apese "Connect" mai târziu.

---

### config.py — Configurări centralizate

Toate setările aplicației sunt definite aici, într-un singur loc. Încarcă variabile din `.env` (dacă există) prin `python-dotenv`.

| Variabilă | Valoare implicită | Descriere |
|-----------|-------------------|-----------|
| `OLLAMA_BASE_URL` | `"http://localhost:11434"` | Adresa serverului Ollama |
| `OLLAMA_MODEL` | `"llama3.2"` | Modelul LLM folosit pentru generare |
| `REQUEST_TIMEOUT` | `60` | Timeout (secunde) pentru cererile HTTP către Ollama |
| `GENERATION_CONFIG` | `{"temperature": 0.9, "top_p": 0.95, "num_predict": 1024}` | Parametri de generare: temperature controlează creativitatea (0=determinist, 1=maxim creativ), top_p filtrează tokenii improbabili, num_predict limitează lungimea răspunsului |
| `SUPPORTED_LANGUAGES` | `{"English": "en", "Romanian": "ro"}` | Limbile suportate pentru generare |
| `TTS_LANGUAGES` | `{"English": "en", "Romanian": "ro"}` | Limbile suportate pentru sinteză vocală |
| `JOKE_TONES` | `["Clean", "Dark", "Sarcastic"]` | Tonurile disponibile pentru glume |
| `MIN_JOKES` | `1` | Numărul minim de glume |
| `MAX_JOKES` | `10` | Numărul maxim de glume |
| `DEFAULT_JOKES` | `3` | Numărul implicit de glume |

---

### prompts.py — Template-uri pentru LLM

Conține toate prompturile trimise către modelul Ollama. Separat de `config.py` pentru claritate.

**Constante:**

| Constantă | Structură | Descriere |
|-----------|-----------|-----------|
| `SYSTEM` | `{"en": "...", "ro": "..."}` | Prompturi de sistem care definesc personalitatea LLM-ului — un comedian profesionist |
| `TONES` | `{"en": {"Clean": "...", ...}, "ro": {...}}` | Descrieri ale fiecărui ton per limbă. Explică LLM-ului ce stil de umor să folosească. |
| `EXAMPLES` | `{"en": {"Clean": "...", ...}, "ro": {...}}` | Exemple concrete de glume pentru fiecare combinație ton+limbă, ca model de referință |

**Funcția `build()`:**

| Parametru | Tip | Descriere |
|-----------|-----|-----------|
| `context` | `str` | Subiectul/contextul glumelor (ex: "programming", "cats") |
| `num_jokes` | `int` | Câte glume să genereze |
| `language` | `str` | Limba ("en" sau "ro") |
| `tone` | `str` | Tonul ("Clean", "Dark", "Sarcastic") |

**Returnează:** `str` — promptul complet asamblat.

**Ce face:** Validează limba și tonul (fallback la "en"/"Clean" dacă sunt invalide). Asamblează un prompt structurat care conține: system prompt (personalitate) + descriere ton + exemplu de referință + contextul utilizatorului + instrucțiuni stricte de formatare (număr exact de glume, fără introduceri, fără explicații).

---

### joke_generator.py — Comunicare cu Ollama

Gestionează toată comunicarea cu API-ul Ollama pentru a genera glume.

**Clasa `JokeGeneratorError`** — Excepție custom aruncată când Ollama nu e disponibil sau modelul nu există.

**Clasa `JokeGenerator`:**

| Metodă | Parametri | Returnează | Ce face |
|--------|-----------|------------|---------|
| `__init__()` | - | - | Salvează `base_url` și `model` din config. Apelează `_check_ollama()` imediat. Dacă verificarea eșuează, aruncă `JokeGeneratorError`. |
| `_check_ollama()` | - | - | Face GET la `/api/tags` — obține lista modelelor disponibile. Verifică că modelul cerut (ex: `llama3.2`) există în listă. Dacă serverul nu răspunde → eroare cu "Ollama is not running". Dacă modelul nu există → eroare cu "Model X not found, run: ollama pull X". |
| `generate_jokes(context, num_jokes, language, tone)` | `str, int, str, str` | `dict` | **Metoda principală.** 1) Validează că `context` nu e gol. 2) Clampează `num_jokes` între MIN și MAX. 3) Construiește prompt cu `prompts.build()`. 4) Trimite POST la `/api/generate` cu body: `{"model": "...", "prompt": "...", "stream": false, "options": GENERATION_CONFIG}`. 5) Parsează răspunsul. 6) Returnează: `{"success": True/False, "jokes": [...], "raw_response": "...", "error": "..."}`. 7) Trunchiază lista dacă LLM-ul returnează mai multe glume decât cerute. |
| `_parse_jokes(raw_text)` | `str` | `list[str]` | Extrage glumele individuale din textul brut. Împarte după: linii goale, prefixe numerotate (1., 2., etc.), sau liniuțe (-). Filtrează intrările mai scurte de 10 caractere (probabil artefacte). Dacă parsarea nu găsește nimic, returnează textul brut ca o singură glumă. |

**Tratarea erorilor:**
- `ConnectionError` → "Cannot connect to Ollama. Is it running?"
- `Timeout` → "Request timed out. The model might be loading."
- Alte excepții → mesajul erorii originale

---

### text_processing.py — Analiză text

Analizează input-ul utilizatorului pentru a detecta limba, extrage cuvinte cheie și calcula statistici. Rezultatele sunt afișate în secțiunea "Analysis" din GUI.

**Constante:**

| Constantă | Descriere |
|-----------|-----------|
| `STOP_WORDS` | Dicționar cu cuvinte comune ignorate per limbă. En: "the", "and", "is", "a", "to"... Ro: "si", "sau", "dar", "la", "de"... |
| `LANG_PATTERNS` | Cuvinte și caractere indicatoare pentru fiecare limbă. Folosite de `detect_language()`. |

**Funcții:**

| Funcție | Parametri | Returnează | Ce face |
|---------|-----------|------------|---------|
| `tokenize(text)` | `str` | `list[str]` | Transformă textul în lowercase, elimină semnele de punctuație, împarte în cuvinte individuale. Ex: "Hello, World!" → ["hello", "world"] |
| `detect_language(text)` | `str` | `(str, float)` | Tokenizează textul, numără câte cuvinte se potrivesc cu pattern-urile fiecărei limbi. Verifică și caractere speciale românești (ă, î, ț, ș, â). Returnează `("en", 0.85)` sau `("ro", 0.72)`. Dacă niciun pattern nu se potrivește, returnează `("en", 0.0)` (fallback la engleză). |
| `extract_keywords(text, language, top_n)` | `str, str, int` | `list[str]` | Tokenizează, elimină stop words pentru limba detectată, numără frecvența cuvintelor rămase, returnează cele mai frecvente `top_n` cuvinte. Ex: "I love programming and coding" → ["love", "programming", "coding"] |
| `get_text_stats(text)` | `str` | `dict` | Calculează și returnează: `word_count` (nr. total cuvinte), `character_count` (caractere fără spații), `sentence_count` (propoziții — numără `.!?`), `unique_words` (cuvinte distincte), `average_word_length` (lungime medie cuvânt), `detected_language`, `language_confidence`, `keywords` |
| `analyze_input(text)` | `str` | `dict` | Funcția principală de analiză. Verifică dacă textul e valid (non-gol). Returnează: `{"is_valid": bool, "error": str/None, "statistics": dict, "tokens": list, "keywords": list}`. Dacă textul e gol, returnează `is_valid=False` cu mesaj de eroare. |

---

### tts_engine.py — Text-to-Speech (text → voce)

Convertește textul în vorbire folosind serviciul Google gTTS. Generează un fișier MP3 temporar și îl redă cu player-ul audio al sistemului.

**Clasa `TTSEngineError`** — Excepție custom pentru erori TTS (ex: gTTS nu e instalat, player audio nu e găsit).

**Clasa `TTSEngine`:**

| Metodă | Parametri | Returnează | Ce face |
|--------|-----------|------------|---------|
| `__init__()` | - | - | Inițializează: `language="en"`, `is_playing=False`, `temp_file=None`, `process=None`, `stop_flag=False` |
| `set_language(language)` | `str` (ex: "English") | - | Convertește numele limbii în cod (folosind `config.TTS_LANGUAGES`) și actualizează `self.language`. |
| `play(text, on_complete)` | `str, callable/None` | - | **Metoda principală.** 1) Oprește orice redare curentă (`stop()`). 2) Creează obiect `gTTS(text, lang=self.language)`. 3) Salvează într-un fișier `.mp3` temporar. 4) Detectează player-ul audio al platformei. 5) Pornește redarea într-un thread de fundal. 6) Când se termină, apelează `on_complete()` dacă e definit. 7) Dacă apare o eroare, aruncă `TTSEngineError`. |
| `_get_player_cmd()` | - | `list[str]` | Returnează comanda audio specifică OS-ului: macOS → `["afplay", filepath]`, Windows → `["powershell", "-c", "(New-Object Media.SoundPlayer ...).PlaySync()"]`, Linux → `["mpg123", filepath]` |
| `stop()` | - | - | Setează `stop_flag=True`, termină subprocess-ul de redare (`process.terminate()`), resetează starea. |
| `_cleanup_temp()` | - | - | Șterge fișierul MP3 temporar de pe disc (dacă există). |
| `cleanup()` | - | - | Apelează `stop()` apoi `_cleanup_temp()`. Folosită la închiderea aplicației. |

**Flux redare:** `play()` → gTTS generează MP3 → `_get_player_cmd()` → `subprocess.Popen()` → redare audio → `on_complete()` callback → `_cleanup_temp()`

---

### stt_engine.py — Speech-to-Text (voce → text)

Convertește input-ul vocal (microfon) în text folosind biblioteca SpeechRecognition și API-ul Google Speech.

**Clasa `STTEngineError`** — Excepție custom (ex: PyAudio nu e instalat, microfon negăsit).

**Clasa `STTEngine`:**

| Metodă | Parametri | Returnează | Ce face |
|--------|-----------|------------|---------|
| `__init__()` | - | - | **Validare completă:** 1) Verifică `speech_recognition` e instalat. 2) Verifică `pyaudio` e instalat (cu instrucțiuni specifice platformei: `brew install portaudio` pe macOS, `apt install portaudio19-dev` pe Linux). 3) Creează `Recognizer` cu: `energy_threshold=300` (nivel minim de sunet pentru detectare), `dynamic_energy_threshold=True` (se adaptează la zgomotul ambiant), `pause_threshold=0.8` (0.8 sec de tăcere = sfârșit frază). 4) Testează accesul la microfon — dacă nu găsește niciunul, aruncă `STTEngineError`. |
| `listen(timeout, phrase_time_limit, on_result, on_error)` | `float, float, callable, callable` | - | **Înregistrare și recunoaștere:** Rulează într-un thread daemon (nu blochează UI-ul). 1) Deschide microfonul. 2) Ajustează pentru zgomot ambient (0.5 sec de calibrare). 3) Ascultă cu `timeout` (max secunde de așteptare până detectează vorbire) și `phrase_time_limit` (max secunde de înregistrare). 4) Trimite audio-ul la Google Speech API (`recognize_google()`). 5) La succes → apelează `on_result(text_transcris)`. 6) La eroare → apelează `on_error(mesaj_eroare)`. |
| `stop()` | - | - | Setează `is_listening=False` pentru a semnala thread-ului să se oprească. |

**Erori tratate în `listen()`:**
- `WaitTimeoutError` → "Nu s-a detectat vorbire în timpul alocat"
- `UnknownValueError` → "Nu s-a putut înțelege audio-ul"
- `RequestError` → "Eroare la API-ul Google Speech"

---

### utils.py — Funcții utilitare

Funcții helper folosite în mai multe locuri din aplicație.

| Funcție | Parametri | Returnează | Ce face |
|---------|-----------|------------|---------|
| `validate_context(context)` | `str` | `(bool, str)` | Verifică input-ul utilizatorului: 1) Nu e gol (după strip). 2) Între 2 și 500 caractere. 3) Conține cel puțin o literă sau cifră (nu doar simboluri). Returnează `(True, "")` dacă e valid sau `(False, "mesaj_eroare")` dacă nu. |
| `format_jokes_for_display(jokes)` | `list[str]` | `str` | Formatează glumele pentru afișare în GUI. Numerotează fiecare glumă (1., 2., 3...), elimină numerotarea existentă dacă e prezentă, le unește cu linii goale duble (`\n\n`). |
| `format_jokes_for_tts(jokes)` | `list[str]` | `str` | Formatează glumele pentru citit cu voce. Elimină caractere markdown (`*`, `_`, `#`), elimină numerotarea, adaugă prefix "Joke number X." la fiecare, le unește cu " ... " (pauză naturală). |
| `save_jokes_to_file(jokes, filepath, context, language)` | `list[str], str/None, str, str` | `(bool, str)` | Salvează glumele într-un fișier text. Dacă `filepath` nu e dat, generează automat `jokes_YYYYMMDD_HHMMSS.txt`. Scrie header cu: data/ora, limba, contextul original. Apoi scrie fiecare glumă numerotată. Returnează `(True, cale_fișier)` sau `(False, mesaj_eroare)`. |
| `get_language_code(name)` | `str` | `str` | Convertește numele limbii în cod: "English" → "en", "Romanian" → "ro". Folosește mapping-ul din `config.SUPPORTED_LANGUAGES`. |

---

### gui.py — Interfața grafică

Cea mai mare componentă — interfața Tkinter cu dark theme modern.

**Clasa `ModernStyle`** — Constante vizuale:

| Constantă | Valoare | Scop |
|-----------|---------|------|
| `BG_DARK` | `#1a1b26` | Fundal principal al ferestrei |
| `BG_CARD` | `#24283b` | Fundal pentru carduri/secțiuni |
| `BG_INPUT` | `#1f2335` | Fundal pentru câmpuri de input |
| `ACCENT` | `#7aa2f7` | Culoare accent (butoane, link-uri) |
| `SUCCESS` | `#9ece6a` | Verde pentru stări de succes |
| `ERROR` | `#f7768e` | Roșu pentru erori |
| `WARNING` | `#e0af68` | Galben pentru avertismente |
| `TEXT_PRIMARY` | `#c0caf5` | Text principal |
| `TEXT_SECONDARY` | `#565f89` | Text secundar/diminuat |

**Clasa `JokeGeneratorApp`** — Aplicația principală:

| Metodă | Ce face |
|--------|---------|
| `__init__(root)` | Primește fereastra Tk. Apelează setup-ul ferestrei, stilurilor, serviciilor și widgeturilor. |
| `_setup_window()` | Setează dimensiunea 700×800, minimul 600×500, centrează pe ecran, setează titlul și fundalul. |
| `_setup_styles()` | Configurează stilurile ttk: TFrame, TLabel, TButton, TRadiobutton, TCombobox cu culorile din ModernStyle. |
| `_init_services()` | Creează instanțe: `JokeGenerator` (cu try/except — dacă Ollama nu e disponibil, setează `None`), `TTSEngine` (dacă gTTS e instalat), `STTEngine` (dacă PyAudio e instalat). |
| `_create_widgets()` | Creează un Canvas scrollabil cu toate secțiunile UI. Adaugă suport pentru scroll cu rotița mouse-ului. |
| `_create_header()` | Titlul "AI Joke Generator" + subtitlul aplicației. |
| `_create_connection_section()` | Label de status conexiune + buton "Connect to Ollama" + afișare model activ. |
| `_create_input_section()` | Card cu: Text area pentru context (subiectul glumelor) + buton "Voice Input" (dacă STT e disponibil). |
| `_create_options_section()` | Slider pentru nr. glume (1-10) + Radiobuttons pentru limbă (English/Romanian) + Combobox pentru ton (Clean/Dark/Sarcastic) + buton mare "Generate Jokes". |
| `_create_output_section()` | Card cu: Text area read-only pentru afișare glume + rând de butoane: "Read Aloud", "Stop", "Save to File", "Clear". |
| `_create_analysis_section()` | Card cu text area read-only afișând: nr. cuvinte, limba detectată, confidence, cuvinte cheie. |
| `_create_card(title)` | Helper — creează un frame stilizat cu titlu și bordură, returnează frame-ul interior. |
| `_create_footer()` | Label de status în partea de jos a ferestrei (afișează mesaje temporare). |
| `_connect_ollama()` | Handler buton: pornește thread de fundal care creează `JokeGenerator`. La succes actualizează status-ul la verde. La eroare afișează mesajul. |
| `_generate_jokes()` | Handler buton: 1) Validează input-ul. 2) Analizează textul (afișează în Analysis). 3) Pornește thread care apelează `joke_generator.generate_jokes()`. 4) Dezactivează butonul în timpul generării. |
| `_on_generation_complete(result)` | Callback din thread: afișează glumele în output, reactivează butonul, activează butoanele Read Aloud/Save. |
| `_speak_jokes()` | Formatează glumele pentru TTS (`format_jokes_for_tts`), apelează `tts_engine.play()` în background. |
| `_stop_speaking()` | Apelează `tts_engine.stop()`, actualizează starea butoanelor. |
| `_start_recording()` | Apelează `stt_engine.listen()` cu callback-urile `_on_stt_result` și `_on_stt_error`. Schimbă textul butonului la "Listening...". |
| `_on_stt_result(text)` | Primește textul transcris de la STT, îl adaugă în câmpul de context. |
| `_on_stt_error(error)` | Afișează eroarea STT în status bar. |
| `_save_jokes()` | Deschide file dialog, apelează `save_jokes_to_file()`, afișează confirmare sau eroare. |
| `_clear_output()` | Golește text area-ul de output + secțiunea de analiză. |
| `_set_output(text)` | Actualizează conținutul widgetului de output (sterge + inserează text nou). |
| `_set_status(message)` | Actualizează label-ul de status din footer. |
| `_on_close()` | Cleanup la închidere: oprește TTS (`cleanup()`), distruge fereastra. |

**Funcția `run_app()`** — Creează fereastra `Tk()`, instanțiază `JokeGeneratorApp`, apelează `root.mainloop()` (bucla principală Tkinter).

---

### pyproject.toml — Configurare proiect

Definește metadatele pachetului Python:

| Câmp | Valoare |
|------|---------|
| `name` | `ai-joke-generator` |
| `version` | `1.0.0` |
| `requires-python` | `>=3.9` |

**Dependențe:**

| Pachet | Versiune minimă | Scop |
|--------|-----------------|------|
| `requests` | ≥2.28.0 | Cereri HTTP către API-ul Ollama |
| `gtts` | ≥2.4.0 | Google Text-to-Speech — generare audio |
| `python-dotenv` | ≥1.0.0 | Încărcare variabile din fișierul `.env` |
| `SpeechRecognition` | ≥3.10.0 | Recunoaștere vocală via Google Speech API |
| `pyaudio` | ≥0.2.14 | Acces la microfon pentru input vocal |

---

## Utilizare

1. Pornește Ollama: `ollama serve`
2. Rulează aplicația: `python main.py`
3. Apasă "Connect to Ollama" (dacă nu s-a conectat automat)
4. Introdu un subiect în câmpul de context (ex: "programming", "pisici", "viața de student")
5. Selectează: număr de glume, limba, tonul
6. Apasă "Generate Jokes"
7. Opțional: "Read Aloud" pentru a auzi glumele citite
8. Opțional: "Save to File" pentru a salva glumele într-un fișier text

---

## Arhitectură

- **UI single-threaded** — interfața Tkinter rulează pe thread-ul principal
- **Operații blocante pe thread-uri separate** — generarea, TTS și STT rulează în thread-uri daemon pentru a nu bloca interfața
- **Error handling cu excepții custom** — `JokeGeneratorError`, `TTSEngineError`, `STTEngineError`
- **Configurare centralizată** — toate setările în `config.py`, modificabile dintr-un singur loc
- **Cross-platform** — detectare automată a platformei pentru redare audio (macOS/Windows/Linux)
- **Fără baze de date** — totul în memorie; salvarea e opțională, în fișiere `.txt`
