"""
续写语言风格专项评估智能体
专门评估续写内容中语言风格的一致性
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationStyleConsistencyAssessor(BaseAgent):
    """续写语言风格专项评估智能体"""
    
    def __init__(self):
        super().__init__("续写语言风格专项评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容中语言风格的一致性"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行语言风格一致性评估
        assessment_result = self._assess_style_consistency(
            continuation_content, original_knowledge_base, content_type
        )
        
        return assessment_result
    
    def _assess_style_consistency(self, continuation_content: Dict[str, Any], 
                                knowledge_base: Dict[str, Any], 
                                content_type: str) -> Dict[str, Any]:
        """评估语言风格一致性"""
        try:
            if content_type == "story":
                return self._assess_story_style_consistency(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_style_consistency(continuation_content, knowledge_base)
            else:
                return self._assess_general_style_consistency(continuation_content, knowledge_base)
                
        except Exception as e:
            self.log(f"语言风格一致性评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_style_consistency(self, chapter_content: Dict[str, Any], 
                                      knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容中的语言风格一致性"""
        content = chapter_content.get("content", "")
        story_tone = knowledge_base.get("story_tone", "")
        original_chapters = knowledge_base.get("chapters", [])
        
        # 获取原文样本
        original_sample = self._get_original_style_sample(original_chapters)
        
        # 构建评估提示
        prompt = f"""
        请专门评估以下续写章节中语言风格的一致性，重点关注以下维度：
        
        原文故事基调：
        {story_tone}
        
        原文语言风格样本：
        {original_sample}
        
        续写章节内容：
        {content}
        
        请从以下维度评估语言风格一致性（每项0-100分）：
        1. 语言风格一致性：语言风格是否与原文保持一致
        2. 文笔质量：文笔质量是否达到原文水平
        3. 修辞手法运用：修辞手法的运用是否与原文一致
        4. 节奏感控制：节奏感控制是否与原文一致
        5. 情感表达方式：情感表达方式是否与原文一致
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "language_style_consistency": 90,
                "writing_quality": 85,
                "rhetorical_device_usage": 80,
                "rhythm_control": 85,
                "emotional_expression_consistency": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "语言风格与原文保持一致",
                "文笔质量良好",
                "建议加强修辞手法的运用"
            ],
            "detailed_analysis": {{
                "language_style_analysis": "语言风格一致性分析...",
                "writing_quality_analysis": "文笔质量分析...",
                "rhetorical_analysis": "修辞手法分析...",
                "rhythm_analysis": "节奏感分析...",
                "emotional_analysis": "情感表达分析..."
            }},
            "style_issues": [
                "具体风格问题1",
                "具体风格问题2"
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的语言风格编辑，擅长评估续写内容中语言风格的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_style_consistency(self, storyline_content: Dict[str, Any], 
                                          knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线中的语言风格一致性"""
        story_tone = knowledge_base.get("story_tone", "")
        
        prompt = f"""
        请评估以下续写故事线中语言风格的一致性：
        
        原文故事基调：
        {story_tone}
        
        续写故事线：
        {storyline_content}
        
        请评估故事线中语言风格的一致性和合理性。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线中语言风格的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_style_consistency(self, content: Dict[str, Any], 
                                        knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用语言风格一致性评估"""
        story_tone = knowledge_base.get("story_tone", "")
        
        prompt = f"""
        请评估以下续写内容中语言风格的一致性：
        
        原文故事基调：
        {story_tone}
        
        续写内容：
        {content}
        
        请进行综合语言风格一致性评估。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容中语言风格的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _get_original_style_sample(self, original_chapters: List[Dict[str, Any]]) -> str:
        """获取原文语言风格样本"""
        try:
            if not original_chapters:
                return "无原文样本"
            
            # 选择最近的几章作为样本
            sample_chapters = original_chapters[-3:] if len(original_chapters) >= 3 else original_chapters
            
            sample_text = ""
            for chapter in sample_chapters:
                content = chapter.get("content", "")
                if content:
                    # 取前500字作为样本
                    sample_text += content[:500] + "\n\n"
            
            return sample_text if sample_text else "无原文样本"
            
        except Exception as e:
            self.log(f"获取原文风格样本失败: {e}")
            return "无原文样本"
    
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
        
        if "style_issues" not in result:
            result["style_issues"] = []
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
