"""
续写情节逻辑专项评估智能体
专门评估续写内容中情节的逻辑性
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationPlotLogicAssessor(BaseAgent):
    """续写情节逻辑专项评估智能体"""
    
    def __init__(self):
        super().__init__("续写情节逻辑专项评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容中情节的逻辑性"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行情节逻辑评估
        assessment_result = self._assess_plot_logic(
            continuation_content, original_knowledge_base, content_type
        )
        
        return assessment_result
    
    def _assess_plot_logic(self, continuation_content: Dict[str, Any], 
                          knowledge_base: Dict[str, Any], 
                          content_type: str) -> Dict[str, Any]:
        """评估情节逻辑"""
        try:
            if content_type == "story":
                return self._assess_story_plot_logic(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_plot_logic(continuation_content, knowledge_base)
            else:
                return self._assess_general_plot_logic(continuation_content, knowledge_base)
                
        except Exception as e:
            self.log(f"情节逻辑评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_plot_logic(self, chapter_content: Dict[str, Any], 
                               knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容中的情节逻辑"""
        content = chapter_content.get("content", "")
        plot_lines = knowledge_base.get("plot_lines", {})
        last_chapter = knowledge_base.get("last_chapter_summary", {})
        
        # 构建评估提示
        prompt = f"""
        请专门评估以下续写章节中情节的逻辑性，重点关注以下维度：
        
        原文情节线：
        {self._format_plot_lines(plot_lines)}
        
        上一章结尾：
        {self._format_last_chapter(last_chapter)}
        
        续写章节内容：
        {content}
        
        请从以下维度评估情节逻辑（每项0-100分）：
        1. 因果关系合理性：事件之间的因果关系是否合理
        2. 时间线一致性：时间顺序是否一致，无矛盾
        3. 事件发展逻辑：事件发展是否符合逻辑规律
        4. 冲突升级合理性：冲突发展是否合理递进
        5. 伏笔呼应完整性：伏笔设置和呼应是否完整
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "causality_reasonableness": 90,
                "timeline_consistency": 85,
                "event_development_logic": 80,
                "conflict_escalation_reasonableness": 85,
                "foreshadowing_echo_completeness": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "因果关系处理得当",
                "时间线保持一致",
                "建议加强事件发展的逻辑性"
            ],
            "detailed_analysis": {{
                "causality_analysis": "因果关系分析...",
                "timeline_analysis": "时间线分析...",
                "event_analysis": "事件发展分析...",
                "conflict_analysis": "冲突发展分析...",
                "foreshadowing_analysis": "伏笔呼应分析..."
            }},
            "logic_issues": [
                "具体逻辑问题1",
                "具体逻辑问题2"
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估续写内容中情节的逻辑性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_plot_logic(self, storyline_content: Dict[str, Any], 
                                   knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线中的情节逻辑"""
        plot_lines = knowledge_base.get("plot_lines", {})
        last_chapter = knowledge_base.get("last_chapter_summary", {})
        
        prompt = f"""
        请评估以下续写故事线中情节的逻辑性：
        
        原文情节线：
        {self._format_plot_lines(plot_lines)}
        
        上一章结尾：
        {self._format_last_chapter(last_chapter)}
        
        续写故事线：
        {storyline_content}
        
        请评估故事线中情节逻辑的合理性和连贯性。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线中情节的逻辑性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_plot_logic(self, content: Dict[str, Any], 
                                 knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用情节逻辑评估"""
        prompt = f"""
        请评估以下续写内容中情节的逻辑性：
        
        原文情节信息：
        {self._format_plot_lines(knowledge_base.get("plot_lines", {}))}
        
        续写内容：
        {content}
        
        请进行综合情节逻辑评估。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容中情节的逻辑性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _validate_assessment_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证评估结果"""
        # 确保必要字段存在
        if "overall_score" not in result:
            # 尝试从dimensions计算总分
            dimensions = result.get("dimensions", {})
            if dimensions:
                total = sum(score for score in dimensions.values() if isinstance(score, (int, float)))
                count = len([score for score in dimensions.values() if isinstance(score, (int, float))])
                result["overall_score"] = total / count if count > 0 else 75
            else:
                result["overall_score"] = 75
        
        if "is_high_quality" not in result:
            result["is_high_quality"] = result.get("overall_score", 0) >= config.QUALITY_THRESHOLD
        
        if "suggestions" not in result:
            result["suggestions"] = []
        
        if "dimensions" not in result:
            result["dimensions"] = {}
        
        if "logic_issues" not in result:
            result["logic_issues"] = []
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
    
    def _format_plot_lines(self, plot_lines: Dict[str, Any]) -> str:
        """格式化故事线"""
        if not plot_lines:
            return "无故事线信息"
        
        formatted = "主线：\n"
        main_line = plot_lines.get("main_line", [])
        for i, line in enumerate(main_line, 1):
            formatted += f"  {i}. {line}\n"
        
        sub_lines = plot_lines.get("sub_lines", [])
        if sub_lines:
            formatted += "\n支线：\n"
            for i, line in enumerate(sub_lines, 1):
                formatted += f"  {i}. {line}\n"
        
        return formatted
    
    def _format_last_chapter(self, last_chapter: Dict[str, Any]) -> str:
        """格式化上一章信息"""
        if not last_chapter:
            return "无上一章信息"
        
        formatted = f"第{last_chapter.get('chapter_number', 0)}章：{last_chapter.get('title', '未知标题')}\n"
        formatted += f"概要：{last_chapter.get('summary', '无概要')}\n"
        
        key_events = last_chapter.get("key_events", [])
        if key_events:
            formatted += f"关键事件：{', '.join(key_events)}\n"
        
        foreshadowing = last_chapter.get("foreshadowing", [])
        if foreshadowing:
            formatted += f"伏笔：{', '.join(foreshadowing)}\n"
        
        next_hint = last_chapter.get("next_chapter_hint", "")
        if next_hint:
            formatted += f"下章预告：{next_hint}\n"
        
        return formatted
