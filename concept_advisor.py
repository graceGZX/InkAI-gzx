"""AI-assisted novel concept and worldbuilding dialogue."""

import json
import html
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_market_snapshot(seed: Dict[str, str]) -> Dict[str, Any]:
    """Fetch a small, non-blocking market snapshot with graceful fallback."""
    checked_at = datetime.now().strftime("%Y-%m-%d")
    sources: List[str] = []
    highlights: List[str] = []
    errors: List[str] = []
    headers = {"User-Agent": "Mozilla/5.0 (InkAI concept research)"}

    try:
        request = Request("https://fanqienovel.com/rank", headers=headers)
        with urlopen(request, timeout=8) as response:
            page = response.read().decode("utf-8", errors="replace")
        sources.append("番茄小说实时排行榜")
        raw_titles = re.findall(r'bookName\\?"\s*:\s*\\?"([^"\\]+)', page)
        readable_titles = []
        for title in raw_titles:
            if any("\ue000" <= char <= "\uf8ff" for char in title):
                continue
            cleaned = html.unescape(title).strip()
            if cleaned and cleaned not in readable_titles:
                readable_titles.append(cleaned)
        if readable_titles:
            highlights.append("榜单样本：" + "、".join(readable_titles[:6]))
        else:
            highlights.append("已访问番茄实时榜单；榜单书名使用动态字体，交由 AI 结合品类知识判断。")
    except Exception as exc:
        errors.append(f"番茄榜单未取到：{exc}")

    query_seed = (seed.get("requirements") or seed.get("title") or "热门题材").strip()[:80]
    try:
        query = f"番茄小说 {query_seed} 热门题材 网文趋势"
        url = "https://www.bing.com/search?" + urlencode({"q": query})
        request = Request(url, headers=headers)
        with urlopen(request, timeout=8) as response:
            page = response.read().decode("utf-8", errors="replace")
        sources.append("Bing 题材趋势搜索")
        result_titles = []
        for block in re.findall(r"<h2[^>]*>.*?</h2>", page, re.DOTALL | re.IGNORECASE):
            title = html.unescape(re.sub(r"<[^>]+>", "", block)).strip()
            is_relevant = title and any(word in title for word in ("小说", "网文", "番茄", "题材"))
            is_noise = any(word in title for word in ("下载", "官网", "Microsoft", "百度百科", "书库"))
            if is_relevant and not is_noise:
                result_titles.append(title)
        if result_titles:
            highlights.append("趋势搜索：" + "；".join(result_titles[:5]))
    except Exception as exc:
        errors.append(f"趋势搜索未取到：{exc}")

    if not highlights:
        highlights.append("本次未取到可读的实时数据，请基于成熟网文品类知识给出候选，并明确这是降级判断。")

    return {
        "status": "live" if sources else "fallback",
        "checked_at": checked_at,
        "sources": sources,
        "highlights": highlights,
        "note": "；".join(errors) if errors else "实时调研完成",
    }


class ConceptAdvisor:
    """Coordinates research-backed concept dialogue behind one interface."""

    def __init__(
        self,
        llm: Callable[[List[Dict[str, str]]], str],
        researcher: Callable[[Dict[str, str]], Dict[str, Any]],
    ) -> None:
        self._llm = llm
        self._researcher = researcher

    def respond(
        self,
        messages: List[Dict[str, str]],
        seed: Dict[str, str],
        research: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        research = research or self._researcher(seed)
        llm_messages = self._build_messages(messages, seed, research)
        result = self._parse_result(self._llm(llm_messages))
        user_turns = sum(1 for message in messages if message.get("role") == "user")
        invalid_restart = user_turns > 0 and result.get("stage") == "recommending"
        incomplete_initial = user_turns == 0 and (
            result.get("stage") != "recommending" or len(result.get("proposals") or []) != 3
        )
        if invalid_restart or incomplete_initial:
            correction = (
                "纠错：作者已经选择了候选方案。禁止重新推荐题材，必须承接最后一条用户消息，"
                "只追问一个会影响该方案世界观的关键决策，stage 必须为 clarifying。"
                if invalid_restart else
                "纠错：首轮必须返回完整的 3 项 proposals 结构化候选，不得省略 proposals。"
            )
            retry_messages = [llm_messages[0], {"role": "system", "content": correction}] + llm_messages[1:]
            result = self._parse_result(self._llm(retry_messages))
        result = self._normalize_result(result, messages)
        result["research"] = research
        return result

    @staticmethod
    def _build_messages(
        messages: List[Dict[str, str]],
        seed: Dict[str, str],
        research: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        user_turns = sum(1 for message in messages if message.get("role") == "user")
        if user_turns == 0:
            stage_instruction = "首轮：给出 3 个真正不同的候选题材，等待作者选择。"
        else:
            stage_instruction = (
                "首轮推荐已经结束，绝对禁止再次给出候选题材或返回 recommending。"
                "必须承接作者最后选择的方案，继续逐轮确认：目标读者与爽点、核心卖点与 logline、力量体系、"
                "金手指的限制和代价、社会地理势力与核心冲突。一次只追问一个关键决策。"
                "至少经过两轮用户回答且信息足够后，才进入 confirming。"
            )

        system_prompt = f"""你是资深网文主编与世界观架构师，负责通过多轮对话帮助作者确定新小说。
你的工作方式参考 novel-concept 与 novel-worldbuilder：商业定位优先，世界观必须服务爽点和冲突。

当前想法：{seed.get('requirements') or '暂无'}
暂定书名：{seed.get('title') or '暂无'}
市场调研：{json.dumps(research, ensure_ascii=False)}

{stage_instruction}

候选题材必须包含：拟用书名、题材大类/子类、具体 logline、差异化卖点、目标读者、爽点基调、商业潜力与写作风险。
首轮 question 总长度不超过 1800 个中文字符，每个候选不超过 550 字；options 只放“方案代号 + 书名 + 题材”的短标签。
世界观必须明确：底层前提、力量/规则体系、主角优势、限制与代价、社会结构、舞台递进、主要势力、核心冲突和设定红线。
禁止创建项目或写文件；当前阶段只做提案与确认。

只返回纯 JSON：
{{
  "question":"给作者看的提案或追问",
  "options":["2-4 个与当前问题直接相关的选项"],
  "stage":"recommending|clarifying|confirming",
  "concept":null,
  "proposals":[]
}}

首轮 recommending 时 proposals 必须包含 3 项：
{{"code":"甲","title":"书名","genre":"题材大类/子类","logline":"一句话故事","selling_points":["差异卖点"],"audience":"目标读者","tone":"爽点基调","tradeoff":"商业潜力与写作风险"}}

进入 confirming 时 concept 必须是：
{{
  "title":"书名",
  "genre":"题材大类",
  "subgenre":"子类型",
  "audience":"平台与读者画像",
  "logline":"一句话故事",
  "selling_points":["卖点"],
  "tone":"爽点与文风基调",
  "opening_direction":"黄金三章方向",
  "estimated_length":"体量",
  "world":{{
    "premise":"世界底层前提",
    "power_system":"力量体系与等级思路",
    "protagonist_advantage":"主角优势/金手指",
    "limitations":"明确限制与代价",
    "society":"社会背景",
    "geography":"舞台递进",
    "factions":["主要势力"],
    "core_conflicts":["持续冲突"],
    "taboos":["不可违背的设定红线"]
  }}
}}
"""
        result = [{"role": "system", "content": system_prompt}]
        result.extend(messages)
        if not messages:
            result.append({"role": "user", "content": "请搜索并推荐几个适合立项的小说题材。"})
        return result

    @staticmethod
    def _parse_result(response: str) -> Dict[str, Any]:
        text = response.strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return {
            "question": text or "我们继续确认你的小说想法。",
            "options": ["继续完善题材", "继续完善世界观"],
            "stage": "clarifying",
            "concept": None,
        }

    @classmethod
    def _normalize_result(
        cls,
        result: Dict[str, Any],
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        stage = result.get("stage", "clarifying")
        user_turns = sum(1 for message in messages if message.get("role") == "user")
        concept = result.get("concept")

        if stage == "confirming" and (user_turns < 2 or not isinstance(concept, dict)):
            return {
                "question": "方向已经逐渐清晰了。你更想先确认核心爽点，还是世界运行规则？",
                "options": ["先确认核心爽点", "先确认世界运行规则", "我直接补充想法"],
                "stage": "clarifying",
                "concept": None,
            }

        if stage == "confirming":
            concept["requirements_text"] = cls._format_requirements(concept)
            result["options"] = ["确认并填写创作需求", "继续修改方案"]
        elif stage == "recommending":
            proposals = result.get("proposals") or []
            result["proposals"] = proposals[:3]
            if proposals:
                result["options"] = [
                    f"{proposal.get('code') or index + 1}：{proposal.get('title', '未命名')}（{proposal.get('genre', '待定题材')}）"
                    for index, proposal in enumerate(proposals[:3])
                ]
            else:
                result["options"] = (result.get("options") or [])[:3]

        result.setdefault("question", "请继续补充你的想法。")
        result.setdefault("options", [])
        result["stage"] = stage
        result["concept"] = concept if isinstance(concept, dict) else None
        return result

    @staticmethod
    def _format_requirements(concept: Dict[str, Any]) -> str:
        world = concept.get("world") or {}

        def joined(value: Any) -> str:
            if isinstance(value, list):
                return "；".join(str(item) for item in value)
            return str(value or "")

        genre = " - ".join(filter(None, [concept.get("genre"), concept.get("subgenre")]))
        lines = [
            f"【题材定位】{genre}",
            f"【目标读者】{joined(concept.get('audience'))}",
            f"【一句话故事】{joined(concept.get('logline'))}",
            f"【核心卖点】{joined(concept.get('selling_points'))}",
            f"【爽点与基调】{joined(concept.get('tone'))}",
            f"【黄金三章】{joined(concept.get('opening_direction'))}",
            f"【预估体量】{joined(concept.get('estimated_length'))}",
            f"【世界前提】{joined(world.get('premise'))}",
            f"【力量体系】{joined(world.get('power_system'))}",
            f"【主角优势】{joined(world.get('protagonist_advantage'))}",
            f"【限制与代价】{joined(world.get('limitations'))}",
            f"【社会背景】{joined(world.get('society'))}",
            f"【舞台递进】{joined(world.get('geography'))}",
            f"【主要势力】{joined(world.get('factions'))}",
            f"【核心冲突】{joined(world.get('core_conflicts'))}",
            f"【设定红线】{joined(world.get('taboos'))}",
        ]
        return "\n".join(line for line in lines if not line.endswith("】"))[:4800]
