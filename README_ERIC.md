# Partea ta: GUI + Joke Generator + Prompts

Aceasta este partea cea mai complexă a proiectului. Tu ești responsabil de:
- **gui.py** — Interfața grafică completă (cea mai mare componentă)
- **joke_generator.py** — Comunicarea cu API-ul Ollama (inteligența artificială)
- **prompts.py** — Construirea prompturilor pentru LLM (prompt engineering)

Aceste 3 fișiere formează **creierul aplicației**: interfața utilizatorului, comunicarea cu AI-ul, și modul în care "instruim" modelul să genereze glume.

---

## Concepte cheie pe care trebuie să le înțelegi

### 1. Threading (fire de execuție paralele)

Tkinter rulează pe un **singur thread** (thread-ul principal). Dacă faci o operație lentă (ex: aștepți răspuns de la Ollama 10 secunde) pe thread-ul principal, **interfața se blochează** — utilizatorul nu poate apăsa butoane, fereastra pare "înghețată".

**Soluția:** Operațiile lente se execută pe **thread-uri daemon separate**:

```python
# GREȘIT - blochează interfața:
result = self.joke_generator.generate_jokes(context, num_jokes, language, tone)
self._set_output(result)

# CORECT - nu blochează:
def generate():
    result = self.joke_generator.generate_jokes(context, num_jokes, language, tone)
    # root.after() trimite rezultatul ÎNAPOI pe thread-ul principal
    self.root.after(0, lambda: self._on_generation_complete(result))

threading.Thread(target=generate, daemon=True).start()
```

**De ce `daemon=True`?** Thread-urile daemon se opresc automat când aplicația se închide. Fără `daemon=True`, aplicația ar rămâne deschisă în fundal dacă un thread încă rulează.

**De ce `root.after(0, ...)`?** Tkinter NU permite modificarea widgeturilor din alt thread. `root.after()` programează o funcție să fie executată pe thread-ul principal. Parametrul `0` înseamnă "cât mai curând posibil".

---

### 2. Callback Pattern (funcții apelate ulterior)

Un callback este o funcție pe care o dai ca parametru altei funcții, pentru a fi apelată când se termină o operație:

```python
# on_complete este un callback
self.tts_engine.play(text, on_complete=lambda: self.root.after(0, self._on_speech_complete))
```

**Fluxul:**
1. `play()` pornește redarea audio
2. Când audio-ul se termină, apelează `on_complete`
3. `on_complete` conține `root.after(0, self._on_speech_complete)`
4. `_on_speech_complete` se execută pe thread-ul principal și actualizează butoanele

Acest pattern apare peste tot în cod: STT (`on_result`, `on_error`), TTS (`on_complete`), generare (`_on_generation_complete`).

---

### 3. Comunicare HTTP cu API (requests)

Ollama expune un REST API local. Comunicarea se face prin cereri HTTP:

```python
# GET - obține informații (lista modelelor)
resp = requests.get("http://localhost:11434/api/tags", timeout=5)

# POST - trimite date și primește răspuns (generare)
resp = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.2", "prompt": "...", "stream": False, "options": {...}},
    timeout=60
)
```

**`stream: False`** — Primim tot răspunsul odată (nu token cu token). Simplific implementarea.

**`timeout`** — Dacă Ollama nu răspunde în X secunde, se aruncă excepție. Previne blocarea infinită.

---

### 4. State Management (gestionarea stării)

Aplicația are mai multe "stări" care controlează ce butoane sunt active:

```
Stare inițială:  Generate=disabled, Speak=disabled, Save=disabled
După Connect:    Generate=enabled
În timp ce generează: Generate=disabled, status="Generating..."
După generare:   Generate=enabled, Speak=enabled, Save=enabled
În timp ce vorbește: Speak=disabled, Stop=enabled
```

Starea e gestionată prin variabile de instanță (`self.is_generating`, `self.current_jokes`, etc.) și prin `widget.config(state="normal"/"disabled")`.

---

## Fișierul 1: gui.py (569 linii)

Acesta este **cel mai mare și mai complex fișier** din proiect. Conține toată interfața grafică și logica de interacțiune.

### Importuri (liniile 1-13)

```python
import tkinter as tk          # Framework-ul GUI
from tkinter import ttk       # Widgeturi cu stil (themed)
from tkinter import messagebox # Dialoguri de eroare/info
from tkinter import filedialog # Dialog de salvare fișier
import threading              # Thread-uri pentru operații asincrone
from typing import Optional, List  # Type hints
```

**Diferența tk vs ttk:** `tk.Button` e un buton simplu pe care îi poți seta direct culorile. `ttk.Label` e un widget "themed" — stilul se aplică prin `ttk.Style()`, nu direct pe widget.

### Clasa ModernStyle (liniile 17-39)

```python
class ModernStyle:
    BG_DARK = "#1a1b26"      # Fundal principal (albastru-gri foarte închis)
    BG_CARD = "#24283b"      # Fundal carduri (puțin mai deschis)
    BG_INPUT = "#414868"     # Fundal câmpuri editabile
    ACCENT = "#7aa2f7"       # Albastru pentru butoane/accent
    ACCENT_HOVER = "#89b4fa" # Albastru mai deschis la hover
    SUCCESS = "#9ece6a"      # Verde - conexiune reușită
    ERROR = "#f7768e"        # Roșu - erori
    WARNING = "#e0af68"      # Galben - avertismente
    TEXT_PRIMARY = "#c0caf5" # Text principal (alb-albăstrui)
    TEXT_SECONDARY = "#565f89" # Text secundar (gri)
    TEXT_MUTED = "#414868"   # Text foarte diminuat
    BORDER = "#414868"       # Borduri

    FONT_TITLE = ("Helvetica", 22, "bold")   # Titlu mare
    FONT_SUBTITLE = ("Helvetica", 11)         # Subtitlu
    FONT_HEADING = ("Helvetica", 12, "bold")  # Titlu de card
    FONT_BODY = ("Helvetica", 11)             # Text normal
    FONT_BUTTON = ("Helvetica", 10, "bold")   # Text butoane
    FONT_MONO = ("Courier", 11)               # Font monospaced (output)
    FONT_SMALL = ("Helvetica", 9)             # Text mic (status, analiză)
```

**De ce o clasă separată?** Pentru a schimba tema vizuală dintr-un singur loc. Dacă vrei culori diferite, modifici doar această clasă.

### Clasa JokeGeneratorApp — Inițializare (liniile 42-68)

```python
class JokeGeneratorApp:
    def __init__(self, root: tk.Tk):
        self.root = root                                    # Fereastra principală
        self.joke_generator: Optional[JokeGenerator] = None # None până la Connect
        self.tts_engine: Optional[TTSEngine] = None         # None dacă gTTS lipsește
        self.stt_engine: Optional[STTEngine] = None         # None dacă PyAudio lipsește
        self.current_jokes: List[str] = []                  # Glumele curente generate
        self.current_language = "English"                   # Limba selectată
        self.is_generating = False                          # Flag: generare în curs?

        self._setup_window()      # 1. Configurează fereastra
        self._setup_styles()      # 2. Definește stilurile vizuale
        self._init_services()     # 3. Inițializează serviciile (TTS, STT)
        self._create_widgets()    # 4. Creează toate elementele UI
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)  # 5. Handler la X
```

**`Optional[JokeGenerator]`** — Type hint care spune "poate fi JokeGenerator sau None". La început e `None` până când utilizatorul apasă Connect.

**`root.protocol("WM_DELETE_WINDOW", ...)`** — Interceptează butonul X de la fereastră. În loc să închidă direct, apelează `_on_close()` care face cleanup (oprește TTS) înainte de a închide.

### _setup_window() (liniile 59-68)

```python
def _setup_window(self):
    self.root.title("AI Joke Generator")
    self.root.geometry("700x800")      # Lățime x Înălțime
    self.root.minsize(500, 600)        # Minimum redimensionare
    self.root.configure(bg=ModernStyle.BG_DARK)

    # Centrare pe ecran
    self.root.update_idletasks()        # Forțează calculul dimensiunilor
    x = (self.root.winfo_screenwidth() - 700) // 2   # Centru orizontal
    y = (self.root.winfo_screenheight() - 800) // 2  # Centru vertical
    self.root.geometry(f"700x800+{x}+{y}")  # +x+y = poziția pe ecran
```

**`update_idletasks()`** — Forțează Tkinter să calculeze dimensiunile reale ale ferestrei. Fără asta, `winfo_screenwidth()` ar putea returna valori greșite.

### _setup_styles() (liniile 70-123)

Configurează stilurile pentru **widgeturile ttk** (nu tk clasice). Fiecare stil are un **nume unic** (ex: `"Card.TFrame"`, `"Title.TLabel"`).

```python
self.style = ttk.Style()
self.style.theme_use('clam')  # Tema de bază (cea mai personalizabilă)

# Stilul pentru frame-urile de tip card
self.style.configure("Card.TFrame", background=ModernStyle.BG_CARD)

# Stilul pentru label-urile de titlu
self.style.configure("Title.TLabel",
    background=ModernStyle.BG_DARK,
    foreground=ModernStyle.TEXT_PRIMARY,
    font=ModernStyle.FONT_TITLE)
```

**Cum se aplică:** Când creezi un widget, specifici stilul:
```python
ttk.Label(parent, text="Hello", style="Title.TLabel")
ttk.Frame(parent, style="Card.TFrame")
```

**`style.map()`** — Definește stiluri pentru stări (hover, active, disabled):
```python
self.style.map("Modern.TRadiobutton",
    background=[("active", ModernStyle.BG_CARD)])  # Fundal la click
```

### _init_services() (liniile 124-139)

```python
def _init_services(self):
    self.stt_error_msg = None

    try:
        self.tts_engine = TTSEngine()    # Încearcă să creeze motorul TTS
    except TTSEngineError:
        self.tts_engine = None           # Dacă gTTS nu e instalat, None

    try:
        self.stt_engine = STTEngine()    # Încearcă să creeze motorul STT
    except STTEngineError as e:
        self.stt_error_msg = str(e)      # Salvează mesajul de eroare
        self.stt_engine = None           # Dacă PyAudio lipsește, None

    self.joke_generator = None           # Se creează la Connect, nu acum
```

**De ce `joke_generator = None` aici?** Conexiunea la Ollama poate dura. Nu vrem să blocăm lansarea aplicației. Utilizatorul conectează manual cu butonul.

**De ce try/except?** TTS și STT sunt opționale. Dacă nu sunt instalate, aplicația funcționează fără ele (butoanele sunt dezactivate).

### _create_widgets() — Layoutul scrollabil (liniile 141-169)

```python
def _create_widgets(self):
    # Canvas = zonă pe care poți face scroll
    self.canvas = tk.Canvas(self.root, bg=ModernStyle.BG_DARK, highlightthickness=0)
    scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)

    self.canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")       # Scrollbar-ul la dreapta
    self.canvas.pack(side="left", fill="both", expand=True)  # Canvas umple restul

    # Frame-ul principal — conține toate secțiunile
    self.main_frame = ttk.Frame(self.canvas, style="Dark.TFrame")
    self.canvas_frame = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

    # Când main_frame se redimensionează, actualizează zona scrollabilă
    self.main_frame.bind("<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    # Când canvas-ul se redimensionează, ajustează lățimea frame-ului
    self.canvas.bind("<Configure>", self._on_canvas_resize)

    # Scroll cu rotița mouse-ului (cross-platform)
    self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
    self.canvas.bind_all("<Button-4>", lambda e: ...)              # Linux scroll up
    self.canvas.bind_all("<Button-5>", lambda e: ...)              # Linux scroll down
```

**De ce Canvas + Frame?** Tkinter nu are un widget "scrollable frame" nativ. Trucul e:
1. Creezi un Canvas (suportă scroll)
2. Pui un Frame înăuntru cu `create_window()`
3. Toate widgeturile se adaugă în Frame
4. Canvas-ul face scroll peste tot conținutul

**`scrollregion`** — Zona totală pe care Canvas-ul o poate afișa. Se actualizează când se adaugă widgeturi noi.

### _create_card() — Helper pentru secțiuni (liniile 336-348)

```python
def _create_card(self, title: str) -> ttk.Frame:
    outer = ttk.Frame(self.main_frame, style="Dark.TFrame")  # Container exterior
    outer.pack(fill="x", padx=20, pady=(0, 10))              # Margini laterale

    card = ttk.Frame(outer, style="Card.TFrame")             # Cardul propriu-zis
    card.pack(fill="x")                                       # Umple orizontal

    inner = ttk.Frame(card, style="Card.TFrame")             # Padding interior
    inner.pack(fill="x", padx=15, pady=12)                   # Margini interioare

    ttk.Label(inner, text=title, style="CardHeading.TLabel").pack(anchor="w", pady=(0, 10))

    return inner  # Returnează frame-ul interior — aici se adaugă conținutul
```

**Structura:** `outer (dark) → card (gray) → inner (gray + padding) → conținut`

Fiecare secțiune (Connection, Input, Options, Output, Analysis) e un "card" creat cu această funcție.

### _create_connection_section() (liniile 189-207)

```python
def _create_connection_section(self):
    card = self._create_card("Ollama Connection")

    row = ttk.Frame(card, style="Card.TFrame")
    row.pack(fill="x")

    # Label de status — inițial roșu "Not connected"
    self.connection_status = ttk.Label(row, text="Not connected", style="Error.TLabel")
    self.connection_status.pack(side="left")

    # Buton Connect — tk.Button (nu ttk) pentru control direct al culorilor
    self.connect_btn = tk.Button(row, text="Connect",
        font=ModernStyle.FONT_BUTTON,
        bg=ModernStyle.ACCENT, fg=ModernStyle.BG_DARK,  # Albastru pe negru
        activebackground=ModernStyle.ACCENT_HOVER,       # La click
        relief="flat", cursor="hand2",                   # Fără bordură 3D, cursor mână
        padx=15, pady=5,
        command=self._connect_ollama)                     # Handler la click
    self.connect_btn.pack(side="right")

    # Afișare model
    ttk.Label(card, text=f"Model: {config.OLLAMA_MODEL}", style="Card.TLabel").pack(...)
```

### _create_input_section() (liniile 209-238)

```python
def _create_input_section(self):
    card = self._create_card("Context / Keywords")

    # Text area pentru context — tk.Text (suportă multi-line)
    self.context_text = tk.Text(card, height=3,
        font=ModernStyle.FONT_BODY,
        bg=ModernStyle.BG_INPUT, fg=ModernStyle.TEXT_PRIMARY,
        insertbackground=ModernStyle.TEXT_PRIMARY,  # Culoarea cursorului
        relief="flat", wrap="word",                 # Fără bordură, wrap la cuvinte
        padx=10, pady=8,
        highlightthickness=1,                       # Bordură 1px
        highlightbackground=ModernStyle.BORDER,     # Bordură normală
        highlightcolor=ModernStyle.ACCENT)          # Bordură la focus (albastru)
    self.context_text.pack(fill="x")
    self.context_text.insert("1.0", "school, exams, programming")  # Placeholder

    # Buton Voice Input
    self.mic_btn = tk.Button(mic_row, text="🎤 Voice Input", ...)

    # Dacă STT nu e disponibil, dezactivează butonul
    if not self.stt_engine:
        self.mic_btn.config(state="disabled", text="🎤 Voice Input (Unavailable)")
        # La click pe buton dezactivat, arată eroarea
        self.mic_btn.bind("<Button-1>", lambda e: self._show_stt_error())
```

**`tk.Text` vs `tk.Entry`:** Entry e pentru o singură linie. Text e multi-line (aici 3 rânduri).

**`"1.0"`** — Poziția în Text widget: linia 1, caracterul 0. Format Tkinter: `"linie.caracter"`.

### _create_options_section() (liniile 240-289)

```python
# Slider pentru număr de glume
self.num_jokes_var = tk.IntVar(value=3)  # Variabilă Tkinter legată de slider
self.num_jokes_scale = ttk.Scale(jokes_frame,
    from_=1, to=10,                       # Range: 1-10
    orient="horizontal",
    variable=self.num_jokes_var,           # Se actualizează automat
    command=self._update_jokes_label)      # Apelat la fiecare schimbare

# Radiobuttons pentru limbă
self.language_var = tk.StringVar(value="English")  # Variabilă partajată
for lang in ["English", "Romanian"]:
    ttk.Radiobutton(lang_frame, text=lang, value=lang,
        variable=self.language_var, ...)   # Toate partajează aceeași variabilă

# Combobox pentru ton
self.tone_var = tk.StringVar(value="Clean")
self.tone_combo = ttk.Combobox(tone_frame,
    textvariable=self.tone_var,
    values=["Clean", "Dark", "Sarcastic"],
    state="readonly",                      # Nu poate fi editat manual
    width=10)
```

**`tk.IntVar` / `tk.StringVar`** — Variabile speciale Tkinter care notifică widgeturile când se schimbă. Permiti legarea automată widget ↔ valoare.

**Radiobuttons** — Toate cu aceeași `variable` → numai unul poate fi selectat.

### _create_output_section() (liniile 291-324)

```python
# Text area read-only pentru output
self.output_text = tk.Text(card, height=12,
    font=ModernStyle.FONT_MONO,  # Monospaced — aliniere frumoasă
    state="disabled",            # READ-ONLY inițial
    ...)

# Butoane de acțiune
btn_style = {"font": ..., "bg": ..., "fg": ..., "relief": "flat", ...}

self.speak_btn = tk.Button(btn_frame, text="Read Aloud", state="disabled", ...)
self.stop_btn = tk.Button(btn_frame, text="Stop", state="disabled", ...)
self.save_btn = tk.Button(btn_frame, text="Save", state="disabled", ...)
self.clear_btn = tk.Button(btn_frame, text="Clear", ...)  # Mereu activ
```

**`state="disabled"`** — Butoanele sunt gri și neapăsabile. Devin active doar după generarea de glume.

**`btn_style` dict** — Reutilizează aceleași proprietăți pentru toate butoanele (DRY = Don't Repeat Yourself).

### _connect_ollama() — Conectare asincronă (liniile 362-384)

```python
def _connect_ollama(self):
    self._set_status("Connecting to Ollama...")
    self.connect_btn.config(state="disabled")  # Previne click-uri multiple

    def connect():
        try:
            self.joke_generator = JokeGenerator()  # Poate dura câteva secunde
            # Succes → actualizează UI pe thread-ul principal
            self.root.after(0, self._on_connect_success)
        except JokeGeneratorError as e:
            # Eroare → afișează eroarea pe thread-ul principal
            self.root.after(0, lambda: self._on_connect_error(str(e)))

    threading.Thread(target=connect, daemon=True).start()
```

**Fluxul complet:**
1. Utilizatorul apasă "Connect"
2. Butonul se dezactivează (previne spam click)
3. Un thread nou pornește funcția `connect()`
4. `connect()` creează `JokeGenerator()` — asta face GET la Ollama
5. Dacă reușește → `root.after(0, _on_connect_success)` → label verde "Connected"
6. Dacă eșuează → `root.after(0, _on_connect_error)` → messagebox cu eroarea

### _generate_jokes() — Generare asincronă (liniile 386-418)

```python
def _generate_jokes(self):
    # Validări
    if not self.joke_generator:
        messagebox.showerror("Error", "Please connect to Ollama first.")
        return
    if self.is_generating:
        return  # Previne generare multiplă simultană

    # Extrage valorile din UI
    context = self.context_text.get("1.0", "end").strip()  # Tot textul din input
    num_jokes = int(self.num_jokes_var.get())               # Valoarea slider-ului
    language = self.language_var.get()                       # "English" sau "Romanian"
    tone = self.tone_var.get()                              # "Clean"/"Dark"/"Sarcastic"

    # Validare context
    is_valid, error = utils.validate_context(context)
    if not is_valid:
        messagebox.showerror("Invalid Input", error)
        return

    # Analiză text (afișează statistici)
    analysis = text_processing.analyze_input(context)
    self._update_analysis(analysis)

    # Start generare
    self.is_generating = True
    self.generate_btn.config(state="disabled", bg=ModernStyle.BG_INPUT)  # Buton gri
    self._set_status("Generating jokes...")

    def generate():
        result = self.joke_generator.generate_jokes(
            context=context, num_jokes=num_jokes,
            language=language, tone=tone)
        self.root.after(0, lambda: self._on_generation_complete(result))

    threading.Thread(target=generate, daemon=True).start()
```

### _on_generation_complete() — Procesare rezultat (liniile 420-434)

```python
def _on_generation_complete(self, result: dict):
    self.is_generating = False
    self.generate_btn.config(state="normal", bg=ModernStyle.ACCENT)  # Buton activ

    if result["success"]:
        self.current_jokes = result["jokes"]         # Salvează glumele
        formatted = utils.format_jokes_for_display(result["jokes"])
        self._set_output(formatted)                  # Afișează în output
        self._set_status(f"Generated {len(result['jokes'])} joke(s)")

        # Activează butoanele
        self.speak_btn.config(state="normal" if self.tts_engine else "disabled")
        self.save_btn.config(state="normal")
    else:
        self._set_output(f"Error: {result['error']}")
        messagebox.showerror("Error", result["error"])
```

### _speak_jokes() și _stop_speaking() (liniile 450-476)

```python
def _speak_jokes(self):
    if not self.tts_engine or not self.current_jokes:
        return

    self._set_status("Speaking...")
    self.speak_btn.config(state="disabled")  # Nu poate apăsa din nou
    self.stop_btn.config(state="normal")     # Poate opri

    def speak():
        try:
            text = utils.format_jokes_for_tts(self.current_jokes)
            self.tts_engine.set_language(self.current_language)
            self.tts_engine.play(text,
                on_complete=lambda: self.root.after(0, self._on_speech_complete))
        except TTSEngineError:
            self.root.after(0, self._on_speech_complete)

    threading.Thread(target=speak, daemon=True).start()

def _stop_speaking(self):
    if self.tts_engine:
        self.tts_engine.stop()          # Oprește subprocess-ul audio
        self._on_speech_complete()       # Resetează butoanele
```

### _start_recording() și callback-uri STT (liniile 514-546)

```python
def _start_recording(self):
    if not self.stt_engine or self.stt_engine.is_listening:
        return

    # UI feedback — butonul devine roșu
    self.mic_btn.config(bg=ModernStyle.ERROR, text="🎤 Listening...")
    self.mic_status.config(text="Calibrating... then speak")

    self.stt_engine.listen(
        timeout=8.0,              # Max 8 sec așteptare pentru vorbire
        phrase_time_limit=15.0,   # Max 15 sec de înregistrare
        # Callback-urile trimit rezultatul pe thread-ul principal
        on_result=lambda text: self.root.after(0, lambda: self._on_stt_result(text)),
        on_error=lambda err: self.root.after(0, lambda: self._on_stt_error(err))
    )

def _on_stt_result(self, text: str):
    self.mic_btn.config(bg=ModernStyle.BG_INPUT, text="🎤 Voice Input")  # Reset buton

    # Adaugă textul la context (sau înlocuiește placeholder-ul)
    current = self.context_text.get("1.0", "end").strip()
    if current and current != "school, exams, programming":
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", f"{current}, {text}")  # Adaugă
    else:
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", text)  # Înlocuiește

    self._set_status(f"Heard: \"{text}\"")
```

### _save_jokes() (liniile 478-496)

```python
def _save_jokes(self):
    if not self.current_jokes:
        return

    # Deschide dialogul nativ de salvare
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        title="Save Jokes")

    if filepath:  # Utilizatorul a ales un fișier (nu a apăsat Cancel)
        context = self.context_text.get("1.0", "end").strip()
        success, result = utils.save_jokes_to_file(
            self.current_jokes, filepath, context, self.current_language)

        if success:
            messagebox.showinfo("Success", f"Saved to:\n{result}")
        else:
            messagebox.showerror("Error", result)
```

### _set_output() și _set_status() — Helper-e UI (liniile 505-512)

```python
def _set_output(self, text: str):
    self.output_text.config(state="normal")    # Temporar editabil
    self.output_text.delete("1.0", "end")      # Șterge tot
    self.output_text.insert("1.0", text)       # Inserează textul nou
    self.output_text.config(state="disabled")  # Read-only din nou

def _set_status(self, message: str):
    self.status_var.set(message)  # StringVar actualizează Label-ul automat
```

**De ce `state="normal"` apoi `state="disabled"`?** Widget-urile Text cu `state="disabled"` nu pot fi modificate programatic. Trebuie deblocat temporar.

### _on_close() și run_app() (liniile 559-568)

```python
def _on_close(self):
    if self.tts_engine:
        self.tts_engine.cleanup()  # Oprește audio + șterge fișiere temp
    self.root.destroy()            # Închide fereastra

def run_app():
    root = tk.Tk()                 # Creează fereastra principală
    JokeGeneratorApp(root)         # Inițializează aplicația
    root.mainloop()                # Bucla principală — așteaptă evenimente la infinit
```

**`mainloop()`** — Tkinter intră într-o buclă infinită unde: 1) Desenează interfața, 2) Ascultă click-uri/taste, 3) Apelează handler-ele. Se oprește doar la `root.destroy()`.

---

## Fișierul 2: joke_generator.py (109 linii)

Gestionează comunicarea cu Ollama.

### Clasa JokeGeneratorError (linia 8)

```python
class JokeGeneratorError(Exception):
    pass
```

Excepție custom. Permite GUI-ului să distingă între "eroare Ollama" și alte erori.

### __init__() (liniile 14-17)

```python
def __init__(self):
    self.base_url = config.OLLAMA_BASE_URL   # "http://localhost:11434"
    self.model = config.OLLAMA_MODEL         # "llama3.2"
    self._check_ollama()                     # Verifică IMEDIAT
```

Constructorul apelează `_check_ollama()`. Dacă verificarea eșuează, aruncă excepție → obiectul NU se creează. Asta e detectat în GUI (`try/except`).

### _check_ollama() (liniile 19-32)

```python
def _check_ollama(self):
    try:
        resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
        if resp.status_code != 200:
            raise JokeGeneratorError("Ollama not responding. Run: ollama serve")

        # Extrage numele modelelor (fără tag-ul ":latest")
        models = [m.get("name", "").split(":")[0] for m in resp.json().get("models", [])]
        if self.model not in models:
            raise JokeGeneratorError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")

    except requests.exceptions.ConnectionError:
        raise JokeGeneratorError("Cannot connect to Ollama. Run: ollama serve")
    except requests.exceptions.Timeout:
        raise JokeGeneratorError("Ollama connection timed out.")
```

**Fluxul:**
1. GET la `/api/tags` → returnează `{"models": [{"name": "llama3.2:latest", ...}]}`
2. Extrage numele: `"llama3.2:latest".split(":")[0]` → `"llama3.2"`
3. Verifică dacă modelul nostru e în listă
4. Dacă nu → eroare cu instrucțiuni ("Run: ollama pull ...")

### generate_jokes() (liniile 34-79)

```python
def generate_jokes(self, context: str, num_jokes: int = 3,
                   language: str = "English", tone: str = "Clean") -> dict:

    # 1. Validare input
    if not context or not context.strip():
        return {"success": False, "jokes": [], "raw_response": "", "error": "Context cannot be empty."}

    # 2. Clampare valori
    num_jokes = max(config.MIN_JOKES, min(num_jokes, config.MAX_JOKES))  # 1-10
    language = language if language in config.SUPPORTED_LANGUAGES else "English"
    tone = tone if tone in config.JOKE_TONES else "Clean"

    # 3. Construire prompt
    prompt = prompts.build(context, num_jokes, language, tone)

    # 4. Cerere la Ollama
    try:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,           # Primim tot răspunsul odată
                "options": {
                    "temperature": config.GENERATION_CONFIG["temperature"],  # 0.9
                    "top_p": config.GENERATION_CONFIG["top_p"],              # 0.95
                    "num_predict": config.GENERATION_CONFIG["num_predict"],  # 1024
                }
            },
            timeout=config.REQUEST_TIMEOUT  # 60 secunde
        )

        # 5. Verificare răspuns
        if resp.status_code != 200:
            return {"success": False, ..., "error": f"Ollama error: {resp.status_code}"}

        raw_text = resp.json().get("response", "")  # Textul generat
        if not raw_text:
            return {"success": False, ..., "error": "Empty response from Ollama."}

        # 6. Parsare și returnare
        jokes = self._parse_jokes(raw_text)
        if len(jokes) > num_jokes:
            jokes = jokes[:num_jokes]  # Trunchiază dacă LLM a generat prea multe

        return {"success": True, "jokes": jokes, "raw_response": raw_text, "error": None}

    except requests.exceptions.ConnectionError:
        return {"success": False, ..., "error": "Lost connection to Ollama."}
    except requests.exceptions.Timeout:
        return {"success": False, ..., "error": "Request timed out."}
```

**Parametrii de generare:**
- `temperature: 0.9` — Cât de "creativ" e modelul. 0 = determinist (același răspuns mereu), 1 = maxim aleator. 0.9 = foarte creativ (bun pentru glume).
- `top_p: 0.95` — "Nucleus sampling". Consideră doar tokenii cu probabilitate cumulativă ≤ 95%. Elimină răspunsuri absurde.
- `num_predict: 1024` — Maximum tokeni în răspuns. Previne răspunsuri infinite.

**De ce returnează dict și nu aruncă excepții?** Design choice: GUI-ul verifică `result["success"]` în loc de try/except. Mai curat pentru fluxul asincron cu threads.

### _parse_jokes() (liniile 81-108)

```python
def _parse_jokes(self, raw_text: str) -> list[str]:
    jokes = []
    current = []  # Buffer pentru gluma curentă

    for line in raw_text.strip().split('\n'):
        line = line.strip()

        if not line:  # Linie goală = separator
            if current:
                jokes.append('\n'.join(current))
                current = []
            continue

        # Linie care începe cu cifră sau "-" = glumă nouă
        if line[0].isdigit() or line.startswith('-'):
            if current:
                jokes.append('\n'.join(current))
                current = []

        current.append(line)

    if current:  # Ultima glumă
        jokes.append('\n'.join(current))

    # Filtrare: elimină fragmente < 10 caractere
    jokes = [j.strip() for j in jokes if len(j.strip()) > 10]

    return jokes if jokes else [raw_text]  # Fallback: returnează tot textul
```

**Logica de parsare:** LLM-ul returnează text de genul:
```
1. Why do programmers prefer dark mode?
Because light attracts bugs!

2. I told my computer I needed a break.
Now it won't stop sending me vacation ads.
```

Parser-ul: împarte la linii goale SAU la cifre noi → obține fiecare glumă separat.

---

## Fișierul 3: prompts.py (61 linii)

Cel mai mic din cele 3, dar **crucial** — definește CUM vorbim cu AI-ul.

### Constantele SYSTEM, TONES, EXAMPLES (liniile 3-32)

```python
SYSTEM = {
    "English": "You are a witty stand-up comedian specializing in clever wordplay...",
    "Romanian": "Ești un comedian român cu simț ascuțit, specializat în umor situațional..."
}

TONES = {
    "English": {
        "Clean": "Family-friendly humor with clever observations and harmless puns.",
        "Dark": "Edgy black comedy about life's absurdities - dry wit, NOT harmful content.",
        "Sarcastic": "Witty, ironic observations with a cynical edge..."
    },
    "Romanian": { ... }
}

EXAMPLES = {
    "English": {
        "Clean": "Why do programmers prefer dark mode? Because light attracts bugs.",
        "Dark": "I have a fish that can breakdance. Only for 20 seconds though, and only once.",
        ...
    },
    "Romanian": { ... }
}
```

**De ce exemple?** "Few-shot prompting" — când dai LLM-ului un exemplu de output dorit, calitatea răspunsului crește semnificativ. Modelul înțelege stilul, lungimea, și formatul așteptat.

### Funcția build() (liniile 35-60)

```python
def build(context: str, num_jokes: int, language: str, tone: str) -> str:
    # Validare cu fallback
    lang = language if language in SYSTEM else "English"
    tone = tone if tone in TONES[lang] else "Clean"

    system = SYSTEM[lang]           # Personalitatea
    tone_guide = TONES[lang][tone]  # Descrierea tonului
    example = EXAMPLES[lang][tone]  # Exemplu concret

    # Prompt diferit per limbă
    if lang == "Romanian":
        return f"""{system}

Ton: {tone} - {tone_guide}
Exemplu: {example}

Generează EXACT {num_jokes} glumă/glume despre: {context}

IMPORTANT: Exact {num_jokes} glume, numerotate (1., 2., etc.), în română, cu linie goală între ele."""

    return f"""{system}

Tone: {tone} - {tone_guide}
Example: {example}

Generate EXACTLY {num_jokes} joke(s) about: {context}

IMPORTANT: Exactly {num_jokes} jokes, numbered (1., 2., etc.), in English, with blank line between them."""
```

**Structura promptului:**
1. **System prompt** — "Ești un comedian..." → definește rolul
2. **Ton + descriere** — "Clean - Family-friendly..." → definește stilul
3. **Exemplu** — O glumă model → arată formatul dorit
4. **Cererea** — "Generate EXACTLY 3 jokes about: programming"
5. **Instrucțiuni stricte** — "numbered, with blank line" → controlează formatarea

**De ce "EXACTLY" și "IMPORTANT"?** LLM-urile tind să ignore instrucțiuni subtile. Cuvintele tari (EXACTLY, IMPORTANT, MUST) cresc compliance-ul.

**De ce formatul specific (numerotate, linii goale)?** Pentru că `_parse_jokes()` se bazează pe acest format ca să separe glumele. Dacă LLM-ul ar returna text continuu, parser-ul ar eșua.

---

## Cum interacționează cele 3 fișiere

```
┌─────────────────────────────────────────────────────┐
│                    gui.py                            │
│                                                     │
│  [Connect] ──────────► joke_generator.__init__()    │
│                              │                      │
│                              ▼                      │
│                       _check_ollama()               │
│                       (GET /api/tags)               │
│                                                     │
│  [Generate] ─────────► generate_jokes()             │
│       │                      │                      │
│       │                      ▼                      │
│       │               prompts.build()  ◄──── prompts.py
│       │                      │                      │
│       │                      ▼                      │
│       │               POST /api/generate            │
│       │                      │                      │
│       │                      ▼                      │
│       │               _parse_jokes()                │
│       │                      │                      │
│       ▼                      ▼                      │
│  _on_generation_complete(result)                    │
│       │                                             │
│       ▼                                             │
│  _set_output() ─── afișează glumele                 │
└─────────────────────────────────────────────────────┘
```

---

## Întrebări de verificare

1. De ce operațiile cu Ollama rulează pe thread-uri separate și nu pe thread-ul principal?
2. Ce face `root.after(0, callback)` și de ce e necesar?
3. Ce se întâmplă dacă utilizatorul apasă "Generate" de 2 ori rapid? Cum prevenim asta?
4. De ce `_parse_jokes()` filtrează intrările cu < 10 caractere?
5. Ce efect are `temperature: 0.9` asupra glumelor generate?
6. De ce promptul include "EXACTLY" și "IMPORTANT"?
7. Ce se întâmplă în GUI dacă Ollama nu e pornit când utilizatorul apasă Connect?
8. De ce `output_text` e `state="disabled"` și cum scriem totuși în el?
9. Care e diferența între `tk.Button` și `ttk.Button` și de ce le folosim pe ambele?
10. Ce e un callback și unde apare acest pattern în cod?
