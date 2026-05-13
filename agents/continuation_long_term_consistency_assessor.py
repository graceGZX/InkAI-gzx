"""
续写长期连贯性专项评估智能体
专门评估续写内容的长期连贯性
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationLongTermConsistencyAssessor(BaseAgent):
    """续写长期连贯性专项评估智能体"""
    
    def __init__(self):
        super().__init__("续写长期连贯性专项评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容的长期连贯性"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行长期连贯性评估
        assessment_result = self._assess_long_term_consistency(
            continuation_content, original_knowledge_base, content_type
        )
        
        return assessment_result
    
    def _assess_long_term_consistency(self, continuation_content: Dict[str, Any], 
                                    knowledge_base: Dict[str, Any], 
                                    content_type: str) -> Dict[str, Any]:
        """评估长期连贯性"""
        try:
            if content_type == "story":
                return self._assess_story_long_term_consistency(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_long_term_consistency(continuation_content, knowledge_base)
            else:
                return self._assess_general_long_term_consistency(continuation_content, knowledge_base)
                
        except Exception as e:
            self.log(f"长期连贯性评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_long_term_consistency(self, chapter_content: Dict[str, Any], 
                                          knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容的长期连贯性"""
        content = chapter_content.get("content", "")
        plot_lines = knowledge_base.get("plot_lines", {})
        character_evolution = knowledge_base.get("character_evolution", {})
        foreshadowing_tracking = knowledge_base.get("foreshadowing_tracking", {})
        
        # 构建评估提示
        prompt = f"""
        请专门评估以下续写章节的长期连贯性，重点关注以下维度：
        
        整体故事线：
        {self._format_plot_lines(plot_lines)}
        
        人物发展轨迹：
        {self._format_character_evolution(character_evolution)}
        
        伏笔追踪：
        {self._format_foreshadowing_tracking(foreshadowing_tracking)}
        
        续写章节内容：
        {content}
        
        请从以下维度评估长期连贯性（每项0-100分）：
        1. 整体故事发展一致性：是否符合整体故事发展方向
        2. 人物成长轨迹连贯性：人物成长是否符合发展轨迹
        3. 主题发展一致性：主题发展是否与原文一致
        4. 伏笔线索完整性：伏笔线索是否完整连贯
        5. 故事节奏控制：故事节奏是否与整体节奏一致
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "overall_story_development_consistency": 90,
                "character_growth_trajectory_consistency": 85,
                "theme_development_consistency": 80,
                "foreshadowing_clue_completeness": 85,
                "story_rhythm_control": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "整体故事发展保持一致",
                "人物成长轨迹连贯",
                "建议加强主题发展的一致性"
            ],
            "detailed_analysis": {{
                "story_development_analysis": "整体故事发展分析...",
                "character_growth_analysis": "人物成长轨迹分析...",
                "theme_analysis": "主题发展分析...",
                "foreshadowing_analysis": "伏笔线索分析...",
                "rhythm_analysis": "故事节奏分析..."
            }},
            "long_term_consistency_issues": [
                "具体长期连贯性问题1",
                "具体长期连贯性问题2"
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的长期连贯性编辑，擅长评估续写内容的长期连贯性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_long_term_consistency(self, storyline_content: Dict[str, Any], 
                                              knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线的长期连贯性"""
        plot_lines = knowledge_base.get("plot_lines", {})
        character_evolution = knowledge_base.get("character_evolution", {})
        
        prompt = f"""
        请评估以下续写故事线的长期连贯性：
        
        整体故事线：
        {self._format_plot_lines(plot_lines)}
        
        人物发展轨迹：
        {self._format_character_evolution(character_evolution)}
        
        续写故事线：
        {storyline_content}
        
        请评估故事线的长期连贯性和合理性。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线的长期连贯性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_long_term_consistency(self, content: Dict[str, Any], 
                                            knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用长期连贯性评估"""
        plot_lines = knowledge_base.get("plot_lines", {})
        character_evolution = knowledge_base.get("character_evolution", {})
        
        prompt = f"""
        请评估以下续写内容的长期连贯性：
        
        整体故事线：
        {self._format_plot_lines(plot_lines)}
        
        人物发展轨迹：
        {self._format_character_evolution(character_evolution)}
        
        续写内容：
        {content}
        
        请进行综合长期连贯性评估。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容的长期连贯性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
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
    
    def _format_character_evolution(self, character_evolution: Dict[str, Any]) -> str:
        """格式化人物发展轨迹"""
        if not character_evolution:
            return "无人物发展轨迹"
        
        formatted = ""
        for char_name, evolution_list in character_evolution.items():
            formatted += f"{char_name}的发展轨迹：\n"
            for evolution in evolution_list[-3:]:  # 显示最近3次发展
                formatted += f"  第{evolution.get('chapter_number', 0)}章: {evolution.get('description', '')}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_foreshadowing_tracking(self, foreshadowing_tracking: Dict[str, Any]) -> str:
        """格式化伏笔追踪"""
        if not foreshadowing_tracking:
            return "无伏笔追踪"
        
        formatted = ""
        for foreshadowing_type, foreshadowing_list in foreshadowing_tracking.items():
            formatted += f"{foreshadowing_type}伏笔：\n"
            for foreshadowing in foreshadowing_list[-3:]:  # 显示最近3个伏笔
                formatted += f"  第{foreshadowing.get('chapter_number', 0)}章: {foreshadowing.get('content', '')}\n"
            formatted += "\n"
        
        return formatted
    
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
        
        if "long_term_consistency_issues" not in result:
            result["long_term_consistency_issues"] = []
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
