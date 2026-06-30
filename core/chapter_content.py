"""Utilities for keeping persisted chapter bodies as plain prose."""

import json
from typing import Any


_CONTENT_KEYS = ("content", "chapter_content", "body", "text")


def extract_chapter_text(value: Any) -> str:
    """Extract prose from structured or JSON-wrapped chapter responses."""
    if isinstance(value, dict):
        for key in _CONTENT_KEYS:
            if key in value:
                return extract_chapter_text(value[key])
        return ""

    if value is None:
        return ""

    if not isinstance(value, str):
        return str(value)

    raw = value.strip()
    candidate = raw
    if raw.startswith("```json"):
        candidate = raw[len("```json"):]
        if candidate.rstrip().endswith("```"):
            candidate = candidate.rstrip()[:-3]
        candidate = candidate.strip()

    if candidate.startswith("{") or candidate.startswith("["):
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, (dict, list)):
            extracted = extract_chapter_text(parsed)
            if extracted:
                return extracted
        elif candidate.startswith("{"):
            # 模型可能在正文后的建议字段处被截断；正文字符串本身仍可独立解码。
            decoder = json.JSONDecoder()
            for key in _CONTENT_KEYS:
                key_position = candidate.find(json.dumps(key))
                if key_position == -1:
                    continue
                colon_position = candidate.find(":", key_position + len(key) + 2)
                if colon_position == -1:
                    continue
                value_position = colon_position + 1
                while value_position < len(candidate) and candidate[value_position].isspace():
                    value_position += 1
                try:
                    field_value, _ = decoder.raw_decode(candidate[value_position:])
                except (json.JSONDecodeError, TypeError):
                    continue
                extracted = extract_chapter_text(field_value)
                if extracted:
                    return extracted

    return value
