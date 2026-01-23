# Partea ta: Config + Main + Utils + Text Processing

Tu ești responsabil de **utilitarele și configurarea** aplicației:
- **config.py** — Setări centralizate (12 linii)
- **main.py** — Punctul de intrare (54 linii)
- **utils.py** — Funcții helper (73 linii)
- **text_processing.py** — Analiză text (90 linii)

Aceste fișiere sunt mai simple, conțin **funcții pure** (input → output) și constante. Nu folosesc threading sau interfață grafică.

---

## Fișierul 1: config.py (22 linii)

Toate setările aplicației, într-un singur loc.

```python
from pathlib import Path
from dotenv import load_dotenv

# Încarcă variabile din fișierul .env (dacă există)
load_dotenv(Path(__file__).parent / ".env")

# Setări Ollama
OLLAMA_BASE_URL = "http://localhost:11434"   # Adresa serverului
OLLAMA_MODEL = "llama3.2"                    # Modelul AI folosit
REQUEST_TIMEOUT = 60                          # Max secunde de așteptare

# Parametri de generare
GENERATION_CONFIG = {
    "temperature": 0.9,     # Creativitate (0=repetitiv, 1=maxim creativ)
    "top_p": 0.95,          # Filtrare tokeni improbabili
    "num_predict": 1024,    # Max tokeni în răspuns
}

# Setări aplicație
SUPPORTED_LANGUAGES = {"English": "en", "Romanian": "ro"}
TTS_LANGUAGES = {"English": "en", "Romanian": "ro"}
JOKE_TONES = ["Clean", "Dark", "Sarcastic"]
MIN_JOKES, MAX_JOKES, DEFAULT_JOKES = 1, 10, 3
```

**`load_dotenv()`** — Încarcă variabile de mediu din `.env`. Permite suprascrierea setărilor fără a modifica codul (ex: alt model, alt URL).

**`Path(__file__).parent / ".env"`** — Calea absolută către `.env` relativ la locația fișierului config.py.

**De ce un fișier separat?** Dacă vrei să schimbi modelul sau timeout-ul, modifici doar acest fișier. Toate celelalte fișiere fac `import config` și folosesc `config.OLLAMA_MODEL` etc.

---

## Fișierul 2: main.py (54 linii)

Punctul de intrare — prima funcție executată când rulezi `python main.py`.

### check_deps() (liniile 7-19)

```python
def check_deps():
    missing = []
    for pkg, name in [("requests", "requests"), ("gtts", "gtts"), ("dotenv", "python-dotenv")]:
        try:
            __import__(pkg)       # Încearcă să importe pachetul
        except ImportError:
            missing.append(name)  # Adaugă la lista celor lipsă

    if missing:
        print("Missing packages:", ", ".join(missing))
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    return True
```

**`__import__(pkg)`** — Importă un modul dinamic (ca `import requests` dar cu string). Util pentru a verifica fără a folosi efectiv modulul.

**De ce `("dotenv", "python-dotenv")`?** Pachetul se importă ca `dotenv` dar se instalează ca `python-dotenv`. Cele 2 nume sunt diferite.

### check_ollama() (liniile 22-27)

```python
def check_ollama():
    try:
        import requests
        return requests.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except Exception:
        return False
```

Verificare rapidă: Ollama răspunde? Timeout scurt (2 sec) pentru a nu bloca lansarea.

### main() (liniile 30-53)

```python
def main():
    print("\n  AI Joke Generator v1.0")
    print("  Powered by Ollama\n")

    if not check_deps():    # Dependențe lipsă → EXIT
        return 1

    if not check_ollama():  # Ollama nu rulează → WARNING (dar continuă)
        print("  Ollama not running. Start with: ollama serve")
        print("  You can still launch the app and connect later.\n")

    try:
        from gui import run_app   # Import GUI doar dacă dependențele sunt OK
        run_app()                  # Lansează interfața
        return 0
    except KeyboardInterrupt:     # Ctrl+C
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())  # Returnează exit code-ul la OS
```

**`if __name__ == "__main__"`** — Execută `main()` DOAR dacă fișierul e rulat direct (`python main.py`). Dacă e importat din alt fișier, nu se execută.

**`sys.exit(main())`** — Trimite exit code-ul la OS (0 = succes, 1 = eroare). Util pentru scripturi/automatizări.

**De ce `from gui import run_app` e ÎNĂUNTRUL funcției?** Import "lazy" — GUI-ul se importă doar dacă dependențele sunt OK. Dacă `requests` lipsește, nu vrem să importăm GUI-ul (care și el importă `requests`).

---

## Fișierul 3: utils.py (73 linii)

Funcții helper folosite în mai multe locuri din aplicație.

### validate_context() (liniile 7-19)

```python
def validate_context(context: str) -> tuple[bool, str]:
    if not context:
        return False, "Context cannot be empty."

    context = context.strip()   # Elimină spații la capete

    if len(context) < 2:
        return False, "Context must be at least 2 characters."
    if len(context) > 500:
        return False, "Context must not exceed 500 characters."

    # Verifică dacă conține litere sau cifre (nu doar simboluri)
    if re.match(r'^[^a-zA-Z0-9\u0100-\u017F]+$', context):
        return False, "Context must contain some letters or numbers."

    return True, ""
```

**Returnează `tuple[bool, str]`** — `(True, "")` dacă e valid, `(False, "mesaj eroare")` dacă nu.

**Regex `[^a-zA-Z0-9\u0100-\u017F]+`** — Caractere care NU sunt: litere engleze, cifre, sau caractere Unicode din blocul latin extins (include ă, î, ț, ș). Dacă TOT textul e din această categorie → nu e valid.

**Unde e apelat:** `gui.py → _generate_jokes()` — înainte de a trimite la Ollama.

### format_jokes_for_display() (liniile 22-31)

```python
def format_jokes_for_display(jokes: list[str]) -> str:
    if not jokes:
        return "No jokes generated."

    parts = []
    for i, joke in enumerate(jokes, 1):   # enumerate cu start=1
        # Elimină numerotarea existentă (1. sau 1) sau 1- sau 1:)
        joke = re.sub(r'^\d+[.)\-:]\s*', '', joke.strip())
        parts.append(f"{i}. {joke}")      # Adaugă numerotare uniformă

    return "\n\n".join(parts)  # Separat cu linii goale
```

**De ce elimină și re-adaugă numerotarea?** LLM-ul poate returna "1." sau "1)" sau "1-". Această funcție standardizează la "1. ..." pentru afișare uniformă.

**`enumerate(jokes, 1)`** — Numără de la 1, nu de la 0.

### format_jokes_for_tts() (liniile 34-44)

```python
def format_jokes_for_tts(jokes: list[str]) -> str:
    if not jokes:
        return ""

    parts = []
    for i, joke in enumerate(jokes, 1):
        joke = re.sub(r'^\d+[.)\-:]\s*', '', joke.strip())  # Elimină numerotare
        joke = re.sub(r'[*_#~`]', '', joke)                  # Elimină markdown
        parts.append(f"Joke number {i}. {joke}")             # "Joke number 1. ..."

    return " ... ".join(parts)  # Separat cu " ... " (pauză la citit)
```

**De ce elimină markdown?** LLM-ul poate returna `**bold**` sau `_italic_`. Motorul TTS ar citi literalmente "*" ceea ce sună ciudat.

**De ce `" ... "`?** Punctele de suspensie creează o pauză naturală în vorbire între glume.

### save_jokes_to_file() (liniile 47-68)

```python
def save_jokes_to_file(jokes: list[str], filepath: str = None,
                       context: str = "", language: str = "English") -> tuple[bool, str]:
    if not jokes:
        return False, "No jokes to save."

    # Generează nume automat dacă nu e specificat
    if not filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"jokes_{timestamp}.txt"   # ex: jokes_20240315_143052.txt

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"AI Joke Generator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Language: {language} | Context: {context}\n")
            f.write("-" * 40 + "\n\n")

            # Glumele
            for i, joke in enumerate(jokes, 1):
                joke = re.sub(r'^\d+[.)\-:]\s*', '', joke.strip())
                f.write(f"{i}. {joke}\n\n")

        return True, os.path.abspath(filepath)   # Returnează calea absolută
    except OSError as e:
        return False, f"Failed to save: {e}"
```

**Exemplu output fișier:**
```
AI Joke Generator - 2024-03-15 14:30:52
Language: English | Context: programming, coffee
----------------------------------------

1. Why do programmers prefer dark mode? Because light attracts bugs!

2. A programmer's wife tells him: "Go to the store and buy a loaf of bread..."
```

**`encoding='utf-8'`** — Important pentru caractere românești (ă, î, ț, ș).

### get_language_code() (liniile 71-72)

```python
def get_language_code(name: str) -> str:
    return config.SUPPORTED_LANGUAGES.get(name, "en")  # Fallback la "en"
```

Conversie simplă: "English" → "en", "Romanian" → "ro".

---

## Fișierul 4: text_processing.py (90 linii)

Analizează textul introdus de utilizator: detectează limba, extrage cuvinte cheie, calculează statistici.

### Constantele STOP_WORDS și LANG_PATTERNS (liniile 6-20)

```python
STOP_WORDS = {
    "en": {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", ...},
    "ro": {"si", "sau", "dar", "in", "pe", "la", "de", "cu", "din", ...}
}
```

**Stop words** = cuvinte foarte comune care nu au valoare semantică. Le eliminăm ca să găsim cuvintele importante.

```python
LANG_PATTERNS = {
    "en": {"words": ["the", "and", "is", "are", ...], "chars": []},
    "ro": {"words": ["si", "este", "sunt", "pentru", ...], "chars": ["ă", "î", "ț", "ș"]}
}
```

**Language patterns** = indicii pentru detectarea limbii. Dacă textul conține "ă" sau "ț" → probabil română.

### tokenize() (liniile 23-27)

```python
def tokenize(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r'[^\w\s]', ' ', text.lower())  # Elimină punctuație, lowercase
    return [t for t in text.split() if t]           # Împarte în cuvinte
```

**`[^\w\s]`** — Orice caracter care NU e literă/cifră/underscore (`\w`) și NU e spațiu (`\s`). Adică: punctuație, simboluri.

**Exemplu:** `"Hello, World! How are you?"` → `["hello", "world", "how", "are", "you"]`

### detect_language() (liniile 30-49)

```python
def detect_language(text: str) -> tuple[str, float]:
    if not text:
        return "en", 0.0

    tokens = set(tokenize(text))  # Set pentru intersecție rapidă
    text_lower = text.lower()
    scores = {}

    for lang, patterns in LANG_PATTERNS.items():
        # Cuvinte din text care sunt în pattern-ul limbii × 2 (weight mai mare)
        score = len(tokens.intersection(patterns["words"])) * 2
        # Caractere speciale din text care sunt în pattern
        score += sum(1 for c in patterns["chars"] if c in text_lower)
        scores[lang] = score

    total = sum(scores.values())
    if total == 0:
        return "en", 0.7  # Default: engleză cu confidence mediu

    best = max(scores, key=scores.get)  # Limba cu scor maxim
    confidence = 0.5 + (scores[best] / total) * 0.5  # Normalizare la 0.5-1.0
    return best, min(confidence, 1.0)
```

**Algoritm:**
1. Tokenizează textul
2. Pentru fiecare limbă, calculează un scor:
   - +2 pentru fiecare cuvânt comun găsit (the, and, este, sunt...)
   - +1 pentru fiecare caracter special găsit (ă, î, ț, ș)
3. Limba cu scorul cel mai mare câștigă
4. Confidence = cât de "sigur" e (0.5 = incert, 1.0 = sigur)

**Exemplu:**
- `"I love programming"` → "I" nu e pattern, "love" nu e pattern, dar "and"/"the" ar fi → scor en mic, dar mai mare decât ro → `("en", 0.7)`
- `"Îmi place programarea în România"` → "Î" în text, "î" = pattern ro → `("ro", 0.9)`

### extract_keywords() (liniile 52-59)

```python
def extract_keywords(text: str, language: str = "en", top_n: int = 5) -> list[str]:
    tokens = tokenize(text)
    if not tokens:
        return []

    stop = STOP_WORDS.get(language, STOP_WORDS["en"])
    # Păstrează cuvintele care NU sunt stop words și au > 2 caractere
    keywords = [t for t in tokens if t not in stop and len(t) > 2]
    # Returnează cele mai frecvente top_n cuvinte
    return [w for w, _ in Counter(keywords).most_common(top_n)]
```

**`Counter(keywords).most_common(top_n)`** — Numără frecvența fiecărui cuvânt și returnează top N.

**Exemplu:** `"I love programming and coding and programming"` → stop words: "I", "and" → keywords: ["programming", "love", "coding"] → most_common(3) → `["programming", "love", "coding"]`

### get_text_stats() (liniile 62-75)

```python
def get_text_stats(text: str) -> dict:
    tokens = tokenize(text)
    lang, conf = detect_language(text)

    return {
        "word_count": len(tokens),                    # Nr. total cuvinte
        "character_count": len(text.replace(" ", "")),  # Caractere fără spații
        "sentence_count": len([s for s in re.split(r'[.!?]+', text) if s.strip()]),  # Propoziții
        "unique_words": len(set(tokens)),             # Cuvinte distincte
        "average_word_length": round(sum(len(t) for t in tokens) / max(len(tokens), 1), 2),
        "detected_language": lang,
        "language_confidence": round(conf, 2),
        "keywords": extract_keywords(text, lang)
    }
```

**`re.split(r'[.!?]+', text)`** — Împarte textul la puncte, semne de exclamare sau întrebare. `+` = unul sau mai multe consecutive (ex: "?!" = un singur separator).

**`max(len(tokens), 1)`** — Previne împărțirea la 0 dacă textul e gol.

### analyze_input() (liniile 78-89)

```python
def analyze_input(text: str) -> dict:
    if not text or not text.strip():
        return {"is_valid": False, "error": "Input is empty", "statistics": None}

    text = text.strip()
    return {
        "is_valid": True,
        "error": None,
        "statistics": get_text_stats(text),
        "tokens": tokenize(text),
        "keywords": extract_keywords(text, detect_language(text)[0])
    }
```

Funcția principală apelată din GUI. Combină toate celelalte funcții.

**`detect_language(text)[0]`** — Ia doar limba (nu și confidence-ul) din tuple.

---

## Cum sunt apelate din GUI

```python
# gui.py → _generate_jokes()

# 1. Validare cu utils
is_valid, error = utils.validate_context(context)

# 2. Analiză cu text_processing
analysis = text_processing.analyze_input(context)

# 3. La afișare
formatted = utils.format_jokes_for_display(result["jokes"])

# 4. La citit cu voce
text = utils.format_jokes_for_tts(self.current_jokes)

# 5. La salvare
success, result = utils.save_jokes_to_file(jokes, filepath, context, language)
```

---

## Diagrama interacțiunii

```
┌──────────────────────────────────────────────────────┐
│                      GUI                             │
│                                                      │
│  Utilizator introduce text                           │
│       │                                              │
│       ▼                                              │
│  utils.validate_context(text)                        │
│       │ (valid/invalid)                              │
│       ▼                                              │
│  text_processing.analyze_input(text)                 │
│       │                                              │
│       ├── tokenize() → cuvinte                       │
│       ├── detect_language() → limba                  │
│       ├── extract_keywords() → cuvinte cheie         │
│       └── get_text_stats() → statistici              │
│                                                      │
│  ... generare glume ...                              │
│                                                      │
│  utils.format_jokes_for_display(jokes) → afișare     │
│  utils.format_jokes_for_tts(jokes) → citit cu voce   │
│  utils.save_jokes_to_file(jokes, ...) → salvare      │
└──────────────────────────────────────────────────────┘
```

---

## Întrebări de verificare

1. Ce face `load_dotenv()` și de ce e util?
2. De ce `check_deps()` folosește `__import__()` în loc de `import`?
3. Ce returnează `validate_context("!!!")` și de ce?
4. Care e diferența între `format_jokes_for_display()` și `format_jokes_for_tts()`?
5. Cum funcționează `detect_language()` — ce se întâmplă dacă textul e în franceză?
6. Ce sunt "stop words" și de ce le eliminăm?
7. De ce `save_jokes_to_file()` folosește `encoding='utf-8'`?
8. Ce returnează `Counter(["a", "b", "a", "c", "a"]).most_common(2)`?
