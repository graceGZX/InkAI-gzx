<div align="center">

<br>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=36&duration=3000&pause=1000&color=3B82F6&center=true&vCenter=true&width=600&lines=InkAI;AI+%C3%97+%E5%B0%8F%E8%AF%B4%E5%88%9B%E4%BD%9C;%E4%BB%8E%E5%88%9B%E6%84%8F%E5%88%B0%E6%88%90%E5%93%81" alt="InkAI" />

**<sup>长篇小说智能创作框架</sup>**

<br>

<a href="#-quick-start"><img src="https://img.shields.io/badge/QUICK_START-⚡-3B82F6?style=for-the-badge&labelColor=1E293B" /></a>
<a href="#-architecture"><img src="https://img.shields.io/badge/ARCHITECTURE-🏗-6366F1?style=for-the-badge&labelColor=1E293B" /></a>
<a href="#-api"><img src="https://img.shields.io/badge/API-🔌-8B5CF6?style=for-the-badge&labelColor=1E293B" /></a>

<br>

---

<table align="center"><tr>
<td align="center" width="140"><b>25</b><br><sup>专业 Agent</sup></td>
<td align="center" width="140"><b>5</b><br><sup>创作阶段</sup></td>
<td align="center" width="140"><b>6</b><br><sup>评估维度</sup></td>
<td align="center" width="140"><b>70+</b><br><sup>风格标签</sup></td>
<td align="center" width="140"><b>1000+</b><br><sup>章续航</sup></td>
<td align="center" width="140"><b>MIT</b><br><sup>开源协议</sup></td>
</tr></table>

---

</div>

## 概述

**InkAI** 不是"AI 续写"——它是一个**完整的创作工场**。

输入一句"我想写一本都市悬疑"，25 个专业 Agent 协同运转：分析需求 → 推荐标签 → 塑造角色（Big Five 人格模型）→ 构建三幕故事线 → 写作正文 → 多维度质量评估 → 自动改进。循环往复，直到完成一部逻辑自洽、人物立体、伏笔闭合的长篇小说。

<div align="center">

> *"短篇靠单点爆发，中长篇靠长线闭环"*

</div>

---

## 创作流水线

```mermaid
graph LR
    A["<b>🎯 需求输入</b><br/>一句话描述"] -->|"TagSelector"| B["<b>🏷 标签推荐</b><br/>70+ 四维标签库"]
    B -->|"CharacterCreator"| C["<b>👤 角色创建</b><br/>Big Five × 20 维度"]
    C -->|"StorylineGenerator"| D["<b>📖 故事线</b><br/>三幕剧 × 章纲 × 伏笔"]
    D -->|"ChapterWriter"| E["<b>✍ 章节写作</b><br/>2000-5000 字/章"]
    E -->|"QualityAssessor"| F{"<b>✅ 质量评估</b><br/>五维综合评分"}
    F -->|"≥ 80 分"| G["<b>📦 保存入库</b>"]
    F -->|"&lt; 80 分"| H["<b>🔧 自动改进</b>"]
    H --> E

    style A fill:#3B82F6,color:#fff,stroke:#2563EB
    style B fill:#6366F1,color:#fff,stroke:#4F46E5
    style C fill:#8B5CF6,color:#fff,stroke:#7C3AED
    style D fill:#A855F7,color:#fff,stroke:#9333EA
    style E fill:#EC4899,color:#fff,stroke:#DB2777
    style F fill:#F59E0B,color:#fff,stroke:#D97706
    style G fill:#10B981,color:#fff,stroke:#059669
    style H fill:#EF4444,color:#fff,stroke:#DC2626
```

---

## 系统架构

```mermaid
graph TB
    subgraph L1["&nbsp;&nbsp;🖥 用户界面层&nbsp;&nbsp;"]
        WEB["Web 前端<br/>Bootstrap 5 + vanilla JS<br/>交互式向导 / 续写面板 / 实时监控"]
    end

    subgraph L2["&nbsp;&nbsp;🌐 API 服务层&nbsp;&nbsp;"]
        FLASK["Flask REST API<br/>路由 · 校验 · 编排 · 状态"]
    end

    subgraph L3["&nbsp;&nbsp;⚙ 核心编排层&nbsp;&nbsp;"]
        WF["InkAIWorkflowOptimized<br/><sub>140KB 单体状态机</sub>"]
        QCE["QuickContinuationExecutor<br/><sub>异步续写引擎</sub>"]
    end

    subgraph L4["&nbsp;&nbsp;🤖 智能体层 · 25 Agents&nbsp;&nbsp;"]
        direction LR
        A1["创作 ×5"]
        A2["续写 ×3"]
        A3["评估 ×6"]
        A4["改进 ×11"]
    end

    subgraph L5["&nbsp;&nbsp;📦 基础设施层&nbsp;&nbsp;"]
        CORE["知识图谱 · 上下文选择 · 缓存"]
        DATA["DataManager · JSON 存储"]
    end

    WEB --> FLASK
    FLASK --> WF
    FLASK --> QCE
    WF --> L4
    QCE --> L4
    L4 --> CORE
    CORE --> DATA

    style L1 fill:#EFF6FF,stroke:#3B82F6
    style L2 fill:#EEF2FF,stroke:#6366F1
    style L3 fill:#F3E8FF,stroke:#8B5CF6
    style L4 fill:#FCE7F3,stroke:#EC4899
    style L5 fill:#ECFDF5,stroke:#10B981
```

---

## 智能续写引擎

```mermaid
sequenceDiagram
    autonumber
    participant K as 📚 知识库
    participant S as 🧠 续写故事线
    participant W as ✍ 章节写作
    participant A as 🔍 评估矩阵
    participant I as 🔧 改进引擎

    Note over K,I: 每章一个完整闭环

    W->>K: ① 提取前文状态
    K-->>S: 角色 · 情节 · 伏笔 · 世界观
    S->>S: ② 生成续写故事线
    S-->>W: 章纲 + 事件 + 角色调度
    W->>W: ③ 正文写作
    W-->>A: 2000-5000 字
    A->>A: ④ 六维并行评估
    alt ⑤ 评分 ≥ 80
        A-->>K: 合格 · 保存 · 更新知识库
    else ⑥ 评分 &lt; 80
        A-->>I: 触发专项改进
        I-->>W: 改进后重写
    end
```

<table align="center"><tr>
<td align="center"><b>角色一致性</b><br/><sub>行为 · 语言 · 性格轨迹</sub></td>
<td align="center"><b>情节逻辑</b><br/><sub>因果链 · 漏洞检测</sub></td>
<td align="center"><b>世界观</b><br/><sub>规则一贯 · 设定统一</sub></td>
<td align="center"><b>风格一致</b><br/><sub>语气 · 叙事 · 节奏</sub></td>
<td align="center"><b>读者体验</b><br/><sub>张力 · 共鸣 · 可读性</sub></td>
<td align="center"><b>长期线索</b><br/><sub>跨卷伏笔 · 大结局</sub></td>
</tr></table>

---

## 快速开始

<div id="-quick-start"></div>

```bash
git clone https://github.com/yan2959088709/InkAI-.git && cd InkAI-
pip install -r requirements.txt
```

编辑 `config.py` 填入 API 密钥，然后：

```bash
python start_web.py
# → http://localhost:5000
```

| 配置项 | 说明 |
|------|------|
| `API_KEY` | 智谱 AI GLM-4.5-flash |
| `EMBEDDING_API_KEY` | SiliconFlow BAAI/bge-m3 |
| `BASE_URL` | OpenAI 兼容地址（模型可换） |
| `QUALITY_THRESHOLD` | 质量合格线，默认 80 |

> **兼容性**: Python 3.8+ · Windows / macOS / Linux · 零数据库依赖 · 复制目录即迁移

---

## API

<div id="-api"></div>

所有端点返回统一格式：

```json
{ "ok": true, "data": { } }
{ "ok": false, "error": "..." }
```

<table>
<tr>
<th width="8%">方法</th>
<th width="42%">端点</th>
<th width="50%">功能</th>
</tr>
<tr><td><code>POST</code></td><td><code>/api/novels</code></td><td>创建新小说</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/tags</code></td><td>智能标签推荐</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/characters</code></td><td>创建角色档案</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/storyline</code></td><td>生成三幕故事线</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/chapters</code></td><td>写作第一章</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/continue</code></td><td>启动异步续写</td></tr>
<tr><td><code>GET</code></td><td><code>/api/novels/&lt;id&gt;/continue/status</code></td><td>查询续写进度</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/continue/stop</code></td><td>停止续写</td></tr>
<tr><td><code>GET</code></td><td><code>/api/novels/&lt;id&gt;</code></td><td>获取小说完整数据</td></tr>
<tr><td><code>GET</code></td><td><code>/api/novels/&lt;id&gt;/chapter/&lt;n&gt;</code></td><td>获取指定章节</td></tr>
</table>

---

## 项目结构

<div id="-architecture"></div>

```
InkAI/
│
├── 🤖 agents/                         25 个专业 Agent
│   ├── tag_selector.py                标签推荐
│   ├── character_creator.py           角色创建 (Big Five)
│   ├── storyline_generator.py         三幕故事线
│   ├── chapter_writer.py              章节写作
│   ├── quality_assessor.py            质量评估
│   ├── novel_continuation_agent.py    续写管理器
│   ├── continuation_storyline_*.py    续写故事线
│   ├── continuation_chapter_*.py      续写章节 ± 改进
│   ├── continuation_*_assessor.py     六维一致性评估 ×6
│   └── continuation_*_improver.py     专项改进 ×11
│
├── ⚙ core/                           核心服务
│   ├── core_knowledge_manager.py      知识图谱
│   ├── dynamic_knowledge_manager.py   动态状态追踪
│   └── intelligent_context_selector.py 智能上下文
│
├── 🖥 frontend/                       Web 前端
│   ├── index.html                     Bootstrap 5 SPA
│   ├── app.js                         前端逻辑
│   └── styles.css                     样式
│
├── 📄 app.py                          Flask 服务 (1500 行)
├── 📄 inkai_workflow_optimized.py     核心编排器 (1650 行)
├── 📄 quick_continuation_executor.py  异步续写 (900 行)
├── 📄 data_manager.py                 数据持久化层
├── 📄 workflow_context.py             工作流上下文
├── 📄 base_agent.py                   Agent 基类
├── 📄 config.py                       全局配置
│
└── 💾 data/                          运行时数据
    ├── novels/<uuid>/                 每本小说独立目录
    └── knowledge_graphs/              知识图谱持久化
```

---

<div align="center">

<br>

**InkAI** · AI × 小说创作 · 从创意到成品

<sub>Powered by LLMs · Built with ☕</sub>

<br>

<img src="https://img.shields.io/badge/version-1.10-3B82F6?style=flat-square" />
<img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" />
<img src="https://img.shields.io/badge/python-3.8+-F59E0B?style=flat-square" />

</div>
