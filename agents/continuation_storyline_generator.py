"""
续写故事线生成智能体
负责生成下一章的故事线进度逻辑
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationStorylineGenerator(BaseAgent):
    """续写故事线生成智能体"""
    
    def __init__(self):
        super().__init__("续写故事线生成智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成续写故事线"""
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not knowledge_base:
            return {"error": "缺少知识库数据"}
        
        # 生成下一章的故事线
        next_chapter_storyline = self._generate_next_chapter_storyline(knowledge_base, user_requirements)
        
        return {
            "success": True,
            "status": "success",
            "next_chapter_storyline": next_chapter_storyline,
            "next_step": "chapter_writing"
        }
    
    def _generate_next_chapter_storyline(self, knowledge_base: Dict[str, Any], 
                                       user_requirements: str) -> Dict[str, Any]:
        """生成下一章故事线"""
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
            
            # 确定下一章号
            next_chapter_number = len(chapters) + 1
            
            # 构建生成提示
            prompt = f"""
            请为小说《{novel_info.get('title', '未知标题')}》生成第{next_chapter_number}章的故事线。
            
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
            
            请生成第{next_chapter_number}章的详细故事线，要求：
            1. 合理承接上一章的情节发展
            2. 推进主线故事发展
            3. 保持人物性格一致性
            4. 符合世界观设定
            5. 设置适当的伏笔和悬念
            6. 保持故事节奏和基调
            7. 为后续章节发展留下空间
            
            请返回JSON格式：
            {{
                "chapter_number": {next_chapter_number},
                "chapter_title": "章节标题",
                "scene_setting": {{
                    "time": "时间设定",
                    "location": "地点设定",
                    "atmosphere": "氛围描述",
                    "weather": "天气状况"
                }},
                "plot_points": [
                    "情节要点1",
                    "情节要点2",
                    "情节要点3"
                ],
                "character_interactions": [
                    {{
                        "characters": ["角色1", "角色2"],
                        "interaction_type": "对话/冲突/合作",
                        "purpose": "互动目的"
                    }}
                ],
                "key_events": [
                    "关键事件1",
                    "关键事件2"
                ],
                "conflicts": [
                    {{
                        "type": "内心冲突/外部冲突/人际冲突",
                        "description": "冲突描述",
                        "resolution": "解决方式"
                    }}
                ],
                "foreshadowing": [
                    "伏笔1",
                    "伏笔2"
                ],
                "character_development": {{
                    "main_character": "主角在本章的发展",
                    "supporting_characters": "配角的发展"
                }},
                "chapter_ending": "章节结尾描述",
                "next_chapter_hint": "下章预告",
                "writing_notes": "写作注意事项"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的故事策划师，擅长创作连贯且引人入胜的故事线。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 检查解析结果
            if not result or not isinstance(result, dict):
                self.log(f"JSON解析结果无效: {result}")
                return self._create_default_storyline(next_chapter_number)
            
            # 验证和补充结果
            return self._validate_storyline_result(result, next_chapter_number)
            
        except Exception as e:
            self.log(f"生成故事线失败: {e}")
            return self._create_default_storyline(len(chapters) + 1)
    
    def _validate_storyline_result(self, result: Dict[str, Any], chapter_number: int) -> Dict[str, Any]:
        """验证故事线结果"""
        try:
            # 确保result是字典类型
            if not isinstance(result, dict):
                self.log(f"故事线结果不是字典类型: {type(result)}")
                return self._create_default_storyline(chapter_number)
            
            # 确保必要字段存在
            required_fields = {
                "chapter_number": chapter_number,
                "chapter_title": f"第{chapter_number}章",
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
                "writing_notes": "待补充"
            }
            
            # 补充缺失字段
            for field, default_value in required_fields.items():
                if field not in result:
                    result[field] = default_value
            
            return result
            
        except Exception as e:
            self.log(f"验证故事线结果失败: {e}")
            return self._create_default_storyline(chapter_number)
    
    def _create_default_storyline(self, chapter_number: int) -> Dict[str, Any]:
        """创建默认故事线"""
        return {
            "chapter_number": chapter_number,
            "chapter_title": f"第{chapter_number}章",
            "scene_setting": {
                "time": "待设定",
                "location": "待设定",
                "atmosphere": "待设定",
                "weather": "待设定"
            },
            "plot_points": ["情节发展待补充"],
            "character_interactions": [],
            "key_events": ["关键事件待补充"],
            "conflicts": [],
            "foreshadowing": [],
            "character_development": {
                "main_character": "待补充",
                "supporting_characters": "待补充"
            },
            "chapter_ending": "待补充",
            "next_chapter_hint": "待补充",
            "writing_notes": "请根据原文设定补充具体内容"
        }
    
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
