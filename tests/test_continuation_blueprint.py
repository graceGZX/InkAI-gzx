import unittest
import json

from agents.continuation_storyline_generator import ContinuationStorylineGenerator
from core.continuation_blueprint import ContinuationBlueprintManager


class ContinuationBlueprintTests(unittest.TestCase):
    def test_attached_blueprint_is_rebased_to_the_novels_next_chapter(self):
        class FakeDataManager:
            def __init__(self):
                self.saved = None

            def get_novel_chapters(self, novel_id):
                return [{"chapter_number": number} for number in range(1, 7)]

            def save_continuation_blueprint(self, novel_id, blueprint):
                self.saved = blueprint
                return True

            def load_continuation_blueprint(self, novel_id):
                return self.saved

        analysis_state = {
            "analysis_id": "analysis-123",
            "title": "参考小说",
            "status": "completed",
            "deep_extraction": {
                "result": {
                    "book_outline": "原创化后的整书主线",
                    "three_act_structure": {"act1": "建立", "act2": "对抗", "act3": "解决"},
                    "protagonist_arc": "从求生到建立秩序",
                    "world_progression": "边城到诸天",
                    "market_optimization": ["高密度冲突"],
                    "originality_guardrails": ["禁止复用专有角色"],
                    "fine_outlines": [
                        {"chapter_range": "1-8", "unit_title": "边城危机", "source_summary": "危机爆发"},
                        {"chapter_range": "9-16", "unit_title": "王都试炼", "source_summary": "进入新地图"},
                    ],
                    "volume_outlines": [{
                        "volume_number": 1,
                        "title": "第一卷",
                        "optimized_arc": "主角守住边城后进入王都",
                        "optimized_units": [
                            {
                                "chapter_range": "1-8",
                                "goal": "守住边城",
                                "conflict": "城破危机",
                                "character_milestone": "主角承担责任",
                                "worldbuilding": "展示城邦规则",
                                "hook": "王都使者到来",
                                "avoid": "重复打脸",
                            },
                            {
                                "chapter_range": "9-16",
                                "goal": "赢得试炼",
                                "conflict": "派系博弈",
                                "character_milestone": "建立第一支队伍",
                                "worldbuilding": "展示王朝势力",
                                "hook": "上界线索出现",
                                "avoid": "无意义比赛",
                            },
                        ],
                        "climax": "边城保卫战",
                        "ending_hook": "进入王都",
                    }],
                }
            },
        }
        data_manager = FakeDataManager()
        manager = ContinuationBlueprintManager(data_manager)

        blueprint = manager.attach("novel-id", analysis_state)
        context = manager.context_for_chapter("novel-id", 10)

        self.assertEqual(7, blueprint["start_chapter"])
        self.assertEqual("7-14", blueprint["volumes"][0]["units"][0]["target_chapter_range"])
        self.assertEqual("守住边城", context["current_unit"]["goal"])
        self.assertEqual("第一卷", context["current_volume"]["title"])
        self.assertIn("禁止复用专有角色", context["originality_guardrails"])

    def test_storyline_agent_receives_the_current_blueprint_unit(self):
        captured = {}
        agent = ContinuationStorylineGenerator.__new__(ContinuationStorylineGenerator)
        agent.name = "测试故事线"

        def fake_call_llm(messages, **kwargs):
            captured["prompt"] = messages[-1]["content"]
            return json.dumps({
                "chapter_number": 10,
                "chapter_title": "守城之夜",
                "scene_setting": {"time": "夜", "location": "边城", "atmosphere": "紧张"},
                "plot_points": ["主角组织守城"],
            }, ensure_ascii=False)

        agent.call_llm = fake_call_llm
        result = agent.process({
            "knowledge_base": {
                "novel_info": {"title": "原创小说"},
                "chapters": [{"chapter_number": number} for number in range(1, 10)],
                "continuation_blueprint": {
                    "status": "active",
                    "blueprint_range": "7-22",
                    "book_outline": "建立新秩序",
                    "originality_guardrails": ["禁止复用专有角色"],
                    "current_volume": {
                        "title": "第一卷",
                        "target_chapter_range": "7-22",
                        "optimized_arc": "守城后进入王都",
                    },
                    "current_unit": {
                        "title": "边城危机",
                        "target_chapter_range": "7-14",
                        "goal": "守住边城",
                        "conflict": "城破危机",
                        "character_milestone": "主角承担责任",
                        "worldbuilding": "城邦规则",
                        "hook": "王都使者到来",
                        "avoid": "重复打脸",
                    },
                },
            },
        })

        self.assertEqual("守城之夜", result["next_chapter_storyline"]["chapter_title"])
        self.assertIn("守住边城", captured["prompt"])
        self.assertIn("7-14", captured["prompt"])
        self.assertIn("禁止复用专有角色", captured["prompt"])


if __name__ == "__main__":
    unittest.main()
