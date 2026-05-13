<div align="center">

<img src="https://img.shields.io/badge/version-1.10-blue" alt="version">
<img src="https://img.shields.io/badge/license-MIT-green" alt="license">
<img src="https://img.shields.io/badge/python-3.8%2B-orange" alt="python">
<img src="https://img.shields.io/badge/agents-25-red" alt="agents">

# InkAI — AI 长篇小说智能创作框架

**从创意到成品，一步到位**<br>
<sub>基于大语言模型 × 多智能体协作 × 全流程自动化</sub>

</div>

---

## 概述

InkAI 是一个面向中长篇小说创作的 AI 框架。它不是一个简单的"AI 续写"工具——而是一个完整的**创作工场**：从一句"我想写一本都市悬疑"开始，系统自动完成标签推荐、角色塑造、三幕故事线构建、章节正文写作、质量评估与自动改进，直至产出完整作品。

**核心理念**：短篇靠单点爆发，中长篇靠长线闭环。InkAI 通过 25 个专业 Agent 的编排协作，解决了 AI 写作中最大的痛点——**跨章节一致性**和**长期剧情把控**。

---

## 功能矩阵

### 创作流水线

| 阶段 | 负责 Agent | 输入 | 输出 |
|------|-----------|------|------|
| ① 标签推荐 | TagSelectorAgent | 用户一句话需求 | 类型/主题/风格/受众 四维标签（70+可选） |
| ② 角色创建 | CharacterCreatorAgent | 标签 + 需求 | 主角完整档案（Big Five 人格 × 20 维度）+ 配角群 |
| ③ 故事线生成 | StorylineGeneratorAgent | 角色 + 标签 | 三幕剧结构 × 世界设定 × 主题提炼 |
| ④ 章节写作 | ChapterWriterAgent | 故事线 + 角色 | 2000-5000 字正文 + 章节元数据 |
| ⑤ 质量评估 | QualityAssessorAgent | 产出内容 | 五维评分（情节连贯性/人物立体度/语言风格/创新吸引力）+ 改进建议 |

### 智能续写引擎

已创作的小说可无限续写，每个新章节自动：

1. **构建知识库** — 从历史章节提取角色状态、情节线、伏笔、世界观规则
2. **智能上下文选择** — 从海量前文中筛选当前续写最相关的片段
3. **续写故事线生成** — 规划新章节的情节框架
4. **正文写作** — 按故事线生成正文，严格保持一致
5. **多维度评估** — 6 个专项一致性 Agent 并行检查
6. **自动改进** — 不达标则触发改进 Agent，评估→改进→重评估直到合格

### 质量保证体系

```
新章节生成
    ↓
┌─ 角色一致性评估 ── 角色行为/语言/性格是否符合原设定
├─ 情节逻辑评估 ── 情节线闭合，无逻辑漏洞
├─ 世界观一致性评估 ── 世界规则贯穿，无前后矛盾
├─ 风格一致性评估 ── 文风、语气、叙事角度统一
├─ 读者体验评估 ── 节奏张力、情感共鸣、可读性
└─ 长期一致性评估 ── 跨卷长期线索跟踪
    ↓
综合评分 ≥ 80 → 保存 | < 80 → 自动改进 → 重评估
```

---

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                   Web 前端                        │
│          Bootstrap 5 + 原生 JavaScript            │
│         交互式向导 / 续写面板 / 实时监控           │
└──────────────────┬──────────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────────┐
│               Flask 服务层 (app.py)               │
│         路由 / 请求校验 / 任务编排 / 状态管理      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         核心编排器 (InkAIWorkflowOptimized)        │
│      140KB 单体状态机：创作流 / 续写流 / 评估流    │
└──────┬───────────────────────┬──────────────────┘
       │                       │
┌──────▼──────────┐   ┌───────▼───────────────────┐
│  创作 Agent (5) │   │   续写 Agent (3)          │
│  标签 / 角色    │   │   知识库 / 续写线 / 续写章 │
│  故事线 / 写作  │   └───────────────────────────┘
│  质量控制       │
└─────────────────┘
       │
┌──────▼──────────────────────────────────────────┐
│              评估 Agent (6)                       │
│  角色一致性 / 情节逻辑 / 世界观 / 风格 / 体验 / 长线 │
└──────┬──────────────────────────────────────────┘
       │ 不达标触发
┌──────▼──────────────────────────────────────────┐
│              改进 Agent (11)                      │
│  按维度专项修复 → 送回评估 → 合格后入库            │
└─────────────────────────────────────────────────┘
       │
┌──────▼──────────┐   ┌───────────────────────────┐
│  DataManager    │   │   Core Services            │
│  JSON 文件存储   │   │   知识图谱 / 上下文选择器    │
│  版本化 / 可备份 │   │   缓存管理 / 性能监控       │
└─────────────────┘   └───────────────────────────┘
```

---

## 快速开始

### 安装

```bash
git clone https://github.com/yan2959088709/InkAI-.git
cd InkAI-
pip install -r requirements.txt
```

### 配置

编辑 `config.py`：

```python
API_KEY = "your_glm_api_key"          # 智谱 AI GLM-4.5-flash
EMBEDDING_API_KEY = "your_key"        # SiliconFlow BAAI/bge-m3
MODEL_NAME = "glm-4.5-flash"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
```

### 启动

```bash
python start_web.py
# 浏览器打开 http://localhost:5000
```

---

## API 速览

所有接口返回 JSON，`ok` 字段表示成功/失败：

```python
{"ok": True, "data": {...}}
{"ok": False, "error": "..."}
```

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/novels` | 创建新小说 |
| POST | `/api/novels/<id>/tags` | 智能标签推荐 |
| POST | `/api/novels/<id>/characters` | 创建角色档案 |
| POST | `/api/novels/<id>/storyline` | 生成三幕故事线 |
| POST | `/api/novels/<id>/chapters` | 写作第一章 |
| POST | `/api/novels/<id>/continue` | 启动异步续写 |
| GET | `/api/novels/<id>/continue/status` | 查询续写进度 |
| POST | `/api/novels/<id>/continue/stop` | 停止续写任务 |
| GET | `/api/novels/<id>` | 获取小说完整数据 |
| GET | `/api/novels/<id>/chapter/<n>` | 获取指定章节 |

---

## 项目结构

```
InkAI/
├── app.py                              # Flask Web 服务 (1496 行)
├── inkai_workflow_optimized.py         # 核心编排器 (1649 行)
├── quick_continuation_executor.py      # 异步续写引擎 (900 行)
├── data_manager.py                     # 数据持久化层
├── workflow_context.py                 # 工作流上下文管理
├── base_agent.py                       # Agent 基类（LLM 调用 / JSON 解析）
├── config.py                           # 全局配置
│
├── agents/                             # 25 个专业 Agent
│   ├── tag_selector.py                 #   1. 标签推荐
│   ├── character_creator.py            #   2. 角色创建 (Big Five)
│   ├── storyline_generator.py          #   3. 三幕故事线
│   ├── chapter_writer.py               #   4. 章节写作
│   ├── quality_assessor.py             #   5. 质量评估
│   ├── novel_continuation_agent.py     #   6. 续写管理器
│   ├── continuation_storyline_*.py     #   7. 续写故事线
│   ├── continuation_chapter_writer.py  #   8. 续写章节
│   ├── continuation_*_assessor.py      #   9-14. 六维一致性评估
│   └── continuation_*_improver.py      #  15-25. 专项改进
│
├── core/                               # 核心服务
│   ├── core_knowledge_manager.py       # 知识图谱管理
│   ├── dynamic_knowledge_manager.py    # 动态状态追踪
│   └── intelligent_context_selector.py # 智能上下文选择
│
├── frontend/                           # Web 前端
│   ├── index.html                      # Bootstrap 5 SPA
│   ├── app.js                          # 前端逻辑
│   └── styles.css                      # 样式
│
└── data/                               # 运行时数据
    ├── novels/<uuid>/                  # 每本小说独立目录
    └── knowledge_graphs/               # 知识图谱持久化
```

---

## 兼容性

- **Python**: 3.8+
- **LLM 后端**: 默认智谱 GLM-4.5-flash，`BASE_URL` 改为 OpenAI 兼容地址即可切换
- **存储**: 纯 JSON 文件，零数据库依赖，复制目录即可迁移
- **OS**: Windows / macOS / Linux

---

## License

MIT — 自由使用、修改、分发。

---

<div align="center">
<sub>Made with ☕ and LLMs</sub>
</div>
