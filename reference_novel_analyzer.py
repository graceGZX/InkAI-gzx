"""Reference-novel screening and hierarchical outline extraction."""

import html
import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CHAPTER_HEADING = re.compile(
    r"(?m)^\s*(第\s*[0-9零〇一二三四五六七八九十百千万两]+\s*[章节回卷部]\s*[^\n]{0,80})\s*$"
)
SCREENING_SAMPLE_COUNT = 12
SCREENING_EXCERPT_LENGTH = 2500


def decode_txt_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def split_novel_sections(text: str) -> List[Dict[str, Any]]:
    matches = list(CHAPTER_HEADING.finditer(text))
    if matches:
        sections = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append({
                "index": index + 1,
                "title": re.sub(r"\s+", "", match.group(1)).strip(),
                "content": text[match.end():end].strip(),
            })
        return sections

    chunk_size = 12000
    return [
        {
            "index": index + 1,
            "title": f"文本片段{index + 1}",
            "content": text[start:start + chunk_size].strip(),
        }
        for index, start in enumerate(range(0, len(text), chunk_size))
        if text[start:start + chunk_size].strip()
    ]


def fetch_reference_novel_research(title: str) -> Dict[str, Any]:
    """Search public metadata and reviews without blocking analysis on failure."""
    query = f'"{title}" 小说 简介 评价 剧情 节奏'
    url = "https://www.bing.com/search?" + urlencode({"q": query})
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (InkAI reference analysis)"})
    highlights: List[str] = []
    sources: List[str] = []
    error = ""
    try:
        with urlopen(request, timeout=10) as response:
            page = response.read().decode("utf-8", errors="replace")
        for block in re.findall(r'<li class="b_algo".*?</li>', page, re.DOTALL | re.IGNORECASE)[:8]:
            heading = re.search(r"<h2[^>]*>(.*?)</h2>", block, re.DOTALL | re.IGNORECASE)
            snippet = re.search(r"<p[^>]*>(.*?)</p>", block, re.DOTALL | re.IGNORECASE)
            if not heading:
                continue
            heading_text = html.unescape(re.sub(r"<[^>]+>", "", heading.group(1))).strip()
            snippet_text = html.unescape(re.sub(r"<[^>]+>", "", snippet.group(1))).strip() if snippet else ""
            if heading_text:
                highlights.append(f"{heading_text}：{snippet_text}"[:500])
        if highlights:
            sources.append("Bing 公开资料搜索")
    except Exception as exc:
        error = str(exc)

    return {
        "status": "live" if highlights else "fallback",
        "checked_at": datetime.now().strftime("%Y-%m-%d"),
        "sources": sources,
        "highlights": highlights or ["未取得可靠的公开资料，本次报告主要依据上传文本抽样。"],
        "note": error or "公开资料检索完成",
    }


class ReferenceNovelAnalyzer:
    def __init__(
        self,
        llm: Callable[[List[Dict[str, str]]], str],
        researcher: Callable[[str], Dict[str, Any]] = fetch_reference_novel_research,
    ) -> None:
        self._llm = llm
        self._researcher = researcher

    def analyze(self, title: str, text: str, target_direction: str = "") -> Dict[str, Any]:
        sections = split_novel_sections(text)
        if not sections:
            raise ValueError("TXT 中没有可分析的正文")
        research = self._researcher(title)
        sample = self._build_screening_sample(sections)
        prompt = self._screening_prompt(title, target_direction, sample, research, len(sections))
        report = self._normalize_report(self._request_json([
            {
                "role": "system",
                "content": "你是资深网文主编，只评估结构参考价值，不复述长段原文，也不建议照搬具体情节。",
            },
            {"role": "user", "content": prompt},
        ]))
        report["research"] = research
        report["source_profile"] = {
            "character_count": len("".join(text.split())),
            "chapter_count": len(sections) if CHAPTER_HEADING.search(text) else 0,
            "section_count": len(sections),
            "sampled_sections": min(len(sections), SCREENING_SAMPLE_COUNT),
            "analysis_mode": "representative_screening",
        }
        return report

    def deep_extract(
        self,
        text: str,
        screening_report: Dict[str, Any],
        target_direction: str = "",
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Read the novel in 5-10 chapter units, then review at volume and book level."""
        progress_callback = progress_callback or (lambda value, message: None)
        sections = split_novel_sections(text)
        if not sections:
            raise ValueError("TXT 中没有可深度提取的正文")

        section_groups = self._group_sections(sections)
        fine_outlines = []
        progress_callback(2, "正在按章节建立细纲单元")
        for index, group in enumerate(section_groups):
            source_text = self._format_section_group(group)
            prompt = f"""任务阶段：5-10章细纲抽取
目标方向：{target_direction or '通用网文结构研究'}
这是第 {index + 1}/{len(section_groups)} 个单元。只提取抽象结构，不复刻原文表达。

章节正文：
{source_text}

只返回 JSON：
{{
  "chapter_range":"起止章",
  "unit_title":"单元标题",
  "source_summary":"本单元剧情因果链",
  "plot_progression":["开端","升级","转折","兑现"],
  "protagonist_development":"主角变化",
  "worldbuilding":["新增规则或地图"],
  "hooks":["悬念"],
  "payoffs":["兑现"],
  "structural_patterns":["可抽象借鉴的结构"],
  "outdated_elements":["拖沓、过时或重复模式"]
}}
"""
            fine_outlines.append(self._request_json([
                {"role": "system", "content": "你是长篇网文拆书编辑，擅长还原剧情因果、节奏和读者期待。"},
                {"role": "user", "content": prompt},
            ]))
            progress = 5 + round(60 * (index + 1) / len(section_groups))
            progress_callback(progress, f"已完成 {index + 1}/{len(section_groups)} 个细纲单元")

        fine_batches = [fine_outlines[index:index + 8] for index in range(0, len(fine_outlines), 8)]
        volume_outlines = []
        editorial_context = {
            "research": screening_report.get("research", {}),
            "strengths": screening_report.get("strengths", []),
            "weaknesses": screening_report.get("weaknesses", []),
            "reusable_patterns": screening_report.get("reusable_patterns", []),
            "avoid_patterns": screening_report.get("avoid_patterns", []),
        }
        progress_callback(68, "正在进行卷级审查与优化")
        for index, batch in enumerate(fine_batches):
            prompt = f"""任务阶段：卷级审查与优化
目标新书方向：{target_direction or '尚未指定'}
初筛与公开资料：{json.dumps(editorial_context, ensure_ascii=False)}
原始细纲单元：{json.dumps(batch, ensure_ascii=False)}

请先还原这一卷的故事弧，再删除拖沓、过时和重复模式，用更符合当前读者期待但保持原创的机制替换。
只返回 JSON：
{{
  "volume_number":{index + 1},
  "title":"卷名",
  "source_arc":"原始故事弧",
  "optimized_arc":"优化后的原创故事弧模板",
  "retain":["保留的结构优势"],
  "replace":[{{"outdated":"待替换模式","replacement":"流行且原创的替换方式"}}],
  "optimized_units":["按原细纲单元顺序给出优化方向"],
  "climax":"卷末高潮设计",
  "ending_hook":"下一卷钩子"
}}
"""
            volume_outlines.append(self._request_json([
                {"role": "system", "content": "你是当前网文市场的一线主编，负责结构审查与原创化改造。"},
                {"role": "user", "content": prompt},
            ]))
            progress = 70 + round(18 * (index + 1) / len(fine_batches))
            progress_callback(progress, f"已完成 {index + 1}/{len(fine_batches)} 个卷级大纲")

        progress_callback(90, "正在合成整书大纲与三幕结构")
        final_prompt = f"""任务阶段：整书大纲合成
目标新书方向：{target_direction or '尚未指定'}
初筛报告：{json.dumps(editorial_context, ensure_ascii=False)}
卷级优化结果：{json.dumps(volume_outlines, ensure_ascii=False)}

请合成可供原创小说参考的整书结构，不得沿用原书专有名词、角色关系映射或标志性桥段。
只返回 JSON：
{{
  "book_outline":"优化后的整书主线",
  "three_act_structure":{{"act1":"建立","act2":"对抗","act3":"解决"}},
  "protagonist_arc":"主角完整成长弧",
  "world_progression":"世界与地图递进",
  "market_optimization":["针对当前市场的优化"],
  "originality_guardrails":["防止照搬的原创红线"]
}}
"""
        book_result = self._request_json([
            {"role": "system", "content": "你是总编，负责把拆书结果转化为原创、流行、可执行的长篇结构。"},
            {"role": "user", "content": final_prompt},
        ])
        result = {
            **book_result,
            "fine_outlines": fine_outlines,
            "volume_outlines": volume_outlines,
            "source_profile": {
                "section_count": len(sections),
                "fine_outline_units": len(fine_outlines),
                "chapters_per_unit": [len(group) for group in section_groups],
            },
        }
        progress_callback(100, "深度提取与大纲优化完成")
        return result

    @staticmethod
    def _group_sections(sections: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Balance units around eight chapters without leaving a tiny tail group."""
        count = len(sections)
        if count <= 10:
            return [sections]
        group_count = max((count + 9) // 10, (count + 4) // 8)
        while group_count > 1 and count / group_count < 5:
            group_count -= 1
        base_size, remainder = divmod(count, group_count)
        sizes = [base_size + (1 if index < remainder else 0) for index in range(group_count)]
        groups = []
        start = 0
        for size in sizes:
            groups.append(sections[start:start + size])
            start += size
        return groups

    def _format_section_group(self, group: List[Dict[str, Any]]) -> str:
        formatted = []
        max_per_section = 6000
        for section in group:
            content = section["content"]
            if len(content) > max_per_section:
                chunks = [content[index:index + max_per_section] for index in range(0, len(content), max_per_section)]
                chunk_summaries = []
                for index, chunk in enumerate(chunks):
                    chunk_summaries.append(self._request_json([
                        {
                            "role": "system",
                            "content": "你是剧情记录员，只提取当前文本块中的事件、人物变化、设定和伏笔。",
                        },
                        {
                            "role": "user",
                            "content": (
                                f"超长章节《{section['title']}》第{index + 1}/{len(chunks)}块：\n{chunk}\n\n"
                                "只返回JSON：{\"events\":[],\"character_changes\":[],\"worldbuilding\":[],\"hooks\":[]}"
                            ),
                        },
                    ]))
                content = "超长章节完整分块结构摘要：\n" + json.dumps(chunk_summaries, ensure_ascii=False)
            formatted.append(f"## {section['title']}\n{content}")
        return "\n\n".join(formatted)

    @staticmethod
    def _build_screening_sample(sections: List[Dict[str, Any]]) -> str:
        sample_count = min(len(sections), SCREENING_SAMPLE_COUNT)
        if sample_count == 1:
            indexes = [0]
        else:
            indexes = sorted({
                round(position * (len(sections) - 1) / (sample_count - 1))
                for position in range(sample_count)
            })
        excerpts = []
        for index in indexes:
            section = sections[index]
            content = section["content"]
            if len(content) > SCREENING_EXCERPT_LENGTH:
                half = SCREENING_EXCERPT_LENGTH // 2
                content = content[:half] + "\n……\n" + content[-half:]
            excerpts.append(f"### {section['title']}（全书位置 {index + 1}/{len(sections)}）\n{content}")
        return "\n\n".join(excerpts)

    @staticmethod
    def _screening_prompt(
        title: str,
        target_direction: str,
        sample: str,
        research: Dict[str, Any],
        section_count: int,
    ) -> str:
        return f"""请对参考小说《{title}》做低成本立项初筛。
目标新书方向：{target_direction or '尚未指定，请评估通用网文参考价值'}
文本规模：{section_count} 个章节/片段。本轮采用覆盖开篇、中段、后段和结尾的代表性抽样，不得声称逐字通读。
公开资料：{json.dumps(research, ensure_ascii=False)}

代表性文本：
{sample}

请判断它是否值得进入昂贵的全量拆解。只返回 JSON：
{{
  "summary":"整本书主线概览",
  "three_act_structure":{{"act1":"建立","act2":"对抗","act3":"解决"}},
  "protagonist_arc":"主角成长路线",
  "worldbuilding":"世界观与舞台递进",
  "strengths":["值得参考的优势"],
  "weaknesses":["过时、拖沓或不流行之处"],
  "reusable_patterns":["只描述抽象结构，不复制专有情节"],
  "avoid_patterns":["不建议借鉴的模式"],
  "scores":{{
    "market_appeal":0,
    "opening_hook":0,
    "long_form_structure":0,
    "characterization":0,
    "payoff_design":0,
    "current_trend_fit":0,
    "target_match":0
  }},
  "verdict":"recommended|conditional|not_recommended",
  "verdict_reason":"明确说明是否值得继续及原因",
  "confidence":0.0
}}
"""

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError("AI 未返回有效的参考价值报告")

    def _request_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        current_messages = list(messages)
        last_error: Optional[Exception] = None
        for attempt in range(2):
            raw = self._llm(current_messages)
            try:
                return self._parse_json(raw)
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == 0:
                    current_messages = current_messages + [
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": "上一版JSON不完整或格式错误。请保持原任务内容，只重新返回完整、可解析的纯JSON。",
                        },
                    ]
        raise ValueError(f"AI 连续两次未返回有效 JSON: {last_error}")

    @staticmethod
    def _normalize_report(report: Dict[str, Any]) -> Dict[str, Any]:
        report.setdefault("summary", "暂未提取到明确主线")
        report.setdefault("three_act_structure", {})
        report.setdefault("protagonist_arc", "待进一步确认")
        report.setdefault("worldbuilding", "待进一步确认")
        for key in ("strengths", "weaknesses", "reusable_patterns", "avoid_patterns"):
            report[key] = list(report.get(key) or [])
        score_keys = (
            "market_appeal", "opening_hook", "long_form_structure", "characterization",
            "payoff_design", "current_trend_fit", "target_match",
        )
        scores = report.get("scores") if isinstance(report.get("scores"), dict) else {}
        report["scores"] = {key: max(0, min(100, int(scores.get(key, 0) or 0))) for key in score_keys}
        if report.get("verdict") not in ("recommended", "conditional", "not_recommended"):
            report["verdict"] = "conditional"
        report.setdefault("verdict_reason", "信息不足，建议人工确认后再决定。")
        try:
            report["confidence"] = max(0.0, min(1.0, float(report.get("confidence", 0.5))))
        except (TypeError, ValueError):
            report["confidence"] = 0.5
        return report
