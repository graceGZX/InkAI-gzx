"""
故事线改进智能体
负责基于质量评估结果改进故事线
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class StorylineImprover(BaseAgent):
    """故事线改进智能体"""
    
    def __init__(self):
        super().__init__("故事线改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理故事线改进请求"""
        knowledge_base = input_data.get("knowledge_base", {})
        current_storyline = input_data.get("current_storyline", {})
        quality_assessment = input_data.get("quality_assessment", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not knowledge_base or not current_storyline or not quality_assessment:
            return {"error": "缺少必要的改进数据"}
        
        # 生成改进后的故事线
        improved_storyline = self._improve_storyline(
            knowledge_base, current_storyline, quality_assessment, user_requirements
        )
        
        return {
            "status": "success",
            "improved_storyline": improved_storyline,
            "improvement_notes": self._generate_improvement_notes(quality_assessment)
        }
    
    def _improve_storyline(self, knowledge_base: Dict[str, Any], 
                          current_storyline: Dict[str, Any],
                          quality_assessment: Dict[str, Any],
                          user_requirements: str) -> Dict[str, Any]:
        """改进故事线"""
        try:
            # 获取基本信息
            novel_info = knowledge_base.get("novel_info", {})
            chapters = knowledge_base.get("chapters", [])
            character_profiles = knowledge_base.get("character_profiles", {})
            plot_lines = knowledge_base.get("plot_lines", {})
            last_chapter = knowledge_base.get("last_chapter_summary", {})
            world_setting = knowledge_base.get("world_setting", "")
            story_tone = knowledge_base.get("story_tone", "")
            tags = knowledge_base.get("tags", {})
            
            # 确定章节号
            chapter_number = current_storyline.get("chapter_number", len(chapters) + 1)
            
            # 构建改进提示
            prompt = f"""
            请基于质量评估结果改进以下故事线：
            
            原文信息：
            1. 世界观设定：{world_setting}
            2. 故事基调：{story_tone}
            3. 故事标签：{self._format_tags(tags)}
            
            4. 人物设定：
            {self._format_character_profiles(character_profiles)}
            
            5. 整体故事线：
            {self._format_plot_lines(plot_lines)}
            
            6. 上一章结尾：
            {self._format_last_chapter(last_chapter)}
            
            7. 用户续写需求：{user_requirements if user_requirements else "无特殊要求"}
            
            当前故事线（需要改进）：
            {self._format_current_storyline(current_storyline)}
            
            质量评估结果：
            {self._format_quality_assessment(quality_assessment)}
            
            改进要求：
            1. 根据评估建议进行针对性改进
            2. 保持与原文的一致性
            3. 确保情节连贯性和逻辑合理性
            4. 提升故事线的整体质量
            5. 保持原有的优秀元素
            6. 为后续章节发展留下空间
            
            请返回改进后的JSON格式故事线：
            {{
                "chapter_number": {chapter_number},
                "chapter_title": "改进后的章节标题",
                "scene_setting": {{
                    "time": "时间设定",
                    "location": "地点设定",
                    "atmosphere": "氛围描述",
                    "weather": "天气状况"
                }},
                "plot_points": [
                    "改进后的情节要点1",
                    "改进后的情节要点2",
                    "改进后的情节要点3"
                ],
                "character_interactions": [
                    {{
                        "characters": ["角色1", "角色2"],
                        "interaction_type": "对话/冲突/合作",
                        "purpose": "互动目的"
                    }}
                ],
                "key_events": [
                    "改进后的关键事件1",
                    "改进后的关键事件2"
                ],
                "conflicts": [
                    {{
                        "type": "内心冲突/外部冲突/人际冲突",
                        "description": "冲突描述",
                        "resolution": "解决方式"
                    }}
                ],
                "foreshadowing": [
                    "改进后的伏笔1",
                    "改进后的伏笔2"
                ],
                "character_development": {{
                    "main_character": "主角在本章的发展",
                    "supporting_characters": "配角的发展"
                }},
                "chapter_ending": "改进后的章节结尾描述",
                "next_chapter_hint": "改进后的下章预告",
                "writing_notes": "改进后的写作注意事项",
                "improvement_summary": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的故事编辑，擅长根据评估建议改进故事线，提升故事质量。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和补充结果
            return self._validate_improved_storyline(result, chapter_number)
            
        except Exception as e:
            self.log(f"改进故事线失败: {e}")
            return self._create_fallback_storyline(current_storyline, chapter_number)
    
    def _validate_improved_storyline(self, result: Dict[str, Any], chapter_number: int) -> Dict[str, Any]:
        """验证改进后的故事线结果"""
        # 确保必要字段存在
        required_fields = {
            "chapter_number": chapter_number,
            "chapter_title": f"第{chapter_number}章（改进版）",
            "scene_setting": {
                "time": "待设定",
                "location": "待设定",
                "atmosphere": "待设定",
                "weather": "待设定"
            },
            "plot_points": [],
            "character_interactions": [],
            "key_events": [],
            "conflicts": [],
            "foreshadowing": [],
            "character_development": {
                "main_character": "待补充",
                "supporting_characters": "待补充"
            },
            "chapter_ending": "待补充",
            "next_chapter_hint": "待补充",
            "writing_notes": "待补充",
            "improvement_summary": "待补充"
        }
        
        # 补充缺失字段
        for field, default_value in required_fields.items():
            if field not in result:
                result[field] = default_value
        
        return result
    
    def _create_fallback_storyline(self, current_storyline: Dict[str, Any], chapter_number: int) -> Dict[str, Any]:
        """创建备用故事线"""
        return {
            "chapter_number": chapter_number,
            "chapter_title": f"第{chapter_number}章（改进版）",
            "scene_setting": current_storyline.get("scene_setting", {
                "time": "待设定",
                "location": "待设定",
                "atmosphere": "待设定",
                "weather": "待设定"
            }),
            "plot_points": current_storyline.get("plot_points", ["情节发展待补充"]),
            "character_interactions": current_storyline.get("character_interactions", []),
            "key_events": current_storyline.get("key_events", ["关键事件待补充"]),
            "conflicts": current_storyline.get("conflicts", []),
            "foreshadowing": current_storyline.get("foreshadowing", []),
            "character_development": current_storyline.get("character_development", {
                "main_character": "待补充",
                "supporting_characters": "待补充"
            }),
            "chapter_ending": current_storyline.get("chapter_ending", "待补充"),
            "next_chapter_hint": current_storyline.get("next_chapter_hint", "待补充"),
            "writing_notes": "改进功能暂时不可用，使用原故事线",
            "improvement_summary": "改进失败，使用原故事线"
        }
    
    def _generate_improvement_notes(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进说明"""
        return {
            "original_score": quality_assessment.get("overall_score", 0),
            "main_issues": quality_assessment.get("weaknesses", []),
            "improvement_suggestions": quality_assessment.get("suggestions", []),
            "strengths_preserved": quality_assessment.get("strengths", [])
        }
    
    def _format_current_storyline(self, storyline: Dict[str, Any]) -> str:
        """格式化当前故事线"""
        formatted = f"""
        当前故事线：
        - 章节号: {storyline.get('chapter_number', '未知')}
        - 标题: {storyline.get('chapter_title', '未知')}
        - 场景设定: {storyline.get('scene_setting', {})}
        - 情节要点: {storyline.get('plot_points', [])}
        - 关键事件: {storyline.get('key_events', [])}
        - 冲突设计: {storyline.get('conflicts', [])}
        - 伏笔设置: {storyline.get('foreshadowing', [])}
        - 章节结尾: {storyline.get('chapter_ending', '未知')}
        """
        return formatted
    
    def _format_quality_assessment(self, assessment: Dict[str, Any]) -> str:
        """格式化质量评估结果"""
        formatted = f"""
        质量评估结果：
        - 总分: {assessment.get('overall_score', 0)}分
        - 是否高质量: {assessment.get('is_high_quality', False)}
        
        各维度得分：
        """
        
        scores = assessment.get("scores", {})
        for dimension, score in scores.items():
            formatted += f"  - {dimension}: {score}分\n"
        
        strengths = assessment.get("strengths", [])
        if strengths:
            formatted += f"\n优点：\n"
            for strength in strengths:
                formatted += f"  - {strength}\n"
        
        weaknesses = assessment.get("weaknesses", [])
        if weaknesses:
            formatted += f"\n缺点：\n"
            for weakness in weaknesses:
                formatted += f"  - {weakness}\n"
        
        suggestions = assessment.get("suggestions", [])
        if suggestions:
            formatted += f"\n改进建议：\n"
            for suggestion in suggestions:
                formatted += f"  - {suggestion}\n"
        
        return formatted
    
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
    
    def _format_plot_lines(self, plot_lines: Dict[str, Any]) -> str:
        """格式化故事线"""
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
    
    def _format_last_chapter(self, last_chapter: Dict[str, Any]) -> str:
        """格式化上一章信息"""
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
    
    def _format_tags(self, tags: Dict[str, Any]) -> str:
        """格式化标签信息"""
        if not tags:
            return "无标签信息"
        
        formatted = ""
        selected_tags = tags.get("selected_tags", {})
        for category, tag_list in selected_tags.items():
            if tag_list and isinstance(tag_list, list):
                formatted += f"{category}: {', '.join(tag_list)}\n"
            else:
                formatted += f"{category}: 无标签\n"
        return formatted
