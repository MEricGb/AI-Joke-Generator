from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"
REQUEST_TIMEOUT = 60

GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 0.95,
    "num_predict": 1024,
}

# App settings
SUPPORTED_LANGUAGES = {"English": "en", "Romanian": "ro"}
TTS_LANGUAGES = {"English": "en", "Romanian": "ro"}
JOKE_TONES = ["Clean", "Dark", "Sarcastic"]
MIN_JOKES, MAX_JOKES, DEFAULT_JOKES = 1, 10, 3
