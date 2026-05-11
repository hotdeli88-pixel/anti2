"""NEIS CP949 호환 Byte 카운터 + 입력 정규화."""
from __future__ import annotations

import unicodedata

ZERO_WIDTH = {"\u200B", "\u200C", "\u200D", "\uFEFF", "\u2028", "\u2029"}
SMART_QUOTES = str.maketrans(
    {"\u2018": "'", "\u2019": "'", "\u201C": '"', "\u201D": '"'}
)
DASHES = str.maketrans({"\u2013": "-", "\u2014": "-"})


def normalize_for_neis(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = "".join(c for c in text if c not in ZERO_WIDTH)
    text = text.translate(SMART_QUOTES).translate(DASHES)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    return text


def byte_count_cp949(text: str) -> tuple[int, list[str]]:
    """Returns (byte_count, incompatible_chars). CRLF counted as 2B."""
    normalized = normalize_for_neis(text)
    incompatible: list[str] = []
    encoded = bytearray()
    for ch in normalized:
        try:
            encoded.extend(ch.encode("cp949"))
        except UnicodeEncodeError:
            if ch not in incompatible:
                incompatible.append(ch)
    return len(bytes(encoded)), incompatible


def byte_limit_for(section_code: str) -> int:
    """Quick lookup without DB. Authoritative source is `section_types.byte_limit`."""
    table = {
        "haengjongjeui": 900,
        "chang_jayul": 1500,
        "chang_dongari": 1500,
        "chang_jinro": 1500,
        "chang_bongsa": 150,
        "setuk_subject": 1500,
        "setuk_individual": 1500,
        "dokseo_common": 1500,
        "dokseo_subject": 750,
        "jayuhakgi": 3000,
        "ilsangsaenghwal": 3000,
        "chulgyeol_teuggi": 1500,
        "injeok_teuggi": 1500,
        "susang": 300,
        "hakpok_jochi": 500,
    }
    return table.get(section_code, 500)
