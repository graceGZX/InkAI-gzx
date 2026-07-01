import json
import io
import tempfile
import time
import unittest
from unittest.mock import patch

from reference_novel_analyzer import ReferenceNovelAnalyzer
from reference_novel_service import ReferenceNovelService


class ReferenceNovelAnalyzerTests(unittest.TestCase):
    def test_large_novel_returns_bounded_reference_value_report(self):
        captured = {}
        text = "\n".join(
            f"第{number}章 章节{number}\n" + (f"第{number}章剧情内容。" * 500)
            for number in range(1, 121)
        )

        def fake_llm(messages):
            captured["messages"] = messages
            return json.dumps({
                "summary": "少年从边城崛起并终结旧秩序。",
                "three_act_structure": {
                    "act1": "边城危机与能力觉醒",
                    "act2": "进入王朝并持续升级",
                    "act3": "推翻旧秩序",
                },
                "protagonist_arc": "从求生者成长为秩序建立者",
                "worldbuilding": "城邦、王朝与上界逐层展开",
                "strengths": ["升级反馈明确", "章末钩子稳定"],
                "weaknesses": ["中期副本重复"],
                "reusable_patterns": ["危机开篇", "地图递进"],
                "avoid_patterns": ["重复打脸"],
                "scores": {
                    "market_appeal": 88,
                    "opening_hook": 90,
                    "long_form_structure": 82,
                    "characterization": 78,
                    "payoff_design": 86,
                    "current_trend_fit": 80,
                    "target_match": 91,
                },
                "verdict": "recommended",
                "verdict_reason": "结构与目标题材高度匹配，值得继续拆解。",
                "confidence": 0.82,
            }, ensure_ascii=False)

        analyzer = ReferenceNovelAnalyzer(
            llm=fake_llm,
            researcher=lambda title: {
                "status": "live",
                "sources": ["Bing 搜索"],
                "highlights": ["读者评价节奏快、开篇强"],
            },
        )

        result = analyzer.analyze("测试神作", text, "东方玄幻男频")

        self.assertEqual("recommended", result["verdict"])
        self.assertEqual(120, result["source_profile"]["chapter_count"])
        self.assertEqual("live", result["research"]["status"])
        prompt = captured["messages"][-1]["content"]
        self.assertLess(len(prompt), 50000)
        self.assertIn("第1章", prompt)
        self.assertIn("第120章", prompt)
        self.assertIn("东方玄幻男频", prompt)
        self.assertIn("读者评价节奏快", prompt)

    def test_upload_route_accepts_gb18030_txt_and_returns_analysis_id(self):
        import app as app_module

        captured = {}

        class FakeService:
            def create_screening(self, filename, raw, title, target_direction):
                captured.update(
                    filename=filename,
                    raw=raw,
                    title=title,
                    target_direction=target_direction,
                )
                return {
                    "analysis_id": "analysis-123",
                    "title": title,
                    "status": "screened",
                    "report": {"verdict": "recommended"},
                }

        body = "第一章 开端\n这是一本测试小说。".encode("gb18030")
        with patch.object(app_module, "reference_novel_service", FakeService(), create=True):
            response = app_module.app.test_client().post(
                "/api/reference-novels/analyze",
                data={
                    "file": (io.BytesIO(body), "测试小说.txt"),
                    "title": "测试小说",
                    "target_direction": "都市悬疑",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual("analysis-123", payload["data"]["analysis_id"])
        self.assertEqual(body, captured["raw"])
        self.assertEqual("都市悬疑", captured["target_direction"])

    def test_create_novel_attaches_reference_blueprint_before_responding(self):
        import app as app_module

        events = []

        class FakeWorkflow:
            def start_new_novel(self, requirements, title):
                events.append(("create", requirements, title))
                return {"novel_id": "novel-123", "status": "created"}

        class FakeService:
            def attach_to_novel(self, analysis_id, novel_id):
                events.append(("attach", analysis_id, novel_id))
                return {
                    "analysis_id": analysis_id,
                    "reference_title": "全球高武",
                    "start_chapter": 1,
                    "end_chapter": 1400,
                }

        with patch.object(app_module, "workflow", FakeWorkflow()), patch.object(
            app_module, "reference_novel_service", FakeService()
        ):
            response = app_module.app.test_client().post(
                "/api/novels",
                json={
                    "title": "原创新书",
                    "user_requirements": "5000字内的创作摘要",
                    "reference_analysis_id": "analysis-123",
                },
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual("create", events[0][0])
        self.assertEqual(("attach", "analysis-123", "novel-123"), events[1])
        blueprint = response.get_json()["data"]["continuation_blueprint"]
        self.assertEqual("全球高武", blueprint["reference_title"])

    def test_confirmed_deep_extraction_builds_fine_volume_and_book_outlines(self):
        text = "\n".join(
            f"第{number}章 章节{number}\n" + (f"剧情{number}。" * 40)
            for number in range(1, 18)
        )
        prompts = []

        def fake_llm(messages):
            prompt = messages[-1]["content"]
            prompts.append(prompt)
            if "任务阶段：5-10章细纲抽取" in prompt:
                match = "1-9" if "第1章" in prompt and "第9章" in prompt else "10-17"
                return json.dumps({
                    "chapter_range": match,
                    "unit_title": f"单元{match}",
                    "source_summary": "原剧情推进",
                    "plot_progression": ["危机", "反转", "兑现"],
                    "protagonist_development": "主角完成阶段成长",
                    "worldbuilding": ["扩展新地图"],
                    "hooks": ["章末悬念"],
                    "payoffs": ["兑现旧伏笔"],
                    "structural_patterns": ["递进冲突"],
                    "outdated_elements": ["重复打脸"],
                }, ensure_ascii=False)
            if "任务阶段：卷级审查与优化" in prompt:
                return json.dumps({
                    "volume_number": 1,
                    "title": "第一卷",
                    "source_arc": "原卷故事弧",
                    "optimized_arc": "压缩重复桥段后的故事弧",
                    "retain": ["递进冲突"],
                    "replace": [{"outdated": "重复打脸", "replacement": "立场博弈"}],
                    "optimized_units": ["单元1-9", "单元10-17"],
                    "climax": "卷末高潮",
                    "ending_hook": "新地图开启",
                }, ensure_ascii=False)
            return json.dumps({
                "book_outline": "优化后的整书主线",
                "three_act_structure": {"act1": "建立", "act2": "对抗", "act3": "解决"},
                "protagonist_arc": "完整成长弧",
                "world_progression": "地图逐级扩展",
                "market_optimization": ["减少重复冲突", "增强关系博弈"],
                "originality_guardrails": ["不得复用专有角色和标志性桥段"],
            }, ensure_ascii=False)

        analyzer = ReferenceNovelAnalyzer(llm=fake_llm, researcher=lambda title: {})
        progress = []
        result = analyzer.deep_extract(
            text=text,
            screening_report={
                "research": {"highlights": ["当前读者偏好高密度冲突"]},
                "weaknesses": ["重复打脸"],
                "reusable_patterns": ["递进冲突"],
            },
            target_direction="东方玄幻",
            progress_callback=lambda value, message: progress.append((value, message)),
        )

        self.assertEqual(2, len(result["fine_outlines"]))
        self.assertEqual(1, len(result["volume_outlines"]))
        self.assertEqual("优化后的整书主线", result["book_outline"])
        self.assertEqual(100, progress[-1][0])
        self.assertTrue(any("卷级审查" in prompt for prompt in prompts))

    def test_service_runs_confirmed_deep_extraction_in_background(self):
        class FakeAnalyzer:
            def analyze(self, title, text, target_direction):
                return {"verdict": "recommended", "research": {}}

            def deep_extract(self, text, screening_report, target_direction, progress_callback):
                progress_callback(45, "正在生成细纲")
                return {"book_outline": "完成的大纲", "fine_outlines": [], "volume_outlines": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            service = ReferenceNovelService(temp_dir, FakeAnalyzer())
            state = service.create_screening(
                "测试.txt",
                "第一章\n正文".encode("utf-8"),
                "测试小说",
                "玄幻",
            )

            started = service.start_deep_extraction(state["analysis_id"])
            self.assertEqual("extracting", started["status"])

            deadline = time.time() + 2
            completed = None
            while time.time() < deadline:
                completed = service.get_state(state["analysis_id"])
                if completed["status"] == "completed":
                    break
                time.sleep(0.01)

            self.assertEqual("completed", completed["status"])
            self.assertEqual(100, completed["deep_extraction"]["progress"])
            self.assertEqual("完成的大纲", completed["deep_extraction"]["result"]["book_outline"])


if __name__ == "__main__":
    unittest.main()
