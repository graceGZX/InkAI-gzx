"""
人物改进智能体
负责基于质量评估结果改进人物形象
"""
from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class CharacterImprover(BaseAgent):
    """人物改进智能体"""
    
    def __init__(self):
        super().__init__("人物改进智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理人物改进请求"""
        current_characters = input_data.get("current_characters", {})
        overall_storyline = input_data.get("overall_storyline", {})
        improvement_suggestions = input_data.get("improvement_suggestions", [])
        tags = input_data.get("tags", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not current_characters:
            return {"error": "缺少现有人物数据"}
        
        # 如果没有改进建议，使用默认建议
        if not improvement_suggestions:
            improvement_suggestions = [
                "增强人物性格的立体性和复杂性",
                "丰富人物的内心世界和情感层次",
                "完善人物的背景故事和成长轨迹",
                "优化人物之间的关系和互动"
            ]
        
        # 生成改进后的人物形象
        improved_characters = self._improve_characters(
            current_characters, overall_storyline, improvement_suggestions, tags, user_requirements
        )
        
        return {
            "status": "success",
            "improved_characters": improved_characters,
            "improvement_notes": self._generate_improvement_notes(improvement_suggestions)
        }
    
    def _improve_characters(self, current_characters: Dict[str, Any], 
                           overall_storyline: Dict[str, Any],
                           improvement_suggestions: List[str],
                           tags: Dict[str, List[str]],
                           user_requirements: str) -> Dict[str, Any]:
        """改进人物形象"""
        try:
            # 获取基本信息
            main_character = current_characters.get("main_character", {})
            supporting_characters = current_characters.get("supporting_characters", [])
            
            # 构建改进提示
            prompt = f"""
            请基于以下改进建议，对人物形象进行完善和补充：
            
            原文信息：
            1. 故事标签：
            {self._format_tags(tags)}
            
            2. 整体故事线：
            {self._format_storyline_info(overall_storyline)}
            
            3. 用户需求：
            {user_requirements}
            
            当前人物设定（需要改进）：
            {self._format_current_characters(current_characters)}
            
            改进建议：
            {self._format_improvement_suggestions(improvement_suggestions)}
            
            改进要求：
            1. 根据评估建议进行针对性改进
            2. 保持与故事线和标签的一致性
            3. 确保人物性格的立体性和合理性
            4. 提升人物的吸引力和可信度
            5. 保持原有的优秀元素
            6. 为故事发展提供更好的支撑
            
            请返回改进后的JSON格式人物设定：
            {{
                "main_character": {{
                    "basic_info": {{
                        "name": "姓名",
                        "age": 年龄,
                        "gender": "性别",
                        "occupation": "职业"
                    }},
                    "personality": {{
                        "extraversion": 外向性分数(1-10),
                        "agreeableness": 宜人性分数(1-10),
                        "conscientiousness": 尽责性分数(1-10),
                        "neuroticism": 神经质分数(1-10),
                        "openness": 开放性分数(1-10),
                        "description": "改进后的性格描述"
                    }},
                    "appearance": {{
                        "height": "身高",
                        "build": "体型",
                        "distinctive_features": ["标志性特征"],
                        "clothing_style": "着装风格"
                    }},
                    "background": {{
                        "core_desire": "核心欲望",
                        "fear": "主要恐惧",
                        "past_experience": "重要过往经历",
                        "motivation": "行为动机"
                    }},
                    "skills": ["技能1", "技能2"],
                    "relationships": {{
                        "family": "家庭关系",
                        "friends": "朋友关系",
                        "enemies": "敌对关系"
                    }}
                }},
                "supporting_characters": [
                    {{
                        "role": "角色定位",
                        "basic_info": {{
                            "name": "姓名",
                            "age": 年龄,
                            "gender": "性别",
                            "occupation": "职业"
                        }},
                        "personality": "性格描述",
                        "appearance": "外貌描述",
                        "background": "背景故事",
                        "relationship_with_main": "与主角的关系"
                    }}
                ],
                "character_relationships": {{
                    "main_character": "主角姓名",
                    "relationships": [
                        {{
                            "character": "角色姓名",
                            "role": "角色定位",
                            "relationship_type": "关系类型"
                        }}
                    ]
                }},
                "improvement_summary": "改进要点总结"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的人物设定编辑，擅长根据评估建议改进人物形象，提升人物的立体性和吸引力。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.call_llm(messages)
            result = self.parse_json_response(response)
            
            # 验证和补充结果
            return self._validate_improved_characters(result)
            
        except Exception as e:
            self.log(f"改进人物形象失败: {e}")
            return self._create_fallback_characters(current_characters)
    
    def _validate_improved_characters(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证改进后的人物设定结果"""
        # 确保必要字段存在
        required_fields = {
            "main_character": {
                "basic_info": {
                    "name": "待补充",
                    "age": 25,
                    "gender": "待补充",
                    "occupation": "待补充"
                },
                "personality": {
                    "extraversion": 5,
                    "agreeableness": 5,
                    "conscientiousness": 5,
                    "neuroticism": 5,
                    "openness": 5,
                    "description": "待补充"
                },
                "appearance": {
                    "height": "待补充",
                    "build": "待补充",
                    "distinctive_features": [],
                    "clothing_style": "待补充"
                },
                "background": {
                    "core_desire": "待补充",
                    "fear": "待补充",
                    "past_experience": "待补充",
                    "motivation": "待补充"
                },
                "skills": [],
                "relationships": {
                    "family": "待补充",
                    "friends": "待补充",
                    "enemies": "待补充"
                }
            },
            "supporting_characters": [],
            "character_relationships": {
                "main_character": "待补充",
                "relationships": []
            },
            "improvement_summary": "待补充"
        }
        
        # 补充缺失字段
        for field, default_value in required_fields.items():
            if field not in result:
                result[field] = default_value
        
        return result
    
    def _create_fallback_characters(self, current_characters: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用人物设定"""
        return {
            "main_character": current_characters.get("main_character", {}),
            "supporting_characters": current_characters.get("supporting_characters", []),
            "character_relationships": current_characters.get("character_relationships", {}),
            "improvement_summary": "改进功能暂时不可用，使用原人物设定"
        }
    
    def _generate_improvement_notes(self, improvement_suggestions: List[str]) -> Dict[str, Any]:
        """生成改进说明"""
        return {
            "original_suggestions": improvement_suggestions,
            "improvement_focus": "人物立体度、性格合理性、故事适配性",
            "key_improvements": improvement_suggestions[:3] if improvement_suggestions else []
        }
    
    def _format_current_characters(self, characters: Dict[str, Any]) -> str:
        """格式化当前人物设定"""
        formatted = ""
        
        main_character = characters.get("main_character", {})
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
        
        supporting_characters = characters.get("supporting_characters", [])
        
        # 处理supporting_characters可能是字典或列表的情况
        if isinstance(supporting_characters, dict):
            # 如果是字典，遍历值
            char_list = list(supporting_characters.values())
        else:
            # 如果是列表，直接使用
            char_list = supporting_characters
        
        for char in char_list:
            if isinstance(char, dict):
                basic_info = char.get("basic_info", {})
                formatted += f"配角：{basic_info.get('name', '未知')} ({char.get('role', '未知角色')})\n"
                formatted += f"  性格：{char.get('personality', '未知')}\n"
                formatted += f"  与主角关系：{char.get('relationship_with_main', '未知')}\n\n"
            else:
                # 如果char不是字典，跳过或记录错误
                formatted += f"配角：数据格式错误\n\n"
        
        return formatted
    
    def _format_storyline_info(self, storyline: Dict[str, Any]) -> str:
        """格式化故事线信息"""
        if not storyline:
            return "无故事线信息"
        
        formatted = f"""
        世界观: {storyline.get('world_setting', '未知')}
        主角目标: {storyline.get('main_goal', '未知')}
        核心冲突: {storyline.get('conflict', '未知')}
        故事基调: {storyline.get('tone', '未知')}
        故事主题: {', '.join(storyline.get('themes', []))}
        """
        
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
