"""
续写长期连贯性专项改进智能体
专门改进续写内容的长期连贯性问题
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationLongTermConsistencyImprover(BaseAgent):
    """续写长期连贯性专项改进智能体"""
    
    def __init__(self):
        super().__init__("续写长期连贯性专项改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """改进续写内容的长期连贯性问题"""
        continuation_content = input_data.get("continuation_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not continuation_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析长期连贯性问题
        long_term_issues = self._analyze_long_term_consistency_issues(quality_assessment)
        
        # 执行长期连贯性改进
        improved_content = self._improve_long_term_consistency(
            continuation_content, long_term_issues, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_content": improved_content,
            "long_term_issues": long_term_issues,
            "improvement_summary": self._generate_improvement_summary(long_term_issues)
        }
    
    def _analyze_long_term_consistency_issues(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析长期连贯性问题"""
        try:
            long_term_issues = {
                "needs_improvement": False,
                "issue_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查长期连贯性维度分数
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查整体故事发展一致性问题
            story_development_score = dimensions.get("overall_story_development_consistency", 100)
            if story_development_score < 80:
                long_term_issues["needs_improvement"] = True
                long_term_issues["issue_areas"].append("overall_story_development_consistency")
                long_term_issues["specific_issues"].append("整体故事发展与原文不一致")
                long_term_issues["improvement_strategies"].append("调整整体故事发展方向和节奏")
            
            # 检查人物成长轨迹连贯性问题
            character_growth_score = dimensions.get("character_growth_trajectory_consistency", 100)
            if character_growth_score < 85:
                long_term_issues["needs_improvement"] = True
                long_term_issues["issue_areas"].append("character_growth_trajectory_consistency")
                long_term_issues["specific_issues"].append("人物成长轨迹不连贯")
                long_term_issues["improvement_strategies"].append("完善人物成长轨迹和发展")
            
            # 检查主题发展一致性问题
            theme_development_score = dimensions.get("theme_development_consistency", 100)
            if theme_development_score < 80:
                long_term_issues["needs_improvement"] = True
                long_term_issues["issue_areas"].append("theme_development_consistency")
                long_term_issues["specific_issues"].append("主题发展与原文不一致")
                long_term_issues["improvement_strategies"].append("调整主题发展方向和表达")
            
            # 检查伏笔线索完整性问题
            foreshadowing_score = dimensions.get("foreshadowing_clue_completeness", 100)
            if foreshadowing_score < 85:
                long_term_issues["needs_improvement"] = True
                long_term_issues["issue_areas"].append("foreshadowing_clue_completeness")
                long_term_issues["specific_issues"].append("伏笔线索不完整")
                long_term_issues["improvement_strategies"].append("完善伏笔线索和呼应机制")
            
            # 检查故事节奏控制问题
            story_rhythm_score = dimensions.get("story_rhythm_control", 100)
            if story_rhythm_score < 85:
                long_term_issues["needs_improvement"] = True
                long_term_issues["issue_areas"].append("story_rhythm_control")
                long_term_issues["specific_issues"].append("故事节奏与整体节奏不一致")
                long_term_issues["improvement_strategies"].append("调整故事节奏和整体协调性")
            
            # 确定优先级
            if long_term_issues["needs_improvement"]:
                min_score = min([
                    story_development_score, character_growth_score, theme_development_score, 
                    foreshadowing_score, story_rhythm_score
                ])
                if min_score < 60:
                    long_term_issues["priority_level"] = "high"
                elif min_score < 80:
                    long_term_issues["priority_level"] = "medium"
                else:
                    long_term_issues["priority_level"] = "low"
            
            # 添加具体建议
            for suggestion in suggestions:
                if "长期" in suggestion or "连贯" in suggestion or "发展" in suggestion:
                    long_term_issues["improvement_strategies"].append(suggestion)
            
            return long_term_issues
            
        except Exception as e:
            self.log(f"分析长期连贯性问题失败: {e}")
            return {
                "needs_improvement": True,
                "issue_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["长期连贯性问题需要改进"],
                "improvement_strategies": ["全面优化长期连贯性"]
            }
    
    def _improve_long_term_consistency(self, continuation_content: Dict[str, Any], 
                                     long_term_issues: Dict[str, Any],
                                     knowledge_base: Dict[str, Any],
                                     user_requirements: str) -> Dict[str, Any]:
        """改进长期连贯性"""
        try:
            if not long_term_issues.get("needs_improvement", False):
                return continuation_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下长期连贯性问题，对续写内容进行针对性改进：
            
            整体故事线：
            {self._format_plot_lines(knowledge_base)}
            
            人物发展轨迹：
            {self._format_character_evolution(knowledge_base)}
            
            伏笔追踪：
            {self._format_foreshadowing_tracking(knowledge_base)}
            
            用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前续写内容（需要改进）：
            {self._format_current_content(continuation_content)}
            
            长期连贯性问题分析：
            {self._format_long_term_issues(long_term_issues)}
            
            改进要求：
            1. 根据问题分析进行针对性改进
            2. 调整整体故事发展方向和节奏
            3. 完善人物成长轨迹和发展
            4. 调整主题发展方向和表达
            5. 完善伏笔线索和呼应机制
            6. 调整故事节奏和整体协调性
            7. 保持内容的自然流畅性
            
            请返回改进后的JSON格式内容：
            {{
                "improved_content": "改进后的内容",
                "long_term_improvements": {{
                    "story_development_adjustment": "故事发展调整说明",
                    "character_growth_enhancement": "人物成长完善说明",
                    "theme_development_adjustment": "主题发展调整说明",
                    "foreshadowing_enhancement": "伏笔完善说明",
                    "rhythm_coordination": "节奏协调说明"
                }},
                "improvement_notes": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的长期连贯性编辑，擅长改进续写内容的长期连贯性问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和整合改进结果
            return self._integrate_improvements(continuation_content, result)
            
        except Exception as e:
            self.log(f"改进长期连贯性失败: {e}")
            return self._create_fallback_content(continuation_content, long_term_issues)
    
    def _integrate_improvements(self, original_content: Dict[str, Any], 
                              improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合改进结果"""
        try:
            improved_content = original_content.copy()
            
            # 更新内容
            if "improved_content" in improvement_result:
                improved_content["content"] = improvement_result["improved_content"]
            
            # 添加改进记录
            improved_content["long_term_improvements"] = improvement_result.get("long_term_improvements", {})
            improved_content["improvement_notes"] = improvement_result.get("improvement_notes", "长期连贯性已改进")
            
            # 确保内容不为空
            if not improved_content.get("content", "").strip():
                improved_content["content"] = original_content.get("content", "")
                improved_content["improvement_notes"] = "长期连贯性改进失败，保持原内容"
            
            return improved_content
            
        except Exception as e:
            self.log(f"整合改进结果失败: {e}")
            return original_content
    
    def _create_fallback_content(self, original_content: Dict[str, Any], 
                               long_term_issues: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        fallback_content = original_content.copy()
        fallback_content["long_term_improvements"] = {
            "story_development_adjustment": "改进功能暂时不可用",
            "character_growth_enhancement": "改进功能暂时不可用",
            "theme_development_adjustment": "改进功能暂时不可用",
            "foreshadowing_enhancement": "改进功能暂时不可用",
            "rhythm_coordination": "改进功能暂时不可用"
        }
        fallback_content["improvement_notes"] = f"长期连贯性问题：{', '.join(long_term_issues.get('specific_issues', []))}"
        
        return fallback_content
    
    def _generate_improvement_summary(self, long_term_issues: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "issue_areas": long_term_issues.get("issue_areas", []),
            "priority_level": long_term_issues.get("priority_level", "low"),
            "specific_issues": long_term_issues.get("specific_issues", []),
            "improvement_strategies": long_term_issues.get("improvement_strategies", []),
            "improvement_status": "completed" if long_term_issues.get("needs_improvement") else "not_needed"
        }
    
    def _format_plot_lines(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化故事线"""
        plot_lines = knowledge_base.get("plot_lines", {})
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
    
    def _format_character_evolution(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化人物发展轨迹"""
        character_evolution = knowledge_base.get("character_evolution", {})
        if not character_evolution:
            return "无人物发展轨迹"
        
        formatted = ""
        for char_name, evolution_list in character_evolution.items():
            formatted += f"{char_name}的发展轨迹：\n"
            for evolution in evolution_list[-3:]:  # 显示最近3次发展
                formatted += f"  第{evolution.get('chapter_number', 0)}章: {evolution.get('description', '')}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_foreshadowing_tracking(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化伏笔追踪"""
        foreshadowing_tracking = knowledge_base.get("foreshadowing_tracking", {})
        if not foreshadowing_tracking:
            return "无伏笔追踪"
        
        formatted = ""
        for foreshadowing_type, foreshadowing_list in foreshadowing_tracking.items():
            formatted += f"{foreshadowing_type}伏笔：\n"
            for foreshadowing in foreshadowing_list[-3:]:  # 显示最近3个伏笔
                formatted += f"  第{foreshadowing.get('chapter_number', 0)}章: {foreshadowing.get('content', '')}\n"
            formatted += "\n"
        
        return formatted
    
    def _format_current_content(self, continuation_content: Dict[str, Any]) -> str:
        """格式化当前内容"""
        if isinstance(continuation_content, dict):
            content = continuation_content.get("content", "")
            title = continuation_content.get("title", "")
            return f"标题：{title}\n内容：{content}"
        else:
            return str(continuation_content)
    
    def _format_long_term_issues(self, long_term_issues: Dict[str, Any]) -> str:
        """格式化长期连贯性问题"""
        formatted = f"""
        问题分析：
        - 需要改进: {long_term_issues.get('needs_improvement', False)}
        - 优先级: {long_term_issues.get('priority_level', 'low')}
        - 问题领域: {', '.join(long_term_issues.get('issue_areas', []))}
        - 具体问题: {', '.join(long_term_issues.get('specific_issues', []))}
        - 改进策略: {', '.join(long_term_issues.get('improvement_strategies', []))}
        """
        return formatted
