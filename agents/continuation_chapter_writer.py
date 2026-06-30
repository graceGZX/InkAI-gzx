"""
续写章节写作智能体
负责基于知识库生成续写章节内容
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config
from core.chapter_content import extract_chapter_text


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
            recent_chapters = knowledge_base.get("recent_chapters_summaries", [])
            vector_chapters = knowledge_base.get("vector_retrieved_chapters", [])

            # 读取弧感知字段
            arc_context = storyline.get("arc_context", {})
            ending_type = storyline.get("ending_type", "")
            character_milestones = storyline.get("character_milestones", {})

            # 弧感知写作指令
            arc_writing_instruction = ""
            if arc_context.get("arc_name"):
                arc_role = arc_context.get("arc_role", "")
                arc_idx = arc_context.get("arc_chapter_index", 1)
                arc_total = arc_context.get("arc_total_chapters", 1)
                arc_writing_instruction = f"""
            ## 故事弧定位（必须遵守）

            当前弧：《{arc_context.get("arc_name", "")}》第 {arc_idx}/{arc_total} 章（{arc_role}）

            """

            ending_instruction = ""
            ending_type_map = {
                "cliffhanger": "【章末要求 - cliffhanger】必须在最紧张、最危险的时刻截断。不能解决当前冲突或危机。最后一段必须停在读者最想知道「然后呢」的瞬间，让读者强烈渴望翻到下一章。",
                "hook":        "【章末要求 - hook】章末留下一个明确的疑问、反常细节或意外出现的人/事，引发读者强烈好奇，不需要紧张氛围，但必须留下悬念。",
                "pause":       "【章末要求 - pause】章末让当前冲突暂时平息，节奏放缓。可用内心独白、环境描写或轻松对话收尾，给读者喘息空间。",
                "resolution":  "【章末要求 - resolution】章末完整解决本弧的核心冲突，给读者情绪释放感。但在最后几句中，必须埋下一个新的伏笔或问题，为下一弧做铺垫。",
            }
            if ending_type in ending_type_map:
                ending_instruction = ending_type_map[ending_type]

            milestone_instruction = ""
            main_milestone = character_milestones.get("main", {})
            if main_milestone and main_milestone.get("has_milestone"):
                milestone_instruction = f"【角色里程碑 - 必须在本章写出】主角本章将经历：{main_milestone.get('description', '')}（类型：{main_milestone.get('type', '')}），请将此里程碑作为本章核心事件之一，用充分的笔墨展现过程与情绪。"

            # 构建写作提示
            prompt = f"""
            请根据以下信息续写小说《{novel_info.get('title', '未知标题')}》的第{storyline.get('chapter_number', 1)}章。

            原文设定：
            1. 世界观：{world_setting}
            2. 故事基调：{story_tone}
            3. 故事标签：{self._format_tags(tags)}

            4. 人物档案：
            {self._format_character_profiles(character_profiles)}

            5. 最近几章剧情回顾（请仔细阅读，确保不重复已写过的场景和情节）：
            {self._format_recent_chapters(recent_chapters)}

            6. 语义关联的历史章节（与当前剧情相关，请检查伏笔和前后呼应）：
            {self._format_vector_chapters(vector_chapters)}

            7. 动态知识（角色发展轨迹/情节时间线/活跃伏笔/世界观变化——确保写新章时不矛盾）：
            {self._format_dynamic_knowledge(knowledge_base)}

            9. 上一章结尾：
            {self._format_last_chapter(last_chapter)}

            10. 上一章最后段落（仅供了解剧情衔接点，禁止在章开头逐字复制此文本）：
            {self._format_ending_text(last_chapter)}

            11. 本章故事线：
            {self._format_storyline(storyline)}

            12. 用户要求：{user_requirements if user_requirements else "无特殊要求"}

            写作要求：
            1. 【场景衔接】根据 scene_continuity 决定本章开头方式：

               【模式A - 同场景延续】(continues_from_previous = true 且 scene_phase != "开始")：
               - 本章与上一章共享同一场景，直接从上一章结尾的瞬间继续
               - 开头方式：用一句话自然承接（如"林荒还没来得及喘口气，就听见..."），然后继续推进剧情
               - 禁止用上一章结尾的原文逐字重复！必须用自己的语言重新描述
               - 本章不需要完整的起承转合，可以在剧情中间结束（章末停在关键时刻即可）

               【模式B - 新场景过渡】(continues_from_previous = false 或 scene_phase = "开始")：
               - 本章开始一个新场景或新阶段
               - 开头方式：从上一章结尾的时间/情绪自然过渡到新场景（如上一章结尾夜晚→本章开头次日清晨）

               无论哪种模式：
               - 禁止将上一章 ending_text 原文复制到本章开头
               - 用你自己的语言重新描述过渡，保持情绪连贯但文字不重复

            2. 严格保持与原文的一致性（人物性格、世界观、语言风格）
            3. 按照故事线推进情节
            4. 保持原文的写作风格和基调
            5. 设置适当的伏笔和悬念
            6. 语言生动，描写细腻
            7. 小说正文字数必须大于5000字，目标在5000-8000字之间，务必写满
            8. 确保情节逻辑自洽
            9. 用你最大的输出能力进行输出
            {arc_writing_instruction}
            {ending_instruction}
            {milestone_instruction}

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
        if "content" in content:
            content["content"] = extract_chapter_text(content["content"])
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
        if 5000 <= word_count <= 8000:
            quality_score += 30
        elif 4000 <= word_count < 5000:
            quality_score += 15
        
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
    
    def _format_vector_chapters(self, vector_chapters: list) -> str:
        """格式化向量检索到的历史相关章节"""
        if not vector_chapters:
            return "无语义关联章节"

        formatted = ""
        for ch in vector_chapters:
            num = ch.get("chapter_number", 0)
            title = ch.get("title", "未知标题")
            summary = ch.get("summary", "无概要")
            score = ch.get("relevance_score", 0)
            key_events = ch.get("key_events", [])
            formatted += f"第{num}章《{title}》（相关度: {score}）\n"
            formatted += f"  概要：{summary}\n"
            if key_events:
                formatted += f"  关键事件：\n"
                for ev in key_events:
                    formatted += f"    - {ev}\n"
            formatted += "\n"
        return formatted

    def _format_recent_chapters(self, recent_chapters: list) -> str:
        """格式化最近几章的摘要信息"""
        if not recent_chapters:
            return "无最近章节信息"

        formatted = ""
        for ch in recent_chapters:
            num = ch.get("chapter_number", 0)
            title = ch.get("title", "未知标题")
            summary = ch.get("summary", "无概要")
            key_events = ch.get("key_events", [])
            formatted += f"第{num}章《{title}》\n"
            formatted += f"  概要：{summary}\n"
            if key_events:
                formatted += f"  关键事件：\n"
                for ev in key_events:
                    formatted += f"    - {ev}\n"
            formatted += "\n"
        return formatted

    def _format_ending_text(self, last_chapter: Dict[str, Any]) -> str:
        """格式化上一章结尾文字，仅供衔接参考，禁止逐字复制"""
        ending = last_chapter.get("ending_text", "")
        if not ending:
            return "无上一章结尾文本"
        return (
            f"上一章结尾（仅供了解剧情衔接点，禁止在章开头逐字复制此文本）：\n"
            f"「{ending}」"
        )

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

        scene_continuity = storyline.get("scene_continuity", {})
        if scene_continuity:
            continues = scene_continuity.get("continues_from_previous", False)
            span = scene_continuity.get("scene_span_chapters", 1)
            phase = scene_continuity.get("scene_phase", "开始")
            time_shift = scene_continuity.get("time_shift", "待设定")
            loc_change = scene_continuity.get("location_change", "待设定")
            formatted += f"场景连续性：\n"
            formatted += f"  延续上章场景：{'是' if continues else '否'}\n"
            formatted += f"  场景横跨章数：{span}\n"
            formatted += f"  本章场景阶段：{phase}\n"
            formatted += f"  时间推移：{time_shift}\n"
            formatted += f"  地点变化：{loc_change}\n"
            if continues and phase != "开始":
                formatted += f"  ⚠️ 同场景延续模式：本章不需完整起承转合，可在剧情中间结束\n"

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

    def _format_dynamic_knowledge(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化动态知识——优先使用语义检索结果，回退全量截断模式"""
        semantic = knowledge_base.get("dynamic_knowledge_semantic")
        if semantic:
            return self._format_semantic_dk(semantic)
        return self._format_full_dk(knowledge_base.get("dynamic_knowledge", {}))

    def _format_semantic_dk(self, semantic: Dict[str, Any]) -> str:
        parts = []
        labels = {"character_evolution": "【相关角色发展】", "plot_events": "【相关情节事件】",
                  "foreshadowing": "【相关伏笔】", "world_changes": "【相关世界观揭示】",
                  "chapter_summaries": "【相关章节摘要】"}
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
