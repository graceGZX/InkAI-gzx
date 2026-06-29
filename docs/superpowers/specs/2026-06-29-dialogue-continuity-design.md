# 对话连续性改造设计文档

**日期**：2026-06-29  
**涉及功能**：AI优化对话 / AI连续对话建立规则  
**目标**：修复内容跳跃问题，实现"先呼应 + 针对性选项 + 自由输入"的连续对话体验

---

## 一、问题诊断

### Bug 1 — optimize 对话消息顺序错误（`app.js`）

`startRequirementDialogue` 收到第一轮 AI 回复后，只将 AI 消息存入 `state.messages`，未存入初始用户消息。导致第二轮起发给 LLM 的消息历史以 `assistant` 开头，违反标准对话格式，LLM 无法正确追踪上下文。

**修复位置**：`frontend/app.js` → `startRequirementDialogue` 函数（约第 3893 行）  
**修复方式**：在 push AI 回复前，先 push `{ role: 'user', content: '我想优化这一章' }`

### Bug 2 — 规则对话每轮丢失已有规则上下文（`app.js`）

`selectRulesOption` 每次调用时传 `existing_rules: []`，AI 不知道已建立哪些规则，容易重复建立或答非所问。

**修复位置**：`frontend/app.js` → `selectRulesOption` 函数（约第 7761 行）  
**修复方式**：从 `window._rulesDialogue.existingRules`（新增字段）读取当前规则列表，每轮带上

### Bug 3 — Prompt 缺少对上一句话的显式呼应约束（`app.py`）

两个对话的 system prompt 只告知"第 N 轮"，未注入用户上一条消息，LLM 生成的选项容易是通用选项而非针对刚才内容派生。

---

## 二、改造方案（方案 B）

### 2.1 后端 Prompt 改造（`app.py`）

**涉及路由**：
- `POST /api/novels/<novel_id>/chapters/<int:chapter_number>/improve/dialogue`（第 1506 行）
- `POST /api/novels/<novel_id>/rules/dialogue`（第 2281 行）

**改动**：将 `stage_hint` 从"这是第 N 轮"改为注入用户最后一条消息摘要：

```python
last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
stage_hint = f"用户刚才说：「{last_user[:100]}」。先用一句话呼应这句话，再追问一个具体细节。"
```

并在两个 system prompt 末尾增加强制格式约束：

```
每轮回复格式（必须遵守）：
1. 开头一句话呼应用户刚说的内容，要引用他的具体词语
2. 给出 3-4 个基于用户刚才回答派生的具体选项，选项必须包含章节/规则中的具体内容，不能是通用选项
```

### 2.2 前端消息格式修复（`app.js`）

**optimize 对话**（`startRequirementDialogue`，约第 3920 行）：

```javascript
// 收到第一轮 AI 回复后，先存初始用户消息再存 AI 消息
state.messages.push({ role: 'user', content: '我想优化这一章' });
state.messages.push({ role: 'assistant', content: data.question, options: data.options || [], stage: data.stage });
```

**规则对话**（`startRulesDialogue`，约第 7673 行）：新增 `existingRules` 字段存入 `_rulesDialogue`；`selectRulesOption` 每次从中读取后传给后端。

### 2.3 前端 UI 改造（`app.js`）

**加载状态改造**（两个对话共用）：

- **当前**：`container.innerHTML = '<div>spinner...</div>'`（替换整个容器，历史消失）
- **改后**：在容器底部 append 一个 `.dialogue-typing-bubble`，回复到达后用实际内容替换这个气泡

**UI 布局（两个对话统一）**：

```
┌─────────────────────────────────────┐  ← 滚动区域（消息历史）
│  [AI 气泡] 你提到节奏，第二段……     │
│  [选项气泡] [删减铺垫] [加快对白]   │  ← 仅最后一条 AI 消息下方显示
│  [用户气泡] 加快对白节奏            │
│  [AI 气泡] 明白，那具体是……        │
│  [选项气泡] [...]                   │
├─────────────────────────────────────┤  ← 固定底部输入区
│  ████████████████████  [发送 ↵]    │  ← 始终可见的自由输入框
└─────────────────────────────────────┘
```

**选项气泡行为**：点击后直接作为用户消息发送（不填入输入框），与自由输入框并列，互不干扰。

**自由输入框**：固定在对话底部，Enter 键或点击发送按钮提交，始终可见。

**renderConversation 统一辅助函数**：`renderDialogue`（optimize）和 `renderRulesDialogue`（rules）提取公共气泡渲染逻辑为 `_renderConversationBubbles(messages, container)`，两处复用，减少重复代码。

---

## 三、改动文件清单

| 文件 | 改动范围 | 说明 |
|------|---------|------|
| `app.py` | 第 1529–1556 行（optimize stage_hint + system prompt） | 注入 last_user + 强制格式约束 |
| `app.py` | 第 2308–2336 行（rules stage_hint + system prompt） | 同上 |
| `app.js` | `startRequirementDialogue`（约第 3920 行） | 修复初始用户消息缺失 |
| `app.js` | `startRulesDialogue`（约第 7673 行） | 存入 existingRules |
| `app.js` | `selectRulesOption`（约第 7761 行） | 每轮传入 existingRules |
| `app.js` | `renderDialogue` + `renderRulesDialogue` | 加载态改为 append 气泡；统一输入框布局 |

---

## 四、不在本次范围内

- 流式输出（streaming）
- 对话历史持久化到服务端
- 多轮摘要层（方案 C）
