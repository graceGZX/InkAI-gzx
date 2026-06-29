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
            recent_chapters = knowledge_base.get("recent_chapters_summaries", [])
            vector_chapters = knowledge_base.get("vector_retrieved_chapters", [])
            world_setting = knowledge_base.get("world_setting", "")
            story_tone = knowledge_base.get("story_tone", "")
            tags = knowledge_base.get("tags", {})
            active_arc = knowledge_base.get("active_arc")
            current_arc_role = knowledge_base.get("current_arc_role", {})

            # 确定下一章号
            next_chapter_number = len(chapters) + 1

            # 构建弧上下文段落
            arc_context_section = ""
            if active_arc and current_arc_role:
                arc_idx = active_arc["planned_chapters"] - active_arc["chapters_remaining"] + 1
                arc_context_section = f"""
            ## 当前故事弧（重要，必须严格遵守）

            弧名称：{active_arc.get("arc_name", "")}（{active_arc.get("arc_type", "")}）
            本章是该弧的第 {arc_idx}/{active_arc.get("planned_chapters", 1)} 章
            本章定位：{current_arc_role.get("role", "arc_mid")}
            本章里程碑：{current_arc_role.get("milestone", "")}
            本章结尾类型：{current_arc_role.get("ending_type", "hook")}（必须严格执行）

            结尾类型说明：
            - cliffhanger：在最紧张时刻截断，绝对不解决冲突，让读者强烈渴望翻下一章
            - hook：留下一个让读者好奇的问题或反常细节
            - pause：冲突暂时平息，气氛舒缓，有内心独白或环境描写
            - resolution：完整解决本弧核心冲突，情绪释放，但需埋下新伏笔

            角色里程碑计划（仅在对应章写出）：
            主角：第{active_arc.get("character_milestones", {}).get("main", {}).get("chapter_offset", 0)}章 — {active_arc.get("character_milestones", {}).get("main", {}).get("description", "无")}
            配角：{", ".join(f"{s.get('name')}第{s.get('chapter_offset')}章-{s.get('description','')}" for s in active_arc.get("character_milestones", {}).get("supporting", []))}
            """

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

            6. 最近几章剧情回顾（请仔细阅读，确保不重复已写过的场景和地点）：
            {self._format_recent_chapters(recent_chapters)}

            7. 语义关联的历史章节（与当前剧情方向相关，请检查伏笔和前后呼应）：
            {self._format_vector_chapters(vector_chapters)}

            8. 动态知识（角色发展轨迹/情节时间线/活跃伏笔/世界观变化）：
            {self._format_dynamic_knowledge(knowledge_base)}

            9. 上一章结尾：
            {self._format_last_chapter(last_chapter)}

            9.5. 上一章场景连续性状态（跨章场景追踪）：
            {self._format_previous_scene_continuity(knowledge_base)}

            10. 上一章结尾原文（仅供了解剧情衔接点，禁止作为本章开头逐字复制）：
            {self._format_ending_text(last_chapter)}

            11. 用户续写需求：{user_requirements if user_requirements else "无特殊要求"}

            {arc_context_section}
            请生成第{next_chapter_number}章的详细故事线，要求：
            1. scene_setting 中的 time/location 必须与上一章结尾的场景/时间自然衔接，不得跳转
            2. 推进主线故事发展
            3. 保持人物性格一致性
            4. 符合世界观设定
            5. 设置适当的伏笔和悬念
            6. 保持故事节奏和基调
            7. 为后续章节发展留下空间

            ## 场景连续性规则（重要）

            你不是必须每章都换场景。一个场景可以跨越 2-3 章：

            - **跨章场景**（scene_span_chapters = 2 或 3）：当剧情需要详细展开一个事件（如一场大战、一次探索、一段关键对话），让同一场景跨越多个章节。
              - 第 1 章：scene_phase = "开始"，建立场景、引入冲突
              - 第 2 章：scene_phase = "延续"，发展冲突、加深矛盾
              - 第 3 章（如有）：scene_phase = "高潮"或"收尾"，解决或转折

            - **单章场景**（scene_span_chapters = 1）：当剧情节点自然结束时，本章自成一个完整弧线

            - **何时用跨章场景**（至少满足 2 项）：
              1. 战斗/冲突需要多个阶段展开
              2. 需要深入展示人物在压力下的变化
              3. 世界观揭露需要层层递进
              4. 多条线索在同一地点交汇
              5. 情绪积累需要足够篇幅

            - **比例建议**：每 3-5 章中应有 1-2 次跨章场景，避免每章都换场景

            - **跨章场景时**：scene_setting 的 time/location 保持与上一章一致或延续，chapter_ending 应停在关键时刻（悬念/未完成），而非强行收尾

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
                "scene_continuity": {{
                    "continues_from_previous": true,
                    "scene_span_chapters": 1,
                    "scene_phase": "开始",
                    "time_shift": "紧接上章/数分钟后/次日清晨/...",
                    "location_change": "同一地点/相邻区域/..."
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
                "writing_notes": "写作注意事项",
                "arc_context": {{
                    "arc_id": "",
                    "arc_name": "",
                    "arc_type": "",
                    "arc_chapter_index": 1,
                    "arc_total_chapters": 1,
                    "arc_role": "arc_open",
                    "chapters_remaining": 1
                }},
                "character_milestones": {{
                    "main": {{"has_milestone": false, "type": null, "description": null}},
                    "supporting": []
                }},
                "ending_type": "hook"
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
                "scene_continuity": {
                    "continues_from_previous": False,
                    "scene_span_chapters": 1,
                    "scene_phase": "开始",
                    "time_shift": "待设定",
                    "location_change": "待设定"
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
                "arc_context": {},
                "character_milestones": {
                    "main": {"has_milestone": False, "type": None, "description": None},
                    "supporting": []
                },
                "ending_type": "hook",
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
            "scene_continuity": {
                "continues_from_previous": False,
                "scene_span_chapters": 1,
                "scene_phase": "开始",
                "time_shift": "待设定",
                "location_change": "待设定"
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
        """格式化上一章结尾原文（仅供衔接参考，禁止逐字复制）"""
        ending = last_chapter.get("ending_text", "")
        if not ending:
            return "无上一章结尾文本"
        return (
            f"上一章结尾（仅供了解剧情衔接点，禁止在章开头逐字复制此文本）：\n"
            f"「{ending}」"
        )

    def _format_previous_scene_continuity(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化上一章的场景连续性状态"""
        prev = knowledge_base.get("previous_scene_continuity")
        if not prev:
            return "上一章无跨章场景状态（或场景已结束）"

        continues = prev.get("continues_from_previous", False)
        span = prev.get("scene_span_chapters", 1)
        phase = prev.get("current_phase", "开始")
        remaining = prev.get("chapters_remaining", 0)
        time = prev.get("time", "未知")
        location = prev.get("location", "未知")
        atmosphere = prev.get("atmosphere", "未知")

        if not continues:
            return "上一章场景已结束，本章应开始新场景"

        return (
            f"⚠️ 上一章场景尚未结束！\n"
            f"  - 此场景计划横跨 {span} 章，当前处于「{phase}」阶段\n"
            f"  - 预计还需 {remaining} 章完成此场景\n"
            f"  - 上一章场景：时间={time}，地点={location}，氛围={atmosphere}\n"
            f"  - 本章应：延续同一场景，scene_continuity.continues_from_previous 设为 true，\n"
            f"    scene_phase 设为 \"延续\"（或 \"高潮\"/\"收尾\"如果是最后一章），\n"
            f"    time/location 保持与上一章一致或自然延续"
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
