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


# =============================================================================
# Language-Specific Joke Prompts
# =============================================================================

JOKE_PROMPTS = {
    "English": {
        "system": """You are a witty stand-up comedian who specializes in clever wordplay, puns, and observational humor. Your jokes follow the classic setup-punchline structure and are influenced by comedians like Jerry Seinfeld, Mitch Hedberg, and John Mulaney.""",
        "tone_guidance": {
            "Clean": "Family-friendly humor suitable for all ages. Focus on clever observations, harmless puns, and relatable everyday situations.",
            "Dark": "Edgy black comedy that finds humor in life's absurdities, awkward situations, and ironic observations. Think dry wit about mundane frustrations, NOT harmful content. Similar to Anthony Jeselnik's style but without offensive material.",
            "Sarcastic": "Witty, ironic observations with a cynical edge. Mock everyday absurdities and social situations with sharp, clever commentary."
        },
        "examples": {
            "Clean": [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "I told my wife she was drawing her eyebrows too high. She looked surprised."
            ],
            "Dark": [
                "I have a fish that can breakdance. Only for 20 seconds though, and only once.",
                "My grandfather has the heart of a lion and a lifetime ban from the zoo."
            ],
            "Sarcastic": [
                "I'm not saying I hate morning people, but I've never seen a sunrise I couldn't sleep through.",
                "Nothing says 'I trust you' like sending an email that starts with 'As per my last email...'"
            ]
        }
    },
    "Romanian": {
        "system": """Ești un comedian român cu simț al umorului ascuțit, specializat în umor situațional, auto-ironic și absurd. Stilul tău este influențat de umorul românesc autentic - observații despre viața de zi cu zi, birocraație, și situații cotidiene tipic românești.""",
        "tone_guidance": {
            "Clean": "Umor pentru toate vârstele. Jocuri de cuvinte, observații amuzante despre viața românească, situații familiare și glume inofensive.",
            "Dark": "Umor negru în stil românesc - ironie despre birocrație, sistemul de sănătate, transportul în comun, și absurditățile vieții. Găsește umorul în frustrările zilnice, NU conținut dăunător. Umor cinic dar nu ofensator.",
            "Sarcastic": "Observații ironice și cinice despre societatea românească, politică (fără a fi partizan), și situații sociale. Sarcasm inteligent despre viața modernă."
        },
        "examples": {
            "Clean": [
                "De ce programatorii români lucrează noaptea? Pentru că ziua sunt în ședințe.",
                "Am întrebat GPS-ul cum ajung cel mai repede acasă. Mi-a zis să plec de la muncă."
            ],
            "Dark": [
                "La CFR, trenul întârzie atât de mult încât pasagerii au timp să-și facă prieteni, să se certe, și să se împace.",
                "Am fost la urgențe. După 6 ore de așteptare, m-am vindecat de curiozitate."
            ],
            "Sarcastic": [
                "Nimic nu spune 'eficiență' ca o ședință de 2 ore despre cum să fim mai productivi.",
                "Îmi place cum facturile vin întotdeauna la timp, dar salariul are nevoie de o săptămână să 'se proceseze'."
            ]
        }
    }
}


def build_joke_prompt(context: str, num_jokes: int, language: str, tone: str) -> str:
    """Build a language-specific prompt for joke generation."""
    lang_config = JOKE_PROMPTS.get(language, JOKE_PROMPTS["English"])

    # Get examples for the selected tone
    examples = lang_config["examples"].get(tone, lang_config["examples"]["Clean"])
    examples_text = "\n".join(f"- {ex}" for ex in examples)

    # Get tone guidance
    tone_guide = lang_config["tone_guidance"].get(tone, lang_config["tone_guidance"]["Clean"])

    if language == "Romanian":
        prompt = f"""{lang_config["system"]}

Tonul dorit: {tone}
Ghid pentru ton: {tone_guide}

Exemple de referință (pentru stil, nu copia):
{examples_text}

Generează EXACT {num_jokes} glumă/glume bazate pe următorul context: {context}

IMPORTANT: Generează EXACT {num_jokes} - nu mai multe, nu mai puține!

Reguli:
1. Numerotează fiecare glumă (1., 2., etc.)
2. Scrie DOAR în limba română
3. Glumele trebuie să fie relevante pentru context
4. Fiecare glumă trebuie să fie completă și de sine stătătoare
5. Adaugă o linie goală între glume
6. OPREȘTE-TE după gluma numărul {num_jokes}

Generează glumele acum:"""
    else:
        prompt = f"""{lang_config["system"]}

Desired tone: {tone}
Tone guidance: {tone_guide}

Reference examples (for style, don't copy):
{examples_text}

Generate EXACTLY {num_jokes} joke(s) based on the following context: {context}

IMPORTANT: Generate EXACTLY {num_jokes} jokes - no more, no less!

Rules:
1. Number each joke (1., 2., etc.)
2. Write ONLY in English
3. Jokes must be relevant to the provided context
4. Each joke should be complete and self-contained
5. Add a blank line between jokes
6. STOP after joke number {num_jokes}

Generate the jokes now:"""

    return prompt


# Legacy template (kept for compatibility)
JOKE_PROMPT_TEMPLATE = """You are a professional comedian. Generate exactly {num_jokes} {tone} joke(s) in {language} based on the following context/keywords: {context}

Rules:
1. Each joke must be clearly numbered (1., 2., etc.)
2. Keep jokes appropriate for the selected tone ({tone})
3. Make jokes relevant to the provided context
4. Write in {language} language only
5. Each joke should be self-contained and complete
6. Add a blank line between jokes for readability

Generate the jokes now:"""
