"""
续写读者体验专项评估智能体
专门评估续写内容的读者体验
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationReaderExperienceAssessor(BaseAgent):
    """续写读者体验专项评估智能体"""
    
    def __init__(self):
        super().__init__("续写读者体验专项评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容的读者体验"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行读者体验评估
        assessment_result = self._assess_reader_experience(
            continuation_content, original_knowledge_base, content_type
        )
        
        return assessment_result
    
    def _assess_reader_experience(self, continuation_content: Dict[str, Any], 
                                knowledge_base: Dict[str, Any], 
                                content_type: str) -> Dict[str, Any]:
        """评估读者体验"""
        try:
            if content_type == "story":
                return self._assess_story_reader_experience(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_reader_experience(continuation_content, knowledge_base)
            else:
                return self._assess_general_reader_experience(continuation_content, knowledge_base)
                
        except Exception as e:
            self.log(f"读者体验评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_reader_experience(self, chapter_content: Dict[str, Any], 
                                      knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容的读者体验"""
        content = chapter_content.get("content", "")
        story_tone = knowledge_base.get("story_tone", "")
        target_audience = knowledge_base.get("target_audience", "")
        
        # 构建评估提示
        prompt = f"""
        请专门评估以下续写章节的读者体验，重点关注以下维度：
        
        故事基调：
        {story_tone}
        
        目标读者：
        {target_audience}
        
        续写章节内容：
        {content}
        
        请从以下维度评估读者体验（每项0-100分）：
        1. 阅读流畅度：内容是否流畅易读，无阅读障碍
        2. 情感共鸣度：是否能引起读者的情感共鸣
        3. 悬念设置：悬念设置是否吸引读者继续阅读
        4. 节奏控制：节奏控制是否合适，不会让读者感到疲劳
        5. 期待值管理：是否满足读者的期待，同时创造新的期待
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "reading_fluency": 90,
                "emotional_resonance": 85,
                "suspense_setting": 80,
                "rhythm_control": 85,
                "expectation_management": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "阅读流畅度良好",
                "情感共鸣强烈",
                "建议加强悬念设置"
            ],
            "detailed_analysis": {{
                "fluency_analysis": "阅读流畅度分析...",
                "emotional_analysis": "情感共鸣分析...",
                "suspense_analysis": "悬念设置分析...",
                "rhythm_analysis": "节奏控制分析...",
                "expectation_analysis": "期待值管理分析..."
            }},
            "reader_experience_issues": [
                "具体读者体验问题1",
                "具体读者体验问题2"
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的读者体验编辑，擅长评估续写内容的读者体验。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_reader_experience(self, storyline_content: Dict[str, Any], 
                                          knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线的读者体验"""
        story_tone = knowledge_base.get("story_tone", "")
        target_audience = knowledge_base.get("target_audience", "")
        
        prompt = f"""
        请评估以下续写故事线的读者体验：
        
        故事基调：
        {story_tone}
        
        目标读者：
        {target_audience}
        
        续写故事线：
        {storyline_content}
        
        请评估故事线的读者体验和吸引力。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线的读者体验。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_reader_experience(self, content: Dict[str, Any], 
                                        knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用读者体验评估"""
        story_tone = knowledge_base.get("story_tone", "")
        target_audience = knowledge_base.get("target_audience", "")
        
        prompt = f"""
        请评估以下续写内容的读者体验：
        
        故事基调：
        {story_tone}
        
        目标读者：
        {target_audience}
        
        续写内容：
        {content}
        
        请进行综合读者体验评估。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容的读者体验。"},
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
        
        if "reader_experience_issues" not in result:
            result["reader_experience_issues"] = []
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
