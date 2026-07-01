import unittest
import json

from agents.character_creator import CharacterCreatorAgent


class CharacterCreatorTests(unittest.TestCase):
    def test_supporting_character_prompt_treats_reference_names_as_forbidden_material(self):
        captured = {}
        agent = CharacterCreatorAgent.__new__(CharacterCreatorAgent)

        def fake_call_llm(messages, **kwargs):
            captured["prompt"] = messages[-1]["content"]
            return json.dumps({
                "role": "女主（核心恋人）",
                "basic_info": {"name": "许知微", "gender": "女"},
            }, ensure_ascii=False)

        agent.call_llm = fake_call_llm
        agent._create_single_supporting_character(
            "女主（核心恋人）",
            {"basic_info": {"name": "陆寻"}},
            {"主题标签": ["爱情"]},
            "参考资料中出现严喆珂，但不得复用原作人物。",
        )

        self.assertIn("全部视为禁用素材", captured["prompt"])
        self.assertIn("严禁直接采用", captured["prompt"])

    def test_romance_requirement_forces_a_female_lead_even_without_romance_type_tag(self):
        agent = CharacterCreatorAgent.__new__(CharacterCreatorAgent)
        roles = agent._determine_supporting_roles(
            {
                "类型标签": ["都市", "玄幻"],
                "主题标签": ["成长", "爱情", "校园"],
            },
            "主角与恋人双向成长，最终结婚。",
            {"basic_info": {"gender": "男"}},
        )

        self.assertEqual("女主（核心恋人）", roles[0])
        self.assertIn("朋友", roles)
        self.assertIn("导师", roles)
        self.assertIn("对手", roles)

    def test_non_romance_story_keeps_the_default_supporting_roles(self):
        agent = CharacterCreatorAgent.__new__(CharacterCreatorAgent)

        roles = agent._determine_supporting_roles(
            {"类型标签": ["都市", "玄幻"], "主题标签": ["成长"]},
            "主角独自追查失踪案件。",
            {"basic_info": {"gender": "男"}},
        )

        self.assertEqual(["朋友", "导师", "对手"], roles)


if __name__ == "__main__":
    unittest.main()
