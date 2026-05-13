"""
续写人物一致性专项评估智能体
专门评估续写内容中人物的一致性
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationCharacterConsistencyAssessor(BaseAgent):
    """续写人物一致性专项评估智能体"""
    
    def __init__(self):
        super().__init__("续写人物一致性专项评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容中人物的一致性"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行人物一致性评估
        assessment_result = self._assess_character_consistency(
            continuation_content, original_knowledge_base, content_type
        )
        
        return assessment_result
    
    def _assess_character_consistency(self, continuation_content: Dict[str, Any], 
                                    knowledge_base: Dict[str, Any], 
                                    content_type: str) -> Dict[str, Any]:
        """评估人物一致性"""
        try:
            if content_type == "story":
                return self._assess_story_character_consistency(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_character_consistency(continuation_content, knowledge_base)
            else:
                return self._assess_general_character_consistency(continuation_content, knowledge_base)
                
        except Exception as e:
            self.log(f"人物一致性评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_character_consistency(self, chapter_content: Dict[str, Any], 
                                          knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容中的人物一致性"""
        content = chapter_content.get("content", "")
        character_profiles = knowledge_base.get("character_profiles", {})
        
        # 构建评估提示
        prompt = f"""
        请专门评估以下续写章节中人物的一致性，重点关注以下维度：
        
        原文人物设定：
        {self._format_character_profiles(character_profiles)}
        
        续写章节内容：
        {content}
        
        请从以下维度评估人物一致性（每项0-100分）：
        1. 性格一致性：人物性格特征是否与原文设定一致
        2. 行为逻辑一致性：人物行为是否符合其性格和背景
        3. 语言风格一致性：人物语言风格是否与原文一致
        4. 关系发展合理性：人物关系发展是否合理
        5. 成长轨迹连贯性：人物成长是否符合发展轨迹
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "personality_consistency": 90,
                "behavior_logic_consistency": 85,
                "language_style_consistency": 80,
                "relationship_development_consistency": 85,
                "growth_trajectory_consistency": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "人物性格表现符合原设定",
                "行为逻辑合理",
                "建议加强语言风格统一性"
            ],
            "detailed_analysis": {{
                "personality_analysis": "人物性格表现分析...",
                "behavior_analysis": "行为逻辑分析...",
                "language_analysis": "语言风格分析...",
                "relationship_analysis": "关系发展分析...",
                "growth_analysis": "成长轨迹分析..."
            }},
            "character_specific_issues": {{
                "main_character": ["具体问题1", "具体问题2"],
                "supporting_characters": ["具体问题1", "具体问题2"]
            }}
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的人物设定编辑，擅长评估续写内容中人物的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_character_consistency(self, storyline_content: Dict[str, Any], 
                                              knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线中的人物一致性"""
        character_profiles = knowledge_base.get("character_profiles", {})
        
        prompt = f"""
        请评估以下续写故事线中人物设定的一致性：
        
        原文人物设定：
        {self._format_character_profiles(character_profiles)}
        
        续写故事线：
        {storyline_content}
        
        请评估故事线中人物设定的一致性和合理性。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线中人物设定的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_character_consistency(self, content: Dict[str, Any], 
                                            knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用人物一致性评估"""
        prompt = f"""
        请评估以下续写内容中人物的一致性：
        
        原文人物设定：
        {self._format_character_profiles(knowledge_base.get("character_profiles", {}))}
        
        续写内容：
        {content}
        
        请进行综合人物一致性评估。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容中人物的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _validate_assessment_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证评估结果，适配LLM的实际输出格式"""
        
        # 检查是否是LLM的实际输出格式（嵌套在evaluation对象内）
        if "evaluation" in result and isinstance(result["evaluation"], dict):
            print("🔧 检测到LLM嵌套格式，开始转换...")
            evaluation = result["evaluation"]
            
            # 提取并转换评分数据
            converted_result = {}
            
            # 1. 转换总分（从0-10分制转为0-100分制）
            score_fields = ["character_consistency", "overall_coherence", "consistency_score"]
            for field in score_fields:
                if field in evaluation and isinstance(evaluation[field], (int, float)):
                    base_score = evaluation[field]
                    converted_result["overall_score"] = int(base_score * 10)
                    print(f"✅ 转换总分: {base_score} -> {converted_result['overall_score']}")
                    break
            
            if "overall_score" not in converted_result:
                converted_result["overall_score"] = 75
            
            # 2. 转换维度评分
            dimensions = {}
            if "character_consistency" in evaluation:
                dimensions["character_consistency"] = int(evaluation["character_consistency"] * 10)
            
            converted_result["dimensions"] = dimensions
            
            # 3. 提取建议
            converted_result["suggestions"] = evaluation.get("suggestions", [])
            
            # 4. 构建详细分析
            detailed_analysis = {}
            for key in ["strengths", "weaknesses", "conclusion", "character_analysis"]:
                if key in evaluation:
                    detailed_analysis[key] = evaluation[key]
            
            converted_result["detailed_analysis"] = detailed_analysis
            
            # 使用转换后的结果
            result = converted_result
        
        # 确保必要字段存在（兜底逻辑）
        if "overall_score" not in result:
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
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
    
    def _format_character_profiles(self, character_profiles: Dict[str, Any]) -> str:
        """格式化人物档案"""
        if not character_profiles:
            return "无人物档案"
        
        formatted = ""
        main_character = character_profiles.get("main_character", {})
        if main_character:
            basic_info = main_character.get("basic_info", {})
            personality = main_character.get("personality", {})
            background = main_character.get("background", {})
            
            formatted += f"主角：{basic_info.get('name', '未知')}\n"
            formatted += f"  年龄：{basic_info.get('age', '未知')}\n"
            formatted += f"  职业：{basic_info.get('occupation', '未知')}\n"
            formatted += f"  性格：{personality.get('description', '未知')}\n"
            formatted += f"  核心欲望：{background.get('core_desire', '未知')}\n"
            formatted += f"  主要恐惧：{background.get('fear', '未知')}\n\n"
        
        supporting_characters = character_profiles.get("supporting_characters", [])
        for char in supporting_characters:
            basic_info = char.get("basic_info", {})
            formatted += f"配角：{basic_info.get('name', '未知')} ({char.get('role', '未知角色')})\n"
            formatted += f"  性格：{char.get('personality', '未知')}\n"
            formatted += f"  与主角关系：{char.get('relationship_with_main', '未知')}\n\n"
        
        return formatted
