"""
故事线生成智能体
负责生成整体故事线和第一个模块的故事线
"""
from base_agent import BaseAgent
from typing import Dict, List, Any
import config


class StorylineGeneratorAgent(BaseAgent):
    """故事线生成智能体"""
    
    def __init__(self):
        super().__init__("故事线生成智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理故事线生成请求"""
        selected_tags = input_data.get("selected_tags", {})
        characters = input_data.get("characters", {})
        user_requirements = input_data.get("user_requirements", "")
        
        # 生成整体故事线
        overall_storyline = self._generate_overall_storyline(selected_tags, characters, user_requirements)
        
        # 生成第一个模块故事线
        first_module = self._generate_first_module(overall_storyline, characters, selected_tags)
        
        # 生成暗线伏笔
        subplot_hints = self._generate_subplot_hints(overall_storyline, characters)
        
        return {
            "overall_storyline": overall_storyline,
            "first_module": first_module,
            "subplot_hints": subplot_hints,
            "story_structure": config.STORY_STRUCTURE["三幕剧"]
        }
    
    def _generate_overall_storyline(self, tags: Dict[str, List[str]], characters: Dict[str, Any], requirements: str) -> Dict[str, Any]:
        """生成整体故事线"""
        main_character = characters.get("main_character", {})
        
        prompt = f"""
        你是一位世界级的故事架构师和编剧，请根据以下信息设计一个引人入胜的小说故事线：
        
        【创作背景】
        类型标签：{self._format_tags(tags)}
        目标篇幅：{self._format_word_count_target(tags)}
        主角信息：{self._format_character_info(main_character)}
        用户需求：{requirements}

        【故事设计要求】
        1. 结构完整性：遵循经典三幕剧结构，确保节奏紧凑
        2. 冲突层次性：设计多层次冲突，从外在到内在
        3. 角色驱动：故事要围绕主角的成长和变化展开
        4. 情感共鸣：创造能引起读者情感共鸣的情节
        5. 商业价值：确保故事具有市场吸引力和改编潜力
        6. 篇幅适配：严格依据"目标篇幅"规划全书体量与节奏——短篇紧凑单线、快速收束；中篇单主线带少量支线；长篇多线交织、阶段性高潮；超长篇及巨著需宏大世界观、多势力支线与贯穿全书的长线伏笔。三幕剧的事件密度与支线数量必须与目标篇幅匹配
        
        【专业故事架构】
        请按照以下专业结构设计故事线：
        
        第一幕：建立（25%篇幅）
        - 世界观构建：创造独特而可信的故事世界
        - 角色介绍：展现主角的初始状态和核心特质
        - 目标设定：明确主角的追求和动机
        - 冲突引入：建立主要冲突和对抗力量
        - 关键事件：设计改变主角生活的转折事件
        - 第一幕结尾：设置悬念，推动进入第二幕
        
        第二幕：对抗（50%篇幅）
        - 障碍升级：主角面临越来越大的挑战
        - 关系发展：深化角色间的关系和冲突
        - 技能成长：主角在挑战中获得成长
        - 中期危机：故事中点的重大转折
        - 低谷时刻：主角面临最大挫折
        - 转折点：主角找到新的解决方案或力量
        - 高潮准备：为最终对决做准备
        
        第三幕：解决（25%篇幅）
        - 最终对决：主角与主要对手的终极较量
        - 冲突解决：解决所有主要冲突和悬念
        - 角色成长：展现主角的最终变化
        - 主题升华：深化故事主题和意义
        - 满意结局：给读者带来情感满足
        
        【输出要求】
        请返回详细的JSON格式故事线：
        {{
            "world_setting": {{
                "time_period": "时代背景",
                "location": "主要地点",
                "society": "社会结构",
                "rules": "世界规则",
                "atmosphere": "整体氛围"
            }},
            "main_goal": "主角的终极目标",
            "core_conflict": {{
                "external": "外在冲突（与环境的对抗）",
                "internal": "内在冲突（内心的挣扎）",
                "interpersonal": "人际冲突（与他人的对抗）"
            }},
            "act1": {{
                "setup": "第一幕设定（详细描述）",
                "inciting_incident": "引发事件",
                "key_events": ["关键事件1", "关键事件2", "关键事件3"],
                "character_introduction": "角色介绍方式",
                "world_building": "世界观建立",
                "ending": "第一幕结尾（悬念设置）"
            }},
            "act2": {{
                "confrontation": "第二幕主要冲突",
                "obstacles": ["障碍1", "障碍2", "障碍3"],
                "character_development": "角色发展轨迹",
                "midpoint_crisis": "中点危机",
                "low_point": "低谷时刻",
                "turning_point": "转折点",
                "climax_preparation": "高潮准备"
            }},
            "act3": {{
                "climax": "高潮对决（详细描述）",
                "resolution": "冲突解决方式",
                "character_transformation": "角色最终变化",
                "theme_revelation": "主题揭示",
                "ending": "故事结局"
            }},
            "themes": ["深层主题1", "深层主题2", "深层主题3"],
            "tone": "故事基调和风格",
            "target_audience": "目标读者群体",
            "commercial_potential": "商业价值分析",
            "adaptation_potential": "改编潜力评估"
        }}
        """
        
        messages = [
            {"role": "system", "content": """你是一位世界级的故事架构师、编剧和创意总监，拥有以下专业背景：

1. 故事理论专长：精通各种故事结构和叙事理论
2. 编剧经验：参与过众多成功影视作品的剧本创作
3. 市场洞察：了解不同受众的喜好和市场需求
4. 创意指导：指导过无数创作者提升故事质量
5. 商业经验：具备将创意转化为商业价值的能力

你的设计原则：
- 结构严谨：遵循经典故事结构，确保逻辑清晰
- 情感驱动：以情感为核心，创造读者共鸣
- 角色中心：围绕角色成长设计情节发展
- 冲突丰富：构建多层次、多角度的冲突体系
- 商业价值：确保故事具有市场吸引力和改编潜力

请用专业、创新、商业化的思维完成故事线设计任务。"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_storyline(result)
    
    def _generate_first_module(self, storyline: Dict[str, Any], characters: Dict[str, Any], tags: Dict[str, List[str]]) -> Dict[str, Any]:
        """生成第一个模块（第一章）故事线"""
        main_character = characters.get("main_character", {})
        supporting_characters = characters.get("supporting_characters", [])
        
        prompt = f"""
        基于整体故事线，详细设计第一章的内容，小说第一章是开篇，小说情节跟内容需要足够吸引读者：
        
        整体故事线：
        {self._format_storyline_info(storyline)}
        
        主角信息：
        {self._format_character_info(main_character)}
        
        配角信息：
        {self._format_supporting_characters(supporting_characters)}
        
        故事标签：
        {self._format_tags(tags)}
        
        请设计第一章的详细内容：
        
        返回JSON格式：
        {{
            "chapter_title": "章节标题",
            "scene_setting": {{
                "time": "时间设定",
                "location": "地点设定",
                "atmosphere": "环境氛围"
            }},
            "plot_points": [
                {{
                    "event": "事件描述",
                    "purpose": "事件目的",
                    "characters_involved": ["参与角色"],
                    "tension_level": "紧张程度(1-10)"
                }}
            ],
            "character_development": {{
                "main_character": "主角在本章的发展",
                "supporting_characters": "配角在本章的表现"
            }},
            "foreshadowing": ["伏笔1", "伏笔2"],
            "chapter_ending": "章节结尾",
            "hook": "吸引读者继续阅读的钩子"
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的小说章节设计师，擅长设计引人入胜的开篇章节。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_first_module(result)
    
    def _generate_subplot_hints(self, storyline: Dict[str, Any], characters: Dict[str, Any]) -> Dict[str, Any]:
        """生成暗线伏笔"""
        prompt = f"""
        为故事设计暗线伏笔：
        
        主线故事：
        {self._format_storyline_info(storyline)}
        
        人物关系：
        {self._format_character_relationships(characters)}
        
        请设计2-3条暗线，包括：
        1. 暗线主题
        2. 伏笔设置
        3. 揭露时机
        4. 与主线的关联
        
        返回JSON格式：
        {{
            "subplots": [
                {{
                    "theme": "暗线主题",
                    "hints": [
                        {{
                            "type": "伏笔类型(对话/物品/场景)",
                            "content": "伏笔内容",
                            "chapter": "出现章节",
                            "reveal_chapter": "揭露章节"
                        }}
                    ],
                    "connection_to_main": "与主线的关联"
                }}
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事结构设计师，擅长设计巧妙的伏笔和暗线。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return result
    
    def _format_tags(self, tags: Dict[str, List[str]]) -> str:
        """格式化标签信息"""
        if not tags:
            return "无标签信息"
        
        formatted = ""
        for category, tag_list in tags.items():
            if tag_list and isinstance(tag_list, list):
                formatted += f"{category}: {', '.join(tag_list)}\n"
            else:
                formatted += f"{category}: 无标签\n"
        return formatted

    def _format_word_count_target(self, tags: Dict[str, List[str]]) -> str:
        """从标签中提取目标篇幅档位，供故事线规划体量参考"""
        word_count_tags = (tags or {}).get("字数标签") or []
        if word_count_tags and isinstance(word_count_tags, list):
            return word_count_tags[0]
        return "未指定（默认按长篇（30-80万字）规划）"

    def _format_character_info(self, character: Dict[str, Any]) -> str:
        """格式化人物信息"""
        if not character:
            return "无人物信息"
        
        basic_info = character.get("basic_info", {})
        background = character.get("background", {})
        
        return f"""
        姓名: {basic_info.get('name', '未知')}
        年龄: {basic_info.get('age', '未知')}
        职业: {basic_info.get('occupation', '未知')}
        核心欲望: {background.get('core_desire', '未知')}
        主要恐惧: {background.get('fear', '未知')}
        """
    
    def _format_supporting_characters(self, characters: List[Dict[str, Any]]) -> str:
        """格式化配角信息"""
        if not characters:
            return "无配角信息"
        
        formatted = ""
        for char in characters:
            basic_info = char.get("basic_info", {})
            formatted += f"- {basic_info.get('name', '未知')} ({char.get('role', '未知角色')}): {char.get('personality', '未知性格')}\n"
        
        return formatted
    
    def _format_storyline_info(self, storyline: Dict[str, Any]) -> str:
        """格式化故事线信息"""
        return f"""
        世界观: {storyline.get('world_setting', '未知')}
        主角目标: {storyline.get('main_goal', '未知')}
        核心冲突: {storyline.get('conflict', '未知')}
        故事基调: {storyline.get('tone', '未知')}
        """
    
    def _format_character_relationships(self, characters: Dict[str, Any]) -> str:
        """格式化人物关系"""
        relationships = characters.get("character_relationships", {})
        if not relationships:
            return "无关系信息"
        
        formatted = f"主角: {relationships.get('main_character', '未知')}\n"
        for rel in relationships.get("relationships", []):
            formatted += f"- {rel.get('character', '未知')}: {rel.get('relationship_type', '未知关系')}\n"
        
        return formatted
    
    def _validate_storyline(self, storyline: Dict[str, Any]) -> Dict[str, Any]:
        """验证故事线"""
        required_keys = ["world_setting", "main_goal", "conflict", "act1", "act2", "act3"]
        
        for key in required_keys:
            if key not in storyline:
                storyline[key] = {}
        
        return storyline
    
    def _validate_first_module(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """验证第一个模块"""
        required_keys = ["chapter_title", "scene_setting", "plot_points", "chapter_ending"]
        
        for key in required_keys:
            if key not in module:
                if key == "plot_points":
                    module[key] = []
                elif key == "scene_setting":
                    module[key] = {}
                else:
                    module[key] = "待补充"
        
        return module
