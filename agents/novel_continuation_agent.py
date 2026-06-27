"""
小说续写智能体
负责处理小说续写功能，包括小说查找、知识库构建等
"""

from base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import config
import json
import os

class NovelContinuationAgent(BaseAgent):
    """小说续写智能体"""
    
    def __init__(self):
        super().__init__("小说续写智能体")
        self.data_manager = None  # 将在process方法中初始化
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理小说续写请求"""
        novel_id = input_data.get("novel_id")
        if not novel_id:
            return {"error": "请提供小说ID"}
        
        # 初始化数据管理器
        from data_manager import DataManager
        self.data_manager = DataManager()
        
        # 查找小说
        novel_data = self._find_novel(novel_id)
        if not novel_data:
            return {"error": f"未找到ID为 {novel_id} 的小说"}
        
        # 构建知识库
        knowledge_base = self._build_knowledge_base(novel_data)
        
        return {
            "status": "success",
            "novel_data": novel_data,
            "knowledge_base": knowledge_base,
            "next_step": "storyline_generation"
        }
    
    def _find_novel(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """查找小说"""
        try:
            # 尝试通过ID直接查找
            novel_dir = os.path.join(config.NOVELS_DIR, novel_id)
            if os.path.exists(novel_dir):
                return self._load_novel_data(novel_id)
            
            # 如果直接查找失败，尝试通过标题查找
            novels = self.data_manager.get_novel_list()
            for novel in novels:
                if novel.get("title") == novel_id or novel.get("novel_id") == novel_id:
                    return self._load_novel_data(novel.get("novel_id"))
            
            return None
        except Exception as e:
            self.log(f"查找小说失败: {e}")
            return None
    
    def _load_novel_data(self, novel_id: str) -> Dict[str, Any]:
        """加载小说完整数据"""
        try:
            # 加载元数据
            metadata = self.data_manager.load_novel_data(novel_id, "metadata")
            if not metadata:
                return None
            
            # 加载各种数据
            novel_data = {
                "novel_info": {
                    "novel_id": novel_id,
                    "title": metadata.get("title", "未知标题"),
                    "author": "用户",
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                    "status": metadata.get("status", "未知状态")
                },
                "chapters": self._load_chapters(novel_id),
                "character_profiles": self.data_manager.load_novel_data(novel_id, "characters") or {},
                "storyline": self.data_manager.load_novel_data(novel_id, "storyline") or {},
                "tags": self.data_manager.load_novel_data(novel_id, "tags") or {}
            }
            
            return novel_data
        except Exception as e:
            self.log(f"加载小说数据失败: {e}")
            return None
    
    def _load_chapters(self, novel_id: str) -> List[Dict[str, Any]]:
        """加载所有章节"""
        chapters = []
        novel_dir = os.path.join(config.NOVELS_DIR, novel_id)
        
        if not os.path.exists(novel_dir):
            return chapters
        
        # 查找所有章节文件
        for filename in os.listdir(novel_dir):
            if filename.startswith("chapter_") and filename.endswith(".json"):
                try:
                    chapter_file = os.path.join(novel_dir, filename)
                    with open(chapter_file, 'r', encoding='utf-8') as f:
                        chapter_data = json.load(f)
                    
                    # 提取章节号
                    chapter_num = filename.replace("chapter_", "").replace(".json", "")
                    chapter_data["chapter_number"] = int(chapter_num)
                    
                    chapters.append(chapter_data)
                except Exception as e:
                    self.log(f"加载章节 {filename} 失败: {e}")
        
        # 按章节号排序
        chapters.sort(key=lambda x: x.get("chapter_number", 0))
        return chapters
    
    def _build_knowledge_base(self, novel_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建知识库"""
        try:
            chapters = novel_data.get("chapters", [])
            character_profiles = novel_data.get("character_profiles", {})
            storyline = novel_data.get("storyline", {})
            tags = novel_data.get("tags", {})
            
            # 提取关键信息
            key_events = []
            characters_in_chapters = []
            foreshadowing = []
            
            for chapter in chapters:
                # 提取关键事件
                chapter_events = chapter.get("key_events", [])
                if chapter_events:
                    key_events.extend([{
                        "chapter": chapter.get("chapter_number", 0),
                        "event": event
                    } for event in chapter_events])
                
                # 提取出场角色
                chapter_chars = chapter.get("characters", [])
                if chapter_chars:
                    characters_in_chapters.extend([{
                        "chapter": chapter.get("chapter_number", 0),
                        "character": char
                    } for char in chapter_chars])
                
                # 提取伏笔
                chapter_foreshadowing = chapter.get("foreshadowing", [])
                if chapter_foreshadowing:
                    foreshadowing.extend([{
                        "chapter": chapter.get("chapter_number", 0),
                        "hint": hint
                    } for hint in chapter_foreshadowing])
            
            # 构建知识库
            knowledge_base = {
                "novel_info": novel_data.get("novel_info", {}),
                "chapters": chapters,
                "character_profiles": character_profiles,
                "storyline": storyline,  # 保存完整的故事线信息
                "plot_lines": self._extract_plot_lines(storyline, chapters),
                "foreshadowing": foreshadowing,
                "key_events": key_events,
                "characters_in_chapters": characters_in_chapters,
                "world_setting": self._format_world_setting(storyline.get("overall_storyline", {}).get("world_setting", {})),
                "story_tone": storyline.get("overall_storyline", {}).get("tone", ""),
                "tags": tags,
                "last_chapter_summary": self._get_last_chapter_summary(chapters),
                "recent_chapters_summaries": self._get_recent_chapters_summaries(chapters, n=3)
            }
            
            return knowledge_base
        except Exception as e:
            self.log(f"构建知识库失败: {e}")
            return {}
    
    def _get_recent_chapters_summaries(self, chapters: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
        """获取最近N章的摘要信息（含关键事件），用于章纲生成器了解近期剧情"""
        if not chapters:
            return []
        recent = chapters[-n:] if len(chapters) >= n else chapters[:]
        summaries = []
        for ch in recent:
            summaries.append({
                "chapter_number": ch.get("chapter_number", 0),
                "title": ch.get("title", ""),
                "summary": ch.get("summary", ""),
                "key_events": ch.get("key_events", [])
            })
        return summaries

    def _extract_plot_lines(self, storyline: Dict[str, Any], chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取故事线"""
        plot_lines = {
            "main_line": [],
            "sub_lines": []
        }
        
        # 从故事线中提取主线
        if storyline:
            main_goal = storyline.get("main_goal", "")
            if main_goal:
                plot_lines["main_line"].append(main_goal)
            
            conflict = storyline.get("conflict", "")
            if conflict:
                plot_lines["main_line"].append(conflict)
        
        # 从章节中提取情节发展
        for chapter in chapters:
            summary = chapter.get("summary", "")
            if summary:
                plot_lines["main_line"].append(f"第{chapter.get('chapter_number', 0)}章: {summary}")
        
        return plot_lines
    
    def _format_world_setting(self, world_setting: Dict[str, Any]) -> str:
        """格式化世界观设定为字符串"""
        if not world_setting or not isinstance(world_setting, dict):
            return "世界观设定待补充"
        
        parts = []
        if world_setting.get("time_period"):
            parts.append(f"时代: {world_setting['time_period']}")
        if world_setting.get("location"):
            parts.append(f"地点: {world_setting['location']}")
        if world_setting.get("society"):
            parts.append(f"社会: {world_setting['society']}")
        if world_setting.get("atmosphere"):
            parts.append(f"氛围: {world_setting['atmosphere']}")
        
        return "，".join(parts) if parts else "世界观设定待补充"
    
    def _get_last_chapter_summary(self, chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取最后一章的摘要"""
        if not chapters:
            return {}
        
        last_chapter = chapters[-1]
        # 取上一章结尾文字（最后300字），用于写手做平滑过渡
        content = last_chapter.get("content", "")
        ending_text = content[-300:] if len(content) > 300 else content
        return {
            "chapter_number": last_chapter.get("chapter_number", 0),
            "title": last_chapter.get("title", ""),
            "summary": last_chapter.get("summary", ""),
            "key_events": last_chapter.get("key_events", []),
            "foreshadowing": last_chapter.get("foreshadowing", []),
            "next_chapter_hint": last_chapter.get("next_chapter_hint", ""),
            "ending_text": ending_text
        }
