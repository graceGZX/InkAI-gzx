# 章节 AI 优化功能设计

## 概述
为已有章节增加 AI 质量评估和智能优化功能，用户可对任意已写章节进行质量评估，并输入优化需求让 AI 优化章节内容。优化后自动同步故事线和知识图谱。

## UI 变更

### 章节列表入口
- 每行"编辑"按钮左侧增加"AI优化"按钮
- 点击后弹出优化弹窗（Bootstrap 5 Modal）

### 优化弹窗布局
```
标题: AI优化 - 第X章

[质量评估] 按钮  |  状态: 未评估/评估中/已完成

--- 评估结果区域（评估后显示）---
综合评分: XX分 | 质量等级: 优秀/良好/一般/需改进
维度评分卡片: 文笔 | 节奏 | 人设 | 爽点 | 钩子 | 一致性
改进建议列表（可点击采纳到优化需求）

--- 优化操作区域 ---
[优化需求] textarea: "告诉AI你想怎么优化这章..."
[开始优化] 按钮

--- 优化结果预览（优化后显示）---
text 显示优化后全文（可编辑）
[字数统计]
[接受并保存] [放弃]
```

## 后端 API

### 1. POST /api/novels/<id>/chapters/<n>/quality
评估已有章节质量，包含文学性和一致性两个维度。

**Request**: 无 body
**Response**:
```json
{
  "success": true,
  "data": {
    "overall_score": 85,
    "quality_level": "良好",
    "dimensions": {
      "writing_quality": 80,
      "pacing": 90,
      "character_depth": 85,
      "appeal_density": 75,
      "hook_strength": 70,
      "consistency": 88
    },
    "suggestions": ["建议1", "建议2"],
    "strengths": ["优点1"],
    "weaknesses": ["薄弱点1"],
    "assessed_at": "2026-06-27T..."
  }
}
```

### 2. POST /api/novels/<id>/chapters/<n>/improve
根据用户需求优化章节，返回优化结果预览。不直接落盘，等用户确认后由前端调用 PUT 保存。

**Request**: `{ "requirements": "加强主角心理描写，增加冲突张力", "suggestions": ["建议1"] }`
**Response**:
```json
{
  "success": true,
  "data": {
    "original_content": "...",
    "improved_content": "...",
    "changes_summary": "优化了X处，主要包括..."
  }
}
```

## 后端 Agent

### ChapterQualityAssessor（新增或复用现有 QualityAssessorAgent）
- 输入：章节内容 + 人物档案 + 故事圣经 + 连续性档案
- 评估：文学质量（5维度）+ 一致性（5维度，复用 ContinuationQualityAssessor 逻辑）
- 输出：评分 + 建议

### ChapterImprover（新增或复用现有 ContinuationChapterImprover）
- 输入：章节内容 + 用户需求 + 评估结果 + 知识库
- 输出：优化后章节内容
- 约束：保留原有字数规模，保持人设/世界观一致

## 同步逻辑
用户确认保存优化后：
1. 前端调用 PUT /api/novels/<id>/chapters/<n> 保存优化后内容
2. 后端 update_chapter 方法增强：保存后触发知识图谱更新（人物状态、事件时间线）
3. 前端刷新章节列表和详情

## 实现范围
- 后端：2个新 API + 调用现有 Agent
- 前端：1个新按钮 + 1个新弹窗（带评估、优化、预览三个子区域）
