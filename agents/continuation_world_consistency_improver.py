"""
续写世界观一致性专项改进智能体
专门改进续写内容中世界观的一致性问题
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationWorldConsistencyImprover(BaseAgent):
    """续写世界观一致性专项改进智能体"""
    
    def __init__(self):
        super().__init__("续写世界观一致性专项改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """改进续写内容中世界观的一致性问题"""
        continuation_content = input_data.get("continuation_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not continuation_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析世界观一致性问题
        world_issues = self._analyze_world_consistency_issues(quality_assessment)
        
        # 执行世界观一致性改进
        improved_content = self._improve_world_consistency(
            continuation_content, world_issues, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_content": improved_content,
            "world_issues": world_issues,
            "improvement_summary": self._generate_improvement_summary(world_issues)
        }
    
    def _analyze_world_consistency_issues(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析世界观一致性问题"""
        try:
            world_issues = {
                "needs_improvement": False,
                "issue_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查世界观一致性维度分数
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查世界规则一致性问题
            world_rules_score = dimensions.get("world_rules_consistency", 100)
            if world_rules_score < 90:
                world_issues["needs_improvement"] = True
                world_issues["issue_areas"].append("world_rules_consistency")
                world_issues["specific_issues"].append("世界规则设定与原文不符")
                world_issues["improvement_strategies"].append("修正世界规则设定和描述")
            
            # 检查社会制度一致性问题
            social_system_score = dimensions.get("social_system_consistency", 100)
            if social_system_score < 90:
                world_issues["needs_improvement"] = True
                world_issues["issue_areas"].append("social_system_consistency")
                world_issues["specific_issues"].append("社会制度描述与原文不一致")
                world_issues["improvement_strategies"].append("调整社会制度描述和设定")
            
            # 检查地理环境一致性问题
            geographical_score = dimensions.get("geographical_environment_consistency", 100)
            if geographical_score < 85:
                world_issues["needs_improvement"] = True
                world_issues["issue_areas"].append("geographical_environment_consistency")
                world_issues["specific_issues"].append("地理环境描述与原文不一致")
                world_issues["improvement_strategies"].append("修正地理环境描述和设定")
            
            # 检查历史背景一致性问题
            historical_score = dimensions.get("historical_background_consistency", 100)
            if historical_score < 90:
                world_issues["needs_improvement"] = True
                world_issues["issue_areas"].append("historical_background_consistency")
                world_issues["specific_issues"].append("历史背景与原文不一致")
                world_issues["improvement_strategies"].append("调整历史背景描述和设定")
            
            # 检查文化设定一致性问题
            cultural_score = dimensions.get("cultural_setting_consistency", 100)
            if cultural_score < 90:
                world_issues["needs_improvement"] = True
                world_issues["issue_areas"].append("cultural_setting_consistency")
                world_issues["specific_issues"].append("文化设定与原文不一致")
                world_issues["improvement_strategies"].append("修正文化设定和描述")
            
            # 确定优先级
            if world_issues["needs_improvement"]:
                min_score = min([
                    world_rules_score, social_system_score, geographical_score, 
                    historical_score, cultural_score
                ])
                if min_score < 70:
                    world_issues["priority_level"] = "high"
                elif min_score < 85:
                    world_issues["priority_level"] = "medium"
                else:
                    world_issues["priority_level"] = "low"
            
            # 添加具体建议
            for suggestion in suggestions:
                if "世界" in suggestion or "设定" in suggestion or "环境" in suggestion:
                    world_issues["improvement_strategies"].append(suggestion)
            
            return world_issues
            
        except Exception as e:
            self.log(f"分析世界观一致性问题失败: {e}")
            return {
                "needs_improvement": True,
                "issue_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["世界观一致性问题需要改进"],
                "improvement_strategies": ["全面优化世界观一致性"]
            }
    
    def _improve_world_consistency(self, continuation_content: Dict[str, Any], 
                                 world_issues: Dict[str, Any],
                                 knowledge_base: Dict[str, Any],
                                 user_requirements: str) -> Dict[str, Any]:
        """改进世界观一致性"""
        try:
            if not world_issues.get("needs_improvement", False):
                return continuation_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下世界观一致性问题，对续写内容进行针对性改进：
            
            原文世界观设定：
            {self._format_world_setting(knowledge_base)}
            
            故事基调：
            {self._format_story_tone(knowledge_base)}
            
            用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前续写内容（需要改进）：
            {self._format_current_content(continuation_content)}
            
            世界观一致性问题分析：
            {self._format_world_issues(world_issues)}
            
            改进要求：
            1. 根据问题分析进行针对性改进
            2. 修正世界规则设定和描述
            3. 调整社会制度描述和设定
            4. 修正地理环境描述和设定
            5. 调整历史背景描述和设定
            6. 修正文化设定和描述
            7. 保持内容的自然流畅性
            
            请返回改进后的JSON格式内容：
            {{
                "improved_content": "改进后的内容",
                "world_improvements": {{
                    "world_rules_corrections": "世界规则修正说明",
                    "social_system_adjustments": "社会制度调整说明",
                    "geographical_corrections": "地理环境修正说明",
                    "historical_adjustments": "历史背景调整说明",
                    "cultural_corrections": "文化设定修正说明"
                }},
                "improvement_notes": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的世界观设定编辑，擅长改进续写内容中世界观的一致性问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和整合改进结果
            return self._integrate_improvements(continuation_content, result)
            
        except Exception as e:
            self.log(f"改进世界观一致性失败: {e}")
            return self._create_fallback_content(continuation_content, world_issues)
    
    def _integrate_improvements(self, original_content: Dict[str, Any], 
                              improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合改进结果"""
        try:
            improved_content = original_content.copy()
            
            # 更新内容
            if "improved_content" in improvement_result:
                improved_content["content"] = improvement_result["improved_content"]
            
            # 添加改进记录
            improved_content["world_improvements"] = improvement_result.get("world_improvements", {})
            improved_content["improvement_notes"] = improvement_result.get("improvement_notes", "世界观一致性已改进")
            
            # 确保内容不为空
            if not improved_content.get("content", "").strip():
                improved_content["content"] = original_content.get("content", "")
                improved_content["improvement_notes"] = "世界观一致性改进失败，保持原内容"
            
            return improved_content
            
        except Exception as e:
            self.log(f"整合改进结果失败: {e}")
            return original_content
    
    def _create_fallback_content(self, original_content: Dict[str, Any], 
                               world_issues: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        fallback_content = original_content.copy()
        fallback_content["world_improvements"] = {
            "world_rules_corrections": "改进功能暂时不可用",
            "social_system_adjustments": "改进功能暂时不可用",
            "geographical_corrections": "改进功能暂时不可用",
            "historical_adjustments": "改进功能暂时不可用",
            "cultural_corrections": "改进功能暂时不可用"
        }
        fallback_content["improvement_notes"] = f"世界观一致性问题：{', '.join(world_issues.get('specific_issues', []))}"
        
        return fallback_content
    
    def _generate_improvement_summary(self, world_issues: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "issue_areas": world_issues.get("issue_areas", []),
            "priority_level": world_issues.get("priority_level", "low"),
            "specific_issues": world_issues.get("specific_issues", []),
            "improvement_strategies": world_issues.get("improvement_strategies", []),
            "improvement_status": "completed" if world_issues.get("needs_improvement") else "not_needed"
        }
    
    def _format_world_setting(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化世界观设定"""
        world_setting = knowledge_base.get("world_setting", "")
        if isinstance(world_setting, dict):
            return f"世界观：{world_setting.get('description', '未知')}"
        else:
            return f"世界观：{world_setting}"
    
    def _format_story_tone(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化故事基调"""
        story_tone = knowledge_base.get("story_tone", "")
        return f"故事基调：{story_tone}"
    
    def _format_current_content(self, continuation_content: Dict[str, Any]) -> str:
        """格式化当前内容"""
        if isinstance(continuation_content, dict):
            content = continuation_content.get("content", "")
            title = continuation_content.get("title", "")
            return f"标题：{title}\n内容：{content}"
        else:
            return str(continuation_content)
    
    def _format_world_issues(self, world_issues: Dict[str, Any]) -> str:
        """格式化世界观一致性问题"""
        formatted = f"""
        问题分析：
        - 需要改进: {world_issues.get('needs_improvement', False)}
        - 优先级: {world_issues.get('priority_level', 'low')}
        - 问题领域: {', '.join(world_issues.get('issue_areas', []))}
        - 具体问题: {', '.join(world_issues.get('specific_issues', []))}
        - 改进策略: {', '.join(world_issues.get('improvement_strategies', []))}
        """
        return formatted
