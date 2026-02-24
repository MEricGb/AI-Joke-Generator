# Text analysis and processing utilities

import re
from collections import Counter

STOP_WORDS = {
    "en": {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
           "from", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does",
           "did", "will", "would", "could", "should", "this", "that", "i", "you", "he", "she", "it",
           "we", "they", "what", "which", "who", "where", "when", "why", "how", "all", "some", "no",
           "not", "only", "very", "just", "about", "into", "through", "during", "before", "after"},
    "ro": {"si", "sau", "dar", "in", "pe", "la", "de", "cu", "din", "pentru", "este", "sunt", "era",
           "fi", "fost", "am", "ai", "a", "au", "voi", "eu", "tu", "el", "ea", "noi", "ei", "ele",
           "ce", "care", "cine", "unde", "cand", "cum", "nu", "doar", "foarte", "mai", "un", "o"}
}

LANG_PATTERNS = {
    "en": {"words": ["the", "and", "is", "are", "was", "have", "will"], "chars": []},
    "ro": {"words": ["si", "este", "sunt", "pentru", "care", "sau"], "chars": ["ă", "î", "ț", "ș"]}
}


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return [t for t in text.split() if t]


def detect_language(text: str) -> tuple[str, float]:
    if not text:
        return "en", 0.0

    tokens = set(tokenize(text))
    text_lower = text.lower()
    scores = {}

    for lang, patterns in LANG_PATTERNS.items():
        score = len(tokens.intersection(patterns["words"])) * 2
        score += sum(1 for c in patterns["chars"] if c in text_lower)
        scores[lang] = score

    total = sum(scores.values())
    if total == 0:
        return "en", 0.7

    best = max(scores, key=scores.get)
    confidence = 0.5 + (scores[best] / total) * 0.5
    return best, min(confidence, 1.0)


def extract_keywords(text: str, language: str = "en", top_n: int = 5) -> list[str]:
    tokens = tokenize(text)
    if not tokens:
        return []

    stop = STOP_WORDS.get(language, STOP_WORDS["en"])
    keywords = [t for t in tokens if t not in stop and len(t) > 2]
    return [w for w, _ in Counter(keywords).most_common(top_n)]


def get_text_stats(text: str) -> dict:
    tokens = tokenize(text)
    lang, conf = detect_language(text)

    return {
        "word_count": len(tokens),
        "character_count": len(text.replace(" ", "")),
        "sentence_count": len([s for s in re.split(r'[.!?]+', text) if s.strip()]),
        "unique_words": len(set(tokens)),
        "average_word_length": round(sum(len(t) for t in tokens) / max(len(tokens), 1), 2),
        "detected_language": lang,
        "language_confidence": round(conf, 2),
        "keywords": extract_keywords(text, lang)
    }


def analyze_input(text: str) -> dict:
    if not text or not text.strip():
        return {"is_valid": False, "error": "Input is empty", "statistics": None}

    text = text.strip()
    return {
        "is_valid": True,
        "error": None,
        "statistics": get_text_stats(text),
        "tokens": tokenize(text),
        "keywords": extract_keywords(text, detect_language(text)[0])
    }
