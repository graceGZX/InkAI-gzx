"""
续写质量评估智能体
专门评估续写内容与原文的一致性
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config


class ContinuationQualityAssessor(BaseAgent):
    """续写质量评估智能体"""
    
    def __init__(self):
        super().__init__("续写质量评估智能体")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估续写内容质量"""
        continuation_content = input_data.get("continuation_content", {})
        original_knowledge_base = input_data.get("original_knowledge_base", {})
        content_type = input_data.get("content_type", "story")
        
        if not continuation_content or not original_knowledge_base:
            return {"error": "缺少必要的评估数据"}
        
        # 进行一致性评估
        assessment_result = self._assess_consistency(continuation_content, original_knowledge_base, content_type)
        
        return assessment_result
    
    def _assess_consistency(self, continuation_content: Dict[str, Any], 
                          knowledge_base: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """评估一致性"""
        try:
            if content_type == "story":
                return self._assess_story_consistency(continuation_content, knowledge_base)
            elif content_type == "storyline":
                return self._assess_storyline_consistency(continuation_content, knowledge_base)
            elif content_type == "character":
                return self._assess_character_consistency(continuation_content, knowledge_base)
            else:
                return self._assess_general_consistency(continuation_content, knowledge_base)
        except Exception as e:
            self.log(f"一致性评估失败: {e}")
            return {
                "is_high_quality": False,
                "overall_score": 0,
                "dimensions": {},
                "suggestions": [f"评估过程出错: {str(e)}"]
            }
    
    def _assess_story_consistency(self, chapter_content: Dict[str, Any],
                                knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事内容一致性"""
        content = chapter_content.get("content", "")
        character_profiles = knowledge_base.get("character_profiles", {})
        last_chapter = knowledge_base.get("last_chapter_summary", {})
        recent_chapters = knowledge_base.get("recent_chapters_summaries", [])
        vector_chapters = knowledge_base.get("vector_retrieved_chapters", [])
        world_setting = knowledge_base.get("world_setting", "")
        story_tone = knowledge_base.get("story_tone", "")

        # 构建评估提示
        prompt = f"""
        请评估以下续写章节与原文的一致性，重点关注以下维度：

        原文设定：
        1. 人物设定：
        {self._format_character_profiles(character_profiles)}

        2. 世界观设定：
        {world_setting}

        3. 故事基调：
        {story_tone}

        4. 最近几章实际剧情（用于对照人物行为是否一致、场景是否重复）：
        {self._format_recent_chapters(recent_chapters)}

        5. 语义关联的历史章节（用于检查伏笔回收和前后呼应）：
        {self._format_vector_chapters(vector_chapters)}

        6. 动态知识（角色实际发展轨迹/情节时间线/活跃伏笔/世界观变化——用于校验新章是否矛盾）：
        {self._format_dynamic_knowledge(knowledge_base)}

        7. 上一章结尾：
        {self._format_last_chapter(last_chapter)}

        8. 上一章结尾原文（用于检查本章开头是否逐字复制了上一章结尾）：
        {self._format_ending_text(last_chapter)}

        续写章节内容：
        {content}

        请从以下维度评估一致性（每项0-100分）：
        1. 人物一致性：人物行为、语言、性格是否符合原设定
        2. 情节连贯性：是否合理承接上一章，逻辑是否自洽
        3. 世界观一致性：是否符合原文的世界观设定
        4. 伏笔延续性：是否延续了原文的伏笔线索
        5. 语言风格一致性：是否保持原文的语言风格和基调
        6. 场景衔接质量：本章开头是否自然承接上一章结尾的场景/情绪，是否逐字复制了上一章结尾的原文，章末钩子是否有效

        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "character_consistency": 90,
                "plot_continuity": 85,
                "world_consistency": 80,
                "foreshadowing_continuity": 85,
                "style_consistency": 85,
                "scene_bridging": 80
            }},
            "is_high_quality": true,
            "suggestions": [
                "人物行为符合原设定",
                "情节发展合理",
                "建议加强环境描写"
            ],
            "detailed_analysis": {{
                "character_analysis": "人物行为符合原设定...",
                "plot_analysis": "情节发展合理...",
                "world_analysis": "世界观保持一致...",
                "foreshadowing_analysis": "伏笔处理得当...",
                "style_analysis": "语言风格一致...",
                "scene_bridging_analysis": "场景衔接分析..."
            }}
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的小说编辑，擅长评估续写内容与原文的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        # 验证和补充结果
        return self._validate_assessment_result(result)
    
    def _assess_storyline_consistency(self, storyline_content: Dict[str, Any], 
                                    knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估故事线一致性"""
        plot_lines = knowledge_base.get("plot_lines", {})
        last_chapter = knowledge_base.get("last_chapter_summary", {})
        
        prompt = f"""
        请评估以下续写故事线与原文的一致性：
        
        原文故事线：
        {self._format_plot_lines(plot_lines)}
        
        上一章结尾：
        {self._format_last_chapter(last_chapter)}
        
        续写故事线：
        {storyline_content}
        
        请从以下维度评估故事线的连贯性和合理性（每项0-100分）：
        1. 情节连贯性：是否合理承接上一章，逻辑是否自洽
        2. 人物发展一致性：人物行为和发展是否符合原设定
        3. 世界观一致性：是否符合原文的世界观设定
        4. 伏笔延续性：是否延续了原文的伏笔线索
        5. 风格一致性：是否保持原文的叙述风格和基调
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "plot_continuity": 90,
                "character_consistency": 85,
                "world_consistency": 80,
                "foreshadowing_continuity": 85,
                "style_consistency": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "情节发展合理",
                "人物行为符合设定",
                "建议加强某个方面"
            ],
            "detailed_analysis": {{
                "plot_analysis": "情节连贯性分析...",
                "character_analysis": "人物发展分析...",
                "world_analysis": "世界观一致性分析...",
                "foreshadowing_analysis": "伏笔延续性分析...",
                "style_analysis": "风格一致性分析..."
            }}
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的故事编辑，擅长评估故事线的连贯性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_character_consistency(self, character_content: Dict[str, Any], 
                                    knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """评估人物一致性"""
        original_characters = knowledge_base.get("character_profiles", {})
        
        prompt = f"""
        请评估以下续写人物设定与原文的一致性：
        
        原文人物设定：
        {self._format_character_profiles(original_characters)}
        
        续写人物设定：
        {character_content}
        
        请从以下维度评估人物设定的一致性（每项0-100分）：
        1. 性格一致性：人物性格特征是否与原设定一致
        2. 行为逻辑一致性：人物行为是否符合其性格和背景
        3. 语言风格一致性：人物语言风格是否与原文一致
        4. 关系发展合理性：人物关系发展是否合理
        5. 成长轨迹连贯性：人物成长是否符合发展轨迹
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "character_consistency": 90,
                "behavior_consistency": 85,
                "language_consistency": 80,
                "relationship_consistency": 85,
                "growth_consistency": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "人物性格表现符合原设定",
                "行为逻辑合理",
                "建议加强某个方面"
            ],
            "detailed_analysis": {{
                "character_analysis": "人物性格一致性分析...",
                "behavior_analysis": "行为逻辑分析...",
                "language_analysis": "语言风格分析...",
                "relationship_analysis": "关系发展分析...",
                "growth_analysis": "成长轨迹分析..."
            }}
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的人物设定编辑，擅长评估人物设定的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _assess_general_consistency(self, content: Dict[str, Any], 
                                  knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """通用一致性评估"""
        prompt = f"""
        请评估以下续写内容与原文的一致性：
        
        原文知识库：
        {self._format_knowledge_base_summary(knowledge_base)}
        
        续写内容：
        {content}
        
        请从以下维度进行综合评估（每项0-100分）：
        1. 整体一致性：续写内容与原文的整体一致程度
        2. 逻辑连贯性：内容逻辑是否连贯合理
        3. 风格统一性：写作风格是否与原文统一
        4. 质量水准：内容质量是否达到原文水准
        5. 创新合理性：新增内容是否合理且有创新价值
        
        请返回JSON格式：
        {{
            "overall_score": 85,
            "dimensions": {{
                "overall_consistency": 90,
                "logic_continuity": 85,
                "style_unity": 80,
                "quality_standard": 85,
                "innovation_reasonableness": 85
            }},
            "is_high_quality": true,
            "suggestions": [
                "整体一致性良好",
                "逻辑连贯合理",
                "建议加强某个方面"
            ],
            "detailed_analysis": {{
                "consistency_analysis": "整体一致性分析...",
                "logic_analysis": "逻辑连贯性分析...",
                "style_analysis": "风格统一性分析...",
                "quality_analysis": "质量水准分析...",
                "innovation_analysis": "创新合理性分析..."
            }}
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的内容编辑，擅长评估续写内容的一致性。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages)
        result = self.parse_json_response(response)
        
        return self._validate_assessment_result(result)
    
    def _validate_assessment_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证评估结果，适配LLM的实际输出格式"""
        
        # 检查LLM输出格式并转换
        if "evaluation" in result and isinstance(result["evaluation"], dict):
            print("🔧 检测到LLM嵌套格式，开始转换...")
            evaluation = result["evaluation"]
            result = self._convert_llm_evaluation_format(evaluation)
        elif self._is_direct_llm_format(result):
            print("🔧 检测到LLM直接格式，开始转换...")
            result = self._convert_direct_llm_format(result)
        
        # 确保必要字段存在（兜底逻辑）
        if "overall_score" not in result:
            # 尝试从dimensions计算总分
            dimensions = result.get("dimensions", {})
            if dimensions:
                total = sum(score for score in dimensions.values() if isinstance(score, (int, float)))
                count = len([score for score in dimensions.values() if isinstance(score, (int, float))])
                result["overall_score"] = total / count if count > 0 else 75
            else:
                result["overall_score"] = 75
        
        if "is_high_quality" not in result:
            result["is_high_quality"] = result.get("overall_score", 0) >= config.QUALITY_THRESHOLD

        # 场景衔接质量单独设最低分：低于 60 则强制打回
        dimensions = result.get("dimensions", {})
        scene_bridging_score = dimensions.get("scene_bridging")
        if scene_bridging_score is not None and scene_bridging_score < 60:
            original = result.get("is_high_quality", False)
            result["is_high_quality"] = False
            if "suggestions" not in result:
                result["suggestions"] = []
            result["suggestions"].insert(0,
                f"场景衔接质量({scene_bridging_score}分)不达标：请检查章节开头是否逐字复制了上一章结尾、是否自然承接场景/情绪")
            print(f"⚠️ scene_bridging 得分 {scene_bridging_score} < 60，强制打回（原判定: {original}）")

        if "suggestions" not in result:
            result["suggestions"] = []
        
        if "dimensions" not in result:
            result["dimensions"] = {}
        
        # 确保分数在合理范围内
        result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        print(f"✅ 最终评估结果: 总分{result['overall_score']}, 建议{len(result['suggestions'])}条, 维度{len(result['dimensions'])}个")
        
        return result
    
    def _convert_llm_evaluation_format(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """转换LLM的evaluation格式为系统期望的格式"""
        converted_result = {}
        
        # 1. 转换总分（优先级顺序）
        score_priority = ["overall_coherence", "plot_consistency", "character_consistency", "consistency_score"]
        for field in score_priority:
            if field in evaluation and isinstance(evaluation[field], (int, float)):
                base_score = evaluation[field]
                converted_result["overall_score"] = int(base_score * 10)  # 0-10 -> 0-100
                print(f"✅ 转换总分: {base_score} -> {converted_result['overall_score']}")
                break
        
        # 如果没有找到合适的总分，计算平均分
        if "overall_score" not in converted_result:
            score_fields = ["plot_consistency", "character_consistency", "foreshadowing_handling", "new_elements_integration"]
            scores = []
            for field in score_fields:
                if field in evaluation and isinstance(evaluation[field], (int, float)):
                    scores.append(evaluation[field])
            
            if scores:
                avg_score = sum(scores) / len(scores)
                converted_result["overall_score"] = int(avg_score * 10)
                print(f"✅ 计算平均分: {avg_score} -> {converted_result['overall_score']}")
            else:
                converted_result["overall_score"] = 75
        
        # 2. 转换维度评分
        dimensions = {}
        dimension_mapping = {
            # 实际LLM输出的字段 -> 系统期望的字段
            "coherence_score": "style_consistency",
            "consistency_score": "character_consistency",
            "plot_development": "plot_continuity",
            "character_development": "character_consistency", 
            "world_building": "world_consistency",
            "foreshadowing": "foreshadowing_continuity",
            # 兼容其他可能的字段名
            "character_consistency": "character_consistency",
            "plot_consistency": "plot_continuity", 
            "foreshadowing_handling": "foreshadowing_continuity",
            "new_elements_integration": "world_consistency",
            "overall_coherence": "style_consistency"
        }
        
        for llm_field, system_field in dimension_mapping.items():
            if llm_field in evaluation:
                value = evaluation[llm_field]
                # 处理数值类型
                if isinstance(value, (int, float)):
                    score = int(value * 10) if value <= 10 else int(value)
                    dimensions[system_field] = score
                    print(f"  ✅ {llm_field} ({value}) -> {system_field} ({score})")
                # 处理文字评级
                elif isinstance(value, str):
                    score_map = {"优秀": 90, "良好": 80, "一般": 70, "较差": 60, "不合格": 50}
                    score = score_map.get(value, 75)
                    dimensions[system_field] = score
                    print(f"  ✅ {llm_field} ('{value}') -> {system_field} ({score})")
                else:
                    print(f"  ⚠️ {llm_field}: 未知类型 {type(value)}")
        
        converted_result["dimensions"] = dimensions
        print(f"✅ 转换维度评分: {len(dimensions)}个维度")
        
        # 3. 提取建议
        converted_result["suggestions"] = evaluation.get("suggestions", [])
        print(f"✅ 提取建议: {len(converted_result['suggestions'])}条")
        
        # 4. 构建详细分析
        detailed_analysis = {}
        analysis_fields = ["strengths", "weaknesses", "conclusion", "character_analysis", "plot_analysis", "world_analysis"]
        for field in analysis_fields:
            if field in evaluation:
                detailed_analysis[field] = evaluation[field]
        
        converted_result["detailed_analysis"] = detailed_analysis
        print(f"✅ 构建详细分析: {len(detailed_analysis)}个字段")
        
        return converted_result
    
    def _is_direct_llm_format(self, result: Dict[str, Any]) -> bool:
        """检测是否是LLM的直接输出格式"""
        # 检查是否包含LLM常用的直接字段
        llm_indicators = ["score", "recommendations", "overall_consistency", "strengths", "weaknesses"]
        return any(field in result for field in llm_indicators)
    
    def _convert_direct_llm_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换LLM的直接输出格式"""
        converted_result = {}
        
        # 1. 转换总分
        if "score" in result and isinstance(result["score"], (int, float)):
            # 如果是0-10分制，转换为0-100分制
            score = result["score"]
            if score <= 10:
                converted_result["overall_score"] = int(score * 10)
                print(f"✅ 转换总分(0-10制): {score} -> {converted_result['overall_score']}")
            else:
                converted_result["overall_score"] = int(score)
                print(f"✅ 使用总分(0-100制): {score}")
        else:
            # 尝试从各维度计算平均分
            score_fields = ["plot_consistency", "character_consistency", "setting_consistency", "tone_consistency"]
            scores = []
            for field in score_fields:
                if field in result and isinstance(result[field], (int, float)):
                    score = result[field]
                    # 转换为0-100分制
                    if score <= 10:
                        scores.append(score * 10)
                    else:
                        scores.append(score)
            
            if scores:
                converted_result["overall_score"] = int(sum(scores) / len(scores))
                print(f"✅ 计算平均分: {scores} -> {converted_result['overall_score']}")
            else:
                converted_result["overall_score"] = 75
                print("⚠️ 无法找到评分字段，使用默认75分")
        
        # 2. 转换维度评分
        dimensions = {}
        dimension_mapping = {
            "character_consistency": "character_consistency",
            "plot_consistency": "plot_continuity", 
            "setting_consistency": "world_consistency",
            "tone_consistency": "style_consistency"
        }
        
        for llm_field, system_field in dimension_mapping.items():
            if llm_field in result and isinstance(result[llm_field], (int, float)):
                score = result[llm_field]
                # 转换为0-100分制
                if score <= 10:
                    dimensions[system_field] = int(score * 10)
                else:
                    dimensions[system_field] = int(score)
        
        converted_result["dimensions"] = dimensions
        print(f"✅ 转换维度评分: {len(dimensions)}个维度")
        
        # 3. 转换建议
        suggestions = []
        if "recommendations" in result:
            suggestions = result["recommendations"]
        elif "suggestions" in result:
            suggestions = result["suggestions"]
        
        if not isinstance(suggestions, list):
            suggestions = []
        
        converted_result["suggestions"] = suggestions
        print(f"✅ 提取建议: {len(suggestions)}条")
        
        # 4. 构建详细分析
        detailed_analysis = {}
        analysis_fields = ["strengths", "weaknesses", "summary", "overall_consistency"]
        for field in analysis_fields:
            if field in result:
                detailed_analysis[field] = result[field]
        
        converted_result["detailed_analysis"] = detailed_analysis
        print(f"✅ 构建详细分析: {len(detailed_analysis)}个字段")
        
        return converted_result
    
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
    
    def _format_recent_chapters(self, recent_chapters: list) -> str:
        """格式化最近几章摘要，供评估器对照"""
        if not recent_chapters:
            return "无最近章节信息"
        formatted = ""
        for ch in recent_chapters:
            formatted += f"第{ch.get('chapter_number', 0)}章《{ch.get('title', '')}》\n"
            formatted += f"  概要：{ch.get('summary', '')}\n"
            events = ch.get("key_events", [])
            if events:
                formatted += "  关键事件：\n"
                for ev in events:
                    formatted += f"    - {ev}\n"
            formatted += "\n"
        return formatted

    def _format_vector_chapters(self, vector_chapters: list) -> str:
        """格式化向量检索到的关联章节"""
        if not vector_chapters:
            return "无语义关联章节"
        formatted = ""
        for ch in vector_chapters:
            formatted += f"第{ch.get('chapter_number', 0)}章《{ch.get('title', '')}》（相关度: {ch.get('relevance_score', 0)}）\n"
            formatted += f"  概要：{ch.get('summary', '')}\n"
            events = ch.get("key_events", [])
            if events:
                formatted += "  关键事件：\n"
                for ev in events:
                    formatted += f"    - {ev}\n"
            formatted += "\n"
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

    def _format_ending_text(self, last_chapter: Dict[str, Any]) -> str:
        """格式化上一章结尾原文，用于评估章节开头是否复制"""
        ending = last_chapter.get("ending_text", "")
        if not ending:
            return "无上一章结尾文本"
        return f"「{ending}」"
    
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
    
    def _format_knowledge_base_summary(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化知识库摘要"""
        summary = f"小说标题：{knowledge_base.get('novel_info', {}).get('title', '未知')}\n"
        summary += f"章节数：{len(knowledge_base.get('chapters', []))}\n"
        summary += f"世界观：{knowledge_base.get('world_setting', '未知')}\n"
        summary += f"故事基调：{knowledge_base.get('story_tone', '未知')}\n"
        
        return summary

    def _format_dynamic_knowledge(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化动态知识——优先使用语义检索结果，回退全量截断模式"""
        semantic = knowledge_base.get("dynamic_knowledge_semantic")
        if semantic:
            return self._format_semantic_dk(semantic)
        return self._format_full_dk(knowledge_base.get("dynamic_knowledge", {}))

    def _format_semantic_dk(self, semantic: Dict[str, Any]) -> str:
        parts = []
        labels = {"character_evolution": "【相关角色发展（语义匹配）】", "plot_events": "【相关情节事件（语义匹配）】",
                  "foreshadowing": "【相关伏笔（语义匹配）】", "world_changes": "【相关世界观揭示（语义匹配）】",
                  "chapter_summaries": "【相关章节摘要（语义匹配）】"}
        for dtype, label in labels.items():
            items = semantic.get(dtype, [])
            if items:
                lines = [f"  [{item.get('chapter', '?')}章 | 相关度:{item.get('score', 0):.2f}] {item.get('text', '')[:200]}" for item in items]
                parts.append(f"{label}\n" + "\n".join(lines))
        return "\n\n".join(parts) if parts else "（无相关动态知识）"

    def _format_full_dk(self, dk: Dict[str, Any]) -> str:
        """格式化全量动态知识（兜底——全书分层抽样，不只看最近N条）"""
        if not dk:
            return "暂无动态知识数据"

        parts = []

        # 角色发展：每人每5章取1条里程碑，最多每人5条
        char_evo = dk.get("character_evolution", {})
        if char_evo:
            lines = []
            for name, records in char_evo.items():
                if isinstance(records, list) and records:
                    sorted_recs = sorted(records, key=lambda r: r.get("chapter_number", 0))
                    milestones = [r for i, r in enumerate(sorted_recs) if i % 5 == 0 or i == len(sorted_recs) - 1][-5:]
                    events = [f"  第{r.get('chapter_number', '?')}章: {r.get('description', '')[:80]}" for r in milestones]
                    lines.append(f"  {name}:\n" + "\n".join(events))
            if lines:
                parts.append("【角色发展轨迹（全书里程碑）】\n" + "\n".join(lines))

        # 情节时间线：每章取1-2个高重要性事件，最多20条
        plot_timeline = dk.get("plot_timeline", [])
        if plot_timeline:
            by_ch = {}
            for e in plot_timeline:
                ch = e.get("chapter_number", 0)
                by_ch.setdefault(ch, []).append(e)
            sampled = []
            for ch in sorted(by_ch.keys()):
                ch_events = sorted(by_ch[ch], key=lambda e: 0 if e.get("importance") == "high" else 1)
                sampled.extend(ch_events[:2])
                if len(sampled) >= 20:
                    break
            events = [f"  第{e.get('chapter_number', '?')}章 [{e.get('event_type', 'plot')}] {e.get('description', '')[:100]}" for e in sampled[:20]]
            parts.append("【情节时间线（全书分层抽样）】\n" + "\n".join(events))

        # 伏笔：活跃的全部展示（按重要性排序，high优先，最多15条）
        foreshadowing = dk.get("foreshadowing_tracking", {})
        if foreshadowing:
            all_active = []
            for ftype, flist in foreshadowing.items():
                if isinstance(flist, list):
                    for f in flist:
                        if f.get("status") == "active":
                            all_active.append((f.get("importance", "medium") != "high", f))
            all_active.sort(key=lambda x: x[0])
            active = [f"  [{ftype}] 第{f.get('chapter_number', '?')}章: {f.get('content', '')[:100]}"
                      for _, f in all_active[:15]]
            if active:
                parts.append(f"【活跃伏笔（全部{len(all_active)}条，展示前{len(active)}条）】\n" + "\n".join(active))

        # 世界观变化：每3章取1条，最多8条
        world_changes = dk.get("world_changes", [])
        if world_changes:
            sorted_wc = sorted(world_changes, key=lambda c: c.get("chapter_number", 0))
            milestones = [sorted_wc[i] for i in range(0, len(sorted_wc), max(1, len(sorted_wc) // 8))][:8]
            changes = [f"  第{c.get('chapter_number', '?')}章 [{c.get('change_type', 'world')}] {c.get('description', '')[:120]}" for c in milestones]
            parts.append("【世界观变化（全书里程碑）】\n" + "\n".join(changes))

        # 章节摘要：每5章取1条里程碑
        ch_summaries = dk.get("chapter_summaries", {})
        if ch_summaries:
            sorted_ch = sorted(ch_summaries.items(), key=lambda x: int(x[0]))
            milestones = [sorted_ch[i] for i in range(0, len(sorted_ch), 5)] + [sorted_ch[-1]]
            seen = set()
            unique_milestones = []
            for num, s in milestones:
                if num not in seen:
                    seen.add(num)
                    unique_milestones.append((num, s))
            summaries = [f"  第{num}章: {s.get('summary', s.get('title', ''))[:100]}" for num, s in unique_milestones[-8:]]
            parts.append("【章节摘要（全书里程碑）】\n" + "\n".join(summaries))

        return "\n\n".join(parts) if parts else "动态知识数据为空"