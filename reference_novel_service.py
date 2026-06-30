"""Persistent reference-novel analysis sessions."""

import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from reference_novel_analyzer import ReferenceNovelAnalyzer, decode_txt_bytes


ANALYSIS_ID_PATTERN = re.compile(r"^[0-9a-f-]{36}$")


class ReferenceNovelService:
    def __init__(self, root_dir: str, analyzer: ReferenceNovelAnalyzer, blueprint_manager: Any = None) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = analyzer
        self.blueprint_manager = blueprint_manager
        self._lock = threading.Lock()
        self._jobs: Dict[str, threading.Thread] = {}
        self._recover_interrupted_sessions()

    def create_screening(
        self,
        filename: str,
        raw: bytes,
        title: str = "",
        target_direction: str = "",
    ) -> Dict[str, Any]:
        if not filename.lower().endswith(".txt"):
            raise ValueError("只支持上传 TXT 小说文件")
        if not raw:
            raise ValueError("上传的 TXT 文件为空")

        text = decode_txt_bytes(raw).strip()
        if not text:
            raise ValueError("TXT 中没有可读取的小说正文")
        title = (title or Path(filename).stem).strip()[:120]
        target_direction = target_direction.strip()[:500]
        analysis_id = str(uuid.uuid4())
        session_dir = self.root_dir / analysis_id
        session_dir.mkdir(parents=True)
        (session_dir / "source.txt").write_text(text, encoding="utf-8")

        try:
            report = self.analyzer.analyze(title, text, target_direction)
            state = {
                "analysis_id": analysis_id,
                "title": title,
                "filename": os.path.basename(filename),
                "target_direction": target_direction,
                "status": "screened",
                "report": report,
                "deep_extraction": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            self._write_state(session_dir, state)
            return state
        except Exception:
            for path in session_dir.glob("*"):
                path.unlink(missing_ok=True)
            session_dir.rmdir()
            raise

    def get_state(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        session_dir = self._session_dir(analysis_id)
        state_file = session_dir / "state.json"
        if not state_file.exists():
            return None
        return json.loads(state_file.read_text(encoding="utf-8"))

    def start_deep_extraction(self, analysis_id: str) -> Dict[str, Any]:
        state = self.get_state(analysis_id)
        if not state:
            raise ValueError("分析任务不存在")
        if state.get("status") in ("extracting", "completed"):
            return state

        state["status"] = "extracting"
        state["deep_extraction"] = {
            "progress": 0,
            "message": "深度提取任务已启动",
            "result": None,
            "error": None,
        }
        session_dir = self._session_dir(analysis_id)
        self._write_state(session_dir, state)
        started_state = json.loads(json.dumps(state, ensure_ascii=False))
        thread = threading.Thread(
            target=self._run_deep_extraction,
            args=(analysis_id,),
            name=f"reference-analysis-{analysis_id[:8]}",
            daemon=True,
        )
        self._jobs[analysis_id] = thread
        thread.start()
        return started_state

    def attach_to_novel(self, analysis_id: str, novel_id: str) -> Dict[str, Any]:
        if not self.blueprint_manager:
            raise ValueError("续写蓝图模块尚未初始化")
        state = self.get_state(analysis_id)
        if not state:
            raise ValueError("分析任务不存在")
        return self.blueprint_manager.attach(novel_id, state)

    def _run_deep_extraction(self, analysis_id: str) -> None:
        session_dir = self._session_dir(analysis_id)

        def update_progress(value: int, message: str) -> None:
            current = self.get_state(analysis_id)
            if not current:
                return
            current["status"] = "extracting"
            current["deep_extraction"]["progress"] = max(0, min(100, int(value)))
            current["deep_extraction"]["message"] = message
            self._write_state(session_dir, current)

        try:
            state = self.get_state(analysis_id)
            text = (session_dir / "source.txt").read_text(encoding="utf-8")
            result = self.analyzer.deep_extract(
                text=text,
                screening_report=state.get("report", {}),
                target_direction=state.get("target_direction", ""),
                progress_callback=update_progress,
            )
            state = self.get_state(analysis_id)
            state["status"] = "completed"
            state["deep_extraction"] = {
                "progress": 100,
                "message": "深度提取与大纲优化完成",
                "result": result,
                "error": None,
            }
            self._write_state(session_dir, state)
        except Exception as exc:
            state = self.get_state(analysis_id)
            if state:
                state["status"] = "failed"
                state["deep_extraction"]["error"] = str(exc)
                state["deep_extraction"]["message"] = "深度提取失败"
                self._write_state(session_dir, state)
        finally:
            self._jobs.pop(analysis_id, None)

    def _session_dir(self, analysis_id: str) -> Path:
        if not ANALYSIS_ID_PATTERN.fullmatch(analysis_id or ""):
            raise ValueError("无效的分析任务 ID")
        return self.root_dir / analysis_id

    def _recover_interrupted_sessions(self) -> None:
        for state_file in self.root_dir.glob("*/state.json"):
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if state.get("status") != "extracting":
                    continue
                state["status"] = "failed"
                state.setdefault("deep_extraction", {})["error"] = "服务重启导致任务中断，可重新启动深度提取"
                state["deep_extraction"]["message"] = "任务已中断"
                self._write_state(state_file.parent, state)
            except Exception:
                continue

    def _write_state(self, session_dir: Path, state: Dict[str, Any]) -> None:
        state["updated_at"] = datetime.now().isoformat()
        state_file = session_dir / "state.json"
        temp_file = state_file.with_suffix(".json.tmp")
        with self._lock:
            temp_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_file.replace(state_file)
