"""
续写故事弧规划智能体
根据当前故事状态，规划下一段跨章情节弧
"""

from base_agent import BaseAgent
from typing import Dict, Any
import uuid
from core.continuation_blueprint import format_blueprint_context


class ContinuationArcPlanner(BaseAgent):
    """续写故事弧规划智能体"""

    def __init__(self):
        super().__init__("续写故事弧规划智能体")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        knowledge_base = input_data.get("knowledge_base", {})
        if not knowledge_base:
            return {"success": False, "error": "缺少知识库数据"}
        arc = self._plan_next_arc(knowledge_base)
        if not arc:
            return {"success": False, "error": "弧规划生成失败"}
        return {"success": True, "arc": arc}

    def _plan_next_arc(self, kb: Dict[str, Any]) -> Dict[str, Any]:
        novel_info = kb.get("novel_info", {})
        character_profiles = kb.get("character_profiles", {})
        plot_lines = kb.get("plot_lines", {})
        last_chapter = kb.get("last_chapter_summary", {})
        recent_chapters = kb.get("recent_chapters_summaries", [])
        current_chapter_number = kb.get("current_chapter_number", 1)
        tags = kb.get("tags", {})
        blueprint_context = format_blueprint_context(kb.get("continuation_blueprint"))

        main_char = character_profiles.get("main_character", {})
        main_name = main_char.get("basic_info", {}).get("name", "主角")

        supporting = character_profiles.get("supporting_characters", [])
        supporting_names = [c.get("basic_info", {}).get("name", "配角")
                            for c in supporting[:3]]

        recent_summary = "\n".join(
            f"第{c.get('chapter_number')}章：{c.get('summary', '')[:100]}"
            for c in recent_chapters[-3:]
        )

        plot_main = "\n".join(
            f"- {line}" for line in plot_lines.get("main_line", [])
        )

        system_prompt = "你是一名专业的长篇小说结构策划师，擅长为网络小说设计张力十足的多章情节弧。只返回 JSON，不要其他内容。"

        user_prompt = f"""为小说《{novel_info.get('title', '未知')}》规划下一段故事弧，从第 {current_chapter_number} 章开始。

【小说基本信息】
题材标签：{tags}
主角：{main_name}
配角：{', '.join(supporting_names)}

【主线走向】
{plot_main}

【最近剧情】
{recent_summary}

【上一章结尾】
{last_chapter.get('summary', '无')[:200]}

【已绑定的整书/卷/细纲蓝图】
{blueprint_context}

【要求】
- 如已绑定蓝图，当前故事弧必须服务蓝图中的当前单元目标，不得偏离当前卷故事弧和原创红线
- 弧章数范围 3-8 章，根据故事需要自然决定
- 每章分配一个 role（arc_open / arc_mid / arc_climax / arc_close）和 ending_type（cliffhanger / hook / pause / resolution）
- arc_open 用 hook，arc_mid 用 cliffhanger，arc_climax 用 cliffhanger 或 pause，arc_close 用 resolution
- character_milestones 中必须安排至少一个主角里程碑（level_up 或 growth 或 revelation）
- 弧末章（arc_close）必须为下一弧埋下伏笔
- milestone 字段要具体，引用角色名和故事内容，禁止空泛描述

只返回以下 JSON：
{{
  "arc_id": "arc_{current_chapter_number:03d}",
  "arc_name": "弧名称（不超过10字）",
  "arc_type": "growth|conflict|exploration|revelation",
  "start_chapter": {current_chapter_number},
  "planned_chapters": 5,
  "chapters_remaining": 5,
  "chapter_roles": [
    {{"offset": 1, "role": "arc_open",   "ending_type": "hook",        "milestone": "具体里程碑描述"}},
    {{"offset": 2, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "具体里程碑描述"}},
    {{"offset": 3, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "具体里程碑描述"}},
    {{"offset": 4, "role": "arc_climax", "ending_type": "cliffhanger", "milestone": "具体里程碑描述"}},
    {{"offset": 5, "role": "arc_close",  "ending_type": "resolution",  "milestone": "具体里程碑描述"}}
  ],
  "character_milestones": {{
    "main": {{"chapter_offset": 4, "type": "level_up", "description": "具体描述"}},
    "supporting": [
      {{"name": "角色名", "chapter_offset": 3, "type": "growth", "description": "具体描述"}}
    ]
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.call_llm(messages, temperature=0.8, max_tokens=1500)
        result = self.parse_json_response(response)

        if not result or not result.get("arc_name"):
            self.log(f"弧规划解析失败，原始响应: {response[:300]}")
            return None

        # 确保 arc_id 唯一
        if not result.get("arc_id"):
            result["arc_id"] = f"arc_{current_chapter_number:03d}_{uuid.uuid4().hex[:4]}"

        # 确保 chapters_remaining 与 planned_chapters 一致
        result["chapters_remaining"] = len(result.get("chapter_roles", []))
        result["planned_chapters"] = result["chapters_remaining"]

        return result
