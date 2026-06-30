"""Quality policy for a new novel's golden opening chapters."""


GOLDEN_OPENING_CHAPTERS = 3


_CHAPTER_REQUIREMENTS = {
    1: (
        "黄金第一章：开场尽快抛出强钩子和核心危机；让主角通过选择、行动和对话鲜明展示主角性格、欲望与短板；"
        "自然露出世界观最关键的异常规则；结尾必须留下迫使读者点开下一章的钩子。"
    ),
    2: (
        "黄金第二章：承接上一章后果，禁止重新开场；用冲突、关系和具体代价扩展世界观与力量规则；"
        "让主角性格推动一次困难选择，明确更大的敌人或阻力，并把故事主线再推进一步；结尾设置升级钩子。"
    ),
    3: (
        "黄金第三章：兑现前两章铺垫，形成一次有代价的小高潮或阶段性反转；让主角完成首次关键证明；"
        "清晰展示世界观的独特卖点、故事主线的大致方向与长期核心矛盾；以更大目标或危机作为强钩子进入续写。"
    ),
}


def is_golden_opening_complete(chapter_count: int) -> bool:
    return chapter_count >= GOLDEN_OPENING_CHAPTERS


def golden_chapter_requirements(chapter_number: int) -> str:
    try:
        return _CHAPTER_REQUIREMENTS[chapter_number]
    except KeyError as exc:
        raise ValueError("黄金开篇只包含第1至第3章") from exc
