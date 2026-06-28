"""
新书开篇故事线改进智能体
负责基于质量评估结果改进新书开篇的故事线
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class NovelStorylineImprover(BaseAgent):
    """新书开篇故事线改进智能体"""
    
    def __init__(self):
        super().__init__("新书开篇故事线改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理新书开篇故事线改进请求"""
        current_storyline = input_data.get("current_storyline", {})
        overall_storyline = input_data.get("overall_storyline", {})
        characters = input_data.get("characters", {})
        improvement_suggestions = input_data.get("improvement_suggestions", [])
        tags = input_data.get("tags", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not current_storyline:
            return {"error": "缺少当前故事线数据"}
        
        # 如果没有改进建议，使用默认建议
        if not improvement_suggestions or len(improvement_suggestions) == 0:
            print("没有改进建议，使用默认改进策略")
            improvement_suggestions = ["提升故事线的逻辑性和连贯性", "增强情节的吸引力", "优化人物发展轨迹"]
        
        # 添加调试信息
        print(f"故事线改进输入数据检查:")
        print(f"  - current_storyline 类型: {type(current_storyline)}")
        print(f"  - improvement_suggestions 数量: {len(improvement_suggestions)}")
        print(f"  - characters: {bool(characters)}")
        print(f"  - user_requirements: {bool(user_requirements)}")
        
        # 生成改进后的故事线
        improved_storyline = self._improve_storyline(
            current_storyline, overall_storyline, characters, improvement_suggestions, tags, user_requirements
        )
        
        return {
            "success": True,
            "status": "success",
            "improved_storyline": improved_storyline,
            "improvement_notes": self._generate_improvement_notes(improvement_suggestions)
        }
    
    def _is_chapter_storyline(self, storyline: Dict[str, Any]) -> bool:
        """检测是否为章级故事线（vs 全书级故事线）"""
        return bool(storyline.get("scene_setting") or storyline.get("plot_points"))

    def _improve_storyline(self, current_storyline: Dict[str, Any],
                          overall_storyline: Dict[str, Any],
                          characters: Dict[str, Any],
                          improvement_suggestions: List[str],
                          tags: Dict[str, List[str]],
                          user_requirements: str) -> Dict[str, Any]:
        """改进故事线"""
        try:
            is_chapter = self._is_chapter_storyline(current_storyline)
            main_character = characters.get("main_character", {})
            supporting_characters = characters.get("supporting_characters", [])

            if is_chapter:
                prompt = self._build_chapter_level_prompt(current_storyline, main_character, supporting_characters,
                                                          improvement_suggestions, tags, user_requirements)
            else:
                prompt = self._build_book_level_prompt(current_storyline, main_character, supporting_characters,
                                                       improvement_suggestions, tags, user_requirements)

            messages = [
                {"role": "system", "content": "你是一个专业的故事编辑，擅长根据评估建议改进故事线，提升故事的结构性和吸引力。"},
                {"role": "user", "content": prompt}
            ]

            response = self.call_llm(messages)
            result = self.parse_json_response(response)

            return self._validate_improved_storyline(result, is_chapter=is_chapter)

        except Exception as e:
            self.log(f"改进故事线失败: {e}")
            return self._create_fallback_storyline(current_storyline)

    def _build_chapter_level_prompt(self, storyline, main_char, supporting_chars, suggestions, tags, user_req):
        return f"""
请基于以下改进建议，对下一章故事线进行完善和补充：

原文信息：
1. 故事标签：
{self._format_tags(tags)}

2. 人物设定：
{self._format_character_info(main_char, supporting_chars)}

3. 用户需求：
{user_req}

当前章级故事线（需要改进）：
{self._format_chapter_storyline(storyline)}

改进建议：
{self._format_improvement_suggestions(suggestions)}

改进要求：
1. 根据评估建议进行针对性改进
2. 保持与人物设定和标签的一致性
3. 确保情节逻辑自洽、与前章自然衔接
4. 保持原有的优秀元素，只改不合理的部分
5. scene_setting 中的 time/location 必须能承接上一章结尾

请返回改进后的JSON格式（与输入结构一致）：
{{
    "chapter_number": {storyline.get('chapter_number', 0)},
    "chapter_title": "改进后的章节标题",
    "scene_setting": {{
        "time": "时间设定（承接上章结尾）",
        "location": "地点设定（承接上章结尾）",
        "atmosphere": "氛围描述",
        "weather": "天气状况"
    }},
    "plot_points": ["情节要点1", "情节要点2", "情节要点3"],
    "character_interactions": [
        {{
            "characters": ["角色1", "角色2"],
            "interaction_type": "对话/冲突/合作",
            "purpose": "互动目的"
        }}
    ],
    "key_events": ["关键事件1", "关键事件2"],
    "conflicts": [
        {{
            "type": "内心冲突/外部冲突/人际冲突",
            "description": "冲突描述",
            "resolution": "解决方式"
        }}
    ],
    "foreshadowing": ["伏笔1", "伏笔2"],
    "character_development": {{
        "main_character": "主角在本章的发展",
        "supporting_characters": "配角的发展"
    }},
    "chapter_ending": "章节结尾描述（钩子）",
    "next_chapter_hint": "下章预告",
    "writing_notes": "写作注意事项",
    "improvement_summary": "改进要点总结"
}}
"""

    def _build_book_level_prompt(self, storyline, main_char, supporting_chars, suggestions, tags, user_req):
        return f"""
请基于以下改进建议，对故事线进行完善和补充：

原文信息：
1. 故事标签：
{self._format_tags(tags)}

2. 人物设定：
{self._format_character_info(main_char, supporting_chars)}

3. 用户需求：
{user_req}

当前故事线（需要改进）：
{self._format_current_storyline(storyline)}

改进建议：
{self._format_improvement_suggestions(suggestions)}

改进要求：
1. 根据评估建议进行针对性改进
2. 保持与人物设定和标签的一致性
3. 确保故事结构的完整性和逻辑性
4. 提升故事的吸引力和可读性
5. 保持原有的优秀元素
6. 为后续章节发展提供更好的基础

请返回改进后的JSON格式故事线：
{{
    "overall_storyline": {{
        "world_setting": {{
            "time_period": "时代背景",
            "location": "地点设定",
            "society": "社会背景",
            "atmosphere": "氛围基调"
        }},
        "main_goal": "改进后的主角目标",
        "core_conflict": {{
            "external": "外在冲突（与环境的对抗）",
            "internal": "内在冲突（内心的挣扎）",
            "interpersonal": "人际冲突（与他人的对抗）"
        }},
        "act1": {{"setup": "第一幕设定", "key_events": ["事件1", "事件2"], "ending": "第一幕结尾"}},
        "act2": {{"confrontation": "第二幕冲突", "crisis": "中期危机", "low_point": "低谷期", "turning_point": "转折点"}},
        "act3": {{"climax": "高潮对决", "resolution": "冲突解决", "ending": "故事结局"}},
        "themes": ["主题1", "主题2"],
        "tone": "改进后的故事基调",
        "target_audience": "目标读者群体",
        "commercial_potential": "商业价值分析"
    }},
    "first_module": {{
        "chapter_title": "改进后的章节标题",
        "scene_setting": {{"time": "时间设定", "location": "地点设定", "atmosphere": "环境氛围"}},
        "plot_points": [{{"event": "事件描述", "purpose": "事件目的", "characters_involved": ["参与角色"], "tension_level": "紧张程度(1-10)"}}],
        "character_development": {{"main_character": "主角在本章的发展", "supporting_characters": "配角在本章的表现"}},
        "foreshadowing": ["伏笔1", "伏笔2"],
        "chapter_ending": "改进后的章节结尾",
        "hook": "改进后的吸引读者继续阅读的钩子"
    }},
    "subplot_hints": {{
        "subplots": [{{"theme": "暗线主题", "hints": [{{"type": "伏笔类型", "content": "伏笔内容", "chapter": "出现章节", "reveal_chapter": "揭露章节"}}], "connection_to_main": "与主线的关联"}}]
    }},
    "story_structure": {{
        "三幕剧": {{
            "第一幕": {{"setup": "介绍世界观、主角目标、初始冲突", "length_ratio": 0.25}},
            "第二幕": {{"confrontation": "中期危机、低谷期、转折点", "length_ratio": 0.5}},
            "第三幕": {{"resolution": "高潮对决、结局", "length_ratio": 0.25}}
        }}
    }},
    "improvement_summary": "改进要点总结"
}}
"""

    def _format_chapter_storyline(self, storyline: Dict[str, Any]) -> str:
        """格式化章级故事线"""
        formatted = f"章节号：{storyline.get('chapter_number', '?')}\n"
        formatted += f"章节标题：{storyline.get('chapter_title', '?')}\n"
        s = storyline.get('scene_setting', {})
        if s:
            formatted += f"场景：时间={s.get('time','?')} 地点={s.get('location','?')} 氛围={s.get('atmosphere','?')} 天气={s.get('weather','?')}\n"
        pts = storyline.get('plot_points', [])
        if pts:
            formatted += "情节要点：\n"
            for p in pts:
                formatted += f"  - {str(p)[:120]}\n"
        evts = storyline.get('key_events', [])
        if evts:
            formatted += f"关键事件：{', '.join(evts)}\n"
        fores = storyline.get('foreshadowing', [])
        if fores:
            formatted += f"伏笔：{', '.join(fores)}\n"
        end = storyline.get('chapter_ending', '')
        if end:
            formatted += f"章末钩子：{end}\n"
        return formatted
    
    def _validate_improved_storyline(self, result: Dict[str, Any], is_chapter: bool = False) -> Dict[str, Any]:
        """验证改进后的故事线结果"""
        if is_chapter:
            # 章级字段补全
            defaults = {
                "chapter_number": result.get("chapter_number", 0),
                "chapter_title": "待补充",
                "scene_setting": {"time": "待设定", "location": "待设定", "atmosphere": "待设定", "weather": "待设定"},
                "plot_points": [],
                "character_interactions": [],
                "key_events": [],
                "conflicts": [],
                "foreshadowing": [],
                "character_development": {"main_character": "待补充", "supporting_characters": "待补充"},
                "chapter_ending": "待补充",
                "next_chapter_hint": "待补充",
                "writing_notes": "待补充",
                "improvement_summary": "待补充"
            }
            for field, default_value in defaults.items():
                if field not in result or not result[field]:
                    result[field] = default_value
            # 确保 scene_setting 是字典且字段完整
            if isinstance(result.get("scene_setting"), dict):
                for sf in ["time", "location", "atmosphere", "weather"]:
                    if sf not in result["scene_setting"] or not result["scene_setting"][sf]:
                        result["scene_setting"][sf] = "待设定"
            return result

        # 全书级字段补全（原有逻辑）
        required_fields = {
            "overall_storyline": {
                "world_setting": "待补充",
                "main_goal": "待补充",
                "conflict": "待补充",
                "act1": {"setup": "待补充", "key_events": [], "ending": "待补充"},
                "act2": {"confrontation": "待补充", "crisis": "待补充", "low_point": "待补充", "turning_point": "待补充"},
                "act3": {"climax": "待补充", "resolution": "待补充", "ending": "待补充"},
                "themes": [],
                "tone": "待补充"
            },
            "first_module": {
                "chapter_title": "待补充",
                "scene_setting": {"time": "待设定", "location": "待设定", "atmosphere": "待设定"},
                "plot_points": [],
                "character_development": {"main_character": "待补充", "supporting_characters": "待补充"},
                "foreshadowing": [],
                "chapter_ending": "待补充",
                "hook": "待补充"
            },
            "subplot_hints": {"subplots": []},
            "story_structure": config.STORY_STRUCTURE,
            "improvement_summary": "待补充"
        }
        for field, default_value in required_fields.items():
            if field not in result:
                result[field] = default_value
        return result
    
    def _create_fallback_storyline(self, current_storyline: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用故事线（保留原结构）"""
        if self._is_chapter_storyline(current_storyline):
            return {
                **current_storyline,
                "improvement_summary": "改进功能暂时不可用，使用原故事线"
            }
        return {
            "overall_storyline": current_storyline.get("overall_storyline", {}),
            "first_module": current_storyline.get("first_module", {}),
            "subplot_hints": current_storyline.get("subplot_hints", {}),
            "story_structure": current_storyline.get("story_structure", config.STORY_STRUCTURE),
            "improvement_summary": "改进功能暂时不可用，使用原故事线"
        }
    
    def _generate_improvement_notes(self, improvement_suggestions: List[str]) -> Dict[str, Any]:
        """生成改进说明"""
        return {
            "original_suggestions": improvement_suggestions,
            "improvement_focus": "故事结构、情节逻辑、人物发展、伏笔设置",
            "key_improvements": improvement_suggestions[:3] if improvement_suggestions else []
        }
    
    def _format_current_storyline(self, storyline: Dict[str, Any]) -> str:
        """格式化当前故事线"""
        formatted = ""
        
        overall = storyline.get("overall_storyline", {})
        if overall:
            # 处理世界观设定字段（可能是字符串或字典）
            world_setting = overall.get('world_setting', '未知')
            if isinstance(world_setting, dict):
                world_str = f"时代: {world_setting.get('time_period', '未知')}, 地点: {world_setting.get('location', '未知')}, 社会: {world_setting.get('society', '未知')}, 氛围: {world_setting.get('atmosphere', '未知')}"
            else:
                world_str = str(world_setting)
            formatted += f"世界观: {world_str}\n"
            formatted += f"主角目标: {overall.get('main_goal', '未知')}\n"
            # 处理核心冲突字段（可能是conflict或core_conflict）
            conflict = overall.get('conflict', overall.get('core_conflict', '未知'))
            if isinstance(conflict, dict):
                conflict_str = f"外部: {conflict.get('external', '未知')}, 内部: {conflict.get('internal', '未知')}, 人际: {conflict.get('interpersonal', '未知')}"
            else:
                conflict_str = str(conflict)
            formatted += f"核心冲突: {conflict_str}\n"
            formatted += f"故事基调: {overall.get('tone', '未知')}\n"
            formatted += f"故事主题: {', '.join(overall.get('themes', []))}\n\n"
        
        first_module = storyline.get("first_module", {})
        if first_module:
            formatted += f"第一章标题: {first_module.get('chapter_title', '未知')}\n"
            formatted += f"场景设定: {first_module.get('scene_setting', {})}\n"
            formatted += f"情节要点: {first_module.get('plot_points', [])}\n"
            formatted += f"章节结尾: {first_module.get('chapter_ending', '未知')}\n"
        
        return formatted
    
    def _format_character_info(self, main_character: Dict[str, Any], supporting_characters: List[Dict[str, Any]]) -> str:
        """格式化人物信息"""
        formatted = ""
        
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
        
        for char in supporting_characters:
            basic_info = char.get("basic_info", {})
            formatted += f"配角：{basic_info.get('name', '未知')} ({char.get('role', '未知角色')})\n"
            formatted += f"  性格：{char.get('personality', '未知')}\n"
            formatted += f"  与主角关系：{char.get('relationship_with_main', '未知')}\n\n"
        
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
    
    def _format_improvement_suggestions(self, suggestions: List[str]) -> str:
        """格式化改进建议"""
        if not suggestions:
            return "无改进建议"
        
        formatted = ""
        for i, suggestion in enumerate(suggestions, 1):
            formatted += f"{i}. {suggestion}\n"
        
        return formatted
