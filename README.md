# AI Joke Generator

A desktop application that generates context-aware jokes using a local LLM powered by [Ollama](https://ollama.com). Built with Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Ollama](https://img.shields.io/badge/LLM-Ollama-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **AI-Powered Jokes** — Generates jokes based on your keywords/context using Llama 3.2
- **Multiple Tones** — Clean, Dark, or Sarcastic humor styles
- **Bilingual** — Supports English and Romanian
- **Voice Input** — Speak your keywords using the built-in speech-to-text
- **Text-to-Speech** — Listen to generated jokes read aloud
- **Text Analysis** — Displays word count, detected language, and extracted keywords
- **Save to File** — Export jokes as `.txt` files
- **Dark Modern UI** — Clean, scrollable interface with a dark theme

## Prerequisites

- **Python 3.9+**
- **Ollama** — [Install Ollama](https://ollama.com/download)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/MEricGb/AI-Joke-Generator.git
   cd AI-Joke-Generator
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install requests gtts python-dotenv SpeechRecognition pyaudio
   ```

   > **Note (macOS):** PyAudio requires PortAudio:
   > ```bash
   > brew install portaudio
   > ```

3. Install and start Ollama:
   ```bash
   ollama serve
   ```

4. Pull the Llama 3.2 model (first time only):
   ```bash
   ollama pull llama3.2
   ```

5. Run the app:
   ```bash
   python3 main.py
   ```

## Usage

1. Click **Connect** to connect to your local Ollama instance
2. Enter keywords or context (e.g. `school, exams, programming`)
3. Choose the number of jokes, language, and tone
4. Click **Generate Jokes**
5. Optionally use **Read Aloud**, **Save**, or **Voice Input**

## Project Structure

```
├── main.py              # Entry point — dependency and Ollama checks
├── pyproject.toml       # Project metadata and dependencies
└── src/
    ├── config.py        # App configuration and model settings
    ├── gui.py           # Tkinter GUI with dark theme
    ├── joke_generator.py# Ollama API integration and joke parsing
    ├── prompts.py       # Prompt templates per language and tone
    ├── text_processing.py # Tokenization, language detection, keyword extraction
    ├── tts_engine.py    # Text-to-speech using gTTS
    ├── stt_engine.py    # Speech-to-text using SpeechRecognition
    └── utils.py         # Input validation, formatting, file export
```

## Configuration

Edit `src/config.py` to change:

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2` | Ollama model to use |
| `REQUEST_TIMEOUT` | `60` | API request timeout (seconds) |
| `temperature` | `0.9` | Creativity of generated jokes |
| `MAX_JOKES` | `10` | Maximum jokes per request |
