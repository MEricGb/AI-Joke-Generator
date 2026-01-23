# Prompt templates for joke generation

SYSTEM = {
    "English": "You are a witty stand-up comedian specializing in clever wordplay and observational humor.",
    "Romanian": "Ești un comedian român cu simț ascuțit, specializat în umor situațional și auto-ironic."
}

TONES = {
    "English": {
        "Clean": "Family-friendly humor with clever observations and harmless puns.",
        "Dark": "Edgy black comedy about life's absurdities - dry wit, NOT harmful content.",
        "Sarcastic": "Witty, ironic observations with a cynical edge about everyday absurdities."
    },
    "Romanian": {
        "Clean": "Umor pentru toate vârstele - jocuri de cuvinte și observații amuzante.",
        "Dark": "Umor negru despre birocrație și frustrările zilnice - cinic dar nu ofensator.",
        "Sarcastic": "Observații ironice despre societatea românească și viața modernă."
    }
}

EXAMPLES = {
    "English": {
        "Clean": "Why do programmers prefer dark mode? Because light attracts bugs.",
        "Dark": "I have a fish that can breakdance. Only for 20 seconds though, and only once.",
        "Sarcastic": "Nothing says 'I trust you' like an email starting with 'As per my last email...'"
    },
    "Romanian": {
        "Clean": "De ce programatorii români lucrează noaptea? Pentru că ziua sunt în ședințe.",
        "Dark": "Am fost la urgențe. După 6 ore de așteptare, m-am vindecat de curiozitate.",
        "Sarcastic": "Nimic nu spune 'eficiență' ca o ședință de 2 ore despre cum să fim mai productivi."
    }
}


def build(context: str, num_jokes: int, language: str, tone: str) -> str:
    lang = language if language in SYSTEM else "English"
    tone = tone if tone in TONES[lang] else "Clean"

    system = SYSTEM[lang]
    tone_guide = TONES[lang][tone]
    example = EXAMPLES[lang][tone]

    if lang == "Romanian":
        return f"""{system}

Ton: {tone} - {tone_guide}
Exemplu: {example}

Generează EXACT {num_jokes} glumă/glume despre: {context}

IMPORTANT: Exact {num_jokes} glume, numerotate (1., 2., etc.), în română, cu linie goală între ele."""

    return f"""{system}

Tone: {tone} - {tone_guide}
Example: {example}

Generate EXACTLY {num_jokes} joke(s) about: {context}

IMPORTANT: Exactly {num_jokes} jokes, numbered (1., 2., etc.), in English, with blank line between them."""
