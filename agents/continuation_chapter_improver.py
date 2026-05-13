"""
续写章节改进智能体
负责基于质量评估结果改进续写章节内容
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationChapterImprover(BaseAgent):
    """续写章节改进智能体"""
    
    def __init__(self):
        super().__init__("续写章节改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理续写章节改进请求"""
        chapter_content = input_data.get("chapter_content", {})
        quality_assessment = input_data.get("quality_assessment", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not chapter_content or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 分析改进需求
        improvement_plan = self._analyze_improvement_needs(quality_assessment)
        
        # 执行改进
        improved_chapter = self._improve_chapter(
            chapter_content, improvement_plan, knowledge_base, user_requirements
        )
        
        return {
            "status": "success",
            "improved_chapter": improved_chapter,
            "improvement_plan": improvement_plan,
            "improvement_summary": self._generate_improvement_summary(improvement_plan)
        }
    
    def _analyze_improvement_needs(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """分析改进需求"""
        try:
            improvement_plan = {
                "needs_improvement": False,
                "improvement_areas": [],
                "priority_level": "low",
                "specific_issues": [],
                "improvement_strategies": []
            }
            
            # 检查整体质量分数
            overall_score = quality_assessment.get("overall_score", 0)
            if overall_score < 80:
                improvement_plan["needs_improvement"] = True
                improvement_plan["priority_level"] = "high" if overall_score < 60 else "medium"
            
            # 分析各维度问题
            dimensions = quality_assessment.get("dimensions", {})
            suggestions = quality_assessment.get("suggestions", [])
            
            # 检查人物一致性问题
            character_score = dimensions.get("character_consistency", 100)
            if character_score < 85:
                improvement_plan["improvement_areas"].append("character_consistency")
                improvement_plan["specific_issues"].append("人物行为或语言与原文不一致")
                improvement_plan["improvement_strategies"].append("调整人物对话和行为描述")
            
            # 检查情节连贯性问题
            plot_score = dimensions.get("plot_continuity", 100)
            if plot_score < 80:
                improvement_plan["improvement_areas"].append("plot_continuity")
                improvement_plan["specific_issues"].append("情节发展不够连贯")
                improvement_plan["improvement_strategies"].append("优化情节过渡和逻辑连接")
            
            # 检查世界观一致性问题
            world_score = dimensions.get("world_consistency", 100)
            if world_score < 90:
                improvement_plan["improvement_areas"].append("world_consistency")
                improvement_plan["specific_issues"].append("世界观设定与原文不符")
                improvement_plan["improvement_strategies"].append("修正世界观描述和设定")
            
            # 检查语言风格问题
            style_score = dimensions.get("style_consistency", 100)
            if style_score < 80:
                improvement_plan["improvement_areas"].append("style_consistency")
                improvement_plan["specific_issues"].append("语言风格与原文不一致")
                improvement_plan["improvement_strategies"].append("调整语言表达和修辞手法")
            
            # 检查伏笔延续性问题
            foreshadowing_score = dimensions.get("foreshadowing_continuity", 100)
            if foreshadowing_score < 85:
                improvement_plan["improvement_areas"].append("foreshadowing_continuity")
                improvement_plan["specific_issues"].append("伏笔处理不够连贯")
                improvement_plan["improvement_strategies"].append("完善伏笔设置和呼应")
            
            # 添加具体建议
            for suggestion in suggestions:
                improvement_plan["improvement_strategies"].append(suggestion)
            
            return improvement_plan
            
        except Exception as e:
            self.log(f"分析改进需求失败: {e}")
            return {
                "needs_improvement": True,
                "improvement_areas": ["general"],
                "priority_level": "medium",
                "specific_issues": ["内容质量需要提升"],
                "improvement_strategies": ["全面优化章节内容"]
            }
    
    def _improve_chapter(self, chapter_content: Dict[str, Any], 
                        improvement_plan: Dict[str, Any],
                        knowledge_base: Dict[str, Any],
                        user_requirements: str) -> Dict[str, Any]:
        """改进章节内容"""
        try:
            if not improvement_plan.get("needs_improvement", False):
                return chapter_content
            
            # 构建改进提示
            prompt = f"""
            请基于以下改进需求，对续写章节进行优化改进：
            
            原文信息：
            1. 世界观设定：
            {self._format_world_setting(knowledge_base)}
            
            2. 人物档案：
            {self._format_character_profiles(knowledge_base)}
            
            3. 故事基调：
            {self._format_story_tone(knowledge_base)}
            
            4. 用户需求：
            {user_requirements if user_requirements else "无特殊要求"}
            
            当前章节内容（需要改进）：
            {self._format_current_chapter(chapter_content)}
            
            改进需求分析：
            {self._format_improvement_plan(improvement_plan)}
            
            改进要求：
            1. 根据改进需求进行针对性优化
            2. 保持与原文的一致性
            3. 确保情节连贯性和逻辑合理性
            4. 提升章节的整体质量
            5. 保持原有的优秀元素
            6. 确保改进后的内容自然流畅
            7. 小说正文字数必须大于3000字且在3000-5000字之间
            8. 确保情节逻辑自洽
            9. 用你最大的输出能力进行输出
            
            请返回改进后的JSON格式章节内容：
            {{
                "chapter_number": {chapter_content.get("chapter_number", 0)},
                "title": "改进后的章节标题",
                "content": "改进后的章节正文内容",
                "summary": "改进后的章节摘要",
                "key_events": [
                    "改进后的关键事件1",
                    "改进后的关键事件2"
                ],
                "character_development": {{
                    "main_character": "主角在本章的发展",
                    "supporting_characters": "配角在本章的表现"
                }},
                "foreshadowing": [
                    "改进后的伏笔1",
                    "改进后的伏笔2"
                ],
                "next_chapter_hint": "改进后的下章预告",
                "writing_notes": "改进说明和注意事项",
                "improvement_notes": "具体改进内容说明"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的小说编辑，擅长根据评估建议改进续写章节，提升内容质量和一致性。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和补充结果
            return self._validate_improved_chapter(result, chapter_content)
            
        except Exception as e:
            self.log(f"改进章节内容失败: {e}")
            return self._create_fallback_chapter(chapter_content, improvement_plan)
    
    def _validate_improved_chapter(self, result: Dict[str, Any], 
                                 original_chapter: Dict[str, Any]) -> Dict[str, Any]:
        """验证改进后的章节内容"""
        try:
            # 确保必要字段存在
            required_fields = {
                "chapter_number": original_chapter.get("chapter_number", 0),
                "title": original_chapter.get("title", "改进后的章节"),
                "content": original_chapter.get("content", ""),
                "summary": original_chapter.get("summary", ""),
                "key_events": original_chapter.get("key_events", []),
                "character_development": original_chapter.get("character_development", {}),
                "foreshadowing": original_chapter.get("foreshadowing", []),
                "next_chapter_hint": original_chapter.get("next_chapter_hint", ""),
                "writing_notes": "章节内容已改进",
                "improvement_notes": "基于质量评估结果进行了针对性改进"
            }
            
            # 补充缺失字段
            for field, default_value in required_fields.items():
                if field not in result:
                    result[field] = default_value
            
            # 确保内容不为空
            if not result.get("content", "").strip():
                result["content"] = original_chapter.get("content", "")
                result["improvement_notes"] = "内容改进失败，保持原内容"
            
            return result
            
        except Exception as e:
            self.log(f"验证改进章节失败: {e}")
            return original_chapter
    
    def _create_fallback_chapter(self, original_chapter: Dict[str, Any], 
                               improvement_plan: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用章节内容"""
        fallback_chapter = original_chapter.copy()
        fallback_chapter["improvement_notes"] = "改进功能暂时不可用，使用原章节内容"
        fallback_chapter["writing_notes"] = f"原章节存在以下问题：{', '.join(improvement_plan.get('specific_issues', []))}"
        
        return fallback_chapter
    
    def _generate_improvement_summary(self, improvement_plan: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        return {
            "improvement_areas": improvement_plan.get("improvement_areas", []),
            "priority_level": improvement_plan.get("priority_level", "low"),
            "specific_issues": improvement_plan.get("specific_issues", []),
            "improvement_strategies": improvement_plan.get("improvement_strategies", []),
            "improvement_status": "completed" if improvement_plan.get("needs_improvement") else "not_needed"
        }
    
    def _format_world_setting(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化世界观设定"""
        world_setting = knowledge_base.get("world_setting", "")
        if isinstance(world_setting, dict):
            return f"世界观：{world_setting.get('description', '未知')}"
        else:
            return f"世界观：{world_setting}"
    
    def _format_character_profiles(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化人物档案"""
        character_profiles = knowledge_base.get("character_profiles", {})
        if not character_profiles:
            return "无人物档案"
        
        formatted = ""
        main_character = character_profiles.get("main_character", {})
        if main_character:
            formatted += f"主角：{main_character.get('name', '未知')}\n"
            formatted += f"  性格：{main_character.get('personality', {}).get('description', '未知')}\n"
            formatted += f"  背景：{main_character.get('background', {}).get('core_desire', '未知')}\n\n"
        
        supporting_characters = character_profiles.get("supporting_characters", [])
        for char in supporting_characters:
            formatted += f"配角：{char.get('name', '未知')} ({char.get('role', '未知角色')})\n"
            formatted += f"  性格：{char.get('personality', '未知')}\n\n"
        
        return formatted
    
    def _format_story_tone(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化故事基调"""
        story_tone = knowledge_base.get("story_tone", "")
        return f"故事基调：{story_tone}"
    
    def _format_current_chapter(self, chapter_content: Dict[str, Any]) -> str:
        """格式化当前章节内容"""
        formatted = f"""
        章节信息：
        - 章节号: {chapter_content.get('chapter_number', 0)}
        - 标题: {chapter_content.get('title', '未知')}
        - 内容长度: {len(chapter_content.get('content', ''))}字
        - 关键事件: {chapter_content.get('key_events', [])}
        - 人物发展: {chapter_content.get('character_development', {})}
        - 伏笔设置: {chapter_content.get('foreshadowing', [])}
        """
        return formatted
    
    def _format_improvement_plan(self, improvement_plan: Dict[str, Any]) -> str:
        """格式化改进计划"""
        formatted = f"""
        改进需求：
        - 需要改进: {improvement_plan.get('needs_improvement', False)}
        - 优先级: {improvement_plan.get('priority_level', 'low')}
        - 改进领域: {', '.join(improvement_plan.get('improvement_areas', []))}
        - 具体问题: {', '.join(improvement_plan.get('specific_issues', []))}
        - 改进策略: {', '.join(improvement_plan.get('improvement_strategies', []))}
        """
        return formatted
