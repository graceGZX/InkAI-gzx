"""
Agent 记忆管理器
每个 agent 运行后可以将优化建议沉淀为记忆，供后续章节写作参考。
记忆以 per-novel per-agent 维度存储。
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import config


class AgentMemory:
    """单个 agent 的记忆管理器"""

    def __init__(self, novel_id: str, agent_name: str):
        self.novel_id = novel_id
        self.agent_name = agent_name
        self._data: Dict[str, Any] = {}
        self._loaded = False

    @property
    def _storage_dir(self) -> str:
        return os.path.join(config.NOVELS_DIR, self.novel_id, "memory")

    @property
    def _file_path(self) -> str:
        return os.path.join(self._storage_dir, f"{self.agent_name}.json")

    def load(self) -> Dict[str, Any]:
        """从磁盘加载记忆，不存在则返回空模板"""
        if self._loaded:
            return self._data
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
            if os.path.exists(self._file_path):
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = self._empty_template()
                self._save_raw()
        except Exception as e:
            print(f"[AgentMemory] 加载记忆失败 ({self.agent_name}): {e}")
            self._data = self._empty_template()
        self._loaded = True
        return self._data

    def add_insight(self, insight: Dict[str, Any]) -> str:
        """追加一条经验洞察，返回 insight id"""
        self.load()
        insights: List[Dict] = self._data.setdefault("insights", [])
        entry = {
            "id": insight.get("id") or uuid.uuid4().hex[:12],
            "timestamp": datetime.now().isoformat(),
            "source_chapter": insight.get("source_chapter"),
            "source_agent": insight.get("source_agent", self.agent_name),
            "category": insight.get("category", "other"),
            "content": insight.get("content", ""),
            "severity": insight.get("severity", "medium"),
            "applied": insight.get("applied", False),
        }
        insights.append(entry)
        # 同步更新 patterns
        self._update_patterns(entry)
        self._save_raw()
        return entry["id"]

    def delete_insight(self, insight_id: str) -> bool:
        """删除指定条目"""
        self.load()
        insights: List[Dict] = self._data.get("insights", [])
        new_insights = [i for i in insights if i.get("id") != insight_id]
        if len(new_insights) == len(insights):
            return False
        self._data["insights"] = new_insights
        self._rebuild_patterns()
        self._save_raw()
        return True

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最近 n 条经验（按时间倒序）"""
        self.load()
        insights: List[Dict] = self._data.get("insights", [])
        return sorted(insights, key=lambda x: x.get("timestamp", ""), reverse=True)[:n]

    def get_for_context(self) -> str:
        """生成可注入 prompt 的记忆摘要文本"""
        self.load()
        insights: List[Dict] = self._data.get("insights", [])
        if not insights:
            return ""
        recent = sorted(insights, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]
        lines = ["【从历史优化中学到的经验】"]
        for i, entry in enumerate(recent, 1):
            cat = entry.get("category", "other")
            lines.append(f"{i}. [{cat}] {entry.get('content', '')}")
        patterns = self._data.get("patterns", {})
        if patterns:
            lines.append("\n【常见模式】")
            for key, items in patterns.items():
                if items:
                    lines.append(f"- {key}: {', '.join(items[-3:])}")
        return "\n".join(lines)

    # ── 内部方法 ──

    def _empty_template(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "novel_id": self.novel_id,
            "created_at": datetime.now().isoformat(),
            "insights": [],
            "patterns": {},
        }

    def _save_raw(self):
        os.makedirs(self._storage_dir, exist_ok=True)
        self._data["updated_at"] = datetime.now().isoformat()
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _update_patterns(self, entry: Dict[str, Any]):
        """根据新增 insight 更新 patterns 聚合"""
        cat = entry.get("category", "other")
        content = entry.get("content", "")
        if cat not in self._data.setdefault("patterns", {}):
            self._data["patterns"][cat] = []
        if content not in self._data["patterns"][cat]:
            self._data["patterns"][cat].append(content)

    def _rebuild_patterns(self):
        """从 insights 重建 patterns"""
        self._data["patterns"] = {}
        for entry in self._data.get("insights", []):
            self._update_patterns(entry)


# ── 便捷函数（供 app.py 路由使用） ──

def get_all_memories_summary(novel_id: str) -> str:
    """获取某个小说所有 agent 的记忆摘要，用于注入写作上下文"""
    memory_dir = os.path.join(config.NOVELS_DIR, novel_id, "memory")
    if not os.path.isdir(memory_dir):
        return ""
    parts: List[str] = []
    for fname in sorted(os.listdir(memory_dir)):
        if not fname.endswith(".json"):
            continue
        agent_name = fname[:-5]
        mem = AgentMemory(novel_id, agent_name)
        ctx = mem.get_for_context()
        if ctx:
            parts.append(f"### {agent_name}\n{ctx}")
    return "\n\n".join(parts)


def list_agent_memories(novel_id: str) -> List[Dict[str, Any]]:
    """列出某小说下所有 agent 的记忆摘要"""
    memory_dir = os.path.join(config.NOVELS_DIR, novel_id, "memory")
    if not os.path.isdir(memory_dir):
        return []
    result: List[Dict] = []
    for fname in sorted(os.listdir(memory_dir)):
        if not fname.endswith(".json"):
            continue
        agent_name = fname[:-5]
        mem = AgentMemory(novel_id, agent_name)
        data = mem.load()
        result.append({
            "agent_name": agent_name,
            "insight_count": len(data.get("insights", [])),
            "recent": mem.get_recent(5),
            "patterns": {k: len(v) for k, v in data.get("patterns", {}).items()},
        })
    return result
