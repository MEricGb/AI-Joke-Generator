# AI Joke Generator

Desktop app that generates jokes using Ollama (Llama 3.2) running locally. You give it some keywords, pick a tone and language, and it comes up with jokes. Also has voice input and can read the jokes out loud.

## What it does

- Generates jokes based on keywords/context you provide
- 3 tone options: Clean, Dark, Sarcastic
- Works in English and Romanian
- Voice input (speak your keywords instead of typing)
- Text-to-speech (reads jokes aloud)
- Basic text analysis (word count, language detection, keywords)
- Save jokes to a `.txt` file

## Setup

You need Python 3.9+ and [Ollama](https://ollama.com/download).

```bash
# clone and cd into the project
git clone https://github.com/MEricGb/AI-Joke-Generator.git
cd AI-Joke-Generator

# create a venv and install deps
python3 -m venv venv
source venv/bin/activate
pip install requests gtts python-dotenv SpeechRecognition pyaudio

# on macOS, pyaudio needs portaudio
brew install portaudio

# start ollama and pull the model (first time only)
ollama serve
ollama pull llama3.2

# run
python3 main.py
```

## How to use

1. Hit **Connect** to connect to Ollama
2. Type in some keywords (e.g. `school, exams, programming`)
3. Pick how many jokes, the language, and the tone
4. Click **Generate Jokes**
5. You can also use **Read Aloud**, **Save**, or **Voice Input**

## Project structure

```
├── main.py                # entry point
├── pyproject.toml
└── src/
    ├── config.py          # settings (model, timeouts, etc.)
    ├── gui.py             # tkinter GUI
    ├── joke_generator.py  # talks to ollama API
    ├── prompts.py         # prompt templates
    ├── text_processing.py # tokenization, language detection
    ├── tts_engine.py      # text-to-speech (gTTS)
    ├── stt_engine.py      # speech-to-text
    └── utils.py           # helpers (validation, formatting)
```

## Config

You can tweak settings in `src/config.py` — model name, timeout, temperature, max jokes, etc.
