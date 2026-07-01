import json
import unittest

from agents.chapter_title_agent import ChapterTitleAgent


class ChapterTitleAgentTests(unittest.TestCase):
    def test_title_is_generated_from_finished_chapter_and_prefix_is_removed(self):
        captured = {}
        agent = ChapterTitleAgent.__new__(ChapterTitleAgent)

        def fake_call_llm(messages, **kwargs):
            captured["prompt"] = messages[-1]["content"]
            return json.dumps({
                "title": "第7章 一拳打停全场",
                "reason": "主角在擂台上用一拳结束比赛",
            }, ensure_ascii=False)

        agent.call_llm = fake_call_llm
        result = agent.process({
            "chapter_number": 7,
            "current_title": "擂台赛",
            "content": "裁判挥手。主角只出了一拳。全场没人说话。",
            "summary": "主角一拳获胜",
            "key_events": ["擂台取胜"],
        })

        self.assertEqual("一拳打停全场", result["title"])
        self.assertIn("主角只出了一拳", captured["prompt"])
        self.assertIn("不夸大正文中没有的情节", captured["prompt"])

    def test_invalid_overlong_title_falls_back_to_existing_title(self):
        agent = ChapterTitleAgent.__new__(ChapterTitleAgent)
        agent.call_llm = lambda messages, **kwargs: json.dumps({
            "title": "这是一条明显超过十八个汉字而且完全不适合作为章节名称的标题"
        }, ensure_ascii=False)

        result = agent.process({"content": "正文", "current_title": "雨夜来客"})

        self.assertEqual("雨夜来客", result["title"])
        self.assertTrue(result["used_fallback"])


if __name__ == "__main__":
    unittest.main()
