"""Generate an attractive, faithful chapter title after the body is written."""

import re
from typing import Any, Dict

from base_agent import BaseAgent


class ChapterTitleAgent(BaseAgent):
    """Names a finished chapter from its actual conflict, turn, or memorable line."""

    def __init__(self):
        super().__init__("章节命名智能体")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        content = str(input_data.get("content", ""))
        fallback = str(input_data.get("current_title", "本章"))
        chapter_number = input_data.get("chapter_number", "")
        if not content.strip():
            return {"title": fallback, "used_fallback": True}

        excerpt = self._representative_excerpt(content)
        prompt = f"""
请为已经写完的小说章节拟定标题。

章次：第{chapter_number}章
当前暂定标题：{fallback}
章节概要：{input_data.get('summary', '')}
关键事件：{input_data.get('key_events', [])}
正文代表片段：
{excerpt}

命名要求：
1. 标题必须准确概括本章最重要的冲突、转折、兑现、人物选择或一句真正出现在正文语境中的记忆点。
2. 借鉴热门商业网文章节名的吸引机制，不复制现成标题。优先从以下形式中选最适合本章的一种：
   - 冲突或结果：一眼看出本章发生了什么。
   - 反差或反常事实：前后信息形成张力。
   - 人物金句：短、准、有态度，但必须符合人物口吻。
   - 悬念或问题：只在正文确有对应疑问时使用。
   - 意象或物件：只用本章承担剧情作用的具体事物。
3. 标题通常4-14个汉字，最长不超过18个汉字；简短、有画面、有辨识度。
4. 不添加“第X章”前缀，不使用书名号，不使用网络热梗拼贴，不写空泛标题，如“新的开始”“风云再起”“意外发生”。
5. 不夸大正文中没有的情节，不泄露章末之后的剧情，不为猎奇而标题党。
6. 避免连续使用“震惊”“竟然”“没想到”“恐怖如斯”等廉价措辞。

返回JSON：
{{"title":"最终标题","reason":"标题对应的正文核心"}}
"""
        response = self.call_llm(
            [
                {"role": "system", "content": "你是中文商业小说的章节命名编辑，擅长从已完成正文中提炼准确、有吸引力的短标题。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        parsed = self.parse_json_response(response)
        title = self._clean_title(parsed.get("title", ""))
        if not title:
            return {"title": fallback, "used_fallback": True}
        return {"title": title, "reason": parsed.get("reason", ""), "used_fallback": False}

    @staticmethod
    def _representative_excerpt(content: str) -> str:
        if len(content) <= 6000:
            return content
        midpoint = len(content) // 2
        return "\n【中段】\n".join((content[:2200], content[midpoint - 800:midpoint + 800], content[-2200:]))

    @staticmethod
    def _clean_title(value: Any) -> str:
        title = str(value or "").strip().strip('《》“”"\'')
        title = re.sub(r"^第\s*\d+\s*章[：:\s、-]*", "", title).strip()
        title = re.sub(r"[\r\n]+", " ", title)
        if not title or len(title) > 18:
            return ""
        return title
