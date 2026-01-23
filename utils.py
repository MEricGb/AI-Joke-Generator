import os
import re
from datetime import datetime
import config


def validate_context(context: str) -> tuple[bool, str]:
    if not context:
        return False, "Context cannot be empty."

    context = context.strip()
    if len(context) < 2:
        return False, "Context must be at least 2 characters."
    if len(context) > 500:
        return False, "Context must not exceed 500 characters."
    if re.match(r'^[^a-zA-Z0-9\u0100-\u017F]+$', context):
        return False, "Context must contain some letters or numbers."

    return True, ""


def format_jokes_for_display(jokes: list[str]) -> str:
    if not jokes:
        return "No jokes generated."

    parts = []
    for i, joke in enumerate(jokes, 1):
        joke = re.sub(r'^\d+[.)\-:]\s*', '', joke.strip())
        parts.append(f"{i}. {joke}")

    return "\n\n".join(parts)


def format_jokes_for_tts(jokes: list[str]) -> str:
    if not jokes:
        return ""

    parts = []
    for i, joke in enumerate(jokes, 1):
        joke = re.sub(r'^\d+[.)\-:]\s*', '', joke.strip())
        joke = re.sub(r'[*_#~`]', '', joke)
        parts.append(f"Joke number {i}. {joke}")

    return " ... ".join(parts)


def save_jokes_to_file(jokes: list[str], filepath: str = None,
                       context: str = "", language: str = "English") -> tuple[bool, str]:
    if not jokes:
        return False, "No jokes to save."

    if not filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"jokes_{timestamp}.txt"

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"AI Joke Generator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Language: {language} | Context: {context}\n")
            f.write("-" * 40 + "\n\n")

            for i, joke in enumerate(jokes, 1):
                joke = re.sub(r'^\d+[.)\-:]\s*', '', joke.strip())
                f.write(f"{i}. {joke}\n\n")

        return True, os.path.abspath(filepath)
    except OSError as e:
        return False, f"Failed to save: {e}"


def get_language_code(name: str) -> str:
    return config.SUPPORTED_LANGUAGES.get(name, "en")
