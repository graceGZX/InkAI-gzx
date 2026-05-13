"""
续写人物一致性专项改进智能体
专门改进续写内容中人物的一致性问题
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationCharacterConsistencyImprover(BaseAgent):
    """续写人物一致性专项改进智能体"""
    
    def __init__(self):
        super().__init__("续写人物一致性专项改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """改进续写内容中人物的一致性问题"""
        continuation_content = input_data.get("continuation_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not continuation_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析人物一致性问题
        character_issues = self._analyze_character_consistency_issues(quality_assessment)
        
        # 执行人物一致性改进
        improved_content = self._improve_character_consistency(
            continuation_content, character_issues, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_content": improved_content,
            "character_issues": character_issues,
            "improvement_summary": self._generate_improvement_summary(character_issues)
        }
    
    def _analyze_character_consistency_issues(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析人物一致性问题"""
        try:
            character_issues = {
                "needs_improvement": False,
                "issue_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查人物一致性维度分数
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查性格一致性问题
            personality_score = dimensions.get("personality_consistency", 100)
            if personality_score < 85:
                character_issues["needs_improvement"] = True
                character_issues["issue_areas"].append("personality_consistency")
                character_issues["specific_issues"].append("人物性格特征与原文设定不一致")
                character_issues["improvement_strategies"].append("调整人物性格表现和描述")
            
            # 检查行为逻辑一致性问题
            behavior_score = dimensions.get("behavior_logic_consistency", 100)
            if behavior_score < 85:
                character_issues["needs_improvement"] = True
                character_issues["issue_areas"].append("behavior_logic_consistency")
                character_issues["specific_issues"].append("人物行为逻辑不合理")
                character_issues["improvement_strategies"].append("修正人物行为逻辑和动机")
            
            # 检查语言风格一致性问题
            language_score = dimensions.get("language_style_consistency", 100)
            if language_score < 80:
                character_issues["needs_improvement"] = True
                character_issues["issue_areas"].append("language_style_consistency")
                character_issues["specific_issues"].append("人物语言风格与原文不一致")
                character_issues["improvement_strategies"].append("统一人物语言风格和表达方式")
            
            # 检查关系发展合理性问题
            relationship_score = dimensions.get("relationship_development_consistency", 100)
            if relationship_score < 85:
                character_issues["needs_improvement"] = True
                character_issues["issue_areas"].append("relationship_development_consistency")
                character_issues["specific_issues"].append("人物关系发展不合理")
                character_issues["improvement_strategies"].append("调整人物关系发展逻辑")
            
            # 检查成长轨迹连贯性问题
            growth_score = dimensions.get("growth_trajectory_consistency", 100)
            if growth_score < 85:
                character_issues["needs_improvement"] = True
                character_issues["issue_areas"].append("growth_trajectory_consistency")
                character_issues["specific_issues"].append("人物成长轨迹不连贯")
                character_issues["improvement_strategies"].append("完善人物成长轨迹和发展")
            
            # 确定优先级
            if character_issues["needs_improvement"]:
                min_score = min([
                    personality_score, behavior_score, language_score, 
                    relationship_score, growth_score
                ])
                if min_score < 60:
                    character_issues["priority_level"] = "high"
                elif min_score < 80:
                    character_issues["priority_level"] = "medium"
                else:
                    character_issues["priority_level"] = "low"
            
            # 添加具体建议
            for suggestion in suggestions:
                if "人物" in suggestion or "性格" in suggestion or "行为" in suggestion:
                    character_issues["improvement_strategies"].append(suggestion)
            
            return character_issues
            
        except Exception as e:
            self.log(f"分析人物一致性问题失败: {e}")
            return {
                "needs_improvement": True,
                "issue_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["人物一致性问题需要改进"],
                "improvement_strategies": ["全面优化人物一致性"]
            }
    
    def _improve_character_consistency(self, continuation_content: Dict[str, Any], 
                                     character_issues: Dict[str, Any],
                                     knowledge_base: Dict[str, Any],
                                     user_requirements: str) -> Dict[str, Any]:
        """改进人物一致性"""
        try:
            if not character_issues.get("needs_improvement", False):
                return continuation_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下人物一致性问题，对续写内容进行针对性改进：
            
            原文人物设定：
            {self._format_character_profiles(knowledge_base)}
            
            用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前续写内容（需要改进）：
            {self._format_current_content(continuation_content)}
            
            人物一致性问题分析：
            {self._format_character_issues(character_issues)}
            
            改进要求：
            1. 根据问题分析进行针对性改进
            2. 确保人物性格与原文设定一致
            3. 修正人物行为逻辑和动机
            4. 统一人物语言风格和表达方式
            5. 调整人物关系发展逻辑
            6. 完善人物成长轨迹和发展
            7. 保持内容的自然流畅性
            
            请返回改进后的JSON格式内容：
            {{
                "improved_content": "改进后的内容",
                "character_improvements": {{
                    "personality_adjustments": "性格调整说明",
                    "behavior_corrections": "行为修正说明",
                    "language_unification": "语言统一说明",
                    "relationship_adjustments": "关系调整说明",
                    "growth_enhancement": "成长完善说明"
                }},
                "improvement_notes": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的人物设定编辑，擅长改进续写内容中人物的一致性问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和整合改进结果
            return self._integrate_improvements(continuation_content, result)
            
        except Exception as e:
            self.log(f"改进人物一致性失败: {e}")
            return self._create_fallback_content(continuation_content, character_issues)
    
    def _integrate_improvements(self, original_content: Dict[str, Any], 
                              improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合改进结果"""
        try:
            improved_content = original_content.copy()
            
            # 更新内容
            if "improved_content" in improvement_result:
                improved_content["content"] = improvement_result["improved_content"]
            
            # 添加改进记录
            improved_content["character_improvements"] = improvement_result.get("character_improvements", {})
            improved_content["improvement_notes"] = improvement_result.get("improvement_notes", "人物一致性已改进")
            
            # 确保内容不为空
            if not improved_content.get("content", "").strip():
                improved_content["content"] = original_content.get("content", "")
                improved_content["improvement_notes"] = "人物一致性改进失败，保持原内容"
            
            return improved_content
            
        except Exception as e:
            self.log(f"整合改进结果失败: {e}")
            return original_content
    
    def _create_fallback_content(self, original_content: Dict[str, Any], 
                               character_issues: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        fallback_content = original_content.copy()
        fallback_content["character_improvements"] = {
            "personality_adjustments": "改进功能暂时不可用",
            "behavior_corrections": "改进功能暂时不可用",
            "language_unification": "改进功能暂时不可用",
            "relationship_adjustments": "改进功能暂时不可用",
            "growth_enhancement": "改进功能暂时不可用"
        }
        fallback_content["improvement_notes"] = f"人物一致性问题：{', '.join(character_issues.get('specific_issues', []))}"
        
        return fallback_content
    
    def _generate_improvement_summary(self, character_issues: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "issue_areas": character_issues.get("issue_areas", []),
            "priority_level": character_issues.get("priority_level", "low"),
            "specific_issues": character_issues.get("specific_issues", []),
            "improvement_strategies": character_issues.get("improvement_strategies", []),
            "improvement_status": "completed" if character_issues.get("needs_improvement") else "not_needed"
        }
    
    def _format_character_profiles(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化人物档案"""
        character_profiles = knowledge_base.get("character_profiles", {})
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
    
    def _format_current_content(self, continuation_content: Dict[str, Any]) -> str:
        """格式化当前内容"""
        if isinstance(continuation_content, dict):
            content = continuation_content.get("content", "")
            title = continuation_content.get("title", "")
            return f"标题：{title}\n内容：{content}"
        else:
            return str(continuation_content)
    
    def _format_character_issues(self, character_issues: Dict[str, Any]) -> str:
        """格式化人物一致性问题"""
        formatted = f"""
        问题分析：
        - 需要改进: {character_issues.get('needs_improvement', False)}
        - 优先级: {character_issues.get('priority_level', 'low')}
        - 问题领域: {', '.join(character_issues.get('issue_areas', []))}
        - 具体问题: {', '.join(character_issues.get('specific_issues', []))}
        - 改进策略: {', '.join(character_issues.get('improvement_strategies', []))}
        """
        return formatted
