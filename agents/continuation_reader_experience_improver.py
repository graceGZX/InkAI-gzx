"""
续写读者体验专项改进智能体
专门改进续写内容的读者体验
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationReaderExperienceImprover(BaseAgent):
    """续写读者体验专项改进智能体"""
    
    def __init__(self):
        super().__init__("续写读者体验专项改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """改进续写内容的读者体验"""
        continuation_content = input_data.get("continuation_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not continuation_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析读者体验问题
        reader_issues = self._analyze_reader_experience_issues(quality_assessment)
        
        # 执行读者体验改进
        improved_content = self._improve_reader_experience(
            continuation_content, reader_issues, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_content": improved_content,
            "reader_issues": reader_issues,
            "improvement_summary": self._generate_improvement_summary(reader_issues)
        }
    
    def _analyze_reader_experience_issues(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析读者体验问题"""
        try:
            reader_issues = {
                "needs_improvement": False,
                "issue_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查读者体验维度分数
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查阅读流畅度问题
            fluency_score = dimensions.get("reading_fluency", 100)
            if fluency_score < 80:
                reader_issues["needs_improvement"] = True
                reader_issues["issue_areas"].append("reading_fluency")
                reader_issues["specific_issues"].append("内容不够流畅易读")
                reader_issues["improvement_strategies"].append("提升内容流畅度和可读性")
            
            # 检查情感共鸣度问题
            emotional_score = dimensions.get("emotional_resonance", 100)
            if emotional_score < 80:
                reader_issues["needs_improvement"] = True
                reader_issues["issue_areas"].append("emotional_resonance")
                reader_issues["specific_issues"].append("情感共鸣度不足")
                reader_issues["improvement_strategies"].append("增强情感表达和共鸣效果")
            
            # 检查悬念设置问题
            suspense_score = dimensions.get("suspense_setting", 100)
            if suspense_score < 80:
                reader_issues["needs_improvement"] = True
                reader_issues["issue_areas"].append("suspense_setting")
                reader_issues["specific_issues"].append("悬念设置不够吸引人")
                reader_issues["improvement_strategies"].append("优化悬念设置和吸引力")
            
            # 检查节奏控制问题
            rhythm_score = dimensions.get("rhythm_control", 100)
            if rhythm_score < 85:
                reader_issues["needs_improvement"] = True
                reader_issues["issue_areas"].append("rhythm_control")
                reader_issues["specific_issues"].append("节奏控制不够合适")
                reader_issues["improvement_strategies"].append("调整节奏控制，避免读者疲劳")
            
            # 检查期待值管理问题
            expectation_score = dimensions.get("expectation_management", 100)
            if expectation_score < 85:
                reader_issues["needs_improvement"] = True
                reader_issues["issue_areas"].append("expectation_management")
                reader_issues["specific_issues"].append("期待值管理不够合理")
                reader_issues["improvement_strategies"].append("优化期待值管理和满足度")
            
            # 确定优先级
            if reader_issues["needs_improvement"]:
                min_score = min([
                    fluency_score, emotional_score, suspense_score, 
                    rhythm_score, expectation_score
                ])
                if min_score < 60:
                    reader_issues["priority_level"] = "high"
                elif min_score < 80:
                    reader_issues["priority_level"] = "medium"
                else:
                    reader_issues["priority_level"] = "low"
            
            # 添加具体建议
            for suggestion in suggestions:
                if "读者" in suggestion or "体验" in suggestion or "流畅" in suggestion:
                    reader_issues["improvement_strategies"].append(suggestion)
            
            return reader_issues
            
        except Exception as e:
            self.log(f"分析读者体验问题失败: {e}")
            return {
                "needs_improvement": True,
                "issue_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["读者体验问题需要改进"],
                "improvement_strategies": ["全面优化读者体验"]
            }
    
    def _improve_reader_experience(self, continuation_content: Dict[str, Any], 
                                 reader_issues: Dict[str, Any],
                                 knowledge_base: Dict[str, Any],
                                 user_requirements: str) -> Dict[str, Any]:
        """改进读者体验"""
        try:
            if not reader_issues.get("needs_improvement", False):
                return continuation_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下读者体验问题，对续写内容进行针对性改进：
            
            故事基调：
            {self._format_story_tone(knowledge_base)}
            
            目标读者：
            {self._format_target_audience(knowledge_base)}
            
            用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前续写内容（需要改进）：
            {self._format_current_content(continuation_content)}
            
            读者体验问题分析：
            {self._format_reader_issues(reader_issues)}
            
            改进要求：
            1. 根据问题分析进行针对性改进
            2. 提升内容流畅度和可读性
            3. 增强情感表达和共鸣效果
            4. 优化悬念设置和吸引力
            5. 调整节奏控制，避免读者疲劳
            6. 优化期待值管理和满足度
            7. 保持内容的自然流畅性
            
            请返回改进后的JSON格式内容：
            {{
                "improved_content": "改进后的内容",
                "reader_experience_improvements": {{
                    "fluency_enhancement": "流畅度提升说明",
                    "emotional_enhancement": "情感共鸣增强说明",
                    "suspense_optimization": "悬念优化说明",
                    "rhythm_improvement": "节奏控制改进说明",
                    "expectation_management": "期待值管理优化说明"
                }},
                "improvement_notes": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的读者体验编辑，擅长改进续写内容的读者体验。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和整合改进结果
            return self._integrate_improvements(continuation_content, result)
            
        except Exception as e:
            self.log(f"改进读者体验失败: {e}")
            return self._create_fallback_content(continuation_content, reader_issues)
    
    def _integrate_improvements(self, original_content: Dict[str, Any], 
                              improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合改进结果"""
        try:
            improved_content = original_content.copy()
            
            # 更新内容
            if "improved_content" in improvement_result:
                improved_content["content"] = improvement_result["improved_content"]
            
            # 添加改进记录
            improved_content["reader_experience_improvements"] = improvement_result.get("reader_experience_improvements", {})
            improved_content["improvement_notes"] = improvement_result.get("improvement_notes", "读者体验已改进")
            
            # 确保内容不为空
            if not improved_content.get("content", "").strip():
                improved_content["content"] = original_content.get("content", "")
                improved_content["improvement_notes"] = "读者体验改进失败，保持原内容"
            
            return improved_content
            
        except Exception as e:
            self.log(f"整合改进结果失败: {e}")
            return original_content
    
    def _create_fallback_content(self, original_content: Dict[str, Any], 
                               reader_issues: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        fallback_content = original_content.copy()
        fallback_content["reader_experience_improvements"] = {
            "fluency_enhancement": "改进功能暂时不可用",
            "emotional_enhancement": "改进功能暂时不可用",
            "suspense_optimization": "改进功能暂时不可用",
            "rhythm_improvement": "改进功能暂时不可用",
            "expectation_management": "改进功能暂时不可用"
        }
        fallback_content["improvement_notes"] = f"读者体验问题：{', '.join(reader_issues.get('specific_issues', []))}"
        
        return fallback_content
    
    def _generate_improvement_summary(self, reader_issues: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "issue_areas": reader_issues.get("issue_areas", []),
            "priority_level": reader_issues.get("priority_level", "low"),
            "specific_issues": reader_issues.get("specific_issues", []),
            "improvement_strategies": reader_issues.get("improvement_strategies", []),
            "improvement_status": "completed" if reader_issues.get("needs_improvement") else "not_needed"
        }
    
    def _format_story_tone(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化故事基调"""
        story_tone = knowledge_base.get("story_tone", "")
        return f"故事基调：{story_tone}"
    
    def _format_target_audience(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化目标读者"""
        target_audience = knowledge_base.get("target_audience", "")
        return f"目标读者：{target_audience}"
    
    def _format_current_content(self, continuation_content: Dict[str, Any]) -> str:
        """格式化当前内容"""
        if isinstance(continuation_content, dict):
            content = continuation_content.get("content", "")
            title = continuation_content.get("title", "")
            return f"标题：{title}\n内容：{content}"
        else:
            return str(continuation_content)
    
    def _format_reader_issues(self, reader_issues: Dict[str, Any]) -> str:
        """格式化读者体验问题"""
        formatted = f"""
        问题分析：
        - 需要改进: {reader_issues.get('needs_improvement', False)}
        - 优先级: {reader_issues.get('priority_level', 'low')}
        - 问题领域: {', '.join(reader_issues.get('issue_areas', []))}
        - 具体问题: {', '.join(reader_issues.get('specific_issues', []))}
        - 改进策略: {', '.join(reader_issues.get('improvement_strategies', []))}
        """
        return formatted
