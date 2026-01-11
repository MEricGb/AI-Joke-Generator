"""
Joke Generator Module using Ollama (Local LLM).

Handles LLM integration with Ollama for free, unlimited joke generation.
"""

import requests
from typing import List, Optional, Dict
import config


class JokeGeneratorError(Exception):
    """Custom exception for joke generation errors."""
    pass


class JokeGenerator:
    """
    Generates jokes using Ollama local LLM.

    Attributes:
        base_url: Ollama server URL
        model: Model name to use
        is_configured: Whether Ollama is available
    """

    def __init__(self):
        """Initialize the JokeGenerator with Ollama."""
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.is_configured = False

        self._check_ollama()

    def _check_ollama(self) -> None:
        """Check if Ollama is running and model is available."""
        try:
            # Check if Ollama is running
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )

            if response.status_code != 200:
                raise JokeGeneratorError(
                    "Ollama is not responding. Make sure it's running:\n"
                    "  ollama serve"
                )

            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            if self.model not in model_names and f"{self.model}:latest" not in [m.get("name", "") for m in models]:
                available = ", ".join(model_names[:5]) if model_names else "none"
                raise JokeGeneratorError(
                    f"Model '{self.model}' not found. Pull it with:\n"
                    f"  ollama pull {self.model}\n\n"
                    f"Available models: {available}"
                )

            self.is_configured = True

        except requests.exceptions.ConnectionError:
            raise JokeGeneratorError(
                "Cannot connect to Ollama. Start it with:\n"
                "  ollama serve"
            )
        except requests.exceptions.Timeout:
            raise JokeGeneratorError("Ollama connection timed out.")

    def _build_prompt(
        self,
        context: str,
        num_jokes: int,
        language: str,
        tone: str
    ) -> str:
        """Build the prompt for joke generation."""
        return config.build_joke_prompt(
            context=context,
            num_jokes=num_jokes,
            language=language,
            tone=tone
        )

    def generate_jokes(
        self,
        context: str,
        num_jokes: int = 3,
        language: str = "English",
        tone: str = "Clean"
    ) -> Dict:
        """
        Generate jokes using Ollama.

        Args:
            context: Keywords or context for joke generation
            num_jokes: Number of jokes to generate (1-10)
            language: Target language
            tone: Humor style

        Returns:
            Dictionary with success status, jokes, and any errors
        """
        if not self.is_configured:
            return {
                "success": False,
                "jokes": [],
                "raw_response": "",
                "error": "Ollama not configured. Run: ollama serve"
            }

        # Validate inputs
        if not context or not context.strip():
            return {
                "success": False,
                "jokes": [],
                "raw_response": "",
                "error": "Context cannot be empty."
            }

        # Clamp num_jokes
        num_jokes = max(config.MIN_JOKES, min(num_jokes, config.MAX_JOKES))

        # Validate language and tone
        if language not in config.SUPPORTED_LANGUAGES:
            language = "English"
        if tone not in config.JOKE_TONES:
            tone = "Clean"

        # Build prompt
        prompt = self._build_prompt(context, num_jokes, language, tone)

        try:
            # Call Ollama API
            response = requests.post(
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

            if response.status_code != 200:
                return {
                    "success": False,
                    "jokes": [],
                    "raw_response": "",
                    "error": f"Ollama error: {response.status_code}"
                }

            result = response.json()
            raw_text = result.get("response", "")

            if raw_text:
                jokes = self._parse_jokes(raw_text)
                return {
                    "success": True,
                    "jokes": jokes,
                    "raw_response": raw_text,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "jokes": [],
                    "raw_response": "",
                    "error": "Empty response from Ollama."
                }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "jokes": [],
                "raw_response": "",
                "error": "Lost connection to Ollama. Is it still running?"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "jokes": [],
                "raw_response": "",
                "error": "Request timed out. Try fewer jokes or simpler context."
            }
        except Exception as e:
            return {
                "success": False,
                "jokes": [],
                "raw_response": "",
                "error": f"Error: {str(e)}"
            }

    def _parse_jokes(self, raw_text: str) -> List[str]:
        """Parse individual jokes from the raw response."""
        if not raw_text:
            return []

        jokes = []
        lines = raw_text.strip().split('\n')
        current_joke = []

        for line in lines:
            line = line.strip()

            if not line:
                if current_joke:
                    jokes.append('\n'.join(current_joke))
                    current_joke = []
                continue

            if line and (line[0].isdigit() or line.startswith('-')):
                if current_joke:
                    jokes.append('\n'.join(current_joke))
                    current_joke = []

            current_joke.append(line)

        if current_joke:
            jokes.append('\n'.join(current_joke))

        # Clean up
        cleaned_jokes = []
        for joke in jokes:
            joke = joke.strip()
            if joke and len(joke) > 10:
                cleaned_jokes.append(joke)

        return cleaned_jokes if cleaned_jokes else [raw_text]


def create_generator() -> Optional[JokeGenerator]:
    """Factory function to create a JokeGenerator instance."""
    try:
        return JokeGenerator()
    except JokeGeneratorError as e:
        print(f"Warning: {e}")
        return None
