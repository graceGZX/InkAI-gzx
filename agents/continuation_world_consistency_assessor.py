"""
续写世界观一致性专项评估智能体
专门评估续写内容中世界观的一致性
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationWorldConsistencyAssessor(BaseAgent):
    """续写世界观一致性专项评估智能体"""
    
    def __init__(self):
        super().__init__("续写世界观一致性专项评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容中世界观的一致性"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行世界观一致性评估
        assessment_result = self._assess_world_consistency(
            continuation_content, original_knowledge_base, content_type
        )
        
        return assessment_result
    
    def _assess_world_consistency(self, continuation_content: Dict[str, Any], 
                                knowledge_base: Dict[str, Any], 
                                content_type: str) -> Dict[str, Any]:
        """评估世界观一致性"""
        try:
            if content_type == "story":
                return self._assess_story_world_consistency(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_world_consistency(continuation_content, knowledge_base)
            else:
                return self._assess_general_world_consistency(continuation_content, knowledge_base)
                
        except Exception as e:
            self.log(f"世界观一致性评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_world_consistency(self, chapter_content: Dict[str, Any], 
                                      knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容中的世界观一致性"""
        content = chapter_content.get("content", "")
        world_setting = knowledge_base.get("world_setting", "")
        story_tone = knowledge_base.get("story_tone", "")
        
        # 构建评估提示
        prompt = f"""
        请专门评估以下续写章节中世界观的一致性，重点关注以下维度：
        
        原文世界观设定：
        {world_setting}
        
        故事基调：
        {story_tone}
        
        续写章节内容：
        {content}
        
        请从以下维度评估世界观一致性（每项0-100分）：
        1. 世界规则一致性：是否符合原文的世界规则和设定
        2. 社会制度一致性：社会制度描述是否与原文一致
        3. 地理环境一致性：地理环境描述是否与原文一致
        4. 历史背景一致性：历史背景是否与原文一致
        5. 文化设定一致性：文化设定是否与原文一致
        
        请返回JSON格式：
        {{
            "overall_score": 90,
            "dimensions": {{
                "world_rules_consistency": 95,
                "social_system_consistency": 90,
                "geographical_environment_consistency": 85,
                "historical_background_consistency": 90,
                "cultural_setting_consistency": 90
            }},
            "is_high_quality": true,
            "suggestions": [
                "世界规则设定保持一致",
                "社会制度描述准确",
                "建议加强地理环境描述的一致性"
            ],
            "detailed_analysis": {{
                "world_rules_analysis": "世界规则一致性分析...",
                "social_system_analysis": "社会制度一致性分析...",
                "geographical_analysis": "地理环境一致性分析...",
                "historical_analysis": "历史背景一致性分析...",
                "cultural_analysis": "文化设定一致性分析..."
            }},
            "world_consistency_issues": [
                "具体世界观问题1",
                "具体世界观问题2"
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的世界观设定编辑，擅长评估续写内容中世界观的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_world_consistency(self, storyline_content: Dict[str, Any], 
                                          knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线中的世界观一致性"""
        world_setting = knowledge_base.get("world_setting", "")
        story_tone = knowledge_base.get("story_tone", "")
        
        prompt = f"""
        请评估以下续写故事线中世界观设定的一致性：
        
        原文世界观设定：
        {world_setting}
        
        故事基调：
        {story_tone}
        
        续写故事线：
        {storyline_content}
        
        请评估故事线中世界观设定的一致性和合理性。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线中世界观设定的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_world_consistency(self, content: Dict[str, Any], 
                                        knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用世界观一致性评估"""
        world_setting = knowledge_base.get("world_setting", "")
        story_tone = knowledge_base.get("story_tone", "")
        
        prompt = f"""
        请评估以下续写内容中世界观的一致性：
        
        原文世界观设定：
        {world_setting}
        
        故事基调：
        {story_tone}
        
        续写内容：
        {content}
        
        请进行综合世界观一致性评估。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容中世界观的一致性。"},
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
        
        if "world_consistency_issues" not in result:
            result["world_consistency_issues"] = []
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
