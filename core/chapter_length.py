"""Shared length policy for generated novel chapters."""


CHAPTER_TARGET_LENGTH = 3000
CHAPTER_MIN_LENGTH = 2800
CHAPTER_MAX_LENGTH = 3200
CHAPTER_GENERATION_ATTEMPTS = 4


def count_chapter_characters(content: str) -> int:
    return len("".join((content or "").split()))


def is_chapter_length_valid(content: str) -> bool:
    count = count_chapter_characters(content)
    return CHAPTER_MIN_LENGTH <= count <= CHAPTER_MAX_LENGTH


def chapter_length_correction(actual_count: int) -> str:
    if actual_count < CHAPTER_MIN_LENGTH:
        minimum_addition = CHAPTER_MIN_LENGTH - actual_count
        target_addition = CHAPTER_TARGET_LENGTH + 50 - actual_count
        instruction = (
            f"请扩写：必须在上一版基础上净增加至少{minimum_addition}字，建议净增加约{target_addition}字。"
            "保留已有有效场景和全部剧情节点，不得用概述替换原有正文；"
            "通过补足人物行动、有效对话、冲突反应和场景结果扩写，禁止重复句意或堆砌景物。"
        )
    else:
        minimum_reduction = actual_count - CHAPTER_MAX_LENGTH
        target_reduction = actual_count - CHAPTER_TARGET_LENGTH
        instruction = (
            f"请压缩：必须净删减至少{minimum_reduction}字，建议净删减约{target_reduction}字。"
            "删除重复解释、同义心理活动和无效过渡，不得删除关键事件、人物行为或章末钩子。"
        )

    return (
        f"上一版正文去除空白后为{actual_count}字，不符合要求。{instruction}"
        f"请返回修订后的完整章节JSON；正文必须严格控制在{CHAPTER_MIN_LENGTH}-{CHAPTER_MAX_LENGTH}字，"
        f"目标{CHAPTER_TARGET_LENGTH + 50}字左右。只返回JSON，不要解释。"
    )
