"""Language configuration and utilities."""

SUPPORTED_LANGUAGES = {
    'ko': 'Korean',
    'en': 'English',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ru': 'Russian'
}

ISO_639_2_to_1 = {
    'eng': 'en',
    'kor': 'ko',
    'jpn': 'ja',
    'zho': 'zh',
    'spa': 'es',
    'fra': 'fr',
    'deu': 'de',
    'rus': 'ru'
}


def convert_to_iso639_1(code: str | None) -> str | None:
    """Convert language code to 2-letter ISO 639-1 code."""
    if not code:
        return None
    if len(code) == 2:
        return code.lower()
    return ISO_639_2_to_1.get(code.lower(), code)


def get_language_name(code: str) -> str | None:
    """Get full language name from ISO 639-1 code."""
    return SUPPORTED_LANGUAGES.get(code)


def get_supported_codes() -> list[str]:
    """Get list of supported language codes."""
    return list(SUPPORTED_LANGUAGES.keys())
