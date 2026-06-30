"""Attach reference outlines to novels and resolve the active continuation unit."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


RANGE_PATTERN = re.compile(r"(\d+)\s*[-~—至]\s*(\d+)")


def format_blueprint_context(context: Optional[Dict[str, Any]]) -> str:
    if not context:
        return "未绑定续写蓝图，按现有故事线继续。"
    if context.get("status") == "exhausted":
        return (
            f"蓝图已执行到第{context.get('blueprint_range', '')}章末。"
            "本章不得凭空重复旧单元，应规划新的延伸蓝图或自然开启下一阶段。"
        )
    volume = context.get("current_volume") or {}
    unit = context.get("current_unit") or {}
    return f"""蓝图状态：{context.get('status', '')}
整书主线：{context.get('book_outline', '')}
三幕结构：{context.get('three_act_structure', {})}
主角长期成长：{context.get('protagonist_arc', '')}
世界递进：{context.get('world_progression', '')}
当前卷：{volume.get('title', '')}（目标章节 {volume.get('target_chapter_range', '')}）
当前卷故事弧：{volume.get('optimized_arc', '')}
当前单元：{unit.get('title', '')}（目标章节 {unit.get('target_chapter_range', '')}）
本单元目标：{unit.get('goal', '')}
核心冲突：{unit.get('conflict', '')}
人物里程碑：{unit.get('character_milestone', '')}
世界观任务：{unit.get('worldbuilding', '')}
单元末钩子：{unit.get('hook', '')}
本单元禁用模式：{unit.get('avoid', '')}
市场优化：{context.get('market_optimization', [])}
原创红线：{context.get('originality_guardrails', [])}"""


class ContinuationBlueprintManager:
    """Hides blueprint rebasing, persistence, and per-chapter lookup."""

    def __init__(self, data_manager: Any) -> None:
        self.data_manager = data_manager

    def attach(self, novel_id: str, analysis_state: Dict[str, Any]) -> Dict[str, Any]:
        if analysis_state.get("status") != "completed":
            raise ValueError("参考小说必须完成深度提取后才能绑定续写")
        result = (analysis_state.get("deep_extraction") or {}).get("result")
        if not isinstance(result, dict):
            raise ValueError("深度提取结果不存在")

        start_chapter = len(self.data_manager.get_novel_chapters(novel_id)) + 1
        volumes = self._build_rebased_volumes(result, start_chapter)
        end_chapter = max(
            (unit["target_end_chapter"] for volume in volumes for unit in volume["units"]),
            default=start_chapter - 1,
        )
        blueprint = {
            "version": 1,
            "analysis_id": analysis_state.get("analysis_id", ""),
            "reference_title": analysis_state.get("title", ""),
            "target_direction": analysis_state.get("target_direction", ""),
            "attached_at": datetime.now().isoformat(),
            "start_chapter": start_chapter,
            "end_chapter": end_chapter,
            "book_outline": result.get("book_outline", ""),
            "three_act_structure": result.get("three_act_structure", {}),
            "protagonist_arc": result.get("protagonist_arc", ""),
            "world_progression": result.get("world_progression", ""),
            "market_optimization": result.get("market_optimization", []),
            "originality_guardrails": result.get("originality_guardrails", []),
            "volumes": volumes,
        }
        if not self.data_manager.save_continuation_blueprint(novel_id, blueprint):
            raise ValueError("续写蓝图保存失败")
        if hasattr(self.data_manager, "clear_active_arc"):
            self.data_manager.clear_active_arc(novel_id)
        return blueprint

    def context_for_chapter(self, novel_id: str, chapter_number: int) -> Optional[Dict[str, Any]]:
        blueprint = self.data_manager.load_continuation_blueprint(novel_id)
        if not blueprint:
            return None
        current_volume = None
        current_unit = None
        for volume in blueprint.get("volumes", []):
            for unit in volume.get("units", []):
                if unit["target_start_chapter"] <= chapter_number <= unit["target_end_chapter"]:
                    current_volume = {key: value for key, value in volume.items() if key != "units"}
                    current_unit = unit
                    break
            if current_unit:
                break

        if chapter_number < blueprint.get("start_chapter", 1):
            status = "not_started"
        elif chapter_number > blueprint.get("end_chapter", 0):
            status = "exhausted"
        else:
            status = "active"
        return {
            "status": status,
            "chapter_number": chapter_number,
            "blueprint_range": f"{blueprint.get('start_chapter', 1)}-{blueprint.get('end_chapter', 0)}",
            "book_outline": blueprint.get("book_outline", ""),
            "three_act_structure": blueprint.get("three_act_structure", {}),
            "protagonist_arc": blueprint.get("protagonist_arc", ""),
            "world_progression": blueprint.get("world_progression", ""),
            "market_optimization": blueprint.get("market_optimization", []),
            "originality_guardrails": blueprint.get("originality_guardrails", []),
            "current_volume": current_volume,
            "current_unit": current_unit,
        }

    def _build_rebased_volumes(self, result: Dict[str, Any], start_chapter: int) -> List[Dict[str, Any]]:
        fine_outlines = list(result.get("fine_outlines") or [])
        source_volumes = list(result.get("volume_outlines") or [])
        if not source_volumes and fine_outlines:
            source_volumes = [
                {
                    "volume_number": index // 8 + 1,
                    "title": f"第{index // 8 + 1}卷",
                    "optimized_units": fine_outlines[index:index + 8],
                }
                for index in range(0, len(fine_outlines), 8)
            ]

        target_cursor = start_chapter
        volumes = []
        for volume_index, source_volume in enumerate(source_volumes):
            source_units = list(source_volume.get("optimized_units") or [])
            expected_fines = fine_outlines[volume_index * 8:(volume_index + 1) * 8]
            units = []
            unit_count = max(len(source_units), len(expected_fines))
            for unit_index in range(unit_count):
                fallback_fine = expected_fines[unit_index] if unit_index < len(expected_fines) else {}
                source_unit = source_units[unit_index] if unit_index < len(source_units) else fallback_fine
                unit = self._normalize_unit(source_unit, fallback_fine)
                source_start, source_end = self._parse_range(
                    unit.get("chapter_range") or fallback_fine.get("chapter_range", ""),
                    default_length=8,
                )
                length = max(1, min(10, source_end - source_start + 1))
                target_end = target_cursor + length - 1
                unit.update({
                    "source_chapter_range": f"{source_start}-{source_end}",
                    "target_chapter_range": f"{target_cursor}-{target_end}",
                    "target_start_chapter": target_cursor,
                    "target_end_chapter": target_end,
                })
                units.append(unit)
                target_cursor = target_end + 1

            volumes.append({
                "volume_number": source_volume.get("volume_number", volume_index + 1),
                "title": source_volume.get("title", f"第{volume_index + 1}卷"),
                "optimized_arc": source_volume.get("optimized_arc", ""),
                "retain": source_volume.get("retain", []),
                "replace": source_volume.get("replace", []),
                "climax": source_volume.get("climax", ""),
                "ending_hook": source_volume.get("ending_hook", ""),
                "target_chapter_range": (
                    f"{units[0]['target_start_chapter']}-{units[-1]['target_end_chapter']}" if units else ""
                ),
                "units": units,
            })
        return volumes

    @staticmethod
    def _normalize_unit(source_unit: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(source_unit, dict):
            unit = dict(source_unit)
        else:
            unit = {"goal": str(source_unit)}
        unit.setdefault("chapter_range", fallback.get("chapter_range", ""))
        unit.setdefault("title", fallback.get("unit_title", ""))
        unit.setdefault("source_summary", fallback.get("source_summary", ""))
        unit.setdefault("goal", fallback.get("source_summary", ""))
        unit.setdefault("conflict", "")
        unit.setdefault("character_milestone", fallback.get("protagonist_development", ""))
        unit.setdefault("worldbuilding", fallback.get("worldbuilding", ""))
        unit.setdefault("hook", "；".join(fallback.get("hooks", [])))
        unit.setdefault("avoid", "；".join(fallback.get("outdated_elements", [])))
        return unit

    @staticmethod
    def _parse_range(value: str, default_length: int) -> Tuple[int, int]:
        match = RANGE_PATTERN.search(str(value))
        if not match:
            return 1, default_length
        start, end = int(match.group(1)), int(match.group(2))
        return (start, end) if end >= start else (end, start)
