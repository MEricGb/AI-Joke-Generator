# GUI for AI Joke Generator

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional, List

import config
import utils
import text_processing
from joke_generator import JokeGenerator, JokeGeneratorError
from tts_engine import TTSEngine, TTSEngineError
from stt_engine import STTEngine, STTEngineError


# Modern color scheme and styling
class ModernStyle:
    # Colors - Dark modern theme
    BG_DARK = "#1a1b26"
    BG_CARD = "#24283b"
    BG_INPUT = "#414868"
    ACCENT = "#7aa2f7"
    ACCENT_HOVER = "#89b4fa"
    SUCCESS = "#9ece6a"
    ERROR = "#f7768e"
    WARNING = "#e0af68"
    TEXT_PRIMARY = "#c0caf5"
    TEXT_SECONDARY = "#565f89"
    TEXT_MUTED = "#414868"
    BORDER = "#414868"

    # Fonts
    FONT_TITLE = ("Helvetica", 22, "bold")
    FONT_SUBTITLE = ("Helvetica", 11)
    FONT_HEADING = ("Helvetica", 12, "bold")
    FONT_BODY = ("Helvetica", 11)
    FONT_BUTTON = ("Helvetica", 10, "bold")
    FONT_MONO = ("Courier", 11)
    FONT_SMALL = ("Helvetica", 9)


class JokeGeneratorApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.joke_generator: Optional[JokeGenerator] = None
        self.tts_engine: Optional[TTSEngine] = None
        self.stt_engine: Optional[STTEngine] = None
        self.current_jokes: List[str] = []
        self.current_language = "English"
        self.is_generating = False

        self._setup_window()
        self._setup_styles()
        self._init_services()
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        self.root.title("AI Joke Generator")
        self.root.geometry("700x800")
        self.root.minsize(500, 600)
        self.root.configure(bg=ModernStyle.BG_DARK)

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 700) // 2
        y = (self.root.winfo_screenheight() - 800) // 2
        self.root.geometry(f"700x800+{x}+{y}")

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure("Card.TFrame", background=ModernStyle.BG_CARD)
        self.style.configure("Dark.TFrame", background=ModernStyle.BG_DARK)

        self.style.configure("Title.TLabel",
            background=ModernStyle.BG_DARK,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=ModernStyle.FONT_TITLE)

        self.style.configure("Subtitle.TLabel",
            background=ModernStyle.BG_DARK,
            foreground=ModernStyle.TEXT_SECONDARY,
            font=ModernStyle.FONT_SUBTITLE)

        self.style.configure("Card.TLabel",
            background=ModernStyle.BG_CARD,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=ModernStyle.FONT_BODY)

        self.style.configure("CardHeading.TLabel",
            background=ModernStyle.BG_CARD,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=ModernStyle.FONT_HEADING)

        self.style.configure("Status.TLabel",
            background=ModernStyle.BG_DARK,
            foreground=ModernStyle.TEXT_SECONDARY,
            font=ModernStyle.FONT_SMALL)

        self.style.configure("Success.TLabel",
            background=ModernStyle.BG_CARD,
            foreground=ModernStyle.SUCCESS,
            font=ModernStyle.FONT_BODY)

        self.style.configure("Error.TLabel",
            background=ModernStyle.BG_CARD,
            foreground=ModernStyle.ERROR,
            font=ModernStyle.FONT_BODY)

        self.style.configure("Modern.Horizontal.TScale",
            background=ModernStyle.BG_CARD,
            troughcolor=ModernStyle.BG_INPUT)

        self.style.configure("Modern.TRadiobutton",
            background=ModernStyle.BG_CARD,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=ModernStyle.FONT_BODY)

        self.style.map("Modern.TRadiobutton",
            background=[("active", ModernStyle.BG_CARD)])

    def _init_services(self):
        self.stt_error_msg = None

        try:
            self.tts_engine = TTSEngine()
        except TTSEngineError:
            self.tts_engine = None

        try:
            self.stt_engine = STTEngine()
        except STTEngineError as e:
            self.stt_error_msg = str(e)
            print(f"STT not available: {e}")
            self.stt_engine = None

        self.joke_generator = None

    def _create_widgets(self):
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(self.root, bg=ModernStyle.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create frame inside canvas
        self.main_frame = ttk.Frame(self.canvas, style="Dark.TFrame")
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        self.main_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        # Build UI sections
        self._create_header()
        self._create_connection_section()
        self._create_input_section()
        self._create_options_section()
        self._create_output_section()
        self._create_analysis_section()
        self._create_footer()

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_mousewheel(self, event):
        if event.delta:
            if abs(event.delta) < 10:
                self.canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _create_header(self):
        header = ttk.Frame(self.main_frame, style="Dark.TFrame")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(header, text="AI Joke Generator", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Generate context-aware jokes powered by Ollama",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(5, 0))

    def _create_connection_section(self):
        card = self._create_card("Ollama Connection")

        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")

        self.connection_status = ttk.Label(row, text="Not connected", style="Error.TLabel")
        self.connection_status.pack(side="left")

        self.connect_btn = tk.Button(row, text="Connect",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.ACCENT, fg=ModernStyle.BG_DARK,
            activebackground=ModernStyle.ACCENT_HOVER,
            relief="flat", cursor="hand2", padx=15, pady=5,
            command=self._connect_ollama)
        self.connect_btn.pack(side="right")

        ttk.Label(card, text=f"Model: {config.OLLAMA_MODEL}",
                  style="Card.TLabel").pack(anchor="w", pady=(10, 0))

    def _create_input_section(self):
        card = self._create_card("Context / Keywords")

        self.context_text = tk.Text(card, height=3,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_INPUT, fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief="flat", wrap="word", padx=10, pady=8,
            highlightthickness=1, highlightbackground=ModernStyle.BORDER,
            highlightcolor=ModernStyle.ACCENT)
        self.context_text.pack(fill="x")
        self.context_text.insert("1.0", "school, exams, programming")

        mic_row = ttk.Frame(card, style="Card.TFrame")
        mic_row.pack(fill="x", pady=(8, 0))

        self.mic_btn = tk.Button(mic_row, text="🎤 Voice Input",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.BG_INPUT, fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.ACCENT,
            relief="flat", cursor="hand2", padx=12, pady=5,
            command=self._start_recording)
        self.mic_btn.pack(side="left")

        self.mic_status = ttk.Label(mic_row, text="", style="Card.TLabel")
        self.mic_status.pack(side="left", padx=(10, 0))

        if not self.stt_engine:
            self.mic_btn.config(state="disabled", bg=ModernStyle.TEXT_MUTED, text="🎤 Voice Input (Unavailable)")
            self.mic_btn.bind("<Button-1>", lambda e: self._show_stt_error())

    def _create_options_section(self):
        card = self._create_card("Options")

        options_row = ttk.Frame(card, style="Card.TFrame")
        options_row.pack(fill="x")

        # Number of jokes
        jokes_frame = ttk.Frame(options_row, style="Card.TFrame")
        jokes_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(jokes_frame, text="Jokes:", style="Card.TLabel").pack(side="left")
        self.num_jokes_var = tk.IntVar(value=3)
        self.num_jokes_scale = ttk.Scale(jokes_frame, from_=1, to=10,
            orient="horizontal", variable=self.num_jokes_var,
            command=self._update_jokes_label)
        self.num_jokes_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.num_jokes_label = ttk.Label(jokes_frame, text="3", style="Card.TLabel", width=2)
        self.num_jokes_label.pack(side="left")

        # Language
        lang_frame = ttk.Frame(options_row, style="Card.TFrame")
        lang_frame.pack(side="left", padx=(20, 0))

        ttk.Label(lang_frame, text="Language:", style="Card.TLabel").pack(side="left")
        self.language_var = tk.StringVar(value="English")
        for lang in ["English", "Romanian"]:
            ttk.Radiobutton(lang_frame, text=lang, value=lang,
                variable=self.language_var, style="Modern.TRadiobutton").pack(side="left", padx=3)

        # Tone
        tone_frame = ttk.Frame(options_row, style="Card.TFrame")
        tone_frame.pack(side="left", padx=(20, 0))

        ttk.Label(tone_frame, text="Tone:", style="Card.TLabel").pack(side="left")
        self.tone_var = tk.StringVar(value="Clean")
        self.tone_combo = ttk.Combobox(tone_frame, textvariable=self.tone_var,
            values=["Clean", "Dark", "Sarcastic"], state="readonly", width=10)
        self.tone_combo.pack(side="left", padx=5)

        # Generate button
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(15, 0))

        self.generate_btn = tk.Button(btn_frame, text="Generate Jokes",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.ACCENT, fg=ModernStyle.BG_DARK,
            activebackground=ModernStyle.ACCENT_HOVER,
            relief="flat", cursor="hand2", padx=20, pady=8,
            command=self._generate_jokes)
        self.generate_btn.pack(side="left")

    def _create_output_section(self):
        card = self._create_card("Generated Jokes")

        self.output_text = tk.Text(card, height=12,
            font=ModernStyle.FONT_MONO,
            bg=ModernStyle.BG_INPUT, fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief="flat", wrap="word", padx=10, pady=10,
            highlightthickness=1, highlightbackground=ModernStyle.BORDER,
            state="disabled")
        self.output_text.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=(10, 0))

        btn_style = {"font": ModernStyle.FONT_BUTTON, "bg": ModernStyle.BG_INPUT,
                     "fg": ModernStyle.TEXT_PRIMARY, "relief": "flat",
                     "cursor": "hand2", "padx": 12, "pady": 5}

        self.speak_btn = tk.Button(btn_frame, text="Read Aloud", state="disabled",
            command=self._speak_jokes, **btn_style)
        self.speak_btn.pack(side="left", padx=(0, 5))

        self.stop_btn = tk.Button(btn_frame, text="Stop", state="disabled",
            command=self._stop_speaking, **btn_style)
        self.stop_btn.pack(side="left", padx=(0, 5))

        self.save_btn = tk.Button(btn_frame, text="Save", state="disabled",
            command=self._save_jokes, **btn_style)
        self.save_btn.pack(side="left")

        self.clear_btn = tk.Button(btn_frame, text="Clear",
            command=self._clear_output, **btn_style)
        self.clear_btn.pack(side="right")

    def _create_analysis_section(self):
        card = self._create_card("Text Analysis")

        self.analysis_text = tk.Text(card, height=2,
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_INPUT, fg=ModernStyle.TEXT_PRIMARY,
            relief="flat", wrap="word", padx=10, pady=8,
            state="disabled")
        self.analysis_text.pack(fill="x")

    def _create_card(self, title: str) -> ttk.Frame:
        outer = ttk.Frame(self.main_frame, style="Dark.TFrame")
        outer.pack(fill="x", padx=20, pady=(0, 10))

        card = ttk.Frame(outer, style="Card.TFrame")
        card.pack(fill="x")

        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=15, pady=12)

        ttk.Label(inner, text=title, style="CardHeading.TLabel").pack(anchor="w", pady=(0, 10))

        return inner

    def _create_footer(self):
        footer = ttk.Frame(self.main_frame, style="Dark.TFrame")
        footer.pack(fill="x", padx=20, pady=(5, 20))

        self.status_var = tk.StringVar(value="Ready - Click 'Connect' to start")
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

    # Event handlers

    def _update_jokes_label(self, value):
        self.num_jokes_label.config(text=str(int(float(value))))

    def _connect_ollama(self):
        self._set_status("Connecting to Ollama...")
        self.connect_btn.config(state="disabled")

        def connect():
            try:
                self.joke_generator = JokeGenerator()
                self.root.after(0, self._on_connect_success)
            except JokeGeneratorError as e:
                self.root.after(0, lambda: self._on_connect_error(str(e)))

        threading.Thread(target=connect, daemon=True).start()

    def _on_connect_success(self):
        self.connection_status.config(text="Connected", style="Success.TLabel")
        self.connect_btn.config(state="normal", text="Reconnect")
        self._set_status("Connected to Ollama")

    def _on_connect_error(self, error: str):
        self.connection_status.config(text="Not connected", style="Error.TLabel")
        self.connect_btn.config(state="normal")
        self._set_status("Connection failed")
        messagebox.showerror("Ollama Error", error)

    def _generate_jokes(self):
        if not self.joke_generator:
            messagebox.showerror("Error", "Please connect to Ollama first.")
            return

        if self.is_generating:
            return

        context = self.context_text.get("1.0", "end").strip()
        num_jokes = int(self.num_jokes_var.get())
        language = self.language_var.get()
        tone = self.tone_var.get()

        is_valid, error = utils.validate_context(context)
        if not is_valid:
            messagebox.showerror("Invalid Input", error)
            return

        analysis = text_processing.analyze_input(context)
        self._update_analysis(analysis)

        self.current_language = language
        self.is_generating = True
        self.generate_btn.config(state="disabled", bg=ModernStyle.BG_INPUT)
        self._set_status("Generating jokes...")

        def generate():
            result = self.joke_generator.generate_jokes(
                context=context, num_jokes=num_jokes,
                language=language, tone=tone)
            self.root.after(0, lambda: self._on_generation_complete(result))

        threading.Thread(target=generate, daemon=True).start()

    def _on_generation_complete(self, result: dict):
        self.is_generating = False
        self.generate_btn.config(state="normal", bg=ModernStyle.ACCENT)

        if result["success"]:
            self.current_jokes = result["jokes"]
            formatted = utils.format_jokes_for_display(result["jokes"])
            self._set_output(formatted)
            self._set_status(f"Generated {len(result['jokes'])} joke(s)")
            self.speak_btn.config(state="normal" if self.tts_engine else "disabled")
            self.save_btn.config(state="normal")
        else:
            self._set_output(f"Error: {result['error']}")
            self._set_status("Generation failed")
            messagebox.showerror("Error", result["error"])

    def _update_analysis(self, analysis: dict):
        self.analysis_text.config(state="normal")
        self.analysis_text.delete("1.0", "end")

        if analysis["is_valid"] and analysis["statistics"]:
            stats = analysis["statistics"]
            report = (f"Words: {stats['word_count']}  |  "
                     f"Characters: {stats['character_count']}  |  "
                     f"Language: {stats['detected_language'].upper()} ({stats['language_confidence']:.0%})  |  "
                     f"Keywords: {', '.join(stats['keywords'][:4])}")
            self.analysis_text.insert("1.0", report)

        self.analysis_text.config(state="disabled")

    def _speak_jokes(self):
        if not self.tts_engine or not self.current_jokes:
            return

        self._set_status("Speaking...")
        self.speak_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        def speak():
            try:
                text = utils.format_jokes_for_tts(self.current_jokes)
                self.tts_engine.set_language(self.current_language)
                self.tts_engine.play(text, on_complete=lambda: self.root.after(0, self._on_speech_complete))
            except TTSEngineError:
                self.root.after(0, self._on_speech_complete)

        threading.Thread(target=speak, daemon=True).start()

    def _on_speech_complete(self):
        self.speak_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._set_status("Ready")

    def _stop_speaking(self):
        if self.tts_engine:
            self.tts_engine.stop()
            self._on_speech_complete()

    def _save_jokes(self):
        if not self.current_jokes:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save Jokes")

        if filepath:
            context = self.context_text.get("1.0", "end").strip()
            success, result = utils.save_jokes_to_file(
                self.current_jokes, filepath, context, self.current_language)

            if success:
                self._set_status(f"Saved to {result}")
                messagebox.showinfo("Success", f"Saved to:\n{result}")
            else:
                messagebox.showerror("Error", result)

    def _clear_output(self):
        self._set_output("")
        self.current_jokes = []
        self.speak_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self._set_status("Ready")

    def _set_output(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def _set_status(self, message: str):
        self.status_var.set(message)

    def _start_recording(self):
        if not self.stt_engine or self.stt_engine.is_listening:
            return

        self.mic_btn.config(bg=ModernStyle.ERROR, text="🎤 Listening...")
        self.mic_status.config(text="Calibrating... then speak")
        self._set_status("Calibrating microphone... speak after 1 second")

        self.stt_engine.listen(
            timeout=8.0,
            phrase_time_limit=15.0,
            on_result=lambda text: self.root.after(0, lambda: self._on_stt_result(text)),
            on_error=lambda err: self.root.after(0, lambda: self._on_stt_error(err))
        )

    def _on_stt_result(self, text: str):
        self.mic_btn.config(bg=ModernStyle.BG_INPUT, text="🎤 Voice Input")
        self.mic_status.config(text="")

        current = self.context_text.get("1.0", "end").strip()
        if current and current != "school, exams, programming":
            self.context_text.delete("1.0", "end")
            self.context_text.insert("1.0", f"{current}, {text}")
        else:
            self.context_text.delete("1.0", "end")
            self.context_text.insert("1.0", text)

        self._set_status(f"Heard: \"{text}\"")

    def _on_stt_error(self, error: str):
        self.mic_btn.config(bg=ModernStyle.BG_INPUT, text="🎤 Voice Input")
        self.mic_status.config(text="")
        self._set_status(error)

    def _show_stt_error(self):
        if self.stt_error_msg:
            messagebox.showwarning("Microphone Unavailable", self.stt_error_msg)
        else:
            messagebox.showwarning("Microphone Unavailable",
                "Microphone is not available.\n\n"
                "Make sure you have:\n"
                "1. A microphone connected\n"
                "2. PyAudio installed (pip install pyaudio)\n"
                "3. Granted microphone permissions")

    def _on_close(self):
        if self.tts_engine:
            self.tts_engine.cleanup()
        self.root.destroy()


def run_app():
    root = tk.Tk()
    JokeGeneratorApp(root)
    root.mainloop()
