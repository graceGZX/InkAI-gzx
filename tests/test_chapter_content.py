import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.chapter_content import extract_chapter_text
from data_manager import DataManager


class ChapterContentTests(unittest.TestCase):
    def test_extracts_content_from_bare_json_string(self):
        raw = json.dumps({
            "chapter_number": 6,
            "title": "封印之下",
            "content": "真正的第六章正文\n\n第二段。",
        }, ensure_ascii=False)

        self.assertEqual("真正的第六章正文\n\n第二段。", extract_chapter_text(raw))

    def test_extracts_content_from_markdown_json(self):
        raw = '```json\n{"content": "纯正文"}\n```'

        self.assertEqual("纯正文", extract_chapter_text(raw))

    def test_extracts_closed_content_field_from_truncated_outer_json(self):
        raw = '{"title":"第六章","content":"完整正文\\n第二段","changes":[{"after":"截断'

        self.assertEqual("完整正文\n第二段", extract_chapter_text(raw))

    def test_plain_prose_is_unchanged(self):
        raw = "第一段。\n\n第二段。"

        self.assertEqual(raw, extract_chapter_text(raw))

    def test_data_manager_never_persists_json_as_chapter_body(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            novels_dir = Path(temp_dir) / "novels"
            graphs_dir = Path(temp_dir) / "graphs"
            with (
                patch("data_manager.config.NOVELS_DIR", str(novels_dir)),
                patch("data_manager.config.KNOWLEDGE_GRAPHS_DIR", str(graphs_dir)),
            ):
                manager = DataManager()
                novel_id = manager.create_novel_project({"title": "测试小说"})
                wrapped = json.dumps({"title": "第一章", "content": "真正正文"}, ensure_ascii=False)

                saved = manager.save_chapter(
                    novel_id,
                    1,
                    {"title": "第一章", "content": wrapped},
                    auto_commit=False,
                )

                self.assertTrue(saved)
                chapter = manager.get_novel_chapters(novel_id)[0]
                self.assertEqual("真正正文", chapter["content"])
                self.assertEqual(len("真正正文"), chapter["word_count"])


if __name__ == "__main__":
    unittest.main()
