# InkAI — AI 长篇小说创作系统

基于大语言模型的多智能体中长篇网文自动写作工具。从题材标签选择到章节续写，覆盖创作全流程。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务
python start_web.py
# 浏览器打开 http://localhost:5000
```

## 能做什么

1. **新建小说**：输入书名、主角名、创作需求 → AI 自动选择标签 → 创建角色 → 生成三幕故事线 → 写第一章
2. **续写章节**：加载已有小说，AI 读取前文后继续写新一章，保持角色和剧情一致性
3. **质量评估**：每章写完后自动评估（角色一致性、情节逻辑、世界观、风格、读者体验），不达标自动改进

Web 界面提供新建向导和续写页，不用敲命令。

## 整体架构

```
用户 Web 界面
    ↓
Flask API (app.py)          ← 前端请求入口
    ↓
InkAIWorkflowOptimized      ← 核心编排器（140KB 单体状态机）
    ↓
智能体层 (agents/)           ← 25 个专业 Agent，每个只做一件事
    ├─ 创作类 (5):  标签选择 / 角色创建 / 故事线 / 章节写作 / 质量评估
    ├─ 续写类 (3):  知识库构建 / 续写故事线 / 续写章节
    ├─ 评估类 (6):  角色一致性 / 情节逻辑 / 世界观 / 风格 / 读者体验 / 长期一致性
    └─ 改进类 (11): 对应上述维度的自动修复 Agent
    ↓
数据层 (data_manager.py)     ← JSON 文件系统存储
```

## 目录结构

```
.
├── app.py                          # Flask Web 服务 + API
├── inkai_workflow_optimized.py     # 核心工作流编排器
├── quick_continuation_executor.py  # 续写执行器（异步）
├── data_manager.py                 # 数据持久化
├── workflow_context.py             # 工作流上下文状态
├── base_agent.py                   # Agent 基类（LLM 调用 + JSON 解析）
├── config.py                       # API 密钥 / 模型 / 路径配置
├── agents/
│   ├── tag_selector.py             # 标签选择
│   ├── character_creator.py        # 角色创建
│   ├── storyline_generator.py      # 三幕故事线生成
│   ├── chapter_writer.py           # 章节正文写作
│   ├── quality_assessor.py         # 新章节质量评估
│   ├── novel_continuation_agent.py # 续写管理器
│   ├── continuation_*.py           # 续写 / 评估 / 改进 Agent（18个）
│   └── ...
├── core/                           # 知识管理 + 上下文选择
├── frontend/                       # Web 前端（Bootstrap + 原生 JS）
├── data/
│   ├── novels/         # 生成的小说（每本一个 UUID 目录）
│   └── knowledge_graphs/
└── requirements.txt
```

## API 接口

所有接口前缀 `/api`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/novels` | 创建新小说（title + user_requirements） |
| POST | `/api/novels/<id>/tags` | 选择标签 |
| POST | `/api/novels/<id>/characters` | 创建角色 |
| POST | `/api/novels/<id>/storyline` | 生成故事线 |
| POST | `/api/novels/<id>/chapters` | 写第一章 |
| POST | `/api/novels/<id>/continue` | 启动续写 |
| GET | `/api/novels/<id>/continue/status` | 查询续写进度 |
| GET | `/api/novels/<id>` | 获取小说完整数据 |
| GET | `/api/novels/<id>/chapter/<n>` | 获取指定章节 |

## 配置

编辑 `config.py`：

```python
API_KEY = "your_glm_api_key"              # 智谱 AI GLM 密钥
EMBEDDING_API_KEY = "your_embedding_key"   # SiliconFlow 嵌入模型密钥
MODEL_NAME = "glm-4.5-flash"
QUALITY_THRESHOLD = 80                     # 质量合格线（百分制）
```

## 注意事项

- 每章生成约需 30-90 秒，取决于模型响应
- 质量评估是建议性的，不会自动拒绝"低分"章节
- JSON 文件直接存盘，没有数据库——适合个人使用，多用户场景注意并发
- 当前版本只支持 GLM 系列模型（API 格式是 OpenAI 兼容的，改 BASE_URL 即可切换）

## License

MIT
