import unittest
from unittest.mock import patch

from core.golden_opening import (
    GOLDEN_OPENING_CHAPTERS,
    golden_chapter_requirements,
    is_golden_opening_complete,
)


class GoldenOpeningTests(unittest.TestCase):
    def test_creation_finishes_only_after_three_chapters(self):
        self.assertEqual(3, GOLDEN_OPENING_CHAPTERS)
        self.assertFalse(is_golden_opening_complete(0))
        self.assertFalse(is_golden_opening_complete(1))
        self.assertFalse(is_golden_opening_complete(2))
        self.assertTrue(is_golden_opening_complete(3))

    def test_three_chapter_briefs_cover_character_world_story_and_hooks(self):
        combined = "\n".join(golden_chapter_requirements(number) for number in (1, 2, 3))

        for requirement in ("主角性格", "世界观", "故事主线", "钩子"):
            self.assertIn(requirement, combined)

        self.assertIn("小高潮", golden_chapter_requirements(3))

    def test_rejects_non_golden_chapter_number(self):
        with self.assertRaises(ValueError):
            golden_chapter_requirements(4)

    def test_creation_status_stays_in_writing_until_three_chapters(self):
        import app as app_module

        class FakeDataManager:
            def __init__(self, chapter_count):
                self.chapter_count = chapter_count

            def _load_novel_metadata(self, novel_id):
                return {"novel_id": novel_id, "title": "测试小说"}

            def load_novel_data(self, novel_id, data_type):
                return {"ready": True}

            def get_knowledge_graph_by_novel_id(self, novel_id):
                return {"ready": True}

            def get_novel_chapters(self, novel_id):
                return [{"chapter_number": number} for number in range(1, self.chapter_count + 1)]

        for chapter_count, expected in ((1, "chapter_writing"), (2, "chapter_writing"), (3, "chapter_completed")):
            with self.subTest(chapter_count=chapter_count):
                with patch.object(app_module.workflow, "data_manager", FakeDataManager(chapter_count)):
                    status = app_module.get_creation_workflow_status("novel-id")

                self.assertEqual(expected, status["current_step"])

    def test_workflow_writes_second_and_third_chapters_before_completion(self):
        from inkai_workflow_optimized import InkAIWorkflowOptimized

        class FakeContext:
            novel_id = "novel-id"
            storyline = {"first_module": {"chapter_title": "开端", "plot_points": ["危机爆发"]}}

            def __init__(self):
                self.current_step = "chapter_writing"

            def get_agent_input_data(self, agent_name, extra):
                return {"storyline": self.storyline, **extra}

            def cache_quality_assessment(self, content_type, result):
                pass

            def set_current_step(self, step):
                self.current_step = step

        class FakeDataManager:
            def __init__(self, chapter_count):
                self.chapters = [
                    {
                        "chapter_number": number,
                        "title": f"第{number}章",
                        "summary": f"第{number}章概要",
                        "content": f"第{number}章正文",
                    }
                    for number in range(1, chapter_count + 1)
                ]
                self.saved = None

            def get_novel_chapters(self, novel_id):
                return self.chapters

            def save_chapter(self, novel_id, chapter_number, chapter):
                self.saved = (chapter_number, chapter)
                self.chapters.append({"chapter_number": chapter_number, **chapter})
                return True

            def load_novel_data(self, novel_id, data_type):
                return None

        class FakeWriter:
            def __init__(self):
                self.input_data = None

            def process(self, input_data):
                self.input_data = input_data
                number = input_data["chapter_info"]["chapter_number"]
                return {
                    "chapter_content": {"title": f"第{number}章", "content": f"正文{number}", "summary": "概要"}
                }

        class FakeQualityAssessor:
            def process(self, input_data):
                return {"overall_score": 90}

        for starting_count, expected_number, expected_step in (
            (1, 2, "chapter_writing"),
            (2, 3, "chapter_completed"),
        ):
            with self.subTest(starting_count=starting_count):
                workflow = InkAIWorkflowOptimized.__new__(InkAIWorkflowOptimized)
                workflow.context = FakeContext()
                workflow.data_manager = FakeDataManager(starting_count)
                workflow.chapter_writer = FakeWriter()
                workflow.quality_assessor = FakeQualityAssessor()

                result = workflow.write_first_chapter()

                self.assertEqual(expected_number, workflow.data_manager.saved[0])
                self.assertEqual(expected_step, workflow.context.current_step)
                self.assertEqual(expected_step, result["next_step"])
                chapter_info = workflow.chapter_writer.input_data["chapter_info"]
                self.assertEqual(expected_number, chapter_info["chapter_number"])
                self.assertIn("黄金第", chapter_info["golden_requirements"])
                self.assertIn("上一章", chapter_info["previous_chapter_context"])

    def test_chapter_writer_reads_the_nested_overall_storyline(self):
        from agents.chapter_writer import ChapterWriterAgent

        formatted = ChapterWriterAgent.__new__(ChapterWriterAgent)._format_storyline_info({
            "overall_storyline": {
                "world_setting": {"rules": "情绪可以凝成武器"},
                "main_goal": "找到失踪的太阳",
                "core_conflict": {"external": "永夜吞噬城邦"},
                "overall_outline": {"summary": "少年点燃人造太阳，终结永夜。"},
                "volumes": [{"synopsis": "从边城追查到永夜王庭。"}],
                "act1": {"key_events": ["边城熄灯", "主角觉醒"]},
                "tone": "热血悬疑",
            }
        })

        for expected in ("情绪可以凝成武器", "找到失踪的太阳", "少年点燃人造太阳", "边城熄灯"):
            self.assertIn(expected, formatted)


if __name__ == "__main__":
    unittest.main()
