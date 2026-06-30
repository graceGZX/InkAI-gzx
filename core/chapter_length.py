"""Shared length policy for generated novel chapters."""


CHAPTER_TARGET_LENGTH = 3000
CHAPTER_MIN_LENGTH = 2800
CHAPTER_MAX_LENGTH = 3200
CHAPTER_GENERATION_ATTEMPTS = 3


def count_chapter_characters(content: str) -> int:
    return len("".join((content or "").split()))


def is_chapter_length_valid(content: str) -> bool:
    count = count_chapter_characters(content)
    return CHAPTER_MIN_LENGTH <= count <= CHAPTER_MAX_LENGTH


def chapter_length_correction(actual_count: int) -> str:
    action = "扩写" if actual_count < CHAPTER_MIN_LENGTH else "压缩"
    return (
        f"上一版正文去除空白后为{actual_count}字，不符合要求。请{action}并完整重写本章，"
        f"正文必须严格控制在{CHAPTER_MIN_LENGTH}-{CHAPTER_MAX_LENGTH}字，目标{CHAPTER_TARGET_LENGTH}字左右。"
        "保持原有剧情事件、人物行为与章末钩子，返回完整JSON，不要解释。"
    )
