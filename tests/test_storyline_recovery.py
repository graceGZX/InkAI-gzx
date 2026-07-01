import json
import unittest

from agents.storyline_generator import StorylineGeneratorAgent


class StorylineRecoveryTests(unittest.TestCase):
    def test_recovers_storyline_json_with_a_chinese_closing_quote(self):
        raw = '''{
          "world_setting": {"location": "东洲市"},
          "main_goal": "赢得世界赛",
          "core_conflict": {"external": "强敌环伺"},
          "overall_outline": {"summary": "少年登顶。", "arcs": []},
          "volumes": [{"title": "初入武道”, "volume_number": 1}],
          "act1": {}, "act2": {}, "act3": {}
        }'''
        agent = StorylineGeneratorAgent.__new__(StorylineGeneratorAgent)

        result = agent._validate_storyline({"content": raw, "parse_error": True})

        self.assertEqual("东洲市", result["world_setting"]["location"])
        self.assertEqual("初入武道", result["volumes"][0]["title"])
        self.assertNotIn("parse_error", result)
        self.assertIn("core_conflict", result)

    def test_unrecoverable_content_keeps_safe_default_shape(self):
        agent = StorylineGeneratorAgent.__new__(StorylineGeneratorAgent)

        result = agent._validate_storyline({"content": "not json", "parse_error": True})

        for key in ("world_setting", "main_goal", "core_conflict", "act1", "act2", "act3"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
