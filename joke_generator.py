# Joke generation using Ollama local LLM

import requests
import config
import prompts


class JokeGeneratorError(Exception):
    pass


class JokeGenerator:

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self._check_ollama()

    def _check_ollama(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                raise JokeGeneratorError("Ollama not responding. Run: ollama serve")

            models = [m.get("name", "").split(":")[0] for m in resp.json().get("models", [])]
            if self.model not in models:
                raise JokeGeneratorError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")

        except requests.exceptions.ConnectionError:
            raise JokeGeneratorError("Cannot connect to Ollama. Run: ollama serve")
        except requests.exceptions.Timeout:
            raise JokeGeneratorError("Ollama connection timed out.")

    def generate_jokes(self, context: str, num_jokes: int = 3,
                       language: str = "English", tone: str = "Clean") -> dict:
        if not context or not context.strip():
            return {"success": False, "jokes": [], "raw_response": "", "error": "Context cannot be empty."}

        num_jokes = max(config.MIN_JOKES, min(num_jokes, config.MAX_JOKES))
        language = language if language in config.SUPPORTED_LANGUAGES else "English"
        tone = tone if tone in config.JOKE_TONES else "Clean"

        prompt = prompts.build(context, num_jokes, language, tone)

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.GENERATION_CONFIG["temperature"],
                        "top_p": config.GENERATION_CONFIG["top_p"],
                        "num_predict": config.GENERATION_CONFIG["num_predict"],
                    }
                },
                timeout=config.REQUEST_TIMEOUT
            )

            if resp.status_code != 200:
                return {"success": False, "jokes": [], "raw_response": "", "error": f"Ollama error: {resp.status_code}"}

            raw_text = resp.json().get("response", "")
            if not raw_text:
                return {"success": False, "jokes": [], "raw_response": "", "error": "Empty response from Ollama."}

            jokes = self._parse_jokes(raw_text)
            if len(jokes) > num_jokes:
                jokes = jokes[:num_jokes]

            return {"success": True, "jokes": jokes, "raw_response": raw_text, "error": None}

        except requests.exceptions.ConnectionError:
            return {"success": False, "jokes": [], "raw_response": "", "error": "Lost connection to Ollama."}
        except requests.exceptions.Timeout:
            return {"success": False, "jokes": [], "raw_response": "", "error": "Request timed out."}
        except Exception as e:
            return {"success": False, "jokes": [], "raw_response": "", "error": str(e)}

    def _parse_jokes(self, raw_text: str) -> list[str]:
        if not raw_text:
            return []

        jokes = []
        current = []

        for line in raw_text.strip().split('\n'):
            line = line.strip()
            if not line:
                if current:
                    jokes.append('\n'.join(current))
                    current = []
                continue

            if line[0].isdigit() or line.startswith('-'):
                if current:
                    jokes.append('\n'.join(current))
                    current = []

            current.append(line)

        if current:
            jokes.append('\n'.join(current))

        # Filter short entries
        jokes = [j.strip() for j in jokes if len(j.strip()) > 10]
        return jokes if jokes else [raw_text]
