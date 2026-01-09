import re
import string
from collections import Counter
from typing import Dict, List, Tuple, Optional


# Common stop words for filtering
STOP_WORDS = {
    "en": {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "this", "that", "these", "those", "i", "you", "he", "she", "it", "we",
        "they", "what", "which", "who", "whom", "where", "when", "why", "how",
        "all", "each", "every", "both", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "just", "about", "into", "through", "during", "before", "after"
    },
    "ro": {
        "si", "sau", "dar", "in", "pe", "la", "de", "cu", "din", "pentru",
        "este", "sunt", "era", "erau", "fi", "fost", "fiind", "am", "ai", "a",
        "ati", "au", "voi", "vom", "vor", "as", "ar", "asta", "acesta", "aceasta",
        "acesti", "acestea", "acel", "acea", "acei", "acele", "eu", "tu", "el",
        "ea", "noi", "voi", "ei", "ele", "ce", "care", "cine", "unde", "cand",
        "cum", "cat", "toti", "toate", "fiecare", "alt", "alta", "alti", "alte",
        "nici", "nu", "doar", "foarte", "mai", "cel", "cea", "cei", "cele", "un",
        "o", "unei", "unor", "lui", "sa", "se"
    }
}

# Language detection patterns (common words and patterns)
LANGUAGE_PATTERNS = {
    "en": {
        "words": ["the", "and", "is", "are", "was", "were", "have", "has", "will", "would"],
        "patterns": [r"\bth\w+", r"\bing\b", r"\btion\b", r"\bly\b"]
    },
    "ro": {
        "words": ["si", "este", "sunt", "pentru", "care", "sau", "din", "acest", "foarte"],
        "patterns": [r"\bă\b", r"\bî\b", r"ț", r"ș", r"ă", r"\bul\b", r"\bea\b"]
    }
}


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into individual words.

    Performs basic tokenization by:
    1. Converting to lowercase
    2. Removing punctuation
    3. Splitting on whitespace
    4. Filtering empty tokens

    Args:
        text: Input text to tokenize

    Returns:
        List of tokens (words)

    Example:
        >>> tokenize("Hello, World! How are you?")
        ['hello', 'world', 'how', 'are', 'you']
    """
    if not text:
        return []

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation but keep letters and spaces
    text = re.sub(r'[^\w\s]', ' ', text)

    # Split on whitespace and filter empty strings
    tokens = [token.strip() for token in text.split() if token.strip()]

    return tokens


def count_words(text: str) -> int:
    """
    Count the number of words in the text.

    Args:
        text: Input text

    Returns:
        Number of words
    """
    tokens = tokenize(text)
    return len(tokens)


def count_characters(text: str, include_spaces: bool = False) -> int:
    """
    Count characters in the text.

    Args:
        text: Input text
        include_spaces: Whether to include spaces in count

    Returns:
        Number of characters
    """
    if not text:
        return 0

    if include_spaces:
        return len(text)
    return len(text.replace(" ", ""))


def count_sentences(text: str) -> int:
    """
    Count the number of sentences in the text.

    Uses sentence-ending punctuation (. ! ?) as delimiters.

    Args:
        text: Input text

    Returns:
        Number of sentences
    """
    if not text:
        return 0

    # Split by sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)

    # Filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    return len(sentences)


def get_word_frequency(text: str, top_n: int = 10) -> List[Tuple[str, int]]:
    """
    Get the most frequent words in the text.

    Args:
        text: Input text
        top_n: Number of top words to return

    Returns:
        List of (word, frequency) tuples sorted by frequency
    """
    tokens = tokenize(text)

    if not tokens:
        return []

    counter = Counter(tokens)
    return counter.most_common(top_n)


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect the language of the input text.

    Uses a simple heuristic based on:
    1. Common word matching
    2. Character pattern matching

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (language_code, confidence_score)
        language_code: "en" for English, "ro" for Romanian
        confidence_score: Float between 0 and 1
    """
    if not text:
        return ("en", 0.0)

    text_lower = text.lower()
    tokens = set(tokenize(text))

    scores = {}

    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0.0

        # Check common words
        common_words = set(patterns["words"])
        matches = tokens.intersection(common_words)
        score += len(matches) * 2  # Weight word matches more

        # Check patterns
        for pattern in patterns["patterns"]:
            if re.search(pattern, text_lower):
                score += 1

        scores[lang] = score

    # Determine language with highest score
    total_score = sum(scores.values())
    if total_score == 0:
        return ("en", 0.5)  # Default to English with low confidence

    best_lang = max(scores, key=scores.get)
    confidence = scores[best_lang] / (total_score + 1)

    return (best_lang, min(confidence, 1.0))


def extract_keywords(text: str, language: str = "en", top_n: int = 5) -> List[str]:
    """
    Extract keywords from the text.

    Filters out stop words and returns the most frequent meaningful words.

    Args:
        text: Input text
        language: Language code ("en" or "ro")
        top_n: Number of keywords to extract

    Returns:
        List of keywords sorted by frequency
    """
    tokens = tokenize(text)

    if not tokens:
        return []

    # Get stop words for the language
    stop_words = STOP_WORDS.get(language, STOP_WORDS["en"])

    # Filter out stop words and short words
    keywords = [
        token for token in tokens
        if token not in stop_words and len(token) > 2
    ]

    # Count frequencies
    counter = Counter(keywords)

    # Return top keywords
    return [word for word, _ in counter.most_common(top_n)]


def get_text_statistics(text: str) -> Dict:
    """
    Get comprehensive text statistics.

    Args:
        text: Input text to analyze

    Returns:
        Dictionary containing various text statistics
    """
    tokens = tokenize(text)
    detected_lang, confidence = detect_language(text)

    stats = {
        "word_count": len(tokens),
        "character_count": count_characters(text, include_spaces=False),
        "character_count_with_spaces": count_characters(text, include_spaces=True),
        "sentence_count": count_sentences(text),
        "unique_words": len(set(tokens)),
        "average_word_length": round(sum(len(t) for t in tokens) / max(len(tokens), 1), 2),
        "detected_language": detected_lang,
        "language_confidence": round(confidence, 2),
        "keywords": extract_keywords(text, detected_lang),
        "top_words": get_word_frequency(text, 5)
    }

    return stats


def analyze_input(text: str) -> Dict:
    """
    Analyze user input and return processing results.

    This is the main function to be called by the application
    to process user input before sending to the LLM.

    Args:
        text: User input text

    Returns:
        Dictionary with analysis results
    """
    if not text or not text.strip():
        return {
            "is_valid": False,
            "error": "Input text is empty",
            "statistics": None,
            "processed_text": ""
        }

    # Clean the input
    processed_text = text.strip()

    # Get statistics
    stats = get_text_statistics(processed_text)

    return {
        "is_valid": True,
        "error": None,
        "statistics": stats,
        "processed_text": processed_text,
        "tokens": tokenize(processed_text),
        "keywords": stats["keywords"]
    }


def format_statistics_report(stats: Dict) -> str:
    """
    Format text statistics as a human-readable report.

    Args:
        stats: Statistics dictionary from get_text_statistics()

    Returns:
        Formatted string report
    """
    if not stats:
        return "No statistics available."

    report_lines = [
        "=" * 40,
        "TEXT ANALYSIS REPORT",
        "=" * 40,
        f"Words: {stats['word_count']}",
        f"Characters: {stats['character_count']} (without spaces)",
        f"Sentences: {stats['sentence_count']}",
        f"Unique words: {stats['unique_words']}",
        f"Avg word length: {stats['average_word_length']} chars",
        "-" * 40,
        f"Detected language: {stats['detected_language'].upper()} "
        f"(confidence: {stats['language_confidence']:.0%})",
        "-" * 40,
        f"Keywords: {', '.join(stats['keywords']) if stats['keywords'] else 'None'}",
        "=" * 40
    ]

    return "\n".join(report_lines)
