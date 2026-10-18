"""Explicit, reviewed Simplified Chinese copy for the frozen publication."""

from functools import lru_cache
import json
from pathlib import Path
import re


@lru_cache(maxsize=1)
def _chinese_copy():
    copy = {}
    for filename in ("zh_product.json", "zh_research.json"):
        entries = json.loads(Path(__file__).with_name(filename).read_text())
        for english, chinese in entries.items():
            if english in copy and copy[english] != chinese:
                raise ValueError(f"Conflicting Chinese copy: {english}")
            copy[english] = chinese
    return copy


def translate(text, language):
    if language == "en":
        return text
    if language != "zh":
        raise ValueError(f"Unsupported publication language: {language}")
    # Page numbers continue through the Chinese edition, starting at 21.
    if re.fullmatch(r"\d+", text):
        return text
    try:
        return _chinese_copy()[text]
    except KeyError as error:
        raise ValueError(f"Chinese copy missing for: {text}") from error
