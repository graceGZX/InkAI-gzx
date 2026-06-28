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
        scope = input_data.get("scope", "minor")

        if not chapter_content:
            return {"error": "缺少必要的改进数据"}

        # 分析改进需求
        improvement_plan = self._analyze_improvement_needs(quality_assessment, user_requirements)

        # 执行改进
        improved_chapter = self._improve_chapter(
            chapter_content, improvement_plan, knowledge_base, user_requirements, scope
        )

        return {
            "status": "success",
            "improved_chapter": improved_chapter,
            "improvement_plan": improvement_plan,
            "improvement_summary": self._generate_improvement_summary(improvement_plan)
        }
    
    def _analyze_improvement_needs(self, quality_assessment: Dict[str, Any], user_requirements: str = "") -> Dict[str, Any]:
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

            # 检查是否有用户需求（有需求就必须改进）
            if user_requirements and user_requirements.strip():
                improvement_plan["needs_improvement"] = True
                if not improvement_plan["improvement_areas"]:
                    improvement_plan["priority_level"] = "medium"

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
                        user_requirements: str,
                        scope: str = "minor") -> Dict[str, Any]:
        """改进章节内容"""
        try:
            if not improvement_plan.get("needs_improvement", False):
                return chapter_content

            # 根据 scope 生成范围约束
            scope_rules = self._get_scope_rules(scope)

            # 构建改进提示
            prompt = f"""请根据用户需求对章节进行精准修改。

【最重要约束：修改范围——{scope}】
{scope_rules}

【网文写作风格参考】
- 顶级玄幻/仙侠网文（如《诡秘之主》《大奉打更人》《牧神记》）的写作特点：
  * 开篇即冲突，每章至少一个"爽点钩子"
  * 用短句推进节奏，对话精炼不拖沓，心理描写一句到位不蔓延成段
  * 避免大段环境描写和空洞抒情，用具体动作和细节代替抽象形容
  * 比喻来自日常生活，不堆砌华丽辞藻
  * 人物对话带"网感"但不低幼化——该狠时狠，该幽默时幽默
  * 每段不超 5 行手机屏幕，段落之间节奏张弛交替
- 网络热门小说的行文特点：快节奏、强冲突、人物有"反差萌"、章末留钩子
- 去 AI 腔调：禁止排比句成瘾、翻译腔（"不可否认的是""毫无疑问的是"）、段段升华、陈旧比喻（如"如同一朵盛开的莲花"）

原文信息：
1. 世界观设定：
{self._format_world_setting(knowledge_base)}

2. 主线目标与核心冲突：
{self._format_story_core(knowledge_base)}

3. 全书分卷结构：
{self._format_volumes(knowledge_base)}

4. 三幕结构：
{self._format_story_structure(knowledge_base)}

5. 人物档案：
{self._format_character_profiles(knowledge_base)}

6. 知识图谱（人物关系/设定网络）：
{self._format_knowledge_graph(knowledge_base)}

7. 故事基调：
{self._format_story_tone(knowledge_base)}

8. 上一章结尾（本章必须与此衔接，不得改动衔接段落）：
{self._format_prev_ending(knowledge_base)}

9. 最近章节回顾（避免重复）：
{self._format_recent_chapters(knowledge_base)}

10. 语义关联章节（伏笔/设定参考）：
{self._format_vector_chapters(knowledge_base)}

11. 动态知识（角色发展轨迹/情节时间线/伏笔追踪/世界观变化）：
{self._format_dynamic_knowledge(knowledge_base)}

12. 用户需求：
{user_requirements if user_requirements else "无特殊要求"}

当前章节正文（需改进）：
{chapter_content.get('content', '')}

改进需求分析：
{self._format_improvement_plan(improvement_plan)}

改进要求：
1. 【铁律】严格遵守上面的修改范围约束，不得越界
2. 【铁律】只能改用户需求涉及的段落/句子，其他内容一字不动
3. 【铁律】保持原文的整体叙事节奏和人物性格不变
4. 新增内容必须自然融入原文，读起来不像"补丁"
5. 修改后必须保留所有原文的伏笔和关键信息
6. 小说正文字数控制在 2000-5000 字之间
7. 确保情节逻辑自洽

请返回 JSON 格式：
{{
    "chapter_number": {chapter_content.get("chapter_number", 0)},
    "title": "章节标题",
    "content": "完整正文（包含未修改部分）",
    "summary": "章节摘要",
    "key_events": ["关键事件"],
    "character_development": {{"main_character": "主角发展", "supporting_characters": "配角表现"}},
    "foreshadowing": ["伏笔"],
    "next_chapter_hint": "下章预告",
    "changes": [
        {{"location": "第X段/第Y句", "type": "add/modify/delete", "reason": "改动原因", "before": "原文(≤30字摘要)", "after": "改后(≤30字摘要)"}}
    ],
    "improvement_notes": "改动说明"
}}
"""

            messages = [
                {"role": "system", "content": "你是一个资深网络小说编辑，精通网文写作技法，擅长在最小改动下精准满足作者需求。你熟知番茄小说、起点中文网等平台的头部作品风格，能用网文作家认可的方式改写。"},
                {"role": "user", "content": prompt}
            ]

            response = self.call_llm(messages)
            result = self.parse_json_response(response)

            # 验证和补充结果
            return self._validate_improved_chapter(result, chapter_content)

        except Exception as e:
            self.log(f"改进章节内容失败: {e}")
            return self._create_fallback_chapter(chapter_content, improvement_plan)

    def _get_scope_rules(self, scope: str) -> str:
        """根据 scope 生成严格的范围约束规则"""
        rules = {
            "minor": """
【小改模式】
你只能做最小幅度的文字调整：
- ✅ 修改个别措辞/用词（如把"很生气"改成"怒火中烧"）
- ✅ 调整 1-2 句句式使表达更流畅
- ✅ 在指定位置插入不超过 3 句的新内容
- ❌ 不得重新排列段落顺序
- ❌ 不得改写整段对话
- ❌ 不得增删情节或改变叙事节奏
- ❌ 不得改写超过 20% 的段落
- 修改量不应超过全文的 10%
""",
            "medium": """
【中改模式】
你可以调整段落级别的表达，但保持情节不变：
- ✅ 改写 1-3 个段落使表达更有网感
- ✅ 调整对话节奏，增删部分对白使其更自然
- ✅ 优化描写段落（环境/心理/动作）
- ✅ 调整段落之间的衔接过渡
- ❌ 不得改变情节走向或事件结果
- ❌ 不得新增或删除人物
- ❌ 不得改变章末钩子
- 修改量控制在全文的 25%-50%
""",
            "major": """
【大改模式】
你可以大幅重写章节内容，但保持核心情节：
- ✅ 重新组织段落结构和叙事顺序
- ✅ 大幅改写描写和对话
- ✅ 增删次要情节分支
- ✅ 调整节奏和张力分布
- ❌ 不得改变章节的核心事件和结局
- ❌ 不得改变人物性格设定
- ❌ 不得破坏与前章的衔接
- 可以重写不超过全文的 70%
"""
        }
        return rules.get(scope, rules["minor"])
    
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
            parts = []
            for k, v in world_setting.items():
                if v:
                    parts.append(f"{k}: {v}")
            return "\n".join(parts) if parts else "世界观设定待补充"
        return str(world_setting) if world_setting else "世界观设定待补充"

    def _format_prev_ending(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化上一章结尾"""
        ending = knowledge_base.get("prev_chapter_ending", "")
        return f"「{ending}」" if ending else "无上一章结尾"

    def _format_recent_chapters(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化最近章节摘要"""
        recent = knowledge_base.get("recent_chapters_summaries", [])
        if not recent:
            return "无最近章节信息"
        formatted = ""
        for ch in recent:
            formatted += f"第{ch.get('chapter_number', 0)}章《{ch.get('title', '')}》\n"
            formatted += f"  概要：{ch.get('summary', '')}\n"
            ev = ch.get("key_events", [])
            if ev:
                formatted += f"  关键事件：{'；'.join(ev)}\n"
        return formatted

    def _format_vector_chapters(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化向量检索到的相关章节"""
        vc = knowledge_base.get("vector_retrieved_chapters", [])
        if not vc:
            return "无语义关联章节"
        formatted = ""
        for ch in vc:
            formatted += f"第{ch.get('chapter_number', 0)}章《{ch.get('title', '')}》（相关度: {ch.get('relevance_score', 0)}）\n"
            formatted += f"  概要：{ch.get('summary', '')}\n"
        return formatted
    
    def _format_character_profiles(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化人物档案"""
        character_profiles = knowledge_base.get("character_profiles", {})
        if not character_profiles:
            return "无人物档案"

        formatted = ""
        # 主角信息（兼容两种数据格式）
        mc = character_profiles.get("main_character", {})
        if mc:
            basic = mc.get("basic_info", {})
            pers = mc.get("personality", {})
            bg = mc.get("background", {})
            abilities = mc.get("abilities", {})

            name = basic.get("name") or mc.get("name", "未知")
            formatted += f"主角：{name}\n"

            if isinstance(pers, dict) and pers.get("description"):
                formatted += f"  性格：{pers['description']}\n"
            elif isinstance(pers, str) and pers:
                formatted += f"  性格：{pers}\n"
            elif basic.get("personality_traits"):
                formatted += f"  性格：{', '.join(basic['personality_traits'])}\n"

            if isinstance(bg, dict) and bg.get("core_desire"):
                formatted += f"  核心欲望：{bg['core_desire']}\n"
            if isinstance(bg, dict) and bg.get("inner_drive"):
                formatted += f"  内在驱动力：{bg['inner_drive']}\n"
            if isinstance(abilities, dict) and abilities.get("special_abilities"):
                abs_list = abilities['special_abilities']
                if isinstance(abs_list, list):
                    formatted += f"  能力：{', '.join(abs_list[:5])}\n"

            formatted += f"  身份：{basic.get('occupation', '')}；{basic.get('social_status', '')}\n"
            formatted += "\n"

        # 配角
        supporting = character_profiles.get("supporting_characters", [])
        for char in supporting:
            basic = char.get("basic_info", {})
            name = basic.get("name") or char.get("name", "未知")
            role = char.get("role", "未知")
            pers = char.get("personality", "")
            if isinstance(pers, dict):
                pers = pers.get("description", "")
            formatted += f"配角：{name}（{role}）"
            if pers:
                formatted += f" | {str(pers)[:80]}"
            formatted += "\n"

        # 人物关系
        relationships = character_profiles.get("character_relationships", {})
        if relationships:
            rels = relationships.get("relationships", [])
            if rels:
                formatted += "\n人物关系：\n"
                for r in rels[:10]:
                    formatted += f"  {r.get('character', '?')} ↔ {r.get('role', '')}: {str(r.get('relationship_type', ''))[:100]}\n"

        return formatted or "人物档案待补充"

    def _format_story_core(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化主线目标与核心冲突"""
        parts = []
        main_goal = knowledge_base.get("main_goal", "")
        core_conflict = knowledge_base.get("core_conflict", "")
        overall_outline = knowledge_base.get("overall_outline", "")
        if main_goal:
            parts.append(f"主线目标：{str(main_goal)[:300]}")
        if core_conflict:
            parts.append(f"核心冲突：{str(core_conflict)[:300]}")
        if overall_outline:
            parts.append(f"全书概览：{str(overall_outline)[:500]}")
        return "\n".join(parts) if parts else "待补充"

    def _format_volumes(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化分卷结构"""
        volumes = knowledge_base.get("volumes", [])
        if not volumes:
            return "无分卷信息"
        parts = []
        for v in volumes:
            if isinstance(v, dict):
                parts.append(f"• {v.get('title', '?')}：{str(v.get('description', ''))[:120]}")
            elif isinstance(v, str):
                parts.append(f"• {v[:120]}")
        return "\n".join(parts[:8]) if parts else "无分卷信息"

    def _format_story_structure(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化三幕结构"""
        structure = knowledge_base.get("story_structure", {})
        if not structure:
            return "无三幕结构"
        parts = []
        for act, content in structure.items():
            if isinstance(content, dict):
                parts.append(f"{act}：{str(content.get('summary', content))[:200]}")
            elif isinstance(content, str):
                parts.append(f"{act}：{content[:200]}")
        return "\n".join(parts[:4]) if parts else "无三幕结构"

    def _format_knowledge_graph(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化知识图谱"""
        kg = knowledge_base.get("knowledge_graph", {})
        if not kg:
            return "无知识图谱"
        parts = []
        # 提取关键节点和关系
        if isinstance(kg, dict):
            for key in ["core_entities", "world_elements", "key_locations", "factions", "power_system"]:
                val = kg.get(key, [])
                if val:
                    if isinstance(val, list):
                        items = [str(v)[:100] for v in val[:5]]
                        parts.append(f"{key}: {'; '.join(items)}")
                    elif isinstance(val, dict):
                        items = [f"{k}: {str(v)[:60]}" for k, v in list(val.items())[:5]]
                        parts.append(f"{key}: {'; '.join(items)}")
                    elif isinstance(val, str):
                        parts.append(f"{key}: {val[:200]}")
        return "\n".join(parts) if parts else "知识图谱内容待解析"
    
    def _format_dynamic_knowledge(self, knowledge_base: Dict[str, Any]) -> str:
        """格式化动态知识——优先使用语义检索结果，回退全量截断模式"""
        semantic = knowledge_base.get("dynamic_knowledge_semantic")
        if semantic:
            return self._format_semantic_dynamic_knowledge(semantic)
        return self._format_full_dynamic_knowledge(knowledge_base.get("dynamic_knowledge", {}))

    def _format_semantic_dynamic_knowledge(self, semantic: Dict[str, Any]) -> str:
        """格式化语义检索返回的动态知识"""
        parts = []
        type_labels = {
            "character_evolution": "【相关角色发展】",
            "plot_events": "【相关情节事件】",
            "foreshadowing": "【相关伏笔】",
            "world_changes": "【相关世界观揭示】",
            "chapter_summaries": "【相关章节摘要】"
        }
        for dtype, label in type_labels.items():
            items = semantic.get(dtype, [])
            if items:
                lines = [f"  [{item.get('chapter', '?')}章 | 相关度:{item.get('score', 0):.2f}] {item.get('text', '')[:200]}" for item in items]
                parts.append(f"{label}\n" + "\n".join(lines))
        return "\n\n".join(parts) if parts else "（无相关动态知识）"

    def _format_full_dynamic_knowledge(self, dk: Dict[str, Any]) -> str:
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
                    # 按章节排序后每5章抽1条
                    sorted_recs = sorted(records, key=lambda r: r.get("chapter_number", 0))
                    milestones = [r for i, r in enumerate(sorted_recs) if i % 5 == 0 or i == len(sorted_recs) - 1][-5:]
                    events = [f"  第{r.get('chapter_number', '?')}章: {r.get('description', '')[:80]}" for r in milestones]
                    lines.append(f"  {name}:\n" + "\n".join(events))
            if lines:
                parts.append("【角色发展轨迹（全书里程碑）】\n" + "\n".join(lines))

        # 情节时间线：每5章取1-2个高重要性事件，最多20条
        plot_timeline = dk.get("plot_timeline", [])
        if plot_timeline:
            # 按章节分组，每章取 importance=high 的优先
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
            # high优先
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
            # 去重
            seen = set()
            unique_milestones = []
            for num, s in milestones:
                if num not in seen:
                    seen.add(num)
                    unique_milestones.append((num, s))
            summaries = [f"  第{num}章: {s.get('summary', s.get('title', ''))[:100]}" for num, s in unique_milestones[-8:]]
            parts.append("【章节摘要（全书里程碑）】\n" + "\n".join(summaries))

        return "\n\n".join(parts) if parts else "动态知识数据为空"

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
