# 跨章故事弧系统 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为续写系统新增故事弧状态追踪，使 AI 能规划并持续推进跨越多章的情节弧，支持用户在写章前确认/修改弧计划。

**Architecture:** 在写章流程前插入弧状态检查节点，按需触发 ArcPlannerAgent 生成弧草案并通过前端让用户确认；弧计划持久化为 `active_arc.json`；故事线生成器和章节写手均读取弧上下文来决定本章定位和结尾类型。

**Tech Stack:** Python 3.12, Flask, DeepSeek API（通过 BaseAgent），原生 JS + Bootstrap 5（前端）

## Global Constraints

- Python 文件单文件不超过 300 行；现有超大文件（如 `inkai_workflow_optimized.py`）只做最小化修改，不重构
- 所有 agent 继承 `base_agent.BaseAgent`，使用 `self.call_llm()` 和 `self.parse_json_response()`
- 数据持久化统一走 `data_manager.save_novel_data(novel_id, data_type, data)` / `load_novel_data(novel_id, data_type)`，文件路径格式 `novels/{novel_id}/{data_type}.json`
- 不删除现有字段，只追加新字段
- 不修改评审/一致性 agent

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `data_manager.py` | 修改 | 新增 3 个弧持久化方法 |
| `agents/continuation_arc_planner.py` | 新增 | 弧规划 agent（~150 行）|
| `inkai_workflow_optimized.py` | 修改 | 弧触发检查 + 知识库注入 + 写章后更新 |
| `agents/continuation_storyline_generator.py` | 修改 | 读弧上下文，输出新字段 |
| `agents/continuation_chapter_writer.py` | 修改 | 读 ending_type / milestones，调整写作指令 |
| `app.py` | 修改 | 新增 `/arc/plan` 和 `/arc/confirm` 两个 API |
| `frontend/app.js` | 修改 | 弧确认弹窗 |

---

## Task 1：data_manager.py — 弧持久化方法

**Files:**
- Modify: `data_manager.py`（在现有 `load_novel_data` 方法之后，约第 95 行后追加）

**Interfaces:**
- Produces:
  - `save_active_arc(novel_id: str, arc: dict) -> bool`
  - `load_active_arc(novel_id: str) -> dict | None`
  - `update_arc_progress(novel_id: str) -> bool`（chapters_remaining - 1，归零时删除）

- [ ] **Step 1: 在 `data_manager.py` 第 95 行（`load_novel_data` 末尾）后追加三个方法**

```python
    def save_active_arc(self, novel_id: str, arc: Dict[str, Any]) -> bool:
        """保存当前活跃故事弧计划"""
        return self.save_novel_data(novel_id, "active_arc", arc)

    def load_active_arc(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """加载当前活跃故事弧计划，不存在时返回 None"""
        return self.load_novel_data(novel_id, "active_arc")

    def update_arc_progress(self, novel_id: str) -> bool:
        """章节写完后递减 chapters_remaining；归零时删除弧文件"""
        arc = self.load_active_arc(novel_id)
        if not arc:
            return True
        remaining = arc.get("chapters_remaining", 0) - 1
        if remaining <= 0:
            novel_dir = os.path.join(self.novels_dir, novel_id)
            arc_file = os.path.join(novel_dir, "active_arc.json")
            try:
                if os.path.exists(arc_file):
                    os.remove(arc_file)
            except Exception as e:
                print(f"删除弧文件失败: {e}")
            return True
        arc["chapters_remaining"] = remaining
        return self.save_active_arc(novel_id, arc)
```

- [ ] **Step 2: 验证方法可调用**

```bash
cd /Users/zixiao.gu/book/novel/InkAI-gzx
source .venv/bin/activate
python3 -c "
from data_manager import DataManager
dm = DataManager()
# 使用第一个存在的小说 ID 测试
import os
novels = os.listdir('data/novels') if os.path.exists('data/novels') else []
if novels:
    nid = novels[0]
    arc = {'arc_id': 'test_001', 'arc_name': '测试弧', 'planned_chapters': 3, 'chapters_remaining': 3}
    print('save:', dm.save_active_arc(nid, arc))
    print('load:', dm.load_active_arc(nid))
    print('update:', dm.update_arc_progress(nid))
    print('remaining after update:', (dm.load_active_arc(nid) or {}).get('chapters_remaining', 'deleted'))
else:
    print('无小说，跳过测试')
"
```

期望输出：`save: True`、`load: {'arc_id': 'test_001', ...}`、`update: True`、`remaining after update: 2`

- [ ] **Step 3: commit**

```bash
git add data_manager.py
git commit -m "feat: data_manager 新增故事弧持久化方法"
```

---

## Task 2：agents/continuation_arc_planner.py — 弧规划 Agent

**Files:**
- Create: `agents/continuation_arc_planner.py`

**Interfaces:**
- Consumes: `knowledge_base: dict`（含 novel_info, character_profiles, plot_lines, recent_chapters_summaries, dynamic_knowledge, last_chapter_summary, current_chapter_number）
- Produces: `{"success": True, "arc": active_arc_dict}` 或 `{"success": False, "error": str}`

`active_arc` 结构：
```json
{
  "arc_id": "arc_001",
  "arc_name": "弧名称",
  "arc_type": "growth|conflict|exploration|revelation",
  "start_chapter": 5,
  "planned_chapters": 6,
  "chapters_remaining": 6,
  "chapter_roles": [
    {"offset": 1, "role": "arc_open",   "ending_type": "hook",        "milestone": "..."},
    {"offset": 2, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "..."},
    {"offset": 3, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "..."},
    {"offset": 4, "role": "arc_climax", "ending_type": "cliffhanger", "milestone": "..."},
    {"offset": 5, "role": "arc_climax", "ending_type": "pause",       "milestone": "..."},
    {"offset": 6, "role": "arc_close",  "ending_type": "resolution",  "milestone": "..."}
  ],
  "character_milestones": {
    "main": {"chapter_offset": 4, "type": "level_up", "description": "..."},
    "supporting": [
      {"name": "角色名", "chapter_offset": 5, "type": "growth", "description": "..."}
    ]
  }
}
```

- [ ] **Step 1: 创建 `agents/continuation_arc_planner.py`**

```python
"""
续写故事弧规划智能体
根据当前故事状态，规划下一段跨章情节弧
"""

from base_agent import BaseAgent
from typing import Dict, Any
import uuid


class ContinuationArcPlanner(BaseAgent):
    """续写故事弧规划智能体"""

    def __init__(self):
        super().__init__("续写故事弧规划智能体")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        knowledge_base = input_data.get("knowledge_base", {})
        if not knowledge_base:
            return {"success": False, "error": "缺少知识库数据"}
        arc = self._plan_next_arc(knowledge_base)
        if not arc:
            return {"success": False, "error": "弧规划生成失败"}
        return {"success": True, "arc": arc}

    def _plan_next_arc(self, kb: Dict[str, Any]) -> Dict[str, Any]:
        novel_info = kb.get("novel_info", {})
        character_profiles = kb.get("character_profiles", {})
        plot_lines = kb.get("plot_lines", {})
        last_chapter = kb.get("last_chapter_summary", {})
        recent_chapters = kb.get("recent_chapters_summaries", [])
        dynamic_knowledge = kb.get("dynamic_knowledge", {})
        current_chapter_number = kb.get("current_chapter_number", 1)
        tags = kb.get("tags", {})

        main_char = character_profiles.get("main_character", {})
        main_name = main_char.get("basic_info", {}).get("name", "主角")

        supporting = character_profiles.get("supporting_characters", [])
        supporting_names = [c.get("basic_info", {}).get("name", "配角")
                            for c in supporting[:3]]

        recent_summary = "\n".join(
            f"第{c.get('chapter_number')}章：{c.get('summary', '')[:100]}"
            for c in recent_chapters[-3:]
        )

        plot_main = "\n".join(
            f"- {line}" for line in plot_lines.get("main_line", [])
        )

        system_prompt = "你是一名专业的长篇小说结构策划师，擅长为网络小说设计张力十足的多章情节弧。只返回 JSON，不要其他内容。"

        user_prompt = f"""为小说《{novel_info.get('title', '未知')}》规划下一段故事弧，从第 {current_chapter_number} 章开始。

【小说基本信息】
题材标签：{tags}
主角：{main_name}
配角：{', '.join(supporting_names)}

【主线走向】
{plot_main}

【最近剧情】
{recent_summary}

【上一章结尾】
{last_chapter.get('summary', '无')[:200]}

【要求】
- 弧章数范围 3-8 章，根据故事需要自然决定
- 每章分配一个 role（arc_open / arc_mid / arc_climax / arc_close）和 ending_type（cliffhanger / hook / pause / resolution）
- arc_open 用 hook，arc_mid 用 cliffhanger，arc_climax 用 cliffhanger 或 pause，arc_close 用 resolution
- character_milestones 中必须安排至少一个主角里程碑（level_up 或 growth 或 revelation）
- 弧末章（arc_close）必须为下一弧埋下伏笔
- milestone 字段要具体，引用角色名和故事内容，禁止空泛描述

只返回以下 JSON：
{{
  "arc_id": "arc_{current_chapter_number:03d}",
  "arc_name": "弧名称（不超过10字）",
  "arc_type": "growth|conflict|exploration|revelation",
  "start_chapter": {current_chapter_number},
  "planned_chapters": 5,
  "chapters_remaining": 5,
  "chapter_roles": [
    {{"offset": 1, "role": "arc_open",   "ending_type": "hook",        "milestone": "具体里程碑描述"}},
    {{"offset": 2, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "具体里程碑描述"}},
    {{"offset": 3, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "具体里程碑描述"}},
    {{"offset": 4, "role": "arc_climax", "ending_type": "cliffhanger", "milestone": "具体里程碑描述"}},
    {{"offset": 5, "role": "arc_close",  "ending_type": "resolution",  "milestone": "具体里程碑描述"}}
  ],
  "character_milestones": {{
    "main": {{"chapter_offset": 4, "type": "level_up", "description": "具体描述"}},
    "supporting": [
      {{"name": "角色名", "chapter_offset": 3, "type": "growth", "description": "具体描述"}}
    ]
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.call_llm(messages, temperature=0.8, max_tokens=1500)
        result = self.parse_json_response(response)

        if not result or not result.get("arc_name"):
            self.log(f"弧规划解析失败，原始响应: {response[:300]}")
            return None

        # 确保 arc_id 唯一
        if not result.get("arc_id"):
            result["arc_id"] = f"arc_{current_chapter_number:03d}_{uuid.uuid4().hex[:4]}"

        # 确保 chapters_remaining 与 planned_chapters 一致
        result["chapters_remaining"] = len(result.get("chapter_roles", []))
        result["planned_chapters"] = result["chapters_remaining"]

        return result
```

- [ ] **Step 2: 在 `agents/__init__.py` 中注册新 agent**

找到 `agents/__init__.py` 中现有的 import 列表，追加：

```python
from agents.continuation_arc_planner import ContinuationArcPlanner
```

- [ ] **Step 3: 验证 agent 可实例化**

```bash
cd /Users/zixiao.gu/book/novel/InkAI-gzx
source .venv/bin/activate
python3 -c "
from agents.continuation_arc_planner import ContinuationArcPlanner
planner = ContinuationArcPlanner()
print('ContinuationArcPlanner 实例化成功')
"
```

期望输出：`ContinuationArcPlanner 实例化成功`

- [ ] **Step 4: commit**

```bash
git add agents/continuation_arc_planner.py agents/__init__.py
git commit -m "feat: 新增 ContinuationArcPlanner 弧规划 agent"
```

---

## Task 3：app.py — 新增弧 API

**Files:**
- Modify: `app.py`（在 `/continuation/quick/resume` 路由之后追加，约第 1270 行后）

**Interfaces:**
- Consumes: Task 1 的 `data_manager.save_active_arc()` / `load_active_arc()`；Task 2 的 `ContinuationArcPlanner`
- Produces:
  - `POST /api/novels/<novel_id>/arc/plan` → `{"success": true, "data": active_arc_draft}`
  - `POST /api/novels/<novel_id>/arc/confirm` → `{"success": true}`

- [ ] **Step 1: 在 app.py 顶部 import 区追加 ContinuationArcPlanner**

找到 app.py 中现有的 agent import（如 `from agents import ...`），追加：

```python
from agents.continuation_arc_planner import ContinuationArcPlanner
```

- [ ] **Step 2: 在 app.py 尾部（`if __name__ == '__main__':` 之前）追加两个路由**

```python
@app.route('/api/novels/<novel_id>/arc/plan', methods=['POST'])
def arc_plan(novel_id):
    """触发弧规划，返回 AI 生成的弧草案（不保存，等待用户确认）"""
    try:
        ensure_context_loaded(novel_id)
        if not workflow.context or workflow.context.novel_id != novel_id:
            return jsonify({"success": False, "error": "请先开始续写流程"}), 400

        kb = workflow.context.continuation_data.get("knowledge_base", {})
        chapters = workflow.data_manager.get_novel_chapters(novel_id)
        kb["current_chapter_number"] = len(chapters) + 1

        planner = ContinuationArcPlanner()
        result = planner.process({"knowledge_base": kb})

        if not result.get("success"):
            return jsonify({"success": False, "error": result.get("error", "弧规划失败")}), 500

        return jsonify({"success": True, "data": result["arc"]})
    except Exception as e:
        print(f"弧规划错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/arc/confirm', methods=['POST'])
def arc_confirm(novel_id):
    """保存用户确认（或修改）后的弧计划"""
    try:
        data = request.get_json() or {}
        arc = data.get("arc")
        if not arc:
            return jsonify({"success": False, "error": "缺少 arc 字段"}), 400

        success = workflow.data_manager.save_active_arc(novel_id, arc)
        if not success:
            return jsonify({"success": False, "error": "保存弧计划失败"}), 500

        return jsonify({"success": True})
    except Exception as e:
        print(f"弧确认错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

- [ ] **Step 3: 重启服务并验证两个新 API 可访问**

```bash
bash scripts/restart.sh
sleep 3

# 替换 NOVEL_ID 为实际存在的小说 ID
NOVEL_ID=$(python3 -c "
from data_manager import DataManager
dm = DataManager()
import os
novels = os.listdir('data/novels') if os.path.exists('data/novels') else []
print(novels[0] if novels else 'NO_NOVEL')
")

curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:5000/api/novels/${NOVEL_ID}/arc/confirm \
  -H "Content-Type: application/json" \
  -d '{"arc": {"arc_id":"test","arc_name":"测试","planned_chapters":3,"chapters_remaining":3,"chapter_roles":[],"character_milestones":{"main":null,"supporting":[]}}}'
```

期望输出：`200`

- [ ] **Step 4: commit**

```bash
git add app.py
git commit -m "feat: app.py 新增 /arc/plan 和 /arc/confirm 路由"
```

---

## Task 4：inkai_workflow_optimized.py — 弧触发逻辑

**Files:**
- Modify: `inkai_workflow_optimized.py`
  - 在 `generate_continuation_storyline` 方法开头（约第 676 行）插入弧触发检查
  - 在 `save_continuation_chapter` 末尾（约第 1322 行后）追加弧进度更新

**Interfaces:**
- Consumes: Task 1 的 `data_manager.load_active_arc()` / `update_arc_progress()`；Task 2 的 `ContinuationArcPlanner`
- Produces: `generate_continuation_storyline` 可返回 `{"arc_pending": True, "arc_draft": {...}}`；`knowledge_base` 新增 `active_arc` 字段

- [ ] **Step 1: 在 `inkai_workflow_optimized.py` 顶部 import 区追加**

找到现有 agent import 列表，追加：

```python
from agents.continuation_arc_planner import ContinuationArcPlanner
```

- [ ] **Step 2: 在 `InkAIWorkflow` 类中追加私有方法 `_check_arc_trigger`**

在 `generate_continuation_storyline` 定义之前（约第 665 行）插入：

```python
    def _check_arc_trigger(self, novel_id: str) -> bool:
        """检查是否需要触发弧规划：无活跃弧，或当前弧剩余章数 <= 1"""
        arc = self.data_manager.load_active_arc(novel_id)
        if arc is None:
            return True
        return arc.get("chapters_remaining", 0) <= 1
```

- [ ] **Step 3: 在 `generate_continuation_storyline` 方法体的上下文校验之后（约第 678 行，`if not self.context...` 之后）插入弧触发逻辑**

在以下代码段之后：
```python
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
```

插入：
```python
        # 弧触发检查：无活跃弧或弧快结束时，先规划新弧，返回草案让用户确认
        _novel_id = novel_id or (self.context.novel_id if self.context else None)
        if _novel_id and self._check_arc_trigger(_novel_id):
            kb = self.context.continuation_data.get("knowledge_base", {})
            chapters = self.data_manager.get_novel_chapters(_novel_id)
            kb["current_chapter_number"] = len(chapters) + 1
            planner = ContinuationArcPlanner()
            plan_result = planner.process({"knowledge_base": kb})
            if plan_result.get("success"):
                return {
                    "arc_pending": True,
                    "arc_draft": plan_result["arc"],
                    "message": "请先确认故事弧计划，再继续生成故事线"
                }
```

- [ ] **Step 4: 在知识库构建完成后（向量检索注入之后，调用 ContinuationStorylineGenerator 之前，约第 800 行附近），注入 active_arc**

找到 `self.context.continuation_data["knowledge_base"]` 被最终整理好后、调用 `ContinuationStorylineGenerator().process(...)` 之前的位置，插入：

```python
        # 注入活跃弧上下文到知识库
        _nid = novel_id or (self.context.novel_id if self.context else None)
        if _nid:
            _active_arc = self.data_manager.load_active_arc(_nid)
            if _active_arc:
                kb["active_arc"] = _active_arc
                # 计算本章是弧的第几章
                _arc_chapter_idx = (_active_arc["planned_chapters"]
                                    - _active_arc["chapters_remaining"] + 1)
                _roles = _active_arc.get("chapter_roles", [])
                kb["current_arc_role"] = (
                    _roles[_arc_chapter_idx - 1]
                    if 0 < _arc_chapter_idx <= len(_roles)
                    else {}
                )
```

- [ ] **Step 5: 在 `save_continuation_chapter` 保存成功之后（约第 1322 行 `if success:` 块内），追加弧进度更新**

找到 `if success:` 后的第一行，在保存操作之后追加：

```python
            # 更新故事弧进度（chapters_remaining - 1，归零时自动清除）
            _nid_save = novel_id or (self.context.novel_id if self.context else None)
            if _nid_save:
                self.data_manager.update_arc_progress(_nid_save)
```

- [ ] **Step 6: 重启服务并验证弧触发逻辑不破坏现有续写流程**

```bash
bash scripts/restart.sh
sleep 3
tail -20 logs/web.log
```

期望：服务正常启动，无 import 错误

- [ ] **Step 7: commit**

```bash
git add inkai_workflow_optimized.py
git commit -m "feat: workflow 新增弧触发检查、知识库注入、写章后更新进度"
```

---

## Task 5：continuation_storyline_generator.py — 弧上下文注入

**Files:**
- Modify: `agents/continuation_storyline_generator.py`
  - `_generate_next_chapter_storyline`：读取 `active_arc`，注入 prompt
  - prompt JSON schema：追加 `arc_context`、`character_milestones`、`ending_type`
  - `_validate_storyline_result`：为新字段补充默认值

**Interfaces:**
- Consumes: `knowledge_base["active_arc"]`、`knowledge_base["current_arc_role"]`（Task 4 注入）
- Produces: storyline dict 新增 `arc_context: dict`、`character_milestones: dict`、`ending_type: str`

- [ ] **Step 1: 在 `_generate_next_chapter_storyline` 方法中，获取 `last_chapter` 等变量之后，追加弧上下文读取**

找到第 44-49 行（`last_chapter = ...` 等变量赋值之后），追加：

```python
            active_arc = knowledge_base.get("active_arc")
            current_arc_role = knowledge_base.get("current_arc_role", {})
```

- [ ] **Step 2: 在 prompt 的"请生成第N章的详细故事线，要求："列表之前（约第 89 行），追加弧上下文段落**

在 `请生成第{next_chapter_number}章的详细故事线，要求：` 之前插入：

```python
            arc_context_section = ""
            if active_arc and current_arc_role:
                arc_idx = active_arc["planned_chapters"] - active_arc["chapters_remaining"] + 1
                arc_context_section = f"""
            ## 当前故事弧（重要，必须严格遵守）

            弧名称：{active_arc.get("arc_name", "")}（{active_arc.get("arc_type", "")}）
            本章是该弧的第 {arc_idx}/{active_arc.get("planned_chapters", 1)} 章
            本章定位：{current_arc_role.get("role", "arc_mid")}
            本章里程碑：{current_arc_role.get("milestone", "")}
            本章结尾类型：{current_arc_role.get("ending_type", "hook")}（必须严格执行）

            结尾类型说明：
            - cliffhanger：在最紧张时刻截断，绝对不解决冲突，让读者强烈渴望翻下一章
            - hook：留下一个让读者好奇的问题或反常细节
            - pause：冲突暂时平息，气氛舒缓，有内心独白或环境描写
            - resolution：完整解决本弧核心冲突，情绪释放，但需埋下新伏笔

            角色里程碑计划（仅在对应章写出）：
            主角：第{active_arc.get("character_milestones", {}).get("main", {}).get("chapter_offset", 0)}章 — {active_arc.get("character_milestones", {}).get("main", {}).get("description", "无")}
            配角：{", ".join(f"{s.get('name')}第{s.get('chapter_offset')}章-{s.get('description','')}" for s in active_arc.get("character_milestones", {}).get("supporting", []))}
            """
```

然后在 prompt f-string 中相应位置插入 `{arc_context_section}`。

- [ ] **Step 3: 在 prompt 的 JSON schema（`请返回JSON格式：` 部分）中追加三个新字段**

在现有 `"writing_notes": "写作注意事项"` 之后、`}}` 之前追加：

```
                "arc_context": {{
                    "arc_id": "",
                    "arc_name": "",
                    "arc_type": "",
                    "arc_chapter_index": 1,
                    "arc_total_chapters": 1,
                    "arc_role": "arc_open",
                    "chapters_remaining": 1
                }},
                "character_milestones": {{
                    "main": {{"has_milestone": false, "type": null, "description": null}},
                    "supporting": []
                }},
                "ending_type": "hook"
```

- [ ] **Step 4: 在 `_validate_storyline_result` 的 `required_fields` 字典中追加新字段默认值**

在现有 `"writing_notes": "待补充"` 之后追加：

```python
                "arc_context": {},
                "character_milestones": {
                    "main": {"has_milestone": False, "type": None, "description": None},
                    "supporting": []
                },
                "ending_type": "hook",
```

- [ ] **Step 5: 重启服务并用 curl 触发一次故事线生成（需已有小说且有确认的弧），验证返回的 JSON 包含 `arc_context` 字段**

```bash
bash scripts/restart.sh
sleep 3
# 仅检查服务启动正常，无需完整 e2e 测试（在 Task 7 前端完成后集成测试）
tail -5 logs/web.log
```

- [ ] **Step 6: commit**

```bash
git add agents/continuation_storyline_generator.py
git commit -m "feat: storyline generator 注入弧上下文，输出 arc_context/ending_type/character_milestones"
```

---

## Task 6：continuation_chapter_writer.py — 弧感知写作指令

**Files:**
- Modify: `agents/continuation_chapter_writer.py`（约第 84-109 行，写作要求列表处）

**Interfaces:**
- Consumes: `storyline["arc_context"]`、`storyline["ending_type"]`、`storyline["character_milestones"]`（Task 5 产出）
- Produces: 无新字段，修改写作 prompt 使结尾和里程碑写法符合弧计划

- [ ] **Step 1: 找到 `continuation_chapter_writer.py` 中读取 storyline 的位置（约第 30-52 行）**

在现有变量读取（`storyline.get(...)`）之后追加：

```python
            arc_context = storyline.get("arc_context", {})
            ending_type = storyline.get("ending_type", "")
            character_milestones = storyline.get("character_milestones", {})
```

- [ ] **Step 2: 构建弧感知写作指令文本（在 prompt 变量构建处追加）**

在 prompt f-string 构建之前，追加：

```python
            # 弧感知写作指令
            arc_writing_instruction = ""
            if arc_context.get("arc_name"):
                arc_role = arc_context.get("arc_role", "")
                arc_idx = arc_context.get("arc_chapter_index", 1)
                arc_total = arc_context.get("arc_total_chapters", 1)
                arc_writing_instruction = f"""
            ## 故事弧定位（必须遵守）

            当前弧：《{arc_context.get("arc_name", "")}》第 {arc_idx}/{arc_total} 章（{arc_role}）

            """

            ending_instruction = ""
            ending_type_map = {
                "cliffhanger": "【章末要求 - cliffhanger】必须在最紧张、最危险的时刻截断。不能解决当前冲突或危机。最后一段必须停在读者最想知道"然后呢"的瞬间，让读者强烈渴望翻到下一章。",
                "hook":        "【章末要求 - hook】章末留下一个明确的疑问、反常细节或意外出现的人/事，引发读者强烈好奇，不需要紧张氛围，但必须留下悬念。",
                "pause":       "【章末要求 - pause】章末让当前冲突暂时平息，节奏放缓。可用内心独白、环境描写或轻松对话收尾，给读者喘息空间。",
                "resolution":  "【章末要求 - resolution】章末完整解决本弧的核心冲突，给读者情绪释放感。但在最后几句中，必须埋下一个新的伏笔或问题，为下一弧做铺垫。",
            }
            if ending_type in ending_type_map:
                ending_instruction = ending_type_map[ending_type]

            milestone_instruction = ""
            main_milestone = character_milestones.get("main", {})
            if main_milestone and main_milestone.get("has_milestone"):
                milestone_instruction = f"【角色里程碑 - 必须在本章写出】主角本章将经历：{main_milestone.get('description', '')}（类型：{main_milestone.get('type', '')}），请将此里程碑作为本章核心事件之一，用充分的笔墨展现过程与情绪。"
```

- [ ] **Step 3: 在 prompt f-string 的写作要求列表末尾追加弧感知指令**

在现有写作要求（第 84-108 行）的最后一条 `9. 用你最大的输出能力进行输出` 之后追加：

```
            {arc_writing_instruction}
            {ending_instruction}
            {milestone_instruction}
```

- [ ] **Step 4: 重启服务，验证无语法错误**

```bash
bash scripts/restart.sh
sleep 3
tail -5 logs/web.log
```

- [ ] **Step 5: commit**

```bash
git add agents/continuation_chapter_writer.py
git commit -m "feat: chapter writer 新增弧感知写作指令（ending_type / milestone）"
```

---

## Task 7：frontend/app.js — 弧确认弹窗

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/index.html`（新增弧确认 Modal HTML）

**Interfaces:**
- Consumes: `POST /arc/plan`、`POST /arc/confirm`（Task 3 产出）
- Produces: 当写章 API 返回 `arc_pending: true` 时弹出确认弹窗；用户确认后自动重试写章

**弧确认弹窗触发逻辑：** 续写故事线 API（`/continuation/storyline`）返回 `arc_pending: true` 时弹出。用户确认 → 调用 `/arc/confirm` → 重新调用 `/continuation/storyline`。

- [ ] **Step 1: 在 `frontend/index.html` 中找到其他 Modal 的位置，追加弧确认 Modal**

在 `</body>` 之前追加：

```html
<!-- 故事弧确认 Modal -->
<div class="modal fade" id="arcConfirmModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title"><i class="fas fa-route me-2"></i>故事弧规划 — 请确认或修改</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="arc-modal-body">
        <!-- 由 JS 动态填充 -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" id="arc-btn-regen">
          <i class="fas fa-sync-alt me-1"></i>重新生成
        </button>
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal" id="arc-btn-skip">
          跳过，不使用弧
        </button>
        <button type="button" class="btn btn-primary" id="arc-btn-confirm">
          <i class="fas fa-check me-1"></i>确认弧计划，继续写章
        </button>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 2: 在 `frontend/app.js` 末尾追加弧确认相关函数**

```javascript
// ─── 故事弧确认弹窗 ────────────────────────────────────────────
var _arcDraft = null;          // 当前弧草案
var _arcNovelId = null;        // 当前操作的 novelId
var _arcConfirmCallback = null; // 确认后的回调（重试写章）

// 渲染弧草案到 Modal
function _renderArcModal(arc) {
    var roles = arc.chapter_roles || [];
    var milestones = arc.character_milestones || {};
    var mainM = milestones.main || {};
    var supportingM = milestones.supporting || [];

    var rolesHtml = roles.map(function(r, i) {
        var roleLabel = {arc_open:'开篇', arc_mid:'中段', arc_climax:'高潮', arc_close:'收尾'}[r.role] || r.role;
        var endingLabel = {cliffhanger:'悬念截断', hook:'留钩', pause:'自然停顿', resolution:'完整收尾'}[r.ending_type] || r.ending_type;
        return '<tr>' +
            '<td class="text-center">' + (i + 1) + '</td>' +
            '<td><span class="badge bg-secondary">' + roleLabel + '</span></td>' +
            '<td><span class="badge bg-info text-dark">' + endingLabel + '</span></td>' +
            '<td><input class="form-control form-control-sm arc-milestone-input" data-idx="' + i + '" value="' + Utils.escapeHtml(r.milestone || '') + '"></td>' +
            '</tr>';
    }).join('');

    var mainMilestoneHtml = mainM.chapter_offset
        ? '<div class="alert alert-success py-1 px-2 small mb-1">主角第 ' + mainM.chapter_offset + ' 章：' + Utils.escapeHtml(mainM.description || '') + '（' + (mainM.type || '') + '）</div>'
        : '<div class="text-muted small">无主角里程碑</div>';

    var supportingHtml = supportingM.map(function(s) {
        return '<div class="alert alert-light py-1 px-2 small mb-1">' + Utils.escapeHtml(s.name || '') + ' 第 ' + s.chapter_offset + ' 章：' + Utils.escapeHtml(s.description || '') + '</div>';
    }).join('') || '<div class="text-muted small">无配角里程碑</div>';

    var arcTypeMap = {growth:'成长弧', conflict:'冲突弧', exploration:'探索弧', revelation:'揭露弧'};

    document.getElementById('arc-modal-body').innerHTML =
        '<div class="row mb-3">' +
        '  <div class="col-md-6"><label class="form-label fw-bold">弧名称</label>' +
        '    <input class="form-control" id="arc-edit-name" value="' + Utils.escapeHtml(arc.arc_name || '') + '"></div>' +
        '  <div class="col-md-3"><label class="form-label fw-bold">类型</label>' +
        '    <select class="form-select" id="arc-edit-type">' +
        ['growth','conflict','exploration','revelation'].map(function(t) {
            return '<option value="' + t + '"' + (arc.arc_type === t ? ' selected' : '') + '>' + (arcTypeMap[t] || t) + '</option>';
        }).join('') +
        '  </select></div>' +
        '  <div class="col-md-3"><label class="form-label fw-bold">计划章数</label>' +
        '    <input class="form-control" id="arc-edit-chapters" type="number" min="2" max="10" value="' + (arc.planned_chapters || roles.length) + '"></div>' +
        '</div>' +
        '<h6 class="fw-bold mb-2">每章规划（可编辑里程碑）</h6>' +
        '<table class="table table-sm table-bordered mb-3"><thead><tr>' +
        '<th style="width:50px">章</th><th style="width:80px">定位</th><th style="width:90px">结尾</th><th>里程碑</th>' +
        '</tr></thead><tbody>' + rolesHtml + '</tbody></table>' +
        '<h6 class="fw-bold mb-2">角色里程碑</h6>' +
        mainMilestoneHtml + supportingHtml;
}

// 从 Modal 收集用户编辑结果
function _collectArcFromModal(draft) {
    var arc = JSON.parse(JSON.stringify(draft)); // 深拷贝
    arc.arc_name = document.getElementById('arc-edit-name').value.trim() || arc.arc_name;
    arc.arc_type = document.getElementById('arc-edit-type').value || arc.arc_type;
    var chapInput = parseInt(document.getElementById('arc-edit-chapters').value) || arc.planned_chapters;
    arc.planned_chapters = chapInput;
    arc.chapters_remaining = chapInput;

    // 收集里程碑编辑
    document.querySelectorAll('.arc-milestone-input').forEach(function(el) {
        var idx = parseInt(el.getAttribute('data-idx'));
        if (arc.chapter_roles[idx]) {
            arc.chapter_roles[idx].milestone = el.value.trim();
        }
    });
    return arc;
}

// 当 storyline API 返回 arc_pending 时调用
window.showArcConfirmModal = function(novelId, arcDraft, retryCallback) {
    _arcDraft = arcDraft;
    _arcNovelId = novelId;
    _arcConfirmCallback = retryCallback;
    _renderArcModal(arcDraft);
    new bootstrap.Modal(document.getElementById('arcConfirmModal')).show();
};

// 确认按钮
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('arc-btn-confirm').addEventListener('click', async function() {
        var arc = _collectArcFromModal(_arcDraft);
        try {
            var resp = await Utils.apiRequest('/novels/' + _arcNovelId + '/arc/confirm', {
                method: 'POST',
                body: JSON.stringify({ arc: arc })
            });
            if (!resp.success) throw new Error(resp.error || '保存弧计划失败');
            bootstrap.Modal.getInstance(document.getElementById('arcConfirmModal')).hide();
            if (_arcConfirmCallback) _arcConfirmCallback();
        } catch (e) {
            alert('保存弧计划失败：' + e.message);
        }
    });

    document.getElementById('arc-btn-regen').addEventListener('click', async function() {
        if (!_arcNovelId) return;
        try {
            var resp = await Utils.apiRequest('/novels/' + _arcNovelId + '/arc/plan', { method: 'POST' });
            if (!resp.success) throw new Error(resp.error || '重新生成失败');
            _arcDraft = resp.data;
            _renderArcModal(_arcDraft);
        } catch (e) {
            alert('重新生成失败：' + e.message);
        }
    });

    document.getElementById('arc-btn-skip').addEventListener('click', async function() {
        // 跳过弧：写入一个单章占位弧，让 chapters_remaining = 0 不阻碍写章
        if (!_arcNovelId) return;
        var skipArc = {
            arc_id: 'skip_' + Date.now(),
            arc_name: '单章',
            arc_type: 'standalone',
            start_chapter: 0,
            planned_chapters: 0,
            chapters_remaining: 0,
            chapter_roles: [],
            character_milestones: { main: null, supporting: [] }
        };
        await Utils.apiRequest('/novels/' + _arcNovelId + '/arc/confirm', {
            method: 'POST',
            body: JSON.stringify({ arc: skipArc })
        });
        bootstrap.Modal.getInstance(document.getElementById('arcConfirmModal')).hide();
        if (_arcConfirmCallback) _arcConfirmCallback();
    });
});
```

- [ ] **Step 3: 找到续写故事线 API 调用的前端代码，加入 `arc_pending` 检测**

在 `app.js` 中搜索 `/continuation/storyline` 被调用的位置（约在 `generateContinuationStoryline` 或类似函数中），在处理响应的 `.then()` 或 `if (resp.success)` 处追加：

```javascript
// 在处理 resp 之前，检查 arc_pending
if (resp.arc_pending && resp.arc_draft) {
    window.showArcConfirmModal(novelId, resp.arc_draft, function() {
        // 用户确认后自动重试故事线生成
        generateContinuationStoryline(novelId); // 替换为实际的函数名
    });
    return;
}
```

> **注意**：需要根据 `app.js` 中实际的函数名替换 `generateContinuationStoryline(novelId)`。搜索 `/continuation/storyline` 找到调用位置，确认回调函数名。

- [ ] **Step 4: 重启服务，在浏览器打开 http://localhost:5000，选择一本有续写状态的小说，触发故事线生成**

验证：
- 若 `active_arc.json` 不存在，应弹出弧确认弹窗
- 弹窗显示 AI 规划的弧名、章数、每章里程碑
- 确认后自动继续生成故事线

```bash
bash scripts/restart.sh
sleep 3
open http://localhost:5000
```

- [ ] **Step 5: commit**

```bash
git add frontend/index.html frontend/app.js
git commit -m "feat: 前端新增故事弧确认弹窗，支持查看/编辑/确认/重生成"
```

---

## 自检：Spec 覆盖度

| Spec 要求 | 对应 Task |
|-----------|-----------|
| active_arc 持久化 | Task 1 |
| ArcPlannerAgent 生成弧计划 | Task 2 |
| 弧触发检查（无弧/弧快结束） | Task 4 |
| storyline 注入弧上下文 | Task 5 |
| chapter writer 按 ending_type 写结尾 | Task 6 |
| chapter writer 按 milestone 写晋级场景 | Task 6 |
| 写章后更新 chapters_remaining | Task 4 |
| `/arc/plan` 和 `/arc/confirm` API | Task 3 |
| 前端弧确认弹窗 | Task 7 |
| 支持编辑弧名/章数/里程碑 | Task 7 |
| 支持重新生成 | Task 7 |
| 支持跳过不用弧 | Task 7 |
