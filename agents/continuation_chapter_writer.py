"""
续写章节写作智能体
负责基于知识库生成续写章节内容
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationChapterWriter(BaseAgent):
    """续写章节写作智能体"""
    
    def __init__(self):
        super().__init__("续写章节写作智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理续写章节写作请求"""
        storyline = input_data.get("storyline", {})
        knowledge_base = input_data.get("knowledge_base", {})
        user_requirements = input_data.get("user_requirements", "")
        
        if not storyline or not knowledge_base:
            return {"error": "缺少必要的故事线和知识库数据"}
        
        # 生成续写章节内容
        chapter_content = self._write_continuation_chapter(storyline, knowledge_base, user_requirements)
        
        return {
            "success": True,
            "status": "success",
            "chapter_content": chapter_content,
            "word_count": len(chapter_content.get("content", "")),
            "writing_quality": self._assess_writing_quality(chapter_content)
        }
    
    def _write_continuation_chapter(self, storyline: Dict[str, Any], 
                                  knowledge_base: Dict[str, Any], 
                                  user_requirements: str) -> Dict[str, Any]:
        """写作续写章节内容"""
        try:
            # 获取基本信息
            novel_info = knowledge_base.get("novel_info", {})
            character_profiles = knowledge_base.get("character_profiles", {})
            world_setting = knowledge_base.get("world_setting", "")
            story_tone = knowledge_base.get("story_tone", "")
            tags = knowledge_base.get("tags", {})
            last_chapter = knowledge_base.get("last_chapter_summary", {})
            
            # 构建写作提示
            prompt = f"""
            请根据以下信息续写小说《{novel_info.get('title', '未知标题')}》的第{storyline.get('chapter_number', 1)}章。
            
            原文设定：
            1. 世界观：{world_setting}
            2. 故事基调：{story_tone}
            3. 故事标签：{self._format_tags(tags)}
            
            4. 人物档案：
            {self._format_character_profiles(character_profiles)}
            
            5. 上一章结尾：
            {self._format_last_chapter(last_chapter)}
            
            6. 本章故事线：
            {self._format_storyline(storyline)}
            
            7. 用户要求：{user_requirements if user_requirements else "无特殊要求"}
            
            写作要求：
            1. 严格保持与原文的一致性（人物性格、世界观、语言风格）
            2. 合理承接上一章的情节发展
            3. 按照故事线推进情节
            4. 保持原文的写作风格和基调
            5. 设置适当的伏笔和悬念
            6. 语言生动，描写细腻
            7. 小说正文字数必须大于3000字且在3000-5000字之间
            8. 确保情节逻辑自洽
            9. 用你最大的输出能力进行输出
            
            请返回JSON格式：
            {{
                "title": "章节标题",
                "content": "章节正文内容",
                "summary": "章节概要",
                "key_events": ["关键事件1", "关键事件2"],
                "character_development": "人物发展描述",
                "foreshadowing": ["伏笔1", "伏笔2"],
                "next_chapter_hint": "下章预告",
                "consistency_notes": "一致性说明"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的小说续写作家，擅长保持原文风格和逻辑的续写创作。"},
                {"role": "user", "content": prompt}
            ]
            
            # 续写章节写作需要更多token空间，使用最大限制
            response = self.call_llm(messages, max_tokens=config.CHAPTER_MAX_TOKENS)
            result = self.parse_json_response(response)
            
            # 验证和补充结果
            validated_result = self._validate_chapter_content(result, storyline)
            self.log(f"章节内容验证完成，内容长度: {len(validated_result.get('content', ''))}")
            return validated_result
            
        except Exception as e:
            self.log(f"续写章节失败: {e}")
            return self._create_default_chapter(storyline)
    
    def _validate_chapter_content(self, content: Dict[str, Any], storyline: Dict[str, Any]) -> Dict[str, Any]:
        """验证章节内容"""
        # 只补充真正缺失的字段，不覆盖已有的有效内容
        required_fields = {
            "title": storyline.get("chapter_title", f"第{storyline.get('chapter_number', 1)}章"),
            "content": "内容待生成",
            "summary": "章节概要待生成",
            "key_events": [],
            "character_development": "人物发展待描述",
            "foreshadowing": [],
            "next_chapter_hint": "下章预告待生成",
            "consistency_notes": "一致性说明待补充"
        }
        
        # 只补充真正缺失的字段
        for field, default_value in required_fields.items():
            if field not in content:
                content[field] = default_value
            elif not content[field]:  # 字段存在但为空
                content[field] = default_value
            elif isinstance(content[field], str) and content[field].strip() in ["", "待补充", "概要待补充", "未知"]:
                content[field] = default_value
        
        # 特别处理数组字段 - 只处理真正为空的数组
        if not content.get("key_events") or len(content["key_events"]) == 0:
            content["key_events"] = ["关键事件待提取"]
        
        if not content.get("foreshadowing") or len(content["foreshadowing"]) == 0:
            content["foreshadowing"] = ["伏笔设置待分析"]
        
        # 确保包含字数统计
        if 'word_count' not in content:
            chapter_content = content.get('content', '')
            if chapter_content:
                # 计算实际字数（去除空白字符）
                clean_content = chapter_content.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '').replace('\u3000', '')
                content['word_count'] = len(clean_content)
            else:
                content['word_count'] = 0
        
        # 确保包含创建时间
        if 'created_at' not in content:
            from datetime import datetime
            content['created_at'] = datetime.now().isoformat()
        
        return content
    
    
    
    
    
    def _create_default_chapter(self, storyline: Dict[str, Any]) -> Dict[str, Any]:
        """创建默认章节"""
        return {
            "title": storyline.get("chapter_title", f"第{storyline.get('chapter_number', 1)}章"),
            "content": "章节内容生成失败，请检查输入数据。",
            "summary": "概要待补充",
            "key_events": storyline.get("key_events", []),
            "character_development": "待补充",
            "foreshadowing": storyline.get("foreshadowing", []),
            "next_chapter_hint": "待补充",
            "consistency_notes": "内容生成失败"
        }
    
    def _assess_writing_quality(self, chapter_content: Dict[str, Any]) -> Dict[str, Any]:
        """评估写作质量"""
        content = chapter_content.get("content", "")
        
        # 简单的质量评估指标
        word_count = len(content)
        sentence_count = content.count('。') + content.count('！') + content.count('？')
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # 检查是否有对话
        has_dialogue = '"' in content or '"' in content or '「' in content
        
        # 检查是否有环境描写
        has_description = any(word in content for word in ['的', '地', '得', '着', '了', '过'])
        
        # 检查是否有动作描写
        has_action = any(word in content for word in ['走', '跑', '看', '听', '说', '想', '做'])
        
        quality_score = 0
        if 2000 <= word_count <= 3000:
            quality_score += 30
        elif 1500 <= word_count <= 4000:
            quality_score += 20
        
        if 10 <= avg_sentence_length <= 30:
            quality_score += 20
        elif 5 <= avg_sentence_length <= 50:
            quality_score += 10
        
        if has_dialogue:
            quality_score += 20
        
        if has_description:
            quality_score += 15
        
        if has_action:
            quality_score += 15
        
        return {
            "overall_score": min(quality_score, 100),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "has_dialogue": has_dialogue,
            "has_description": has_description,
            "has_action": has_action
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
    
    def _format_storyline(self, storyline: Dict[str, Any]) -> str:
        """格式化故事线"""
        formatted = f"章节标题：{storyline.get('chapter_title', '未知')}\n"
        
        scene_setting = storyline.get("scene_setting", {})
        if scene_setting:
            formatted += f"场景设定：\n"
            formatted += f"  时间：{scene_setting.get('time', '待设定')}\n"
            formatted += f"  地点：{scene_setting.get('location', '待设定')}\n"
            formatted += f"  氛围：{scene_setting.get('atmosphere', '待设定')}\n"
            formatted += f"  天气：{scene_setting.get('weather', '待设定')}\n"
        
        plot_points = storyline.get("plot_points", [])
        if plot_points:
            formatted += f"情节要点：\n"
            for i, point in enumerate(plot_points, 1):
                formatted += f"  {i}. {point}\n"
        
        key_events = storyline.get("key_events", [])
        if key_events:
            formatted += f"关键事件：{', '.join(key_events)}\n"
        
        conflicts = storyline.get("conflicts", [])
        if conflicts:
            formatted += f"冲突：\n"
            for conflict in conflicts:
                formatted += f"  - {conflict.get('description', '未知冲突')}\n"
        
        foreshadowing = storyline.get("foreshadowing", [])
        if foreshadowing:
            formatted += f"伏笔：{', '.join(foreshadowing)}\n"
        
        chapter_ending = storyline.get("chapter_ending", "")
        if chapter_ending:
            formatted += f"章节结尾：{chapter_ending}\n"
        
        writing_notes = storyline.get("writing_notes", "")
        if writing_notes:
            formatted += f"写作注意事项：{writing_notes}\n"
        
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
