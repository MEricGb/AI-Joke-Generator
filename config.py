# Configuration for AI Joke Generator - Ollama Version

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# =============================================================================
# Ollama Configuration (Free, Local LLM)
# =============================================================================
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2" 

# Generation settings
GENERATION_CONFIG = {
    "temperature": 0.9,      # Higher for more creative jokes
    "top_p": 0.95,
    "num_predict": 1024,     # Max tokens to generate
}

# Request timeout in seconds
REQUEST_TIMEOUT = 60


# Supported languages
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Romanian": "ro"
}

# Joke tone options
JOKE_TONES = [
    "Clean",
    "Dark",
    "Sarcastic"
]

# Number of jokes constraints
MIN_JOKES = 1
MAX_JOKES = 10
DEFAULT_JOKES = 3


# TTS language mapping
TTS_LANGUAGES = {
    "English": "en",
    "Romanian": "ro"
}

# Temporary audio file path
TEMP_AUDIO_FILE = "temp_joke_audio.mp3"


JOKE_PROMPT_TEMPLATE = """You are a professional comedian. Generate exactly {num_jokes} {tone} joke(s) in {language} based on the following context/keywords: {context}

Rules:
1. Each joke must be clearly numbered (1., 2., etc.)
2. Keep jokes appropriate for the selected tone ({tone})
3. Make jokes relevant to the provided context
4. Write in {language} language only
5. Each joke should be self-contained and complete
6. Add a blank line between jokes for readability

Generate the jokes now:"""
