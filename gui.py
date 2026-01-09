"""
Modern GUI Module for the AI Joke Generator (Ollama Version).

Implements a clean, modern graphical user interface using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from typing import Optional, List

import config
import utils
import text_processing
from joke_generator import JokeGenerator, JokeGeneratorError
from tts_engine import TTSEngine, TTSEngineError
from stt_engine import STTEngine, STTEngineError


class ModernStyle:
    """Modern color scheme and styling."""

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
    FONT_TITLE = ("Segoe UI", 24, "bold")
    FONT_SUBTITLE = ("Segoe UI", 11)
    FONT_HEADING = ("Segoe UI", 12, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_BUTTON = ("Segoe UI", 10, "bold")
    FONT_MONO = ("Consolas", 11)
    FONT_SMALL = ("Segoe UI", 9)


class JokeGeneratorApp:
    """Modern AI Joke Generator GUI."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.joke_generator: Optional[JokeGenerator] = None
        self.tts_engine: Optional[TTSEngine] = None
        self.current_jokes: List[str] = []
        self.current_language = "English"
        self.is_generating = False

        self._setup_window()
        self._setup_styles()
        self._init_services()
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self) -> None:
        """Configure the main window."""
        self.root.title("AI Joke Generator")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        self.root.configure(bg=ModernStyle.BG_DARK)

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 900) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"900x700+{x}+{y}")

    def _setup_styles(self) -> None:
        """Configure ttk styles for modern look."""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Frame styles
        self.style.configure("Card.TFrame", background=ModernStyle.BG_CARD)
        self.style.configure("Dark.TFrame", background=ModernStyle.BG_DARK)

        # Label styles
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

        # Scale style
        self.style.configure("Modern.Horizontal.TScale",
            background=ModernStyle.BG_CARD,
            troughcolor=ModernStyle.BG_INPUT,
            sliderthickness=20)

        # Radiobutton style
        self.style.configure("Modern.TRadiobutton",
            background=ModernStyle.BG_CARD,
            foreground=ModernStyle.TEXT_PRIMARY,
            font=ModernStyle.FONT_BODY)

        self.style.map("Modern.TRadiobutton",
            background=[("active", ModernStyle.BG_CARD)])

    def _init_services(self) -> None:
        """Initialize services."""
        try:
            self.tts_engine = TTSEngine()
        except TTSEngineError:
            self.tts_engine = None

        try:
            self.stt_engine = STTEngine()
        except STTEngineError:
            self.stt_engine = None

        self.joke_generator = None

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Header
        self._create_header()

        # Content area with two columns
        content_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Left column - Input
        left_col = ttk.Frame(content_frame, style="Dark.TFrame")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self._create_ollama_card(left_col)
        self._create_input_card(left_col)
        self._create_options_card(left_col)

        # Right column - Output
        right_col = ttk.Frame(content_frame, style="Dark.TFrame")
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self._create_output_card(right_col)
        self._create_analysis_card(right_col)

        # Footer with status
        self._create_footer()

    def _create_header(self) -> None:
        """Create header section."""
        header = ttk.Frame(self.main_frame, style="Dark.TFrame")
        header.pack(fill=tk.X)

        title = ttk.Label(header, text="AI Joke Generator", style="Title.TLabel")
        title.pack(anchor=tk.W)

        subtitle = ttk.Label(header,
            text="Generate context-aware jokes powered by Ollama (Local LLM)",
            style="Subtitle.TLabel")
        subtitle.pack(anchor=tk.W, pady=(5, 0))

    def _create_ollama_card(self, parent) -> None:
        """Create Ollama connection card."""
        card = self._create_card(parent, "Ollama Connection")

        # Status row
        status_frame = ttk.Frame(card, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.connection_status = ttk.Label(status_frame,
            text="Not connected",
            style="Error.TLabel")
        self.connection_status.pack(side=tk.LEFT)

        self.connect_btn = tk.Button(status_frame,
            text="Connect",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.ACCENT,
            fg=ModernStyle.BG_DARK,
            activebackground=ModernStyle.ACCENT_HOVER,
            activeforeground=ModernStyle.BG_DARK,
            relief=tk.FLAT,
            cursor="hand2",
            padx=20, pady=8,
            command=self._connect_ollama)
        self.connect_btn.pack(side=tk.RIGHT)

        # Model info
        model_label = ttk.Label(card,
            text=f"Model: {config.OLLAMA_MODEL}",
            style="Card.TLabel")
        model_label.pack(anchor=tk.W)

    def _create_input_card(self, parent) -> None:
        """Create context input card."""
        card = self._create_card(parent, "Context / Keywords")

        # Input area with text and mic button
        input_frame = ttk.Frame(card, style="Card.TFrame")
        input_frame.pack(fill=tk.X)

        self.context_text = tk.Text(input_frame,
            height=4,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            wrap=tk.WORD,
            highlightthickness=1,
            highlightbackground=ModernStyle.BORDER,
            highlightcolor=ModernStyle.ACCENT,
            padx=10, pady=10)
        self.context_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.context_text.insert("1.0", "school, exams, programming")

        # Microphone button
        mic_frame = ttk.Frame(input_frame, style="Card.TFrame")
        mic_frame.pack(side=tk.RIGHT, padx=(10, 0))

        self.mic_btn = tk.Button(mic_frame,
            text="Mic",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.ACCENT,
            activeforeground=ModernStyle.BG_DARK,
            relief=tk.FLAT,
            cursor="hand2",
            width=6,
            height=3,
            command=self._start_recording)
        self.mic_btn.pack()

        if not self.stt_engine:
            self.mic_btn.config(state=tk.DISABLED)

    def _create_options_card(self, parent) -> None:
        """Create options card."""
        card = self._create_card(parent, "Options")

        options_row = ttk.Frame(card, style="Card.TFrame")
        options_row.pack(fill=tk.X)

        # Number of jokes
        jokes_frame = ttk.Frame(options_row, style="Card.TFrame")
        jokes_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))

        ttk.Label(jokes_frame, text="Number of Jokes", style="Card.TLabel").pack(anchor=tk.W)

        self.num_jokes_var = tk.IntVar(value=3)
        self.num_jokes_scale = ttk.Scale(jokes_frame,
            from_=1, to=10,
            orient=tk.HORIZONTAL,
            variable=self.num_jokes_var,
            style="Modern.Horizontal.TScale",
            command=self._update_jokes_label)
        self.num_jokes_scale.pack(fill=tk.X, pady=(5, 0))

        self.num_jokes_label = ttk.Label(jokes_frame, text="3 jokes", style="Card.TLabel")
        self.num_jokes_label.pack(anchor=tk.W)

        # Language
        lang_frame = ttk.Frame(options_row, style="Card.TFrame")
        lang_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 15))

        ttk.Label(lang_frame, text="Language", style="Card.TLabel").pack(anchor=tk.W)

        self.language_var = tk.StringVar(value="English")
        for lang in ["English", "Romanian"]:
            rb = ttk.Radiobutton(lang_frame,
                text=lang,
                value=lang,
                variable=self.language_var,
                style="Modern.TRadiobutton")
            rb.pack(anchor=tk.W, pady=2)

        # Tone
        tone_frame = ttk.Frame(options_row, style="Card.TFrame")
        tone_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 0))

        ttk.Label(tone_frame, text="Tone", style="Card.TLabel").pack(anchor=tk.W)

        self.tone_var = tk.StringVar(value="Clean")
        self.tone_combo = ttk.Combobox(tone_frame,
            textvariable=self.tone_var,
            values=["Clean", "Dark", "Sarcastic"],
            state="readonly",
            width=12)
        self.tone_combo.pack(anchor=tk.W, pady=(5, 0))

        # Generate button
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        self.generate_btn = tk.Button(btn_frame,
            text="Generate Jokes",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.ACCENT,
            fg=ModernStyle.BG_DARK,
            activebackground=ModernStyle.ACCENT_HOVER,
            activeforeground=ModernStyle.BG_DARK,
            relief=tk.FLAT,
            cursor="hand2",
            padx=30, pady=12,
            command=self._generate_jokes)
        self.generate_btn.pack(side=tk.LEFT)

    def _create_output_card(self, parent) -> None:
        """Create output display card."""
        card = self._create_card(parent, "Generated Jokes", expand=True)

        # Output text
        self.output_text = tk.Text(card,
            font=ModernStyle.FONT_MONO,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            wrap=tk.WORD,
            highlightthickness=1,
            highlightbackground=ModernStyle.BORDER,
            highlightcolor=ModernStyle.ACCENT,
            padx=12, pady=12,
            state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        self.speak_btn = tk.Button(btn_frame,
            text="Read Aloud",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.BORDER,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=16, pady=8,
            state=tk.DISABLED,
            command=self._speak_jokes)
        self.speak_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = tk.Button(btn_frame,
            text="Stop",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.BORDER,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=16, pady=8,
            state=tk.DISABLED,
            command=self._stop_speaking)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.save_btn = tk.Button(btn_frame,
            text="Save",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.BORDER,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=16, pady=8,
            state=tk.DISABLED,
            command=self._save_jokes)
        self.save_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(btn_frame,
            text="Clear",
            font=ModernStyle.FONT_BUTTON,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_PRIMARY,
            activebackground=ModernStyle.BORDER,
            activeforeground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            padx=16, pady=8,
            command=self._clear_output)
        self.clear_btn.pack(side=tk.RIGHT)

    def _create_analysis_card(self, parent) -> None:
        """Create text analysis card."""
        card = self._create_card(parent, "Text Analysis")

        self.analysis_text = tk.Text(card,
            height=3,
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_INPUT,
            fg=ModernStyle.TEXT_SECONDARY,
            relief=tk.FLAT,
            wrap=tk.WORD,
            highlightthickness=0,
            padx=10, pady=8,
            state=tk.DISABLED)
        self.analysis_text.pack(fill=tk.X)

    def _create_card(self, parent, title: str, expand: bool = False) -> ttk.Frame:
        """Create a styled card container."""
        outer = ttk.Frame(parent, style="Dark.TFrame")
        outer.pack(fill=tk.BOTH, expand=expand, pady=(0, 15))

        card = ttk.Frame(outer, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=expand)

        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill=tk.BOTH, expand=expand, padx=20, pady=15)

        ttk.Label(inner, text=title, style="CardHeading.TLabel").pack(anchor=tk.W, pady=(0, 12))

        return inner

    def _create_footer(self) -> None:
        """Create footer with status."""
        footer = ttk.Frame(self.main_frame, style="Dark.TFrame")
        footer.pack(fill=tk.X, pady=(15, 0))

        self.status_var = tk.StringVar(value="Ready - Click 'Connect' to start")
        self.status_label = ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)

    def _update_jokes_label(self, value) -> None:
        num = int(float(value))
        self.num_jokes_label.config(text=f"{num} joke{'s' if num > 1 else ''}")

    def _connect_ollama(self) -> None:
        """Connect to Ollama."""
        self._set_status("Connecting to Ollama...")
        self.connect_btn.config(state=tk.DISABLED)

        def connect():
            try:
                self.joke_generator = JokeGenerator()
                self.root.after(0, self._on_connect_success)
            except JokeGeneratorError as e:
                self.root.after(0, lambda: self._on_connect_error(str(e)))

        threading.Thread(target=connect, daemon=True).start()

    def _on_connect_success(self) -> None:
        self.connection_status.config(text="Connected", style="Success.TLabel")
        self.connect_btn.config(state=tk.NORMAL, text="Reconnect")
        self._set_status("Connected to Ollama")

    def _on_connect_error(self, error: str) -> None:
        self.connection_status.config(text="Not connected", style="Error.TLabel")
        self.connect_btn.config(state=tk.NORMAL)
        self._set_status("Connection failed")
        messagebox.showerror("Ollama Error", error)

    def _generate_jokes(self) -> None:
        if not self.joke_generator:
            messagebox.showerror("Error", "Please connect to Ollama first.")
            return

        if self.is_generating:
            return

        context = self.context_text.get("1.0", tk.END).strip()
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
        self.generate_btn.config(state=tk.DISABLED, bg=ModernStyle.BG_INPUT)
        self._set_status("Generating jokes... (this may take a moment)")

        def generate():
            result = self.joke_generator.generate_jokes(
                context=context,
                num_jokes=num_jokes,
                language=language,
                tone=tone
            )
            self.root.after(0, lambda: self._on_generation_complete(result))

        threading.Thread(target=generate, daemon=True).start()

    def _on_generation_complete(self, result: dict) -> None:
        self.is_generating = False
        self.generate_btn.config(state=tk.NORMAL, bg=ModernStyle.ACCENT)

        if result["success"]:
            self.current_jokes = result["jokes"]
            formatted = utils.format_jokes_for_display(result["jokes"])
            self._set_output(formatted)
            self._set_status(f"Generated {len(result['jokes'])} joke(s)")

            self.speak_btn.config(state=tk.NORMAL if self.tts_engine else tk.DISABLED)
            self.save_btn.config(state=tk.NORMAL)
        else:
            self._set_output(f"Error: {result['error']}")
            self._set_status("Generation failed")
            messagebox.showerror("Error", result["error"])

    def _update_analysis(self, analysis: dict) -> None:
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete("1.0", tk.END)

        if analysis["is_valid"] and analysis["statistics"]:
            stats = analysis["statistics"]
            report = (
                f"Words: {stats['word_count']}  |  "
                f"Characters: {stats['character_count']}  |  "
                f"Language: {stats['detected_language'].upper()} ({stats['language_confidence']:.0%})  |  "
                f"Keywords: {', '.join(stats['keywords'][:4])}"
            )
            self.analysis_text.insert("1.0", report)

        self.analysis_text.config(state=tk.DISABLED)

    def _speak_jokes(self) -> None:
        if not self.tts_engine or not self.current_jokes:
            return

        self._set_status("Speaking...")
        self.speak_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        def speak():
            try:
                text = utils.format_jokes_for_tts(self.current_jokes)
                self.tts_engine.set_language(self.current_language)
                self.tts_engine.play(text, on_complete=lambda: self.root.after(0, self._on_speech_complete))
            except TTSEngineError as e:
                self.root.after(0, lambda: self._on_speech_error(str(e)))

        threading.Thread(target=speak, daemon=True).start()

    def _on_speech_complete(self) -> None:
        self.speak_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._set_status("Ready")

    def _on_speech_error(self, error: str) -> None:
        self.speak_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._set_status("Speech failed")

    def _stop_speaking(self) -> None:
        if self.tts_engine:
            self.tts_engine.stop()
            self._on_speech_complete()

    def _save_jokes(self) -> None:
        if not self.current_jokes:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save Jokes")

        if filepath:
            context = self.context_text.get("1.0", tk.END).strip()
            success, result = utils.save_jokes_to_file(
                self.current_jokes, filepath, context, self.current_language)

            if success:
                self._set_status(f"Saved to {result}")
                messagebox.showinfo("Success", f"Saved to:\n{result}")
            else:
                messagebox.showerror("Error", result)

    def _clear_output(self) -> None:
        self._set_output("")
        self.current_jokes = []
        self.speak_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self._set_status("Ready")

    def _set_output(self, text: str) -> None:
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state=tk.DISABLED)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _start_recording(self) -> None:
        """Start recording audio for speech-to-text."""
        if not self.stt_engine or self.stt_engine.is_listening:
            return

        self.mic_btn.config(bg=ModernStyle.ERROR, text="...")
        self._set_status("Listening... Speak now!")

        self.stt_engine.listen(
            timeout=5.0,
            phrase_time_limit=10.0,
            on_result=lambda text: self.root.after(0, lambda: self._on_stt_result(text)),
            on_error=lambda err: self.root.after(0, lambda: self._on_stt_error(err))
        )

    def _on_stt_result(self, text: str) -> None:
        """Handle successful speech recognition."""
        self.mic_btn.config(bg=ModernStyle.BG_INPUT, text="Mic")

        # Append to existing text or replace
        current = self.context_text.get("1.0", tk.END).strip()
        if current and current != "school, exams, programming":
            self.context_text.delete("1.0", tk.END)
            self.context_text.insert("1.0", f"{current}, {text}")
        else:
            self.context_text.delete("1.0", tk.END)
            self.context_text.insert("1.0", text)

        self._set_status(f"Heard: \"{text}\"")

    def _on_stt_error(self, error: str) -> None:
        """Handle speech recognition error."""
        self.mic_btn.config(bg=ModernStyle.BG_INPUT, text="Mic")
        self._set_status(error)

    def _on_close(self) -> None:
        if self.tts_engine:
            self.tts_engine.cleanup()
        self.root.destroy()


def run_app() -> None:
    """Run the application."""
    root = tk.Tk()
    JokeGeneratorApp(root)
    root.mainloop()
