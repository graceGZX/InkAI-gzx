"""
动态知识管理器
负责管理动态变化的知识，包括人物发展轨迹、情节时间线、伏笔追踪等
"""

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime


class DynamicKnowledgeManager:
    """动态知识管理器"""
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        self.dynamic_knowledge_cache = {}
        self.knowledge_file = "dynamic_knowledge.json"
    
    def initialize_dynamic_knowledge(self, novel_id: str) -> Dict[str, Any]:
        """初始化动态知识"""
        try:
            dynamic_knowledge = {
                "novel_id": novel_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "character_evolution": {},  # 人物发展轨迹
                "plot_timeline": [],        # 情节时间线
                "foreshadowing_tracking": {}, # 伏笔追踪
                "world_changes": [],        # 世界观变化
                "chapter_summaries": {},    # 章节摘要
                "relationship_evolution": {} # 关系发展
            }
            
            # 缓存动态知识
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
            
            # 保存到文件
            self._save_dynamic_knowledge(novel_id, dynamic_knowledge)
            
            return dynamic_knowledge
            
        except Exception as e:
            print(f"初始化动态知识失败: {e}")
            return {}
    
    def get_dynamic_knowledge(self, novel_id: str) -> Dict[str, Any]:
        """获取动态知识"""
        # 先检查缓存
        if novel_id in self.dynamic_knowledge_cache:
            return self.dynamic_knowledge_cache[novel_id]
        
        # 从文件加载
        dynamic_knowledge = self._load_dynamic_knowledge(novel_id)
        if dynamic_knowledge:
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
        
        return dynamic_knowledge
    
    def update_character_evolution(self, novel_id: str, chapter_number: int, 
                                 character_name: str, changes: Dict[str, Any]) -> bool:
        """更新人物发展轨迹"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                dynamic_knowledge = self.initialize_dynamic_knowledge(novel_id)
            
            # 初始化人物发展轨迹
            if character_name not in dynamic_knowledge["character_evolution"]:
                dynamic_knowledge["character_evolution"][character_name] = []
            
            # 添加发展记录
            evolution_record = {
                "chapter_number": chapter_number,
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "change_type": changes.get("type", "general"),
                "description": changes.get("description", "")
            }
            
            dynamic_knowledge["character_evolution"][character_name].append(evolution_record)
            dynamic_knowledge["updated_at"] = datetime.now().isoformat()
            
            # 更新缓存和文件
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
            self._save_dynamic_knowledge(novel_id, dynamic_knowledge)
            
            return True
            
        except Exception as e:
            print(f"更新人物发展轨迹失败: {e}")
            return False
    
    def update_plot_timeline(self, novel_id: str, chapter_number: int, 
                           plot_events: List[Dict[str, Any]]) -> bool:
        """更新情节时间线"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                dynamic_knowledge = self.initialize_dynamic_knowledge(novel_id)
            
            # 添加情节事件
            for event in plot_events:
                timeline_event = {
                    "chapter_number": chapter_number,
                    "timestamp": datetime.now().isoformat(),
                    "event_type": event.get("type", "plot"),
                    "description": event.get("description", ""),
                    "importance": event.get("importance", "medium"),
                    "characters_involved": event.get("characters", []),
                    "consequences": event.get("consequences", [])
                }
                
                dynamic_knowledge["plot_timeline"].append(timeline_event)
            
            dynamic_knowledge["updated_at"] = datetime.now().isoformat()
            
            # 更新缓存和文件
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
            self._save_dynamic_knowledge(novel_id, dynamic_knowledge)
            
            return True
            
        except Exception as e:
            print(f"更新情节时间线失败: {e}")
            return False
    
    def update_foreshadowing_tracking(self, novel_id: str, chapter_number: int,
                                    foreshadowing_data: Dict[str, Any]) -> bool:
        """更新伏笔追踪"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                dynamic_knowledge = self.initialize_dynamic_knowledge(novel_id)
            
            # 添加伏笔记录
            foreshadowing_record = {
                "chapter_number": chapter_number,
                "timestamp": datetime.now().isoformat(),
                "foreshadowing_type": foreshadowing_data.get("type", "general"),
                "content": foreshadowing_data.get("content", ""),
                "target_chapter": foreshadowing_data.get("target_chapter", None),
                "status": "active",  # active, revealed, expired
                "importance": foreshadowing_data.get("importance", "medium")
            }
            
            # 按类型组织伏笔
            foreshadowing_type = foreshadowing_record["foreshadowing_type"]
            if foreshadowing_type not in dynamic_knowledge["foreshadowing_tracking"]:
                dynamic_knowledge["foreshadowing_tracking"][foreshadowing_type] = []
            
            dynamic_knowledge["foreshadowing_tracking"][foreshadowing_type].append(foreshadowing_record)
            dynamic_knowledge["updated_at"] = datetime.now().isoformat()
            
            # 更新缓存和文件
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
            self._save_dynamic_knowledge(novel_id, dynamic_knowledge)
            
            return True
            
        except Exception as e:
            print(f"更新伏笔追踪失败: {e}")
            return False
    
    def update_world_changes(self, novel_id: str, chapter_number: int,
                           world_changes: List[Dict[str, Any]]) -> bool:
        """更新世界观变化"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                dynamic_knowledge = self.initialize_dynamic_knowledge(novel_id)
            
            # 添加世界观变化记录
            for change in world_changes:
                world_change_record = {
                    "chapter_number": chapter_number,
                    "timestamp": datetime.now().isoformat(),
                    "change_type": change.get("type", "general"),
                    "description": change.get("description", ""),
                    "scope": change.get("scope", "local"),  # local, regional, global
                    "permanence": change.get("permanence", "permanent")  # temporary, permanent
                }
                
                dynamic_knowledge["world_changes"].append(world_change_record)
            
            dynamic_knowledge["updated_at"] = datetime.now().isoformat()
            
            # 更新缓存和文件
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
            self._save_dynamic_knowledge(novel_id, dynamic_knowledge)
            
            return True
            
        except Exception as e:
            print(f"更新世界观变化失败: {e}")
            return False
    
    def add_chapter_summary(self, novel_id: str, chapter_number: int,
                          summary_data: Dict[str, Any]) -> bool:
        """添加章节摘要"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                dynamic_knowledge = self.initialize_dynamic_knowledge(novel_id)
            
            # 创建章节摘要
            chapter_summary = {
                "chapter_number": chapter_number,
                "timestamp": datetime.now().isoformat(),
                "title": summary_data.get("title", ""),
                "summary": summary_data.get("summary", ""),
                "key_events": summary_data.get("key_events", []),
                "character_development": summary_data.get("character_development", {}),
                "foreshadowing": summary_data.get("foreshadowing", []),
                "plot_advancement": summary_data.get("plot_advancement", ""),
                "word_count": summary_data.get("word_count", 0)
            }
            
            dynamic_knowledge["chapter_summaries"][str(chapter_number)] = chapter_summary
            dynamic_knowledge["updated_at"] = datetime.now().isoformat()
            
            # 更新缓存和文件
            self.dynamic_knowledge_cache[novel_id] = dynamic_knowledge
            self._save_dynamic_knowledge(novel_id, dynamic_knowledge)
            
            return True
            
        except Exception as e:
            print(f"添加章节摘要失败: {e}")
            return False
    
    def get_character_current_state(self, novel_id: str, character_name: str, 
                                  chapter_number: int) -> Dict[str, Any]:
        """获取人物当前状态"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                return {}
            
            character_evolution = dynamic_knowledge.get("character_evolution", {}).get(character_name, [])
            
            # 找到指定章节之前的最新状态
            current_state = {}
            for evolution_record in character_evolution:
                if evolution_record["chapter_number"] <= chapter_number:
                    current_state.update(evolution_record["changes"])
            
            return current_state
            
        except Exception as e:
            print(f"获取人物当前状态失败: {e}")
            return {}
    
    def get_relevant_foreshadowing(self, novel_id: str, chapter_number: int) -> List[Dict[str, Any]]:
        """获取相关伏笔"""
        try:
            dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
            if not dynamic_knowledge:
                return []
            
            relevant_foreshadowing = []
            foreshadowing_tracking = dynamic_knowledge.get("foreshadowing_tracking", {})
            
            for foreshadowing_type, foreshadowing_list in foreshadowing_tracking.items():
                for foreshadowing in foreshadowing_list:
                    # 检查是否与当前章节相关
                    if (foreshadowing["status"] == "active" and 
                        foreshadowing["chapter_number"] <= chapter_number):
                        relevant_foreshadowing.append(foreshadowing)
            
            return relevant_foreshadowing
            
        except Exception as e:
            print(f"获取相关伏笔失败: {e}")
            return []
    
    def _save_dynamic_knowledge(self, novel_id: str, dynamic_knowledge: Dict[str, Any]) -> bool:
        """保存动态知识到文件"""
        try:
            if self.data_manager and hasattr(self.data_manager, 'novels_dir'):
                # 使用数据管理器保存
                novel_dir = os.path.join(self.data_manager.novels_dir, novel_id)
                os.makedirs(novel_dir, exist_ok=True)
                
                file_path = os.path.join(novel_dir, self.knowledge_file)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(dynamic_knowledge, f, ensure_ascii=False, indent=2)
            else:
                # 使用当前目录作为备选
                os.makedirs("dynamic_knowledge", exist_ok=True)
                file_path = os.path.join("dynamic_knowledge", f"{novel_id}_{self.knowledge_file}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(dynamic_knowledge, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存动态知识失败: {e}")
            return False
    
    def _load_dynamic_knowledge(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载动态知识"""
        try:
            if self.data_manager:
                # 使用数据管理器加载
                novel_dir = os.path.join(self.data_manager.novels_dir, novel_id)
                file_path = os.path.join(novel_dir, self.knowledge_file)
            else:
                # 从当前目录加载
                file_path = self.knowledge_file
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"加载动态知识失败: {e}")
            return None
    
    def clear_cache(self, novel_id: str = None):
        """清理缓存"""
        if novel_id:
            self.dynamic_knowledge_cache.pop(novel_id, None)
        else:
            self.dynamic_knowledge_cache.clear()
    
    def get_dynamic_summary(self, novel_id: str) -> Dict[str, Any]:
        """获取动态知识摘要"""
        dynamic_knowledge = self.get_dynamic_knowledge(novel_id)
        if not dynamic_knowledge:
            return {}
        
        return {
            "characters_tracked": len(dynamic_knowledge.get("character_evolution", {})),
            "plot_events": len(dynamic_knowledge.get("plot_timeline", [])),
            "foreshadowing_types": len(dynamic_knowledge.get("foreshadowing_tracking", {})),
            "world_changes": len(dynamic_knowledge.get("world_changes", [])),
            "chapters_summarized": len(dynamic_knowledge.get("chapter_summaries", {})),
            "last_updated": dynamic_knowledge.get("updated_at", "")
        }
