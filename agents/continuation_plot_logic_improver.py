"""
续写情节逻辑专项改进智能体
专门改进续写内容中情节的逻辑性问题
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationPlotLogicImprover(BaseAgent):
    """续写情节逻辑专项改进智能体"""
    
    def __init__(self):
        super().__init__("续写情节逻辑专项改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """改进续写内容中情节的逻辑性问题"""
        continuation_content = input_data.get("continuation_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not continuation_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析情节逻辑问题
        plot_issues = self._analyze_plot_logic_issues(quality_assessment)
        
        # 执行情节逻辑改进
        improved_content = self._improve_plot_logic(
            continuation_content, plot_issues, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_content": improved_content,
            "plot_issues": plot_issues,
            "improvement_summary": self._generate_improvement_summary(plot_issues)
        }
    
    def _analyze_plot_logic_issues(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析情节逻辑问题"""
        try:
            plot_issues = {
                "needs_improvement": False,
                "issue_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查情节逻辑维度分数
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查因果关系合理性问题
            causality_score = dimensions.get("causality_reasonableness", 100)
            if causality_score < 80:
                plot_issues["needs_improvement"] = True
                plot_issues["issue_areas"].append("causality_reasonableness")
                plot_issues["specific_issues"].append("事件之间的因果关系不合理")
                plot_issues["improvement_strategies"].append("修正事件间的因果关系和逻辑链条")
            
            # 检查时间线一致性问题
            timeline_score = dimensions.get("timeline_consistency", 100)
            if timeline_score < 85:
                plot_issues["needs_improvement"] = True
                plot_issues["issue_areas"].append("timeline_consistency")
                plot_issues["specific_issues"].append("时间顺序存在矛盾")
                plot_issues["improvement_strategies"].append("调整时间线，消除时间矛盾")
            
            # 检查事件发展逻辑问题
            event_score = dimensions.get("event_development_logic", 100)
            if event_score < 80:
                plot_issues["needs_improvement"] = True
                plot_issues["issue_areas"].append("event_development_logic")
                plot_issues["specific_issues"].append("事件发展不符合逻辑规律")
                plot_issues["improvement_strategies"].append("优化事件发展逻辑和合理性")
            
            # 检查冲突升级合理性问题
            conflict_score = dimensions.get("conflict_escalation_reasonableness", 100)
            if conflict_score < 85:
                plot_issues["needs_improvement"] = True
                plot_issues["issue_areas"].append("conflict_escalation_reasonableness")
                plot_issues["specific_issues"].append("冲突发展不够合理")
                plot_issues["improvement_strategies"].append("调整冲突发展节奏和合理性")
            
            # 检查伏笔呼应完整性问题
            foreshadowing_score = dimensions.get("foreshadowing_echo_completeness", 100)
            if foreshadowing_score < 85:
                plot_issues["needs_improvement"] = True
                plot_issues["issue_areas"].append("foreshadowing_echo_completeness")
                plot_issues["specific_issues"].append("伏笔设置和呼应不完整")
                plot_issues["improvement_strategies"].append("完善伏笔设置和呼应机制")
            
            # 确定优先级
            if plot_issues["needs_improvement"]:
                min_score = min([
                    causality_score, timeline_score, event_score, 
                    conflict_score, foreshadowing_score
                ])
                if min_score < 60:
                    plot_issues["priority_level"] = "high"
                elif min_score < 80:
                    plot_issues["priority_level"] = "medium"
                else:
                    plot_issues["priority_level"] = "low"
            
            # 添加具体建议
            for suggestion in suggestions:
                if "情节" in suggestion or "逻辑" in suggestion or "事件" in suggestion:
                    plot_issues["improvement_strategies"].append(suggestion)
            
            return plot_issues
            
        except Exception as e:
            self.log(f"分析情节逻辑问题失败: {e}")
            return {
                "needs_improvement": True,
                "issue_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["情节逻辑问题需要改进"],
                "improvement_strategies": ["全面优化情节逻辑"]
            }
    
    def _improve_plot_logic(self, continuation_content: Dict[str, Any], 
                          plot_issues: Dict[str, Any],
                          knowledge_base: Dict[str, Any],
                          user_requirements: str) -> Dict[str, Any]:
        """改进情节逻辑"""
        try:
            if not plot_issues.get("needs_improvement", False):
                return continuation_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下情节逻辑问题，对续写内容进行针对性改进：
            
            原文情节线：
            {self._format_plot_lines(knowledge_base)}
            
            上一章结尾：
            {self._format_last_chapter(knowledge_base)}
            
            用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前续写内容（需要改进）：
            {self._format_current_content(continuation_content)}
            
            情节逻辑问题分析：
            {self._format_plot_issues(plot_issues)}
            
            改进要求：
            1. 根据问题分析进行针对性改进
            2. 修正事件间的因果关系和逻辑链条
            3. 调整时间线，消除时间矛盾
            4. 优化事件发展逻辑和合理性
            5. 调整冲突发展节奏和合理性
            6. 完善伏笔设置和呼应机制
            7. 保持内容的自然流畅性
            
            请返回改进后的JSON格式内容：
            {{
                "improved_content": "改进后的内容",
                "plot_improvements": {{
                    "causality_corrections": "因果关系修正说明",
                    "timeline_adjustments": "时间线调整说明",
                    "event_logic_enhancement": "事件逻辑优化说明",
                    "conflict_escalation_improvement": "冲突发展改进说明",
                    "foreshadowing_enhancement": "伏笔完善说明"
                }},
                "improvement_notes": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的情节编辑，擅长改进续写内容中情节的逻辑性问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和整合改进结果
            return self._integrate_improvements(continuation_content, result)
            
        except Exception as e:
            self.log(f"改进情节逻辑失败: {e}")
            return self._create_fallback_content(continuation_content, plot_issues)
    
    def _integrate_improvements(self, original_content: Dict[str, Any], 
                              improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合改进结果"""
        try:
            improved_content = original_content.copy()
            
            # 更新内容
            if "improved_content" in improvement_result:
                improved_content["content"] = improvement_result["improved_content"]
            
            # 添加改进记录
            improved_content["plot_improvements"] = improvement_result.get("plot_improvements", {})
            improved_content["improvement_notes"] = improvement_result.get("improvement_notes", "情节逻辑已改进")
            
            # 确保内容不为空
            if not improved_content.get("content", "").strip():
                improved_content["content"] = original_content.get("content", "")
                improved_content["improvement_notes"] = "情节逻辑改进失败，保持原内容"
            
            return improved_content
            
        except Exception as e:
            self.log(f"整合改进结果失败: {e}")
            return original_content
    
    def _create_fallback_content(self, original_content: Dict[str, Any], 
                               plot_issues: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        fallback_content = original_content.copy()
        fallback_content["plot_improvements"] = {
            "causality_corrections": "改进功能暂时不可用",
            "timeline_adjustments": "改进功能暂时不可用",
            "event_logic_enhancement": "改进功能暂时不可用",
            "conflict_escalation_improvement": "改进功能暂时不可用",
            "foreshadowing_enhancement": "改进功能暂时不可用"
        }
        fallback_content["improvement_notes"] = f"情节逻辑问题：{', '.join(plot_issues.get('specific_issues', []))}"
        
        return fallback_content
    
    def _generate_improvement_summary(self, plot_issues: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "issue_areas": plot_issues.get("issue_areas", []),
            "priority_level": plot_issues.get("priority_level", "low"),
            "specific_issues": plot_issues.get("specific_issues", []),
            "improvement_strategies": plot_issues.get("improvement_strategies", []),
            "improvement_status": "completed" if plot_issues.get("needs_improvement") else "not_needed"
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
    
    def _format_last_chapter(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化上一章信息"""
        last_chapter = knowledge_base.get("last_chapter_summary", {})
        if not last_chapter:
            return "无上一章信息"
        
        formatted = f"第{last_chapter.get('chapter_number', 0)}章：{last_chapter.get('title', '未知标题')}\n"
        formatted += f"概要：{last_chapter.get('summary', '无概要')}\n"
        
        key_events = last_chapter.get("key_events", [])
        if key_events:
            formatted += f"关键事件：{', '.join(key_events)}\n"
        
        foreshadowing = last_chapter.get("foreshadowing", [])
        if foreshadowing:
            formatted += f"伏笔：{', '.join(foreshadowing)}\n"
        
        next_hint = last_chapter.get("next_chapter_hint", "")
        if next_hint:
            formatted += f"下章预告：{next_hint}\n"
        
        return formatted
    
    def _format_current_content(self, continuation_content: Dict[str, Any]) -> str:
        """格式化当前内容"""
        if isinstance(continuation_content, dict):
            content = continuation_content.get("content", "")
            title = continuation_content.get("title", "")
            return f"标题：{title}\n内容：{content}"
        else:
            return str(continuation_content)
    
    def _format_plot_issues(self, plot_issues: Dict[str, Any]) -> str:
        """格式化情节逻辑问题"""
        formatted = f"""
        问题分析：
        - 需要改进: {plot_issues.get('needs_improvement', False)}
        - 优先级: {plot_issues.get('priority_level', 'low')}
        - 问题领域: {', '.join(plot_issues.get('issue_areas', []))}
        - 具体问题: {', '.join(plot_issues.get('specific_issues', []))}
        - 改进策略: {', '.join(plot_issues.get('improvement_strategies', []))}
        """
        return formatted
