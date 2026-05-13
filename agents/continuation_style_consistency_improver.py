"""
续写语言风格专项改进智能体
专门改进续写内容中语言风格的一致性问题
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationStyleConsistencyImprover(BaseAgent):
    """续写语言风格专项改进智能体"""
    
    def __init__(self):
        super().__init__("续写语言风格专项改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """改进续写内容中语言风格的一致性问题"""
        continuation_content = input_data.get("continuation_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not continuation_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析语言风格一致性问题
        style_issues = self._analyze_style_consistency_issues(quality_assessment)
        
        # 执行语言风格一致性改进
        improved_content = self._improve_style_consistency(
            continuation_content, style_issues, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_content": improved_content,
            "style_issues": style_issues,
            "improvement_summary": self._generate_improvement_summary(style_issues)
        }
    
    def _analyze_style_consistency_issues(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析语言风格一致性问题"""
        try:
            style_issues = {
                "needs_improvement": False,
                "issue_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查语言风格一致性维度分数
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查语言风格一致性问题
            language_style_score = dimensions.get("language_style_consistency", 100)
            if language_style_score < 80:
                style_issues["needs_improvement"] = True
                style_issues["issue_areas"].append("language_style_consistency")
                style_issues["specific_issues"].append("语言风格与原文不一致")
                style_issues["improvement_strategies"].append("统一语言风格和表达方式")
            
            # 检查文笔质量问题
            writing_quality_score = dimensions.get("writing_quality", 100)
            if writing_quality_score < 80:
                style_issues["needs_improvement"] = True
                style_issues["issue_areas"].append("writing_quality")
                style_issues["specific_issues"].append("文笔质量未达到原文水平")
                style_issues["improvement_strategies"].append("提升文笔质量和表达水平")
            
            # 检查修辞手法运用问题
            rhetorical_score = dimensions.get("rhetorical_device_usage", 100)
            if rhetorical_score < 80:
                style_issues["needs_improvement"] = True
                style_issues["issue_areas"].append("rhetorical_device_usage")
                style_issues["specific_issues"].append("修辞手法运用与原文不一致")
                style_issues["improvement_strategies"].append("调整修辞手法运用和风格")
            
            # 检查节奏感控制问题
            rhythm_score = dimensions.get("rhythm_control", 100)
            if rhythm_score < 85:
                style_issues["needs_improvement"] = True
                style_issues["issue_areas"].append("rhythm_control")
                style_issues["specific_issues"].append("节奏感控制与原文不一致")
                style_issues["improvement_strategies"].append("调整节奏感控制和表达节奏")
            
            # 检查情感表达方式问题
            emotional_score = dimensions.get("emotional_expression_consistency", 100)
            if emotional_score < 85:
                style_issues["needs_improvement"] = True
                style_issues["issue_areas"].append("emotional_expression_consistency")
                style_issues["specific_issues"].append("情感表达方式与原文不一致")
                style_issues["improvement_strategies"].append("统一情感表达方式和风格")
            
            # 确定优先级
            if style_issues["needs_improvement"]:
                min_score = min([
                    language_style_score, writing_quality_score, rhetorical_score, 
                    rhythm_score, emotional_score
                ])
                if min_score < 60:
                    style_issues["priority_level"] = "high"
                elif min_score < 80:
                    style_issues["priority_level"] = "medium"
                else:
                    style_issues["priority_level"] = "low"
            
            # 添加具体建议
            for suggestion in suggestions:
                if "语言" in suggestion or "风格" in suggestion or "文笔" in suggestion:
                    style_issues["improvement_strategies"].append(suggestion)
            
            return style_issues
            
        except Exception as e:
            self.log(f"分析语言风格一致性问题失败: {e}")
            return {
                "needs_improvement": True,
                "issue_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["语言风格一致性问题需要改进"],
                "improvement_strategies": ["全面优化语言风格一致性"]
            }
    
    def _improve_style_consistency(self, continuation_content: Dict[str, Any], 
                                 style_issues: Dict[str, Any],
                                 knowledge_base: Dict[str, Any],
                                 user_requirements: str) -> Dict[str, Any]:
        """改进语言风格一致性"""
        try:
            if not style_issues.get("needs_improvement", False):
                return continuation_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下语言风格一致性问题，对续写内容进行针对性改进：
            
            原文故事基调：
            {self._format_story_tone(knowledge_base)}
            
            原文语言风格样本：
            {self._format_original_style_sample(knowledge_base)}
            
            用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前续写内容（需要改进）：
            {self._format_current_content(continuation_content)}
            
            语言风格一致性问题分析：
            {self._format_style_issues(style_issues)}
            
            改进要求：
            1. 根据问题分析进行针对性改进
            2. 统一语言风格和表达方式
            3. 提升文笔质量和表达水平
            4. 调整修辞手法运用和风格
            5. 调整节奏感控制和表达节奏
            6. 统一情感表达方式和风格
            7. 保持内容的自然流畅性
            
            请返回改进后的JSON格式内容：
            {{
                "improved_content": "改进后的内容",
                "style_improvements": {{
                    "language_style_unification": "语言风格统一说明",
                    "writing_quality_enhancement": "文笔质量提升说明",
                    "rhetorical_adjustments": "修辞手法调整说明",
                    "rhythm_control_improvement": "节奏感控制改进说明",
                    "emotional_expression_unification": "情感表达统一说明"
                }},
                "improvement_notes": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的语言风格编辑，擅长改进续写内容中语言风格的一致性问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和整合改进结果
            return self._integrate_improvements(continuation_content, result)
            
        except Exception as e:
            self.log(f"改进语言风格一致性失败: {e}")
            return self._create_fallback_content(continuation_content, style_issues)
    
    def _integrate_improvements(self, original_content: Dict[str, Any], 
                              improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合改进结果"""
        try:
            improved_content = original_content.copy()
            
            # 更新内容
            if "improved_content" in improvement_result:
                improved_content["content"] = improvement_result["improved_content"]
            
            # 添加改进记录
            improved_content["style_improvements"] = improvement_result.get("style_improvements", {})
            improved_content["improvement_notes"] = improvement_result.get("improvement_notes", "语言风格一致性已改进")
            
            # 确保内容不为空
            if not improved_content.get("content", "").strip():
                improved_content["content"] = original_content.get("content", "")
                improved_content["improvement_notes"] = "语言风格一致性改进失败，保持原内容"
            
            return improved_content
            
        except Exception as e:
            self.log(f"整合改进结果失败: {e}")
            return original_content
    
    def _create_fallback_content(self, original_content: Dict[str, Any], 
                               style_issues: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        fallback_content = original_content.copy()
        fallback_content["style_improvements"] = {
            "language_style_unification": "改进功能暂时不可用",
            "writing_quality_enhancement": "改进功能暂时不可用",
            "rhetorical_adjustments": "改进功能暂时不可用",
            "rhythm_control_improvement": "改进功能暂时不可用",
            "emotional_expression_unification": "改进功能暂时不可用"
        }
        fallback_content["improvement_notes"] = f"语言风格一致性问题：{', '.join(style_issues.get('specific_issues', []))}"
        
        return fallback_content
    
    def _generate_improvement_summary(self, style_issues: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "issue_areas": style_issues.get("issue_areas", []),
            "priority_level": style_issues.get("priority_level", "low"),
            "specific_issues": style_issues.get("specific_issues", []),
            "improvement_strategies": style_issues.get("improvement_strategies", []),
            "improvement_status": "completed" if style_issues.get("needs_improvement") else "not_needed"
        }
    
    def _format_story_tone(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化故事基调"""
        story_tone = knowledge_base.get("story_tone", "")
        return f"故事基调：{story_tone}"
    
    def _format_original_style_sample(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化原文风格样本"""
        original_chapters = knowledge_base.get("chapters", [])
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
    
    def _format_current_content(self, continuation_content: Dict[str, Any]) -> str:
        """格式化当前内容"""
        if isinstance(continuation_content, dict):
            content = continuation_content.get("content", "")
            title = continuation_content.get("title", "")
            return f"标题：{title}\n内容：{content}"
        else:
            return str(continuation_content)
    
    def _format_style_issues(self, style_issues: Dict[str, Any]) -> str:
        """格式化语言风格一致性问题"""
        formatted = f"""
        问题分析：
        - 需要改进: {style_issues.get('needs_improvement', False)}
        - 优先级: {style_issues.get('priority_level', 'low')}
        - 问题领域: {', '.join(style_issues.get('issue_areas', []))}
        - 具体问题: {', '.join(style_issues.get('specific_issues', []))}
        - 改进策略: {', '.join(style_issues.get('improvement_strategies', []))}
        """
        return formatted
