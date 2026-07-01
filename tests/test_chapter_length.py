import json
import unittest

from agents.chapter_writer import ChapterWriterAgent
from agents.continuation_chapter_writer import ContinuationChapterWriter
from inkai_workflow_optimized import InkAIWorkflowOptimized


class ChapterLengthTests(unittest.TestCase):
    def test_both_writers_receive_the_shared_lean_prose_rules(self):
        captured = []

        new_writer = ChapterWriterAgent.__new__(ChapterWriterAgent)
        new_writer.call_llm = lambda messages, **kwargs: (
            captured.append(messages[-1]["content"])
            or json.dumps({"content": "正" * 3000}, ensure_ascii=False)
        )
        new_writer.process({"chapter_info": {}, "storyline": {}})

        continuation_writer = ContinuationChapterWriter.__new__(ContinuationChapterWriter)
        continuation_writer.name = "测试续写写手"
        continuation_writer.call_llm = lambda messages, **kwargs: (
            captured.append(messages[-1]["content"])
            or json.dumps({"content": "正" * 3000}, ensure_ascii=False)
        )
        continuation_writer.process({
            "storyline": {"chapter_number": 2},
            "knowledge_base": {"novel_info": {"title": "测试"}},
        })

        self.assertEqual(2, len(captured))
        for prompt in captured:
            self.assertIn("第三人称限知视角", prompt)
            self.assertIn("句式必须简单直白", prompt)
            self.assertIn("不要词藻堆砌", prompt)
            self.assertIn("禁止独立的景物描写段", prompt)
            self.assertIn("网络流行语每章最多一至两处", prompt)
            self.assertIn("不要机械地每句都换段", prompt)
            self.assertNotIn("语言生动，描写细腻", prompt)

    def test_new_chapter_writer_retries_until_body_is_around_3000_characters(self):
        agent = ChapterWriterAgent.__new__(ChapterWriterAgent)
        responses = iter([
            json.dumps({"title": "第一章", "content": "短" * 2500, "summary": "概要"}, ensure_ascii=False),
            json.dumps({"title": "第一章", "content": "正" * 3000, "summary": "概要"}, ensure_ascii=False),
        ])
        captured_messages = []

        def fake_call_llm(messages, **kwargs):
            captured_messages.append(messages)
            return next(responses)

        agent.call_llm = fake_call_llm
        result = agent.process({
            "chapter_info": {"chapter_number": 1},
            "characters": {},
            "storyline": {},
            "tags": {},
            "user_requirements": "",
        })

        self.assertNotIn("error", result)
        self.assertEqual(3000, result["word_count"])
        self.assertEqual(2, len(captured_messages))
        self.assertIn("2500", captured_messages[1][-1]["content"])
        self.assertIn("2800-3200", captured_messages[1][-1]["content"])

    def test_continuation_writer_compresses_an_overlong_chapter(self):
        agent = ContinuationChapterWriter.__new__(ContinuationChapterWriter)
        agent.name = "测试续写写手"
        responses = iter([
            json.dumps({"title": "第七章", "content": "长" * 3600, "summary": "概要"}, ensure_ascii=False),
            json.dumps({"title": "第七章", "content": "正" * 3000, "summary": "概要"}, ensure_ascii=False),
        ])
        captured_messages = []

        def fake_call_llm(messages, **kwargs):
            captured_messages.append(messages)
            return next(responses)

        agent.call_llm = fake_call_llm
        result = agent.process({
            "storyline": {"chapter_number": 7},
            "knowledge_base": {"novel_info": {"title": "测试小说"}},
            "user_requirements": "",
        })

        self.assertNotIn("error", result)
        self.assertEqual(3000, result["word_count"])
        self.assertEqual(2, len(captured_messages))
        self.assertIn("3600", captured_messages[1][-1]["content"])
        self.assertIn("压缩", captured_messages[1][-1]["content"])

    def test_continuation_save_rejects_out_of_range_body_before_writing(self):
        class FakeContext:
            novel_id = "novel-id"
            is_continuation = True

            def get_cached_result(self, key):
                if key == "next_chapter_content":
                    return {"title": "第七章", "content": "长" * 3600}
                return {}

        class FakeDataManager:
            def __init__(self):
                self.save_called = False

            def get_novel_chapters(self, novel_id):
                return [{"chapter_number": number} for number in range(1, 7)]

            def save_chapter(self, *args, **kwargs):
                self.save_called = True
                return True

        workflow = InkAIWorkflowOptimized.__new__(InkAIWorkflowOptimized)
        workflow.context = FakeContext()
        workflow.data_manager = FakeDataManager()

        result = workflow.save_continuation_chapter("novel-id")

        self.assertFalse(workflow.data_manager.save_called)
        self.assertIn("2800-3200", result["error"])

    def test_new_chapter_writer_fails_after_three_invalid_attempts(self):
        agent = ChapterWriterAgent.__new__(ChapterWriterAgent)
        responses = iter([
            json.dumps({"title": "第一章", "content": "短" * 2500, "summary": "概要"}, ensure_ascii=False)
            for _ in range(3)
        ])
        call_count = 0

        def fake_call_llm(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return next(responses)

        agent.call_llm = fake_call_llm
        result = agent.process({"chapter_info": {}, "storyline": {}})

        self.assertEqual(3, call_count)
        self.assertIn("error", result)
        self.assertIn("2500", result["error"])


if __name__ == "__main__":
    unittest.main()
