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

# [신규] 3자리 -> 2자리 ISO 코드 변환 매핑
ISO_639_2_to_1 = {
    'eng': 'en',
    'kor': 'ko',
    'jpn': 'ja',
    'zho': 'zh',
    'spa': 'es',
    'fra': 'fr',
    'deu': 'de',
    'rus': 'ru'
    # 필요에 따라 추가
}

def convert_to_iso639_1(code: str | None) -> str | None:
    """
    주어진 언어 코드를 2자리 ISO 639-1 코드로 변환합니다.
    이미 2자리이거나, 매핑에 없으면 원래 코드를 반환합니다.
    """
    if not code:
        return None
    if len(code) == 2:
        return code.lower()
    return ISO_639_2_to_1.get(code.lower(), code)


def get_language_name(code: str) -> str | None:
    """ISO 639-1 코드에 해당하는 전체 언어 이름을 반환합니다."""
    return SUPPORTED_LANGUAGES.get(code)

def get_supported_codes() -> list[str]:
    """지원하는 모든 언어의 ISO 639-1 코드 리스트를 반환합니다."""
    return list(SUPPORTED_LANGUAGES.keys())