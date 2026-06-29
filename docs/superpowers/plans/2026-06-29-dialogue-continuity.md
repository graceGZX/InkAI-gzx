# 对话连续性改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 AI 优化对话和规则对话的内容跳跃问题，实现"先呼应用户上一句 + 针对性选项 + 自由输入始终可见"的连续对话体验。

**Architecture:** 后端修复 system prompt（注入 last_user、强制回复格式）；前端修复消息历史顺序、existing_rules 丢失、加载态替换整个容器三个 bug；优化对话把输入框从可重建的消息区分离出来单独固定在底部。

**Tech Stack:** Python/Flask（app.py）、Vanilla JS（frontend/app.js）、HTML（frontend/index.html）

## Global Constraints

- 不引入新的依赖库
- 不修改任何 API 响应结构（`question/options/stage/rule_update/confirmed_requirements/suggested_scope` 字段保持不变）
- 不改动 `novel_rules.py`、`data_manager.py` 等后端模块
- 改动仅限：`app.py`、`frontend/app.js`、`frontend/index.html`
- 服务已在后台运行（pid 文件在 `logs/web.pid`），改完用 `bash scripts/restart.sh` 重启

---

### Task 1：后端 Prompt 改造（app.py）

修复两个对话路由的 system prompt：注入用户上一句话、强制"先呼应再追问"格式。

**Files:**
- Modify: `app.py:1529-1556`（improve_dialogue 路由的 stage_hint + system_prompt）
- Modify: `app.py:2308-2336`（rules_dialogue 路由的 stage_hint + system_prompt）

**Interfaces:**
- Produces: 两个路由的后端行为改变，前端不感知（API 结构不变）

- [ ] **Step 1：修改 improve_dialogue 的 stage_hint**

找到 `app.py` 第 1529 行的 `stage_hint` 赋值块，替换为：

```python
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if user_turns == 0:
            stage_hint = "这是第 1 轮。用户还没说具体需求，请问他「想优化这章的哪个方面」，给 4-5 个具体选项。"
        else:
            stage_hint = (
                f"用户刚才说：「{last_user[:100]}」。"
                f"这是第 {user_turns + 1} 轮。先用一句话直接呼应他刚才说的（引用他的具体词），"
                "再追问一个更深的细节。如果已能回答「改什么/怎么改/改多少」三个问题，给出确认总结（confirming）；否则继续追问。"
            )
```

- [ ] **Step 2：在 improve_dialogue 的 system_prompt 末尾追加格式约束**

找到 `system_prompt` 字符串（第 1536 行）末尾、`"""` 之前，追加：

```
每轮回复格式（严格遵守）：
1. question 开头必须是一句呼应用户刚才内容的话，要引用他说的具体词
2. options 的每个选项必须基于用户刚才回答，包含章节中的具体内容，不能是"优化文笔"这类通用选项
```

- [ ] **Step 3：修改 rules_dialogue 的 stage_hint**

找到 `app.py` 第 2308 行的 `stage_hint` 赋值块，替换为：

```python
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if user_turns == 0:
            stage_hint = "这是第 1 轮。用户刚开始，先问他最想解决什么写作问题，给 4-5 个具体选项引导他开口。"
        else:
            stage_hint = (
                f"用户刚才说：「{last_user[:100]}」。"
                f"这是第 {user_turns + 1} 轮。先用一句话承接这句话（引用他的词），再追问一个更具体的细节或请他举例。"
                "聊清楚 2-3 个具体点后再给出确认总结（confirming），不要着急。"
            )
```

- [ ] **Step 4：在 rules_dialogue 的 system_prompt 末尾追加格式约束**

找到 `system_prompt` 字符串（第 2313 行）末尾、`"""` 之前，追加：

```
每轮回复格式（严格遵守）：
1. question 开头必须是一句承接用户刚才内容的话，要引用他说的具体词
2. options 的每个选项必须是从用户刚才回答延伸出的具体建议，不能是泛泛的分类标签
```

- [ ] **Step 5：重启服务器验证后端不报错**

```bash
bash scripts/restart.sh
sleep 3 && tail -5 logs/web.log
```

预期最后输出包含 `Running on http://127.0.0.1:5000`，无 Python 语法报错。

- [ ] **Step 6：Commit**

```bash
git add app.py
git commit -m "fix: 对话 prompt 注入 last_user，强制先呼应再追问格式"
```

---

### Task 2：修复 optimize 对话（app.js + 布局分离）

**问题**：① 消息历史以 `assistant` 开头（缺初始用户消息）；② `selectDialogueOption` 替换整个 `#dialogue-container`（含输入框），历史消息闪失；③ 自由输入框藏在 `renderDialogue` 重建的 HTML 里。

**修复思路**：把 `#dialogue-container` 拆成可重建的 `#dialogue-messages` + 静态固定的 `#dialogue-input-area`；`renderDialogue` 只写入 `#dialogue-messages`；`selectDialogueOption` append 等待气泡代替整体替换。

**Files:**
- Modify: `frontend/app.js:3964-3965`（startRequirementDialogue，补初始用户消息）
- Modify: `frontend/app.js:3645-3686`（aiOptimizeChapter 生成的 modal HTML，拆分布局）
- Modify: `frontend/app.js:4041-4118`（renderDialogue，只写 #dialogue-messages，移除内嵌输入 HTML）
- Modify: `frontend/app.js:4130-4160`（selectDialogueOption，改为 append 等待气泡）

**Interfaces:**
- `renderDialogue(data, novelId, chapterNumber)` 签名不变，但写入目标改为 `#dialogue-messages`
- `submitDialogueCustom` 读取 `#dialogue-custom-input`，位置从动态变静态，ID 不变

- [ ] **Step 1：startRequirementDialogue 补初始用户消息**

找到 `frontend/app.js` 第 3964 行：
```javascript
        state.messages.push({ role: 'assistant', content: data.question, options: data.options || [] });
```
改为：
```javascript
        state.messages.push({ role: 'user', content: '我想优化这一章' });
        state.messages.push({ role: 'assistant', content: data.question, options: data.options || [], stage: data.stage });
```

- [ ] **Step 2：修改 modal HTML，拆分消息区和输入区**

在 `frontend/app.js` 中找到 `aiOptimizeChapter` 函数生成的 modal HTML（第 3679 行左右），找到这段：
```javascript
                                    <div id="dialogue-container" class="dialogue-container mb-2" style="display:none;">
                                        <!-- 对话消息动态插入 -->
                                    </div>
```
替换为：
```javascript
                                    <div id="dialogue-container" class="dialogue-container mb-2" style="display:none;">
                                        <div id="dialogue-messages" style="max-height:320px;overflow-y:auto;padding-bottom:4px;"></div>
                                        <div id="dialogue-input-area" class="mt-2">
                                            <div class="input-group input-group-sm">
                                                <input type="text" class="form-control" id="dialogue-custom-input" placeholder="直接输入你的想法...">
                                                <button class="btn btn-outline-secondary" onclick="submitDialogueCustom()"><i class="fas fa-paper-plane"></i></button>
                                            </div>
                                        </div>
                                    </div>
```

- [ ] **Step 3：重写 renderDialogue，只写入 #dialogue-messages，移除内嵌输入 HTML**

将 `frontend/app.js` 第 4041 行的整个 `renderDialogue` 函数替换为：

```javascript
var renderDialogue = function(data, novelId, chapterNumber) {
    var messagesEl = document.getElementById('dialogue-messages');
    if (!messagesEl) return;
    var state = _getDialogueState(novelId, chapterNumber);
    var stage = data.stage || 'clarifying';
    var html = '';

    state.messages.forEach(function(msg, idx) {
        var isLastAssistant = msg.role === 'assistant' && idx === state.messages.length - 1;
        if (msg.role === 'assistant') {
            html += '<div class="dialogue-msg dialogue-ai"><div class="dialogue-bubble ai-bubble">' + Utils.escapeHtml(msg.content) + '</div>';
            if (isLastAssistant && stage !== 'done') {
                var opts = data.options || msg.options || [];
                if (opts.length > 0) {
                    html += '<div class="chat-quick-replies">';
                    opts.forEach(function(opt, optIdx) {
                        if (stage === 'confirming') {
                            var cls = optIdx === 0 ? 'chat-reply-btn confirm' : 'chat-reply-btn secondary';
                            html += '<span class="' + cls + '" onclick="confirmDialogueOption(' + optIdx + ')">' + Utils.escapeHtml(opt) + '</span>';
                        } else {
                            html += '<span class="chat-reply-btn" onclick="selectDialogueOption(\'' + opt.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + '\')">' + Utils.escapeHtml(opt) + '</span>';
                        }
                    });
                    html += '</div>';
                }
            }
            html += '</div>';
        } else {
            html += '<div class="dialogue-msg dialogue-user"><div class="dialogue-bubble user-bubble">' + Utils.escapeHtml(msg.content) + '</div></div>';
        }
    });

    if (stage === 'done') {
        var reqs = data.confirmed_requirements || '';
        var scope = data.suggested_scope || 'minor';
        html += '<div class="alert alert-success py-2 mt-2"><i class="fas fa-check-circle me-1"></i>需求已确认！AI 正在生成优化方案供您选择...</div>';
        messagesEl.innerHTML = html;
        state.confirmedRequirements = reqs;
        state.suggestedScope = scope;
        state.done = true;
        document.getElementById('optimize-requirements').value = reqs;
        var scopeRadio = document.querySelector('input[name="optimize-scope"][value="' + scope + '"]');
        if (scopeRadio) scopeRadio.checked = true;
        _fetchProposals(novelId, chapterNumber, reqs, scope);
        return;
    }

    messagesEl.innerHTML = html;
    messagesEl.scrollTop = messagesEl.scrollHeight;

    // 聚焦输入框
    var input = document.getElementById('dialogue-custom-input');
    if (input) input.focus();
};
```

- [ ] **Step 4：修改 selectDialogueOption，改为 append 等待气泡**

将 `frontend/app.js` 第 4130 行的 `selectDialogueOption` 函数替换为：

```javascript
window.selectDialogueOption = async (option) => {
    var info = _getActiveDialogueNovelInfo();
    var state = _getDialogueState(info.novelId, info.chapterNumber);
    state.messages.push({ role: 'user', content: option });
    state.round++;

    // 在消息区追加用户气泡 + 等待气泡（不替换整个容器）
    var messagesEl = document.getElementById('dialogue-messages');
    var typingId = 'typing-' + Date.now();
    messagesEl.innerHTML +=
        '<div class="dialogue-msg dialogue-user"><div class="dialogue-bubble user-bubble">' + Utils.escapeHtml(option) + '</div></div>' +
        '<div id="' + typingId + '" class="dialogue-msg dialogue-ai"><div class="dialogue-bubble ai-bubble"><span class="spinner-border spinner-border-sm me-1"></span>思考中...</div></div>';
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
        var resp = await Utils.apiRequest('/novels/' + info.novelId + '/chapters/' + info.chapterNumber + '/improve/dialogue', {
            method: 'POST',
            body: JSON.stringify({
                messages: state.messages.map(function(m) { return { role: m.role, content: m.content }; }),
                chapter_summary: state.chapterSummary,
                chapter_title: state.chapterTitle,
                tags: state.tags
            })
        });

        if (!resp.success) throw new Error(resp.error || '对话失败');

        var data = resp.data;
        var typingBubble = document.getElementById(typingId);
        if (typingBubble) typingBubble.remove();
        state.messages.push({ role: 'assistant', content: data.question, options: data.options || [], stage: data.stage });
        renderDialogue(data, info.novelId, info.chapterNumber);

    } catch (e) {
        var tb = document.getElementById(typingId);
        if (tb) tb.remove();
        var messagesEl2 = document.getElementById('dialogue-messages');
        if (messagesEl2) messagesEl2.innerHTML += '<div class="alert alert-warning py-2 mt-1">对话出错: ' + Utils.escapeHtml(e.message) + '</div>';
    }
};
```

- [ ] **Step 5：同步修改 confirmDialogueOption 的加载态**

找到第 4163 行 `confirmDialogueOption`，将：
```javascript
    container.innerHTML = '<div class="text-center text-muted py-2">...处理中...</div>';
```
改为：
```javascript
    var messagesEl = document.getElementById('dialogue-messages');
    var typingId2 = 'typing-confirm-' + Date.now();
    if (messagesEl) {
        messagesEl.innerHTML += '<div id="' + typingId2 + '" class="dialogue-msg dialogue-ai"><div class="dialogue-bubble ai-bubble"><span class="spinner-border spinner-border-sm me-1"></span>处理中...</div></div>';
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
```
并在后续两处 `renderDialogue(...)` 调用前加：
```javascript
    var tb2 = document.getElementById(typingId2); if (tb2) tb2.remove();
```

- [ ] **Step 6：修改 startRequirementDialogue 的初始加载态**

找到第 3929 行：
```javascript
    container.innerHTML = '<div class="text-center text-muted py-2"><span class="spinner-border spinner-border-sm me-2"></span>AI 正在准备提问...</div>';
```
改为（container 现在包含 #dialogue-messages 和 #dialogue-input-area，只更新消息区）：
```javascript
    container.style.display = 'block';
    var msgEl = document.getElementById('dialogue-messages');
    if (msgEl) msgEl.innerHTML = '<div class="text-center text-muted py-2"><span class="spinner-border spinner-border-sm me-2"></span>AI 正在准备提问...</div>';
```
注意：此时 `container.style.display = 'block'` 已在前面（第 3903 行）设置，这里只需更新消息区内容。

- [ ] **Step 7：手动测试 optimize 对话**

在浏览器打开 `http://localhost:5000`，打开任意章节的 AI 优化弹窗，点击"对话确认需求"：
- 验证输入框在对话框底部始终可见
- 点击一个选项后，历史消息不消失（出现用户气泡 + 等待气泡）
- AI 回复后，回复内容以"你提到/你说到……"开头
- 选项内容包含具体词（不是通用的"优化文笔"）

- [ ] **Step 8：Commit**

```bash
git add frontend/app.js
git commit -m "fix: optimize 对话布局分离 + append 等待气泡 + 补初始用户消息"
```

---

### Task 3：修复 rules 对话（existing_rules + append 等待气泡）

**Files:**
- Modify: `frontend/app.js:7601`（`_rulesDialogue` 初始化，新增 `existingRules` 字段）
- Modify: `frontend/app.js:7673-7706`（`startRulesDialogue`，存 existingRules）
- Modify: `frontend/app.js:7761-7800`（`selectRulesOption`，传 existingRules，改加载态）

**Interfaces:**
- Consumes: `window._rulesDialogue.existingRules`（新增字段，Task 3 内部定义和消费）
- Produces: 每轮 POST `/rules/dialogue` 携带正确的 `existing_rules`

- [ ] **Step 1：在 _rulesDialogue 初始化时增加 existingRules 字段**

找到第 7601 行：
```javascript
window._rulesDialogue = { messages: [], done: false };
```
改为：
```javascript
window._rulesDialogue = { messages: [], done: false, existingRules: [] };
```

- [ ] **Step 2：startRulesDialogue 存入 existingRules**

找到第 7690 行的 `.then(function (resp) {` 回调，在 `existingRules` 赋值后存入 `_rulesDialogue`：

```javascript
    Utils.apiRequest('/novels/' + novelId + '/rules').then(function (resp) {
        var existingRules = (resp.success && resp.data && resp.data.rules) ? resp.data.rules : [];
        window._rulesDialogue.existingRules = existingRules;   // ← 新增这行
        return Utils.apiRequest('/novels/' + novelId + '/rules/dialogue', {
            method: 'POST',
            body: JSON.stringify({ messages: [], novel_title: novelTitle, existing_rules: existingRules })
        });
    })
```

- [ ] **Step 3：selectRulesOption 传入 existingRules，改加载态为 append 气泡**

将 `frontend/app.js` 第 7761 行整个 `selectRulesOption` 函数替换为：

```javascript
window.selectRulesOption = function (option, idx) {
    var ds = window._rulesDialogue;
    var novelId = AppState.selectedNovelId;
    ds.messages.push({ role: 'user', content: option });

    if (option.indexOf('结束') >= 0 || option.indexOf('完成') >= 0 || option.indexOf('不再添加') >= 0) {
        document.getElementById('rules-dialogue-container').style.display = 'none';
        loadRulesList();
        return;
    }

    // append 用户气泡 + 等待气泡（不替换整个消息区）
    var msgArea = document.getElementById('rules-dialogue-messages');
    var typingId = 'typing-rules-' + Date.now();
    msgArea.innerHTML +=
        '<div class="dialogue-message user"><div>' + Utils.escapeHtml(option) + '</div></div>' +
        '<div id="' + typingId + '" class="dialogue-message assistant"><div><span class="spinner-border spinner-border-sm me-1"></span>思考中...</div></div>';
    msgArea.scrollTop = msgArea.scrollHeight;

    var novelTitle = '';
    if (AppState.continuationData && AppState.continuationData.novel_data) {
        novelTitle = AppState.continuationData.novel_data.title || '';
    }

    var textMessages = ds.messages.map(function (m) { return { role: m.role, content: m.content }; });

    fetch(API_BASE + '/novels/' + novelId + '/rules/dialogue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages: textMessages,
            novel_title: novelTitle,
            existing_rules: ds.existingRules   // ← 传入已有规则（不再传空数组）
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (resp) {
        var tb = document.getElementById(typingId);
        if (tb) tb.remove();
        if (!resp.success) { Utils.showMessage(resp.error || '对话失败', 'danger'); renderRulesDialogue(); return; }
        var data = resp.data;
        ds.messages.push({ role: 'assistant', content: data.question, options: data.options || [], stage: data.stage, rule_update: data.rule_update });
        renderRulesDialogue();
    })
    .catch(function (e) {
        var tb = document.getElementById(typingId);
        if (tb) tb.remove();
        Utils.showMessage('对话失败: ' + e.message, 'danger');
        renderRulesDialogue();
    });
};
```

- [ ] **Step 4：同步更新 saveRuleToServer 后刷新 existingRules 缓存**

在 `saveRuleToServer` 函数的成功回调中（第 7821 行左右），追加刷新缓存：

```javascript
        if (resp.success) {
            Utils.showMessage('规则已保存', 'success');
            loadRulesList();
            // 刷新 existingRules 缓存，下一轮对话能看到刚保存的规则
            Utils.apiRequest('/novels/' + novelId + '/rules').then(function(r) {
                if (r.success && r.data && r.data.rules) {
                    window._rulesDialogue.existingRules = r.data.rules;
                }
            });
        }
```

- [ ] **Step 5：手动测试 rules 对话**

打开"规则管理"页面，点击"AI 对话建立规则"：
- 聊第一轮，回复后消息历史不消失
- 选择一个选项，用户气泡 + 等待气泡 append 到已有消息下方
- AI 回复以"你提到/你说……"开头
- 进入 confirming 阶段保存规则后，再开新一轮对话，新轮回复能感知到刚保存的规则

- [ ] **Step 6：Commit**

```bash
git add frontend/app.js
git commit -m "fix: rules 对话每轮携带 existingRules，改 append 气泡加载态"
```

---

### Task 4：重启验证 + 收尾

**Files:**
- No new files

- [ ] **Step 1：重启服务器**

```bash
bash scripts/restart.sh
sleep 4 && tail -8 logs/web.log
```

预期输出最后包含 `Running on http://127.0.0.1:5000`，无 `SyntaxError` 或 `ImportError`。

- [ ] **Step 2：端到端验证 optimize 对话**

1. 打开 `http://localhost:5000`，选择有章节的小说
2. 打开章节 → AI 优化 → 对话确认需求
3. 检查：自由输入框固定在底部，选项在消息区内
4. 点一个选项：历史不闪，用户气泡出现，等待气泡出现，AI 回复后等待气泡消失
5. AI 回复第一句引用了你点的选项中的词
6. 用自由输入框发一条，同样流畅
7. 达到 confirming 阶段，确认后自动进入方案提案

- [ ] **Step 3：端到端验证 rules 对话**

1. 续写页面 → 规则管理 → AI 对话建立规则
2. 多轮对话，每轮 AI 接上上一句话
3. 规则保存后，继续新一轮对话，AI 知道已有哪些规则

- [ ] **Step 4：最终 Commit**

```bash
git add -p   # 确认无意外文件
git commit -m "fix: 对话连续性改造完成 - prompt 接话 + append 气泡 + 固定输入框"
```
