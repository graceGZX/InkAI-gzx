"""
智能上下文选择器
负责智能选择续写时需要的相关上下文，避免加载完整知识库
"""

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime


class IntelligentContextSelector:
    """智能上下文选择器"""
    
    def __init__(self, data_manager=None, core_knowledge_manager=None, dynamic_knowledge_manager=None):
        self.data_manager = data_manager
        self.core_knowledge_manager = core_knowledge_manager
        self.dynamic_knowledge_manager = dynamic_knowledge_manager
        self.context_cache = {}
        self.relevance_calculator = RelevanceCalculator()
    
    def select_relevant_context(self, novel_id: str, chapter_number: int, 
                              max_tokens: int = 8000) -> Dict[str, Any]:
        """选择相关上下文"""
        try:
            # 计算最优上下文窗口大小
            optimal_window = self._calculate_optimal_window(chapter_number)
            
            # 获取相关章节
            relevant_chapters = self._get_relevant_chapters(
                novel_id, chapter_number, optimal_window
            )
            
            # 智能选择上下文内容
            selected_context = self._select_context_content(
                relevant_chapters, max_tokens
            )
            
            # 添加核心知识
            core_knowledge = self._get_core_knowledge(novel_id)
            selected_context["core_knowledge"] = core_knowledge
            
            # 添加动态知识摘要
            dynamic_summary = self._get_dynamic_summary(novel_id, chapter_number)
            selected_context["dynamic_summary"] = dynamic_summary
            
            # 缓存上下文
            cache_key = f"{novel_id}_{chapter_number}"
            self.context_cache[cache_key] = selected_context
            
            return selected_context
            
        except Exception as e:
            print(f"选择相关上下文失败: {e}")
            return {}
    
    def _calculate_optimal_window(self, chapter_number: int) -> int:
        """计算最优上下文窗口大小"""
        if chapter_number <= 50:
            return 20  # 早期章节需要更多历史信息
        elif chapter_number <= 200:
            return 15  # 中期章节适中上下文
        elif chapter_number <= 400:
            return 10  # 后期章节较少上下文
        else:
            return 5   # 超长章节最小上下文
    
    def _get_relevant_chapters(self, novel_id: str, chapter_number: int, 
                             window_size: int) -> List[Dict[str, Any]]:
        """获取相关章节"""
        try:
            # 获取所有章节
            all_chapters = self._get_all_chapters(novel_id)
            if not all_chapters:
                return []
            
            # 计算相关性分数
            relevance_scores = []
            for chapter in all_chapters:
                score = self.relevance_calculator.calculate_relevance(
                    chapter, chapter_number
                )
                relevance_scores.append((chapter, score))
            
            # 选择最相关的章节
            relevant_chapters = sorted(
                relevance_scores, 
                key=lambda x: x[1], 
                reverse=True
            )[:window_size]
            
            return [chapter for chapter, score in relevant_chapters]
            
        except Exception as e:
            print(f"获取相关章节失败: {e}")
            return []
    
    def _select_context_content(self, relevant_chapters: List[Dict[str, Any]], 
                              max_tokens: int) -> Dict[str, Any]:
        """选择上下文内容"""
        try:
            selected_context = {
                "recent_chapters": [],
                "character_states": {},
                "plot_events": [],
                "foreshadowing": [],
                "world_changes": []
            }
            
            current_tokens = 0
            
            for chapter in relevant_chapters:
                # 估算章节内容的token数
                chapter_tokens = self._estimate_tokens(chapter)
                
                if current_tokens + chapter_tokens > max_tokens:
                    break
                
                # 添加章节摘要而不是完整内容
                chapter_summary = {
                    "chapter_number": chapter.get("chapter_number", 0),
                    "title": chapter.get("title", ""),
                    "summary": chapter.get("summary", ""),
                    "key_events": chapter.get("key_events", []),
                    "character_development": chapter.get("character_development", {}),
                    "foreshadowing": chapter.get("foreshadowing", [])
                }
                
                selected_context["recent_chapters"].append(chapter_summary)
                current_tokens += chapter_tokens
                
                # 提取关键信息
                self._extract_key_information(chapter, selected_context)
            
            return selected_context
            
        except Exception as e:
            print(f"选择上下文内容失败: {e}")
            return {}
    
    def _get_core_knowledge(self, novel_id: str) -> Dict[str, Any]:
        """获取核心知识"""
        try:
            if self.core_knowledge_manager:
                return self.core_knowledge_manager.get_core_knowledge(novel_id)
            else:
                # 从数据管理器获取
                if self.data_manager:
                    novel_data = self.data_manager.load_novel_data(novel_id, "metadata")
                    return {
                        "novel_info": novel_data.get("metadata", {}),
                        "character_profiles": novel_data.get("characters", {}),
                        "world_setting": novel_data.get("storyline", {}).get("overall_storyline", {}).get("world_setting", {}),
                        "story_themes": novel_data.get("storyline", {}).get("overall_storyline", {}).get("themes", [])
                    }
                return {}
                
        except Exception as e:
            print(f"获取核心知识失败: {e}")
            return {}
    
    def _get_dynamic_summary(self, novel_id: str, chapter_number: int) -> Dict[str, Any]:
        """获取动态知识摘要"""
        try:
            if self.dynamic_knowledge_manager:
                dynamic_knowledge = self.dynamic_knowledge_manager.get_dynamic_knowledge(novel_id)
                if not dynamic_knowledge:
                    return {}
                
                # 获取相关的人物发展
                character_evolution = {}
                for char_name, evolution_list in dynamic_knowledge.get("character_evolution", {}).items():
                    recent_evolution = [e for e in evolution_list if e["chapter_number"] <= chapter_number]
                    if recent_evolution:
                        character_evolution[char_name] = recent_evolution[-1]  # 最新状态
                
                # 获取相关的情节事件
                plot_events = [e for e in dynamic_knowledge.get("plot_timeline", []) 
                             if e["chapter_number"] <= chapter_number]
                
                # 获取活跃的伏笔
                active_foreshadowing = []
                for foreshadowing_type, foreshadowing_list in dynamic_knowledge.get("foreshadowing_tracking", {}).items():
                    for foreshadowing in foreshadowing_list:
                        if (foreshadowing["status"] == "active" and 
                            foreshadowing["chapter_number"] <= chapter_number):
                            active_foreshadowing.append(foreshadowing)
                
                return {
                    "character_evolution": character_evolution,
                    "recent_plot_events": plot_events[-10:] if plot_events else [],  # 最近10个事件
                    "active_foreshadowing": active_foreshadowing,
                    "world_changes": dynamic_knowledge.get("world_changes", [])[-5:]  # 最近5个变化
                }
            else:
                return {}
                
        except Exception as e:
            print(f"获取动态摘要失败: {e}")
            return {}
    
    def _get_all_chapters(self, novel_id: str) -> List[Dict[str, Any]]:
        """获取所有章节"""
        try:
            if self.data_manager:
                return self.data_manager.get_novel_chapters(novel_id)
            else:
                # 从文件系统获取
                novel_dir = os.path.join("novels", novel_id)
                if not os.path.exists(novel_dir):
                    return []
                
                chapters = []
                for filename in os.listdir(novel_dir):
                    if filename.startswith("chapter_") and filename.endswith(".json"):
                        chapter_path = os.path.join(novel_dir, filename)
                        try:
                            with open(chapter_path, 'r', encoding='utf-8') as f:
                                chapter_data = json.load(f)
                                chapters.append(chapter_data)
                        except Exception as e:
                            print(f"加载章节文件失败 {filename}: {e}")
                
                # 按章节号排序
                chapters.sort(key=lambda x: x.get("chapter_number", 0))
                return chapters
                
        except Exception as e:
            print(f"获取所有章节失败: {e}")
            return []
    
    def _estimate_tokens(self, chapter: Dict[str, Any]) -> int:
        """估算章节内容的token数"""
        try:
            content = chapter.get("content", "")
            # 简单估算：中文字符数 * 1.5 + 英文单词数 * 1.3
            chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            english_words = len(content.split())
            estimated_tokens = int(chinese_chars * 1.5 + english_words * 1.3)
            return max(estimated_tokens, 100)  # 最小100个token
            
        except Exception as e:
            print(f"估算token数失败: {e}")
            return 100
    
    def _extract_key_information(self, chapter: Dict[str, Any], 
                               selected_context: Dict[str, Any]) -> None:
        """提取关键信息"""
        try:
            # 提取人物状态变化
            character_development = chapter.get("character_development", {})
            for char_name, development in character_development.items():
                if char_name not in selected_context["character_states"]:
                    selected_context["character_states"][char_name] = []
                selected_context["character_states"][char_name].append(development)
            
            # 提取情节事件
            key_events = chapter.get("key_events", [])
            for event in key_events:
                selected_context["plot_events"].append({
                    "chapter": chapter.get("chapter_number", 0),
                    "event": event
                })
            
            # 提取伏笔
            foreshadowing = chapter.get("foreshadowing", [])
            for foreshadow in foreshadowing:
                selected_context["foreshadowing"].append({
                    "chapter": chapter.get("chapter_number", 0),
                    "foreshadowing": foreshadow
                })
            
            # 提取世界观变化
            world_changes = chapter.get("world_changes", [])
            for change in world_changes:
                selected_context["world_changes"].append({
                    "chapter": chapter.get("chapter_number", 0),
                    "change": change
                })
                
        except Exception as e:
            print(f"提取关键信息失败: {e}")
    
    def get_cached_context(self, novel_id: str, chapter_number: int) -> Optional[Dict[str, Any]]:
        """获取缓存的上下文"""
        cache_key = f"{novel_id}_{chapter_number}"
        return self.context_cache.get(cache_key)
    
    def clear_cache(self, novel_id: str = None):
        """清理缓存"""
        if novel_id:
            # 清理特定小说的缓存
            keys_to_remove = [key for key in self.context_cache.keys() if key.startswith(f"{novel_id}_")]
            for key in keys_to_remove:
                self.context_cache.pop(key, None)
        else:
            self.context_cache.clear()


class RelevanceCalculator:
    """相关性计算器"""
    
    def __init__(self):
        self.weights = {
            "character_relevance": 0.3,
            "plot_relevance": 0.4,
            "theme_relevance": 0.2,
            "time_relevance": 0.1
        }
    
    def calculate_relevance(self, chapter: Dict[str, Any], target_chapter: int) -> float:
        """计算章节相关性"""
        try:
            chapter_number = chapter.get("chapter_number", 0)
            
            # 计算时间相关性
            time_relevance = self._calculate_time_relevance(chapter_number, target_chapter)
            
            # 计算人物相关性
            character_relevance = self._calculate_character_relevance(chapter)
            
            # 计算情节相关性
            plot_relevance = self._calculate_plot_relevance(chapter)
            
            # 计算主题相关性
            theme_relevance = self._calculate_theme_relevance(chapter)
            
            # 加权计算总分
            total_score = (
                time_relevance * self.weights["time_relevance"] +
                character_relevance * self.weights["character_relevance"] +
                plot_relevance * self.weights["plot_relevance"] +
                theme_relevance * self.weights["theme_relevance"]
            )
            
            return total_score
            
        except Exception as e:
            print(f"计算相关性失败: {e}")
            return 0.0
    
    def _calculate_time_relevance(self, chapter_number: int, target_chapter: int) -> float:
        """计算时间相关性"""
        distance = abs(chapter_number - target_chapter)
        
        # 距离越近，相关性越高
        if distance == 0:
            return 1.0
        elif distance <= 5:
            return 0.8
        elif distance <= 10:
            return 0.6
        elif distance <= 20:
            return 0.4
        else:
            return 0.2
    
    def _calculate_character_relevance(self, chapter: Dict[str, Any]) -> float:
        """计算人物相关性"""
        try:
            character_development = chapter.get("character_development", {})
            key_events = chapter.get("key_events", [])
            
            # 基于人物发展的重要性评分
            character_score = 0.0
            if character_development:
                character_score += 0.5
            
            # 基于关键事件中的人物参与度评分
            if key_events:
                character_score += 0.3
            
            # 基于章节标题中的人物提及评分
            title = chapter.get("title", "")
            if any(keyword in title for keyword in ["主角", "人物", "角色"]):
                character_score += 0.2
            
            return min(character_score, 1.0)
            
        except Exception as e:
            print(f"计算人物相关性失败: {e}")
            return 0.0
    
    def _calculate_plot_relevance(self, chapter: Dict[str, Any]) -> float:
        """计算情节相关性"""
        try:
            key_events = chapter.get("key_events", [])
            foreshadowing = chapter.get("foreshadowing", [])
            
            # 基于关键事件的重要性评分
            plot_score = 0.0
            if key_events:
                plot_score += 0.4
            
            # 基于伏笔的重要性评分
            if foreshadowing:
                plot_score += 0.3
            
            # 基于章节摘要的重要性评分
            summary = chapter.get("summary", "")
            if any(keyword in summary for keyword in ["重要", "关键", "转折", "高潮"]):
                plot_score += 0.3
            
            return min(plot_score, 1.0)
            
        except Exception as e:
            print(f"计算情节相关性失败: {e}")
            return 0.0
    
    def _calculate_theme_relevance(self, chapter: Dict[str, Any]) -> float:
        """计算主题相关性"""
        try:
            summary = chapter.get("summary", "")
            title = chapter.get("title", "")
            
            # 基于主题关键词的评分
            theme_keywords = ["成长", "爱情", "友情", "家庭", "梦想", "奋斗", "正义", "邪恶"]
            theme_score = 0.0
            
            for keyword in theme_keywords:
                if keyword in summary or keyword in title:
                    theme_score += 0.1
            
            return min(theme_score, 1.0)
            
        except Exception as e:
            print(f"计算主题相关性失败: {e}")
            return 0.0
