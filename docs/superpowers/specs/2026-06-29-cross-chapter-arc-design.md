# 跨章故事弧系统设计文档

## 背景与问题

当前续写系统每章倾向于写一个完整的时间+地点+人物+故事单元，缺乏横跨多章的情节弧意识。虽然代码中已有 `scene_continuity`（局部场景连续性），但没有"故事弧"这一层次的持久化状态，AI 每次生成故事线时无法感知自己处于哪个大弧的哪个阶段，因此总会倾向于在当章自然收尾。

## 目标

1. 支持一个情节弧横跨多章（如6章的秘境探索弧、10章的复仇弧）
2. 弧计划由 AI 根据故事走向自动生成，用户可在写章前查看、修改、确认
3. 角色晋级/成长里程碑显式纳入弧计划，写手 agent 据此在对应章节写出里程碑场景
4. 每章结尾类型（悬念截断/留钩/自然停顿/完整收尾）由弧计划决定，不再每章默认收尾

## 整体流程

```
用户点击"写下一章"
        │
        ▼
  [检查 active_arc]（纯代码判断）
        │
  ┌─────┴───────────────┐
  │ 条件满足时触发弧规划    │
  │ 1. active_arc 不存在  │── ArcPlannerAgent 生成弧草案
  │ 2. chapters_remaining │        │
  │    <= 1              │        ▼
  └──────────────────────┘  前端弧确认弹窗
                                   │ 用户可修改弧名/章数/每章定位/角色里程碑
                                   ▼
                             用户确认 → 弧计划写入 active_arc
                                   │
        ┌──────────────────────────┘
        ▼
  generate_storyline（读取弧计划，输出带 arc_context 的故事线）
        │
        ▼
  write_chapter（按 ending_type 写结尾，按 character_milestones 写晋级场景）
        │
        ▼
  save_chapter + 更新 active_arc（chapters_remaining - 1，归零时清空）
```

## 数据结构

### active_arc（持久化到知识库）

```json
{
  "arc_id": "arc_003",
  "arc_name": "苍云宗秘境探索",
  "arc_type": "exploration",
  "start_chapter": 12,
  "planned_chapters": 6,
  "chapters_remaining": 6,
  "chapter_roles": [
    {"offset": 1, "role": "arc_open",   "ending_type": "hook",        "milestone": "发现秘境入口，未知危险隐现"},
    {"offset": 2, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "遭遇守卫，陷入绝境"},
    {"offset": 3, "role": "arc_mid",    "ending_type": "cliffhanger", "milestone": "揭露前人遗迹，世界观秘密"},
    {"offset": 4, "role": "arc_climax", "ending_type": "cliffhanger", "milestone": "主角突破晋级"},
    {"offset": 5, "role": "arc_climax", "ending_type": "pause",       "milestone": "BOSS战决出胜负"},
    {"offset": 6, "role": "arc_close",  "ending_type": "resolution",  "milestone": "带走关键物品，埋下下弧伏笔"}
  ],
  "character_milestones": {
    "main": {"chapter_offset": 4, "type": "level_up", "description": "突破筑基"},
    "supporting": [
      {"name": "师妹林晚", "chapter_offset": 5, "type": "growth", "description": "首次独立击败强敌"}
    ]
  }
}
```

**arc_type 枚举：**
- `growth`：角色成长弧，以主角内心变化和能力提升为主线
- `conflict`：冲突对抗弧，以外部敌对势力或内部矛盾为主线
- `exploration`：探索发现弧，以探索新地域/揭露世界观秘密为主线
- `revelation`：真相揭露弧，以揭开隐藏秘密/反转为主线

**arc_role 枚举：**
- `arc_open`：弧的开篇，建立场景和初始冲突
- `arc_mid`：弧的中段，深化冲突和矛盾
- `arc_climax`：弧的高潮，决定性事件或对抗
- `arc_close`：弧的收尾，解决或转折，为下一弧埋下伏笔

**ending_type 枚举：**
- `cliffhanger`：悬念截断，紧迫感强，读者无法停下
- `hook`：留下钩子，让读者好奇下一章将发生什么
- `pause`：自然停顿，当前冲突暂时平息，气氛舒缓
- `resolution`：当前弧段完整收尾，适合弧的最后一章

### storyline 新增字段（追加到现有 JSON，不删除现有字段）

```json
{
  "arc_context": {
    "arc_id": "arc_003",
    "arc_name": "苍云宗秘境探索",
    "arc_type": "exploration",
    "arc_chapter_index": 3,
    "arc_total_chapters": 6,
    "arc_role": "arc_mid",
    "chapters_remaining": 4
  },
  "character_milestones": {
    "main": {"has_milestone": false, "type": null, "description": null},
    "supporting": []
  },
  "ending_type": "cliffhanger"
}
```

## 各模块改动

### 新增：`agents/continuation_arc_planner.py`（约150行）

- 继承 `BaseAgent`
- 输入：`knowledge_base`（角色状态、已有伏笔、上一弧结局、书的整体走向、当前章号）
- 输出：完整 `active_arc` JSON
- prompt 要求 AI：
  - 根据当前故事走向选择最合适的弧类型
  - 决定合理的弧章数（3-10章，视故事需要）
  - 为每章分配 role 和 ending_type
  - 在合适章节安排角色成长/晋级里程碑
  - 确保弧末尾为下一弧埋下伏笔

### 修改：`inkai_workflow_optimized.py`

在 `generate_continuation_storyline` 前插入：

```python
def _check_arc_trigger(self, novel_id) -> bool:
    arc = self.data_manager.load_active_arc(novel_id)
    if arc is None:
        return True
    if arc.get("chapters_remaining", 0) <= 1:
        return True
    return False
```

写章完成后调用：
```python
self.data_manager.update_arc_progress(novel_id)
```

弧触发时，写章 API 提前返回 `{"arc_pending": true, "arc_draft": {...}}`，不继续写章。前端弹出确认弹窗，用户确认后调用 `/arc/confirm` 保存弧计划，然后前端重新触发"写下一章"，此时 `active_arc` 已存在，正常进入写章流程。

### 修改：`agents/continuation_storyline_generator.py`

- 在 `_generate_next_chapter_storyline` 中读取 `knowledge_base.get("active_arc")`
- 在 prompt 中注入弧上下文：当前弧名、弧类型、本章 arc_role、本章 ending_type、本章角色里程碑
- 在返回 JSON 的 schema 中新增 `arc_context`、`character_milestones`、`ending_type` 三个字段
- 在 `_validate_storyline_result` 中补充新字段的默认值

### 修改：`agents/continuation_chapter_writer.py`

在写作 prompt 中追加：

```
章节弧定位：{arc_role}（{arc_name} 的第{arc_chapter_index}/{arc_total_chapters}章）
结尾要求：{ending_type_instruction}  ← 根据 ending_type 生成对应指令
角色里程碑：{milestone_instruction}  ← 若本章有里程碑则明确要求写出
```

`ending_type` 对应的写作指令：
- `cliffhanger`："章末必须在最紧张时刻截断，绝对不能解决当前冲突，让读者强烈渴望翻到下一章"
- `hook`："章末留下一个明确的问题或反常细节，引发读者好奇，不需要紧张氛围"
- `pause`："章末冲突暂时平息，节奏放缓，可以有内心独白或环境描写"
- `resolution`："章末完整解决本弧的核心冲突，情绪释放，但需埋下新的伏笔"

### 修改：`data_manager.py`

新增三个方法：
- `save_active_arc(novel_id, arc: dict)` — 写入 `novels/{id}/active_arc.json`
- `load_active_arc(novel_id) → dict | None` — 读取，不存在时返回 None
- `update_arc_progress(novel_id)` — `chapters_remaining - 1`，归零时删除文件（触发下次规划）

### 新增 API：`app.py`

```
POST /api/novels/<id>/arc/plan
  请求：无 body（由 novel_id 定位当前上下文）
  响应：{"success": true, "data": { active_arc 草案 }}

POST /api/novels/<id>/arc/confirm
  请求：{"arc": { 用户修改后的 active_arc }}
  响应：{"success": true}
```

### 新增前端弧确认弹窗：`frontend/app.js`

触发时机：写章 API 返回 `{"arc_pending": true, "arc_draft": {...}}` 时弹出。

弹窗内容：
- 展示弧名、类型、计划章数
- 逐章展示 milestone / ending_type，支持行内编辑
- 展示角色晋级计划，支持修改章节偏移和描述
- 「确认」按钮：调用 `/arc/confirm`，然后继续写章
- 「重新生成」按钮：重新调用 `/arc/plan`
- 「跳过，不使用弧」按钮：写入一个单章弧占位，跳过弧规划

## 不改动的模块

- 所有评审/一致性 agent（continuity、quality_assessor 等）
- 向量检索和语义知识库
- 现有 `scene_continuity` 跨章场景机制（与本设计并存，互补）

## 文件变更清单

| 文件 | 操作 |
|------|------|
| `agents/continuation_arc_planner.py` | 新增 |
| `inkai_workflow_optimized.py` | 修改 |
| `agents/continuation_storyline_generator.py` | 修改 |
| `agents/continuation_chapter_writer.py` | 修改 |
| `data_manager.py` | 修改 |
| `app.py` | 修改（新增2个API） |
| `frontend/app.js` | 修改（新增弧确认弹窗） |
