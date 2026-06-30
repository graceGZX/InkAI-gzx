import json
import unittest
from unittest.mock import patch

from concept_advisor import ConceptAdvisor


class ConceptAdvisorTests(unittest.TestCase):
    def test_initial_turn_returns_three_researched_genre_options(self):
        captured = {}

        def fake_research(seed):
            return {
                "status": "live",
                "checked_at": "2026-06-30",
                "sources": ["番茄小说排行榜"],
                "highlights": ["玄幻与都市脑洞竞争活跃"],
            }

        def fake_llm(messages):
            captured["messages"] = messages
            return json.dumps({
                "question": "这里有三个差异化方向",
                "options": [],
                "stage": "recommending",
                "concept": None,
                "proposals": [
                    {"code": "甲", "title": "薪火边城", "genre": "东方玄幻"},
                    {"code": "乙", "title": "异常档案", "genre": "都市异能"},
                    {"code": "丙", "title": "末日店长", "genre": "末世经营"},
                ],
            }, ensure_ascii=False)

        advisor = ConceptAdvisor(llm=fake_llm, researcher=fake_research)
        result = advisor.respond(messages=[], seed={"title": "", "requirements": ""})

        self.assertEqual("recommending", result["stage"])
        self.assertEqual(3, len(result["options"]))
        self.assertEqual(3, len(result["proposals"]))
        self.assertIn("薪火边城", result["options"][0])
        self.assertEqual("live", result["research"]["status"])
        self.assertIn("玄幻与都市脑洞竞争活跃", captured["messages"][0]["content"])

    def test_confirming_turn_builds_creation_requirements_from_concept(self):
        concept = {
            "title": "薪火边城",
            "genre": "东方玄幻",
            "subgenre": "人族崛起",
            "audience": "番茄男频18-35岁",
            "logline": "守城少年借文明薪火对抗万族封锁。",
            "selling_points": ["文明记忆升级", "边城经营"],
            "tone": "热血快节奏",
            "opening_direction": "第一章城破，第三章点燃第一枚薪火。",
            "world": {
                "premise": "万族垄断超凡知识，人族困守边城。",
                "power_system": "薪火九阶，每阶解锁一段文明能力。",
                "protagonist_advantage": "可读取失落文明记忆。",
                "limitations": "每次读取都会遗失一段个人记忆。",
                "society": "城邦联盟与万族议会对峙。",
                "geography": "边城、荒原、万族中央圣域逐级展开。",
                "factions": ["边城守夜人", "万族议会"],
                "core_conflicts": ["知识封锁", "记忆代价"],
                "taboos": ["能力不能无代价升级"],
            },
        }

        def fake_llm(messages):
            return json.dumps({
                "question": "这是最终方案，确认吗？",
                "options": ["确认", "继续修改"],
                "stage": "confirming",
                "concept": concept,
            }, ensure_ascii=False)

        advisor = ConceptAdvisor(
            llm=fake_llm,
            researcher=lambda seed: {"status": "fallback", "highlights": []},
        )
        result = advisor.respond(
            messages=[
                {"role": "user", "content": "选东方玄幻"},
                {"role": "assistant", "content": "更偏经营还是战斗？"},
                {"role": "user", "content": "边城经营加热血战斗"},
            ],
            seed={"title": "", "requirements": ""},
        )

        self.assertEqual("confirming", result["stage"])
        self.assertEqual(["确认并填写创作需求", "继续修改方案"], result["options"])
        self.assertIn("【题材定位】东方玄幻 - 人族崛起", result["concept"]["requirements_text"])
        self.assertIn("【力量体系】薪火九阶", result["concept"]["requirements_text"])
        self.assertIn("【限制与代价】每次读取", result["concept"]["requirements_text"])

    def test_selected_proposal_cannot_restart_recommendations(self):
        responses = iter([
            json.dumps({
                "question": "又给你三个方向",
                "options": ["甲", "乙", "丙"],
                "stage": "recommending",
                "concept": None,
            }, ensure_ascii=False),
            json.dumps({
                "question": "你选择了逢灯纪，更偏单元诡案还是朝堂主线？",
                "options": ["单元诡案", "朝堂主线", "两者并重"],
                "stage": "clarifying",
                "concept": None,
            }, ensure_ascii=False),
        ])

        advisor = ConceptAdvisor(
            llm=lambda messages: next(responses),
            researcher=lambda seed: {"status": "live", "highlights": []},
        )
        result = advisor.respond(
            messages=[{"role": "user", "content": "我选择甲：逢灯纪"}],
            seed={"title": "", "requirements": ""},
        )

        self.assertEqual("clarifying", result["stage"])
        self.assertIn("逢灯纪", result["question"])

    def test_unstructured_initial_response_is_retried(self):
        responses = iter([
            "我先随便聊聊几个方向",
            json.dumps({
                "question": "三个完整方向如下",
                "options": [],
                "stage": "recommending",
                "concept": None,
                "proposals": [
                    {"code": "甲", "title": "甲书", "genre": "玄幻"},
                    {"code": "乙", "title": "乙书", "genre": "都市"},
                    {"code": "丙", "title": "丙书", "genre": "科幻"},
                ],
            }, ensure_ascii=False),
        ])
        advisor = ConceptAdvisor(
            llm=lambda messages: next(responses),
            researcher=lambda seed: {"status": "fallback", "highlights": []},
        )

        result = advisor.respond(messages=[], seed={"title": "", "requirements": ""})

        self.assertEqual("recommending", result["stage"])
        self.assertEqual(3, len(result["proposals"]))


class ConceptDialogueRouteTests(unittest.TestCase):
    def test_route_forwards_dialogue_state_to_advisor(self):
        import app as app_module

        captured = {}

        class FakeAdvisor:
            def respond(self, messages, seed, research=None):
                captured.update(messages=messages, seed=seed, research=research)
                return {
                    "question": "请选择方向",
                    "options": ["甲", "乙", "丙"],
                    "stage": "recommending",
                    "concept": None,
                    "research": {"status": "live"},
                }

        with patch.object(app_module, "concept_advisor", FakeAdvisor(), create=True):
            response = app_module.app.test_client().post(
                "/api/concept/dialogue",
                json={
                    "messages": [{"role": "user", "content": "偏悬疑"}],
                    "seed": {"title": "暂定", "requirements": "现代悬疑"},
                    "research": {"status": "live"},
                },
            )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.get_json()["success"])
        self.assertEqual("现代悬疑", captured["seed"]["requirements"])
        self.assertEqual("偏悬疑", captured["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
