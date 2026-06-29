"""
InkAI 优化后的主工作流程控制器
使用统一的数据上下文管理和智能体交互
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加agents目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

# 导入智能体
# 导入所有智能体
from agents import (
    TagSelectorAgent,
    CharacterCreatorAgent,
    CharacterImprover,
    StorylineGeneratorAgent,
    QualityAssessorAgent,
    ChapterWriterAgent,
    NovelContinuationAgent,
    ContinuationStorylineGenerator,
    ContinuationChapterWriter,
    NovelStorylineImprover,
    StorylineImprover,
    ContinuationQualityAssessor,
    ContinuationChapterImprover,
    ContinuationCharacterConsistencyAssessor,
    ContinuationPlotLogicAssessor,
    ContinuationWorldConsistencyAssessor,
    ContinuationStyleConsistencyAssessor,
    ContinuationReaderExperienceAssessor,
    ContinuationLongTermConsistencyAssessor,
    ContinuationCharacterConsistencyImprover,
    ContinuationPlotLogicImprover,
    ContinuationWorldConsistencyImprover,
    ContinuationStyleConsistencyImprover,
    ContinuationReaderExperienceImprover,
    ContinuationLongTermConsistencyImprover,
    ContinuationArcPlanner
)

# 导入核心管理模块
from core.core_knowledge_manager import CoreKnowledgeManager
from core.dynamic_knowledge_manager import DynamicKnowledgeManager
from core.intelligent_context_selector import IntelligentContextSelector

# 导入性能优化模块
from performance.parallel_processor import ParallelProcessor
from performance.intelligent_cache_manager import IntelligentCacheManager
from performance.batch_processor import BatchProcessor, LLMRequestBatcher
from performance.performance_monitor import PerformanceMonitor

# 导入长期优化模块
from optimization.runtime_guarantee_system import RuntimeGuaranteeSystem
from optimization.long_term_consistency_system import LongTermConsistencySystem

# 导入其他模块
from data_manager import DataManager
from workflow_context import WorkflowContext
import config


class InkAIWorkflowOptimized:
    """InkAI 优化后的主工作流程控制器"""
    
    def __init__(self):
        # 初始化智能体
        self.tag_selector = TagSelectorAgent()
        self.character_creator = CharacterCreatorAgent()
        self.character_improver = CharacterImprover()
        self.storyline_generator = StorylineGeneratorAgent()
        self.quality_assessor = QualityAssessorAgent()
        self.chapter_writer = ChapterWriterAgent()
        
        # 续写相关智能体
        self.novel_continuation_agent = NovelContinuationAgent()
        self.continuation_storyline_generator = ContinuationStorylineGenerator()
        self.continuation_chapter_writer = ContinuationChapterWriter()
        self.storyline_improver = NovelStorylineImprover()
        self.continuation_storyline_improver = NovelStorylineImprover()
        self.continuation_quality_assessor = ContinuationQualityAssessor()
        self.continuation_chapter_improver = ContinuationChapterImprover()
        
        # 专项评估智能体
        self.continuation_character_consistency_assessor = ContinuationCharacterConsistencyAssessor()
        self.continuation_plot_logic_assessor = ContinuationPlotLogicAssessor()
        self.continuation_world_consistency_assessor = ContinuationWorldConsistencyAssessor()
        self.continuation_style_consistency_assessor = ContinuationStyleConsistencyAssessor()
        self.continuation_reader_experience_assessor = ContinuationReaderExperienceAssessor()
        self.continuation_long_term_consistency_assessor = ContinuationLongTermConsistencyAssessor()
        
        # 专项改进智能体
        self.continuation_character_consistency_improver = ContinuationCharacterConsistencyImprover()
        self.continuation_plot_logic_improver = ContinuationPlotLogicImprover()
        self.continuation_world_consistency_improver = ContinuationWorldConsistencyImprover()
        self.continuation_style_consistency_improver = ContinuationStyleConsistencyImprover()
        self.continuation_reader_experience_improver = ContinuationReaderExperienceImprover()
        self.continuation_long_term_consistency_improver = ContinuationLongTermConsistencyImprover()
        
        self.data_manager = DataManager()

        # 初始化向量嵌入服务
        from core.embedding_service import EmbeddingService
        self.embedding_service = EmbeddingService()
        print(f"[Workflow] 向量嵌入服务初始化完成，可用: {self.embedding_service.is_available}")

        # 初始化核心管理模块
        self.core_knowledge_manager = CoreKnowledgeManager(self.data_manager)
        self.dynamic_knowledge_manager = DynamicKnowledgeManager(self.data_manager)
        self.intelligent_context_selector = IntelligentContextSelector(
            self.data_manager, 
            self.core_knowledge_manager, 
            self.dynamic_knowledge_manager
        )
        
        # 初始化性能优化模块
        try:
            self.parallel_processor = ParallelProcessor(max_workers=4)
            self.cache_manager = IntelligentCacheManager()
            self.batch_processor = BatchProcessor()
            self.llm_batcher = LLMRequestBatcher(self.batch_processor)
            self.performance_monitor = PerformanceMonitor()
            
            # 初始化长期优化模块
            self.runtime_guarantee_system = RuntimeGuaranteeSystem()
            self.long_term_consistency_system = LongTermConsistencySystem(self.data_manager)
            
            # 延迟启动性能监控，避免启动时的问题
            self._performance_monitoring_enabled = True
            print("性能优化模块初始化成功")
        except Exception as e:
            print(f"性能优化模块初始化失败: {e}")
            # 设置默认值，确保系统仍能运行
            self.parallel_processor = None
            self.cache_manager = None
            self.batch_processor = None
            self.llm_batcher = None
            self.performance_monitor = None
            self.runtime_guarantee_system = None
            self.long_term_consistency_system = None
            self._performance_monitoring_enabled = False
        
        # 使用统一的工作流程上下文
        self.context = None
    
    def start_performance_monitoring(self):
        """启动性能监控"""
        try:
            if self._performance_monitoring_enabled and self.performance_monitor:
                self.performance_monitor.start_monitoring()
                print("性能监控已启动")
                return True
            else:
                print("性能监控未启用或不可用")
                return False
        except Exception as e:
            print(f"启动性能监控失败: {e}")
            return False
    
    def stop_performance_monitoring(self):
        """停止性能监控"""
        try:
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
                print("性能监控已停止")
                return True
            return False
        except Exception as e:
            print(f"停止性能监控失败: {e}")
            return False
    
    def start_new_novel(self, user_requirements: str, title: str = "未命名小说") -> Dict[str, Any]:
        """开始新小说创作流程"""
        print(f"开始创作新小说: {title}")
        print(f"用户需求: {user_requirements}")
        
        # 初始化小说项目
        novel_data = {
            "title": title,
            "user_requirements": user_requirements,
            "tags": {},
            "characters": {},
            "storyline": {}
        }
        
        novel_id = self.data_manager.create_novel_project(novel_data)
        
        # 创建统一的工作流程上下文
        self.context = WorkflowContext(novel_id)
        self.context.set_basic_info(title, user_requirements)
        self.context.set_current_step("tag_selection")
        
        # 保存上下文到文件
        self.context.save_context()
        
        return {
            "novel_id": novel_id,
            "status": "created",
            "next_step": "tag_selection"
        }
    
    def select_tags(self, selected_tags: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """选择小说标签"""
        print("开始标签选择流程...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 使用统一的输入数据生成
        input_data = self.context.get_agent_input_data("tag_selector", {"selected_tags": selected_tags})
        
        result = self.tag_selector.process(input_data)
        
        # 保存结果到上下文
        self.context.set_tags(result["selected_tags"])
        self.context.cache_result("tags", result)
        self.context.set_current_step("character_creation")
        
        # 保存到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "tags", result)
        
        print(f"标签选择完成: {result['selected_tags']}")
        
        return {
            "status": "success",
            "tags": result,
            "next_step": "character_creation"
        }
    
    def create_characters(self) -> Dict[str, Any]:
        """创建人物形象"""
        print("开始人物形象创建...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 使用统一的输入数据生成
        input_data = self.context.get_agent_input_data("character_creator")
        
        result = self.character_creator.process(input_data)
        
        # 保存结果到上下文
        self.context.set_characters(result)
        self.context.cache_result("characters", result)
        
        # 质量评估
        quality_input = self.context.get_agent_input_data("quality_assessor", {
            "content": result.get("main_character", {}),
            "content_type": "character"
        })
        
        quality_result = self.quality_assessor.process(quality_input)
        self.context.cache_quality_assessment("character", quality_result)
        
        # 保存到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "characters", result)
        self.data_manager.save_novel_data(self.context.novel_id, "character_quality_assessment", quality_result)
        
        print("人物形象创建完成")
        
        # 根据质量评估结果决定下一步
        if quality_result.get("is_high_quality", False):
            self.context.set_current_step("storyline_generation")
            next_step = "storyline_generation"
        else:
            print(f"人物质量评估: {quality_result['overall_score']}分")
            print(f"改进建议: {quality_result['suggestions']}")
            self.context.set_current_step("character_improvement")
            next_step = "character_improvement"
        
        return {
            "status": "success" if quality_result.get("is_high_quality", False) else "needs_improvement",
            "characters": result,
            "quality_assessment": quality_result,
            "next_step": next_step
        }
    
    def improve_character(self, suggestions: List[str]) -> Dict[str, Any]:
        """改进人物形象"""
        print("开始人物形象改进...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 获取当前人物数据
        current_characters = self.context.characters
        if not current_characters:
            return {"error": "没有找到现有人物数据"}
        
        # 获取质量评估结果（如果没有则使用默认建议）
        quality_assessment = self.context.get_quality_assessment("character")
        if not quality_assessment:
            print("没有找到质量评估结果，使用默认改进建议")
            quality_assessment = {"suggestions": []}
        
        # 构建改进输入数据
        input_data = {
            "current_characters": current_characters,
            "overall_storyline": self.context.storyline,
            "improvement_suggestions": suggestions or quality_assessment.get("suggestions", []),
            "tags": self.context.tags,
            "user_requirements": self.context.get_user_requirements_with_rules()
        }

        # 调用人物改进智能体
        result = self.character_improver.process(input_data)
        
        if "error" in result:
            return result
        
        # 保存改进后的人物数据
        improved_characters = result.get("improved_characters", {})
        self.context.set_characters(improved_characters)
        self.context.cache_result("characters", improved_characters)
        
        # 保存到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "characters", improved_characters)
        
        # 重新进行质量评估
        quality_input = self.context.get_agent_input_data("quality_assessor", {
            "content": improved_characters.get("main_character", {}),
            "content_type": "character"
        })
        
        new_quality_result = self.quality_assessor.process(quality_input)
        self.context.cache_quality_assessment("character", new_quality_result)
        
        # 保存质量评估结果到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "character_quality_assessment", new_quality_result)
        
        print("人物形象改进完成")
        
        # 根据新的质量评估结果决定下一步
        if new_quality_result.get("is_high_quality", False):
            self.context.set_current_step("storyline_generation")
            next_step = "storyline_generation"
        else:
            print(f"改进后人物质量评估: {new_quality_result['overall_score']}分")
            print(f"改进建议: {new_quality_result['suggestions']}")
            self.context.set_current_step("character_improvement")
            next_step = "character_improvement"
        
        return {
            "status": "success" if new_quality_result.get("is_high_quality", False) else "needs_improvement",
            "characters": improved_characters,
            "quality_assessment": new_quality_result,
            "improvement_notes": result.get("improvement_notes", []),
            "next_step": next_step
        }
    
    def generate_storyline(self) -> Dict[str, Any]:
        """生成故事线"""
        print("开始故事线生成...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 使用统一的输入数据生成
        input_data = self.context.get_agent_input_data("storyline_generator")
        
        result = self.storyline_generator.process(input_data)
        
        # 保存结果到上下文
        self.context.set_storyline(result)
        self.context.cache_result("storyline", result)
        
        # 质量评估
        quality_input = self.context.get_agent_input_data("quality_assessor", {
            "content": result.get("overall_storyline", {}),
            "content_type": "storyline"
        })
        
        quality_result = self.quality_assessor.process(quality_input)
        self.context.cache_quality_assessment("storyline", quality_result)
        
        # 保存到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "storyline", result)
        self.data_manager.save_novel_data(self.context.novel_id, "storyline_quality_assessment", quality_result)
        
        print("故事线生成完成")
        
        # 根据质量评估结果决定下一步
        if quality_result.get("is_high_quality", False):
            self.context.set_current_step("knowledge_graph_creation")
            next_step = "knowledge_graph_creation"
        else:
            print(f"故事线质量评估: {quality_result['overall_score']}分")
            print(f"改进建议: {quality_result['suggestions']}")
            # 即使质量不高，也继续到下一步，用户可以在故事线生成模块中手动优化
            self.context.set_current_step("knowledge_graph_creation")
            next_step = "knowledge_graph_creation"
        
        return {
            "status": "success" if quality_result.get("is_high_quality", False) else "needs_improvement",
            "storyline": result,
            "quality_assessment": quality_result,
            "next_step": next_step
        }
    
    def improve_storyline(self, suggestions: List[str]) -> Dict[str, Any]:
        """改进故事线"""
        print("开始故事线改进...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 获取当前故事线数据
        current_storyline = self.context.storyline
        if not current_storyline:
            return {"error": "没有找到现有故事线数据"}
        
        # 获取质量评估结果（如果没有则使用默认建议）
        quality_assessment = self.context.get_quality_assessment("storyline")
        if not quality_assessment:
            print("没有找到质量评估结果，使用默认改进建议")
            quality_assessment = {"suggestions": []}
        
        # 构建改进输入数据
        input_data = {
            "current_storyline": current_storyline,
            "overall_storyline": current_storyline.get("overall_storyline", {}),
            "characters": self.context.characters,
            "improvement_suggestions": suggestions or quality_assessment.get("suggestions", []),
            "tags": self.context.tags,
            "user_requirements": self.context.get_user_requirements_with_rules()
        }

        # 调用故事线改进智能体
        result = self.storyline_improver.process(input_data)
        
        if "error" in result:
            return result
        
        # 保存改进后的故事线数据
        improved_storyline = result.get("improved_storyline", {})
        self.context.set_storyline(improved_storyline)
        self.context.cache_result("storyline", improved_storyline)
        
        # 保存到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "storyline", improved_storyline)
        
        # 重新进行质量评估
        quality_input = self.context.get_agent_input_data("quality_assessor", {
            "content": improved_storyline.get("overall_storyline", {}),
            "content_type": "storyline"
        })
        
        new_quality_result = self.quality_assessor.process(quality_input)
        self.context.cache_quality_assessment("storyline", new_quality_result)
        
        # 保存质量评估结果到数据管理器
        self.data_manager.save_novel_data(self.context.novel_id, "storyline_quality_assessment", new_quality_result)
        
        print("故事线改进完成")
        
        # 根据新的质量评估结果决定下一步
        if new_quality_result.get("is_high_quality", False):
            self.context.set_current_step("knowledge_graph_creation")
            next_step = "knowledge_graph_creation"
        else:
            print(f"改进后故事线质量评估: {new_quality_result['overall_score']}分")
            print(f"改进建议: {new_quality_result['suggestions']}")
            # 即使改进后质量仍不高，也继续到下一步，用户可以在故事线生成模块中继续优化
            self.context.set_current_step("knowledge_graph_creation")
            next_step = "knowledge_graph_creation"
        
        return {
            "status": "success" if new_quality_result.get("is_high_quality", False) else "needs_improvement",
            "storyline": improved_storyline,
            "quality_assessment": new_quality_result,
            "improvement_notes": result.get("improvement_notes", []),
            "next_step": next_step
        }
    
    def create_knowledge_graph(self) -> Dict[str, Any]:
        """创建知识图谱"""
        print("开始创建知识图谱...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 创建知识图谱
        kg_id = self.data_manager.create_knowledge_graph(
            self.context.novel_id, 
            self.context.characters, 
            self.context.storyline
        )
        
        self.context.set_knowledge_graph_id(kg_id)
        self.context.set_current_step("chapter_writing")
        
        print(f"知识图谱创建完成: {kg_id}")
        
        return {
            "status": "success",
            "knowledge_graph_id": kg_id,
            "next_step": "chapter_writing"
        }
    
    def write_first_chapter(self) -> Dict[str, Any]:
        """写作第一章"""
        print("开始写作第一章...")
        
        if not self.context:
            return {"error": "请先创建新小说项目"}
        
        # 智能数据检查和恢复
        if not self.context.storyline:
            print("上下文中storyline为空，尝试重新加载...")
            storyline = self.data_manager.load_novel_data(self.context.novel_id, "storyline")
            if storyline:
                self.context.set_storyline(storyline)
                print("已重新加载storyline数据")
            else:
                return {"error": "未找到故事线数据，请先生成故事线"}
        
        # 获取第一章信息
        first_module = self.context.storyline.get("first_module", {})
        if not first_module:
            # 尝试从文件直接加载storyline数据
            print("上下文中未找到first_module，尝试从文件重新加载...")
            storyline = self.data_manager.load_novel_data(self.context.novel_id, "storyline")
            if storyline:
                self.context.set_storyline(storyline)
                first_module = self.context.storyline.get("first_module", {})
                if first_module:
                    print("已成功重新加载first_module数据")
                else:
                    return {"error": "故事线数据中缺少第一章信息，请重新生成故事线"}
            else:
                return {"error": "未找到第一章信息，请检查故事线数据完整性"}
        
        # 使用统一的输入数据生成
        input_data = self.context.get_agent_input_data("chapter_writer", {
            "chapter_info": first_module
        })
        
        result = self.chapter_writer.process(input_data)
        
        # 质量评估
        quality_input = self.context.get_agent_input_data("quality_assessor", {
            "content": result["chapter_content"],
            "content_type": "story"
        })
        
        quality_result = self.quality_assessor.process(quality_input)
        self.context.cache_quality_assessment("story", quality_result)
        
        # 保存章节
        chapter_saved = self.data_manager.save_chapter(
            self.context.novel_id, 
            1, 
            result["chapter_content"]
        )
        
        if chapter_saved:
            self.context.set_current_step("chapter_completed")
            print("第一章写作完成")
            
            return {
                "status": "success",
                "chapter": result["chapter_content"],
                "quality_assessment": quality_result,
                "next_step": "chapter_completed"
            }
        else:
            return {"error": "章节保存失败"}
    
    def start_novel_continuation(self, novel_id: str, user_requirements: str = "", reset_cache: bool = False) -> Dict[str, Any]:
        """开始小说续写流程"""
        print(f"开始续写小说: {novel_id}, 重置缓存: {reset_cache}")
        
        # 如果用户没有提供需求，从metadata.json中读取原始创作需求
        if not user_requirements:
            print("用户未提供续写需求，从原始创作需求中读取...")
            metadata = self.data_manager._load_novel_metadata(novel_id)
            if metadata and metadata.get("user_requirements"):
                user_requirements = metadata["user_requirements"]
                print(f"成功读取原始创作需求，长度: {len(user_requirements)}")
            else:
                print("警告：无法读取原始创作需求")
        
        # 根据用户选择决定是否清除缓存
        if reset_cache:
            try:
                print("用户选择重新开始，清除续写缓存数据...")
                clear_result = self.clear_continuation_cache(novel_id)
                if "error" in clear_result:
                    print(f"清除缓存时出现警告: {clear_result['error']}")
            except Exception as e:
                print(f"清除缓存时出现异常: {e}")
        else:
            print("用户选择继续上次进度，保留缓存数据...")
        
        # 尝试加载现有上下文
        context_loaded = self.load_context_by_novel_id(novel_id)
        
        if not context_loaded:
            # 如果没有现有上下文，创建新的
            print("没有找到现有上下文，创建新的续写上下文")
            self.context = WorkflowContext(novel_id)
        else:
            print(f"成功加载现有上下文，当前步骤: {self.context.current_step}")
            
            # 如果已经有续写上下文且用户没有选择重置，检查是否可以继续
            if self.context.is_continuation and not reset_cache:
                # 即使继续上次进度，也要确保user_requirements不为空
                if not self.context.user_requirements and user_requirements:
                    print("更新上下文中的用户需求")
                    self.context.user_requirements = user_requirements
                    self.context.save_context()
                
                print("检测到现有续写进度，继续上次的续写流程")
                return {
                    "success": True,
                    "status": "continued",
                    "message": "继续上次的续写进度",
                    "current_step": self.context.current_step,
                    "next_step": self.context.current_step
                }
        
        # 调用续写智能体查找小说并构建知识库
        try:
            print(f"调用续写智能体处理小说: {novel_id}")
            result = self.novel_continuation_agent.process({
                "novel_id": novel_id,
                "user_requirements": user_requirements
            })
            
            if "error" in result:
                print(f"续写智能体处理失败: {result['error']}")
                return {"success": False, "error": result['error']}
                
        except Exception as e:
            print(f"调用续写智能体时发生异常: {e}")
            return {"success": False, "error": f"调用续写智能体失败: {str(e)}"}
        
        # 设置续写上下文
        if not self.context:
            self.context = WorkflowContext(novel_id)
        
        self.context.set_basic_info(
            result["novel_data"]["novel_info"]["title"], 
            user_requirements
        )
        self.context.set_continuation_mode(
            result["novel_data"], 
            result["knowledge_base"]
        )
        self.context.set_current_step("storyline_generation")
        
        # 保存上下文
        self.save_context()
        
        return {
            "success": True,
            "status": "success",
            "novel_id": novel_id,
            "novel_title": result["novel_data"]["novel_info"]["title"],
            "chapter_count": len(result["novel_data"]["chapters"]),
            "next_step": "storyline_generation"
        }
    
    def _check_arc_trigger(self, novel_id: str) -> bool:
        """检查是否需要触发弧规划：无活跃弧，或当前弧剩余章数 <= 1"""
        arc = self.data_manager.load_active_arc(novel_id)
        if arc is None:
            return True
        return arc.get("chapters_remaining", 0) <= 1

    def generate_continuation_storyline(self, novel_id: str = None) -> Dict[str, Any]:
        """生成续写故事线"""
        print("开始生成续写故事线...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}

        # 弧触发检查：无活跃弧或弧快结束时，先规划新弧，返回草案让用户确认
        _novel_id = novel_id or (self.context.novel_id if self.context else None)
        if _novel_id and self._check_arc_trigger(_novel_id):
            kb = self.context.continuation_data.get("knowledge_base", {})
            chapters = self.data_manager.get_novel_chapters(_novel_id)
            kb["current_chapter_number"] = len(chapters) + 1
            planner = ContinuationArcPlanner()
            plan_result = planner.process({"knowledge_base": kb})
            if plan_result.get("success"):
                return {
                    "arc_pending": True,
                    "arc_draft": plan_result["arc"],
                    "message": "请先确认故事弧计划，再继续生成故事线"
                }

        # 向量语义检索：找到与当前剧情方向最相关的前N章
        kb = self.context.continuation_data["knowledge_base"]
        if self.embedding_service.is_available:
            try:
                # 构建查询：用最近章节的摘要 + 剧情方向做语义检索
                novel_dir = os.path.join(self.data_manager.novels_dir, novel_id or self.context.novel_id)
                from core.embedding_service import ChapterEmbeddingStore
                store = ChapterEmbeddingStore(novel_dir, self.embedding_service)

                # 用最近几章的摘要作为查询
                # 回填缺失的历史章节向量（修复：第1,2章可能没有向量）
                store.backfill_chapters(kb.get("chapters", []))

                recent = kb.get("recent_chapters_summaries", [])
                if recent:
                    query_parts = []
                    for ch in recent:
                        query_parts.append(ch.get("summary", ""))
                    query = "；".join(query_parts)
                    retrieved = store.search_relevant_chapters(query, current_chapter=len(kb.get("chapters", [])),
                                                               top_k=5)
                    if retrieved:
                        # 加载检索到的章节详情，注入 KB
                        all_chapters = kb.get("chapters", [])
                        ch_map = {ch.get("chapter_number"): ch for ch in all_chapters}
                        vector_context = []
                        for item in retrieved:
                            ch_num = item["chapter_number"]
                            ch = ch_map.get(ch_num)
                            if ch:
                                vector_context.append({
                                    "chapter_number": ch_num,
                                    "title": ch.get("title", ""),
                                    "summary": ch.get("summary", ""),
                                    "key_events": ch.get("key_events", []),
                                    "relevance_score": item["score"]
                                })
                        if vector_context:
                            kb["vector_retrieved_chapters"] = vector_context
                            self.context.continuation_data["knowledge_base"] = kb
                            print(f"[Vector] 检索到 {len(vector_context)} 个相关章节: {[c['chapter_number'] for c in vector_context]}")
            except Exception as e:
                print(f"[Vector] 语义检索失败（不影响主线）: {e}")

        # 注入动态知识（用最近章节+情节线构建语义查询）
        query_parts = []
        last_ch = kb.get("last_chapter_summary", {})
        if last_ch.get("summary"):
            query_parts.append(last_ch["summary"][:200])
        for rc in kb.get("recent_chapters_summaries", [])[-2:]:
            if rc.get("summary"):
                query_parts.append(rc["summary"][:200])
        storyline_query = "；".join(query_parts) if query_parts else None
        kb = self._inject_dynamic_knowledge(kb, self.context.novel_id, storyline_query)

        # 注入上一章的场景连续性状态（如果上一章场景未结束，则本章需要延续）
        previous_scene = self._get_previous_chapter_scene_continuity(novel_id or self.context.novel_id)
        if previous_scene:
            kb["previous_scene_continuity"] = previous_scene
            print(f"[SceneContinuity] 上一章场景状态: span={previous_scene.get('scene_span_chapters')}, "
                  f"phase={previous_scene.get('scene_phase')}, "
                  f"continues={previous_scene.get('continues_from_previous')}")

        # 注入活跃弧上下文到知识库
        _nid = novel_id or (self.context.novel_id if self.context else None)
        if _nid:
            _active_arc = self.data_manager.load_active_arc(_nid)
            if _active_arc:
                kb["active_arc"] = _active_arc
                # 计算本章是弧的第几章
                _arc_chapter_idx = (_active_arc["planned_chapters"]
                                    - _active_arc["chapters_remaining"] + 1)
                _roles = _active_arc.get("chapter_roles", [])
                kb["current_arc_role"] = (
                    _roles[_arc_chapter_idx - 1]
                    if 0 < _arc_chapter_idx <= len(_roles)
                    else {}
                )

        # 调用续写故事线生成智能体
        result = self.continuation_storyline_generator.process({
            "knowledge_base": kb,
            "user_requirements": self.context.get_user_requirements_with_rules()
        })
        
        if "error" in result:
            print(f"续写故事线生成智能体返回错误: {result['error']}")
            return {"success": False, "error": result["error"]}
        
        # 检查返回结果的结构
        if "next_chapter_storyline" not in result:
            print(f"续写故事线生成智能体返回结果缺少next_chapter_storyline字段: {result}")
            return {"success": False, "error": "故事线生成结果格式错误"}
        
        # 检查故事线数据是否有解析错误
        storyline_data = result["next_chapter_storyline"]
        if isinstance(storyline_data, dict) and storyline_data.get("parse_error"):
            print(f"❌ 故事线生成时发生JSON解析错误，原始内容长度: {len(storyline_data.get('content', ''))}")
            return {"success": False, "error": "故事线生成时JSON解析失败，请重试"}
        
        # 验证故事线数据的完整性
        if isinstance(storyline_data, dict):
            required_fields = ["chapter_title", "scene_setting", "plot_points"]
            missing_fields = [field for field in required_fields if field not in storyline_data or not storyline_data[field]]
            if missing_fields:
                print(f"❌ 故事线数据不完整，缺少字段: {missing_fields}")
                return {"success": False, "error": f"故事线数据不完整，缺少: {', '.join(missing_fields)}"}
        
        # 保存故事线到上下文
        self.context.cache_result("next_chapter_storyline", result["next_chapter_storyline"])
        
        # 自动进行质量评估（与正常故事线生成流程保持一致）
        print("开始续写故事线质量评估...")
        quality_result = self.assess_continuation_quality(novel_id, "storyline")
        
        if quality_result.get("success", False):
            print(f"续写故事线质量评估完成: {quality_result.get('quality_assessment', {}).get('overall_score', '未知')}分")
            # 根据质量评估结果决定下一步（assess_continuation_quality已经设置了current_step）
            next_step = quality_result.get("next_step", "chapter_writing")
        else:
            print(f"续写故事线质量评估失败: {quality_result.get('error', '未知错误')}")
            # 即使质量评估失败，也继续到下一步
            self.context.set_current_step("chapter_writing")
            next_step = "chapter_writing"
        
        # 保存上下文和缓存数据到文件
        self.save_context()
        print(f"已保存上下文，当前步骤: {self.context.current_step}")
        
        return {
            "success": True,
            "status": "success",
            "storyline": result["next_chapter_storyline"],
            "next_step": next_step,
            "quality_assessment": quality_result.get("quality_assessment") if quality_result.get("success") else None
        }
    
    def improve_continuation_storyline(self, novel_id: str = None) -> Dict[str, Any]:
        """改进续写故事线"""
        print("开始改进续写故事线...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
        
        # 获取当前故事线
        current_storyline = self.context.get_cached_result("next_chapter_storyline")
        if not current_storyline:
            return {"error": "请先生成故事线"}
        
        # 获取质量评估结果（如果没有则使用默认建议）
        quality_assessment = self.context.get_quality_assessment("storyline")
        if not quality_assessment:
            print("没有找到质量评估结果，使用默认改进建议")
            quality_assessment = {"suggestions": ["提升故事线的逻辑性和连贯性", "增强情节的吸引力"]}
        
        # 确保有改进建议
        suggestions = quality_assessment.get("suggestions", [])
        if not suggestions or len(suggestions) == 0:
            print("质量评估结果中没有改进建议，使用默认建议")
            suggestions = ["提升故事线的逻辑性和连贯性", "增强情节的吸引力", "优化人物发展轨迹"]
        
        # 构建改进输入数据
        knowledge_base = self.context.continuation_data["knowledge_base"]
        input_data = {
            "current_storyline": current_storyline,
            "overall_storyline": knowledge_base.get("plot_lines", {}),
            "characters": knowledge_base.get("character_profiles", {}),
            "improvement_suggestions": suggestions,
            "tags": knowledge_base.get("tags", {}),
            "user_requirements": self.context.get_user_requirements_with_rules()
        }

        print(f"改进输入数据检查:")
        print(f"  - current_storyline: {bool(current_storyline)}")
        print(f"  - improvement_suggestions: {len(suggestions)} 条")
        print(f"  - knowledge_base: {bool(knowledge_base)}")
        print(f"  - user_requirements: {bool(self.context.get_user_requirements_with_rules())}")

        # 调用续写故事线改进智能体
        result = self.continuation_storyline_improver.process(input_data)
        
        if "error" in result:
            print(f"续写故事线改进智能体返回错误: {result['error']}")
            return {"success": False, "error": result["error"]}
        
        # 检查返回结果的结构
        if "improved_storyline" not in result:
            print(f"续写故事线改进智能体返回结果缺少improved_storyline字段: {result}")
            return {"success": False, "error": "故事线改进结果格式错误"}
        
        # 保存改进后的故事线
        improved_storyline = result.get("improved_storyline", {})
        self.context.cache_result("next_chapter_storyline", improved_storyline)
        
        # 保存到数据管理器（持久化存储）
        self.data_manager.save_novel_data(self.context.novel_id, "next_chapter_storyline", improved_storyline)

        # 重新进行质量评估
        quality_input = self.context.get_agent_input_data("quality_assessor", {
            "content": improved_storyline.get("overall_storyline", improved_storyline),
            "content_type": "storyline"
        })
        new_quality_result = self.quality_assessor.process(quality_input)
        self.context.cache_quality_assessment("continuation_storyline", new_quality_result)
        self.data_manager.save_novel_data(self.context.novel_id, "continuation_storyline_quality_assessment", new_quality_result)

        # 保存上下文
        self.save_context()

        print("续写故事线改进完成")
        
        return {
            "success": True,
            "status": "success",
            "storyline": improved_storyline,
            "improvement_notes": result.get("improvement_notes", []),
            "quality_assessment": new_quality_result,
            "next_step": "quality_assessment"
        }

    def improve_continuation_chapter(self, novel_id: str = None, suggestions: List[str] = None) -> Dict[str, Any]:
        """改进续写章节"""
        print("开始改进续写章节...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
        
        try:
            # 获取当前续写章节
            continuation_chapter = self.context.get_cached_result("continuation_chapter")
            if not continuation_chapter:
                return {"error": "未找到续写章节数据，请先生成章节"}
            
            # 获取质量评估数据（如果有的话）
            quality_assessment = self.context.get_quality_assessment("chapter")
            if not quality_assessment:
                print("没有找到章节质量评估结果，使用默认改进建议")
                quality_assessment = {"suggestions": suggestions or []}
            
            # 构建改进输入
            knowledge_base = self.context.continuation_data["knowledge_base"]
            improvement_input = {
                "chapter_content": continuation_chapter,
                "quality_assessment": quality_assessment,
                "knowledge_base": {
                    "characters": knowledge_base.get("character_profiles", {}),
                    "storyline": knowledge_base.get("plot_lines", {}),
                    "continuation_storyline": self.context.get_cached_result("next_chapter_storyline"),
                    "tags": knowledge_base.get("tags", {})
                },
                "user_requirements": self.context.get_user_requirements_with_rules(),
                "suggestions": suggestions or []
            }

            # 调用续写章节改进智能体
            improved_result = self.continuation_chapter_improver.process(improvement_input)
            
            if "error" in improved_result:
                return {"error": f"章节改进失败: {improved_result['error']}"}
            
            # 更新上下文中的续写章节
            improved_chapter = improved_result.get("improved_chapter", continuation_chapter)
            self.context.cache_result("continuation_chapter", improved_chapter)
            
            # 保存改进后的章节到数据管理器
            self.data_manager.save_novel_data(
                self.context.novel_id,
                "continuation_chapter",
                improved_chapter
            )

            # 对改进后的章节重新进行质量评估
            print("对改进后的续写章节重新进行质量评估...")
            chapter_content = improved_chapter.get("content", "")
            quality_input = self.context.get_agent_input_data("quality_assessor", {
                "content": improved_chapter,
                "content_type": "story"
            })
            new_quality_result = self.quality_assessor.process(quality_input)
            self.context.cache_quality_assessment("chapter", new_quality_result)
            self.data_manager.save_novel_data(self.context.novel_id, "continuation_chapter_quality_assessment", new_quality_result)
            print(f"续写章节改进后质量评估完成: {new_quality_result.get('quality_assessment', {}).get('overall_score', '未知')}分")

            # 保存上下文
            self.save_context()

            print("续写章节改进完成")

            return {
                "success": True,
                "status": "success",
                "improved_chapter": improved_chapter,
                "improvement_plan": improved_result.get("improvement_plan", {}),
                "improvement_summary": improved_result.get("improvement_summary", "章节已改进"),
                "quality_assessment": new_quality_result,
                "next_step": "save_chapter"
            }
            
        except Exception as e:
            print(f"改进续写章节时出错: {e}")
            return {"error": f"改进续写章节失败: {str(e)}"}
    
    def update_continuation_storyline(self, novel_id: str = None, update_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """更新续写故事线"""
        print("开始更新续写故事线...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
        
        if not update_data:
            return {"error": "没有提供更新数据"}
        
        try:
            # 获取当前的故事线数据
            current_storyline = self.context.get_cached_result("next_chapter_storyline")
            if not current_storyline:
                return {"error": "没有找到续写故事线数据"}
            
            # 更新故事线数据
            updated_storyline = {**current_storyline}
            
            # 处理各种字段的更新
            for field, value in update_data.items():
                if field == "scene_setting" and isinstance(value, dict):
                    # 更新场景设定
                    if not updated_storyline.get("scene_setting"):
                        updated_storyline["scene_setting"] = {}
                    updated_storyline["scene_setting"].update(value)
                elif field in ["plot_points", "key_events", "foreshadowing"] and isinstance(value, str):
                    # 处理列表字段（从字符串转换为列表）
                    lines = [line.strip() for line in value.split('\n') if line.strip()]
                    updated_storyline[field] = lines
                else:
                    # 直接更新其他字段
                    updated_storyline[field] = value
            
            # 保存更新后的故事线到缓存
            self.context.cache_result("next_chapter_storyline", updated_storyline)
            
            # 保存到数据管理器（持久化存储）
            self.data_manager.save_novel_data(self.context.novel_id, "next_chapter_storyline", updated_storyline)
            
            # 保存上下文
            self.save_context()
            
            print("续写故事线更新成功")
            return {
                "status": "success",
                "message": "续写故事线更新成功",
                "storyline": updated_storyline
            }
            
        except Exception as e:
            print(f"更新续写故事线失败: {e}")
            return {"error": f"更新续写故事线失败: {str(e)}"}
    
    def assess_continuation_quality(self, novel_id: str = None, content_type: str = "storyline") -> Dict[str, Any]:
        """评估续写质量"""
        print("开始评估续写质量...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
        
        # 获取要评估的内容
        if content_type == "storyline":
            content = self.context.get_cached_result("next_chapter_storyline")
        elif content_type == "story":
            content = self.context.get_cached_result("next_chapter_content")
            # 如果缓存中没有内容，尝试从已保存的章节中获取最新的章节
            if not content:
                print("缓存中没有章节内容，尝试从已保存的章节中获取...")
                chapters = self.data_manager.get_chapters(self.context.novel_id)
                if chapters and len(chapters) > 0:
                    # 获取最新的章节（续写章节）
                    latest_chapter = chapters[-1]
                    if latest_chapter.get("chapter_number", 0) > 1:  # 确保是续写章节
                        content = latest_chapter
                        print(f"从已保存的章节中获取到内容: 第{latest_chapter.get('chapter_number')}章")
        else:
            return {"error": "不支持的内容类型"}
        
        if not content:
            return {"error": f"缺少{content_type}内容"}
        
        # 构建续写质量评估输入，注入向量检索结果
        kb = dict(self.context.continuation_data["knowledge_base"])
        if self.embedding_service.is_available and "vector_retrieved_chapters" not in kb:
            try:
                novel_dir = os.path.join(self.data_manager.novels_dir, novel_id or self.context.novel_id)
                from core.embedding_service import ChapterEmbeddingStore
                store = ChapterEmbeddingStore(novel_dir, self.embedding_service)
                store.backfill_chapters(kb.get("chapters", []))
                recent = kb.get("recent_chapters_summaries", [])
                if recent:
                    query = "；".join([ch.get("summary", "") for ch in recent])
                    retrieved = store.search_relevant_chapters(query, current_chapter=len(kb.get("chapters", [])), top_k=5)
                    if retrieved:
                        all_chapters = kb.get("chapters", [])
                        ch_map = {ch.get("chapter_number"): ch for ch in all_chapters}
                        vector_context = []
                        for item in retrieved:
                            ch = ch_map.get(item["chapter_number"])
                            if ch:
                                vector_context.append({
                                    "chapter_number": item["chapter_number"],
                                    "title": ch.get("title", ""),
                                    "summary": ch.get("summary", ""),
                                    "key_events": ch.get("key_events", []),
                                    "relevance_score": item["score"]
                                })
                        if vector_context:
                            kb["vector_retrieved_chapters"] = vector_context
            except Exception as e:
                print(f"[Vector] 评估器检索失败（不影响主线）: {e}")

        # 注入动态知识（用待评估内容构建语义查询）
        assessor_query = None
        if content_type == "story" and content:
            assessor_query = content.get("content", "")[:500]
        elif content_type == "storyline" and content:
            plot_pts = content.get("plot_points", [])
            assessor_query = "；".join(str(p)[:200] for p in plot_pts[:5]) if plot_pts else None
        kb = self._inject_dynamic_knowledge(kb, self.context.novel_id, assessor_query)

        quality_input = {
            "continuation_content": content,
            "original_knowledge_base": kb,
            "content_type": content_type,
            "user_requirements": self.context.get_user_requirements_with_rules()
        }

        result = self.continuation_quality_assessor.process(quality_input)
        
        if "error" in result:
            print(f"续写质量评估智能体返回错误: {result['error']}")
            return {"success": False, "error": result["error"]}
        
        self.context.cache_quality_assessment(content_type, result)
        
        # 保存质量评估结果到数据管理器
        # 统一命名：story -> chapter, storyline -> storyline
        if content_type == "story":
            data_key = "continuation_chapter_quality_assessment"
        else:
            data_key = f"continuation_{content_type}_quality_assessment"
        self.data_manager.save_novel_data(self.context.novel_id, data_key, result)
        
        # 根据评估结果决定下一步
        if result.get("is_high_quality", False):
            if content_type == "storyline":
                self.context.set_current_step("chapter_writing")
                next_step = "chapter_writing"
            else:
                self.context.set_current_step("chapter_save")
                next_step = "chapter_save"
        else:
            if content_type == "storyline":
                self.context.set_current_step("storyline_improvement")
                next_step = "storyline_improvement"
            else:
                self.context.set_current_step("content_improvement")
                next_step = "content_improvement"
        
        # 保存上下文，确保步骤变更被持久化
        self.save_context()
        print(f"质量评估完成，已保存上下文，当前步骤: {self.context.current_step}")
        
        return {
            "success": True,
            "status": "success",
            "quality_assessment": result,
            "next_step": next_step
        }
    
    def write_continuation_chapter(self, novel_id: str = None) -> Dict[str, Any]:
        """写作续写章节"""
        print("开始写作续写章节...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
        
        storyline = self.context.get_cached_result("next_chapter_storyline")
        if not storyline:
            return {"error": "请先生成故事线"}
        
        # 确保 KB 中包含向量检索结果
        kb = self.context.continuation_data["knowledge_base"]
        if self.embedding_service.is_available and "vector_retrieved_chapters" not in kb:
            try:
                novel_dir = os.path.join(self.data_manager.novels_dir, novel_id or self.context.novel_id)
                from core.embedding_service import ChapterEmbeddingStore
                store = ChapterEmbeddingStore(novel_dir, self.embedding_service)
                store.backfill_chapters(kb.get("chapters", []))
                recent = kb.get("recent_chapters_summaries", [])
                if recent:
                    query = "；".join([ch.get("summary", "") for ch in recent])
                    retrieved = store.search_relevant_chapters(query, current_chapter=len(kb.get("chapters", [])), top_k=5)
                    if retrieved:
                        all_chapters = kb.get("chapters", [])
                        ch_map = {ch.get("chapter_number"): ch for ch in all_chapters}
                        vector_context = []
                        for item in retrieved:
                            ch = ch_map.get(item["chapter_number"])
                            if ch:
                                vector_context.append({
                                    "chapter_number": item["chapter_number"],
                                    "title": ch.get("title", ""),
                                    "summary": ch.get("summary", ""),
                                    "key_events": ch.get("key_events", []),
                                    "relevance_score": item["score"]
                                })
                        if vector_context:
                            kb["vector_retrieved_chapters"] = vector_context
                            self.context.continuation_data["knowledge_base"] = kb
                            print(f"[Vector] 章节写手检索到 {len(vector_context)} 个相关章节")
            except Exception as e:
                print(f"[Vector] 章节写手检索失败（不影响主线）: {e}")

        # 注入动态知识（用本章故事线+上一章摘要构建语义查询）
        writer_query_parts = []
        if storyline:
            scene = storyline.get("scene_setting", {})
            if isinstance(scene, dict):
                writer_query_parts.append(scene.get("atmosphere", ""))
            plot_pts = storyline.get("plot_points", [])
            if plot_pts:
                writer_query_parts.append("；".join(str(p)[:200] for p in plot_pts[:3]))
        last_ch = kb.get("last_chapter_summary", {})
        if last_ch.get("summary"):
            writer_query_parts.append(last_ch["summary"][:200])
        writer_query = "；".join(writer_query_parts) if writer_query_parts else None
        kb = self._inject_dynamic_knowledge(kb, self.context.novel_id, writer_query)

        # 调用续写章节写作智能体
        result = self.continuation_chapter_writer.process({
            "storyline": storyline,
            "knowledge_base": kb,
            "user_requirements": self.context.get_user_requirements_with_rules()
        })
        
        if "error" in result:
            print(f"续写章节写作智能体返回错误: {result['error']}")
            return {"success": False, "error": result["error"]}
        
        # 检查返回结果的结构
        if "chapter_content" not in result:
            print(f"续写章节写作智能体返回结果缺少chapter_content字段: {result}")
            return {"success": False, "error": "章节写作结果格式错误"}
        
        # 检查章节内容是否为空
        chapter_content = result["chapter_content"]
        if not chapter_content or not chapter_content.get("content"):
            print(f"章节内容为空: {chapter_content}")
            return {"success": False, "error": "章节内容为空"}
        
        # 保存章节内容到上下文
        self.context.cache_result("next_chapter_content", result["chapter_content"])
        
        # 自动进行章节质量评估（与续写故事线生成流程保持一致）
        print("开始续写章节质量评估...")
        quality_result = self.assess_continuation_quality(novel_id, "story")
        
        if quality_result.get("success", False):
            print(f"续写章节质量评估完成: {quality_result.get('quality_assessment', {}).get('overall_score', '未知')}分")
            # 根据质量评估结果决定下一步（assess_continuation_quality已经设置了current_step）
            next_step = quality_result.get("next_step", "chapter_save")
        else:
            print(f"续写章节质量评估失败: {quality_result.get('error', '未知错误')}")
            # 即使质量评估失败，也继续到下一步
            self.context.set_current_step("chapter_save")
            next_step = "chapter_save"
        
        # 保存上下文和缓存数据到文件
        self.save_context()
        print(f"已保存上下文，当前步骤: {self.context.current_step}")
        
        return {
            "success": True,
            "status": "success",
            "chapter_content": result["chapter_content"],
            "word_count": result["word_count"],
            "writing_quality": result["writing_quality"],
            "next_step": next_step,
            "quality_assessment": quality_result.get("quality_assessment") if quality_result.get("success") else None
        }
    
    def save_continuation_chapter(self, novel_id: str = None) -> Dict[str, Any]:
        """保存续写章节"""
        print("开始保存续写章节...")
        
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {"error": "请先开始续写流程"}
        
        chapter_content = self.context.get_cached_result("next_chapter_content")
        if not chapter_content:
            return {"error": "请先写作章节内容"}
        
        # 获取当前章节号 - 修复：使用文件系统章节数而不是上下文数据
        current_chapter_number = len(self.data_manager.get_novel_chapters(novel_id)) + 1
        
        # 提取纯文本内容
        raw_content = chapter_content.get("content", "")
        clean_content = self._extract_clean_content(raw_content)
        
        # 保存章节（包含所有字段）
        # 从故事线中提取 scene_continuity，用于跨章场景追踪
        storyline = self.context.get_cached_result("next_chapter_storyline") or {}
        chapter_data = {
            "chapter_number": current_chapter_number,
            "title": chapter_content.get("title", f"第{current_chapter_number}章"),
            "content": clean_content,  # 使用清理后的纯文本内容
            "summary": chapter_content.get("summary", ""),
            "key_events": chapter_content.get("key_events", []),
            "character_development": chapter_content.get("character_development", ""),
            "foreshadowing": chapter_content.get("foreshadowing", []),
            "next_chapter_hint": chapter_content.get("next_chapter_hint", ""),
            "consistency_notes": chapter_content.get("consistency_notes", ""),
            "scene_setting": storyline.get("scene_setting", {}),
            "scene_continuity": storyline.get("scene_continuity", {}),
            "created_at": datetime.now().isoformat(),
            "word_count": len(clean_content)
        }
        
        success = self.data_manager.save_chapter(self.context.novel_id, current_chapter_number, chapter_data)
        
        if success:
            # 更新故事弧进度（chapters_remaining - 1，归零时自动清除）
            _nid_save = novel_id or (self.context.novel_id if self.context else None)
            if _nid_save:
                self.data_manager.update_arc_progress(_nid_save)

            # 验证章节字数
            word_count = len(clean_content)
            MIN_WORD_COUNT = 2500

            # 清除相关缓存，避免状态检测错误
            if "next_chapter_storyline" in self.context._cache:
                del self.context._cache["next_chapter_storyline"]
            if "next_chapter_content" in self.context._cache:
                del self.context._cache["next_chapter_content"]
            
            # 修复：更新上下文中的章节数据并重建知识库
            if self.context.continuation_data and "novel_data" in self.context.continuation_data:
                # 重新加载最新的章节数据
                latest_chapters = self.data_manager.get_novel_chapters(novel_id)
                self.context.continuation_data["novel_data"]["chapters"] = latest_chapters
                print(f"上下文章节数据已更新，当前章节数: {len(latest_chapters)}")
                # 重建知识库，让下一章能看见最新章节
                from agents.novel_continuation_agent import NovelContinuationAgent
                kb_agent = NovelContinuationAgent()
                new_kb = kb_agent._build_knowledge_base(self.context.continuation_data["novel_data"])
                self.context.continuation_data["knowledge_base"] = new_kb
                print(f"知识库已重建，last_chapter_summary 更新为第{new_kb.get('last_chapter_summary', {}).get('chapter_number', 0)}章")

                # 为最新章节构建向量嵌入
                if self.embedding_service.is_available:
                    try:
                        from core.embedding_service import ChapterEmbeddingStore
                        novel_dir = os.path.join(self.data_manager.novels_dir, novel_id)
                        store = ChapterEmbeddingStore(novel_dir, self.embedding_service)
                        store.build_embedding_for_chapter(current_chapter_number, chapter_data)
                    except Exception as e:
                        print(f"[Embedding] 构建向量失败（不影响主线）: {e}")

                # ── 更新动态知识图谱 ──
                try:
                    self._update_knowledge_graph_after_chapter(novel_id, current_chapter_number, chapter_data)
                except Exception as e:
                    print(f"[KnowledgeGraph] 更新失败（不影响主线）: {e}")
            
            self.context.set_current_step("chapter_completed")
            self.save_context()  # 保存上下文以清除缓存
            
            # 检查字数并返回相应的状态
            if word_count < MIN_WORD_COUNT:
                print(f"⚠️ 警告：章节字数({word_count})少于推荐值({MIN_WORD_COUNT})")
                return {
                    "success": True,
                    "status": "warning",
                    "chapter_number": current_chapter_number,
                    "chapter_title": chapter_data["title"],
                    "word_count": word_count,
                    "message": f"章节保存成功，但字数({word_count})偏少，建议重新生成",
                    "warning": f"章节字数({word_count})少于推荐值({MIN_WORD_COUNT})"
                }
            else:
                return {
                    "success": True,
                    "status": "success",
                    "chapter_number": current_chapter_number,
                    "chapter_title": chapter_data["title"],
                    "word_count": word_count,
                    "message": "章节保存成功"
                }
        else:
            return {"error": "章节保存失败"}

    def _update_knowledge_graph_after_chapter(self, novel_id: str, chapter_number: int,
                                               chapter_data: Dict[str, Any]):
        """每章保存后更新动态知识图谱——角色/情节/伏笔/世界观滚动追踪"""
        # 1. 添加章节摘要
        self.dynamic_knowledge_manager.add_chapter_summary(novel_id, chapter_number, {
            "title": chapter_data.get("title", ""),
            "summary": chapter_data.get("summary", ""),
            "key_events": chapter_data.get("key_events", []),
            "character_development": chapter_data.get("character_development", {}),
            "foreshadowing": chapter_data.get("foreshadowing", []),
            "word_count": chapter_data.get("word_count", 0)
        })

        # 2. 更新情节时间线
        key_events = chapter_data.get("key_events", [])
        if key_events:
            plot_events = []
            for ev in key_events:
                if isinstance(ev, str):
                    plot_events.append({"type": "plot", "description": ev, "importance": "medium"})
                elif isinstance(ev, dict):
                    plot_events.append({
                        "type": ev.get("type", "plot"),
                        "description": ev.get("description", ev.get("event", str(ev))),
                        "importance": ev.get("importance", "medium"),
                        "characters": ev.get("characters", []),
                        "consequences": ev.get("consequences", [])
                    })
            if plot_events:
                self.dynamic_knowledge_manager.update_plot_timeline(novel_id, chapter_number, plot_events)

        # 3. 更新人物发展
        char_dev = chapter_data.get("character_development", {})
        if isinstance(char_dev, dict):
            for char_name, changes in char_dev.items():
                if isinstance(changes, str):
                    self.dynamic_knowledge_manager.update_character_evolution(
                        novel_id, chapter_number, char_name,
                        {"type": "development", "description": changes}
                    )
                elif isinstance(changes, dict):
                    self.dynamic_knowledge_manager.update_character_evolution(
                        novel_id, chapter_number, char_name, changes
                    )
        elif isinstance(char_dev, str) and char_dev:
            self.dynamic_knowledge_manager.update_character_evolution(
                novel_id, chapter_number, "主角",
                {"type": "development", "description": char_dev}
            )

        # 4. 更新伏笔台账
        foreshadowing = chapter_data.get("foreshadowing", [])
        if isinstance(foreshadowing, list):
            for fs in foreshadowing:
                if isinstance(fs, str):
                    self.dynamic_knowledge_manager.update_foreshadowing_tracking(
                        novel_id, chapter_number,
                        {"type": "general", "content": fs, "importance": "medium"}
                    )
                elif isinstance(fs, dict):
                    self.dynamic_knowledge_manager.update_foreshadowing_tracking(
                        novel_id, chapter_number, fs
                    )
        elif isinstance(foreshadowing, str) and foreshadowing:
            self.dynamic_knowledge_manager.update_foreshadowing_tracking(
                novel_id, chapter_number,
                {"type": "general", "content": foreshadowing, "importance": "medium"}
            )

        # 5. 更新世界观变动（从关键事件中检测世界观相关变化）
        world_changes = []
        if key_events:
            world_keywords = ["规则", "设定", "境界", "力量", "法则", "天道", "体系", "世界", "领域", "秩序"]
            for ev in key_events:
                text = ev if isinstance(ev, str) else ev.get("description", ev.get("event", ""))
                if any(kw in str(text) for kw in world_keywords):
                    world_changes.append({
                        "type": "world_revelation",
                        "description": str(text)[:200],
                        "scope": "local"
                    })
        if world_changes:
            self.dynamic_knowledge_manager.update_world_changes(novel_id, chapter_number, world_changes)

        # 6. 整合动态知识到知识图谱
        try:
            dynamic_summary = self.dynamic_knowledge_manager.get_dynamic_summary(novel_id)
            existing_kg = self.data_manager.get_knowledge_graph_by_novel_id(novel_id)
            if existing_kg:
                kg_id = existing_kg.get("kg_id", "")
                kg_update = {
                    "dynamic_summary": dynamic_summary,
                    "chapter_count": chapter_number,
                    "last_chapter_title": chapter_data.get("title", ""),
                    "last_updated_chapter": chapter_number,
                    "updated_at": datetime.now().isoformat()
                }
                self.data_manager.update_knowledge_graph(kg_id, kg_update)
                print(f"[KnowledgeGraph] 知识图谱已更新至第 {chapter_number} 章 ({dynamic_summary})")
            else:
                # 首次：创建知识图谱
                characters = self.data_manager.load_novel_data(novel_id, "characters") or {}
                storyline = self.data_manager.load_novel_data(novel_id, "storyline") or {}
                kg_id = self.data_manager.create_knowledge_graph(novel_id, characters, storyline)
                print(f"[KnowledgeGraph] 首次创建知识图谱: {kg_id}")
        except Exception as e:
            print(f"[KnowledgeGraph] 合并动态知识到图谱失败: {e}")

        # 7. 为动态知识构建向量（语义检索用）
        if self.embedding_service.is_available:
            try:
                dk = self.dynamic_knowledge_manager.get_dynamic_knowledge(novel_id)
                if dk:
                    from core.embedding_service import DynamicKnowledgeEmbeddingStore
                    novel_dir = os.path.join(self.data_manager.novels_dir, novel_id)
                    dk_store = DynamicKnowledgeEmbeddingStore(novel_dir, self.embedding_service)
                    dk_store.build_for_chapter(chapter_number, dk)
            except Exception as e:
                print(f"[DynEmbedStore] 构建失败（不影响主线）: {e}")

    def _inject_dynamic_knowledge(self, kb: Dict[str, Any], novel_id: str,
                                   query_text: str = None) -> Dict[str, Any]:
        """将动态知识注入 knowledge_base，优先使用语义检索

        Args:
            kb: 当前的 knowledge_base
            novel_id: 小说 ID
            query_text: 语义检索查询文本（None 则回退到全量截断模式）
        """
        try:
            dk = self.dynamic_knowledge_manager.get_dynamic_knowledge(novel_id)
            if not dk:
                return kb

            # 始终保留全量动态知识作为兜底
            kb["dynamic_knowledge"] = dk

            # 尝试语义检索
            if self.embedding_service.is_available and query_text:
                try:
                    from core.embedding_service import DynamicKnowledgeEmbeddingStore
                    novel_dir = os.path.join(self.data_manager.novels_dir, novel_id)
                    dk_store = DynamicKnowledgeEmbeddingStore(novel_dir, self.embedding_service)
                    semantic = dk_store.search(query_text, top_k=15)
                    if semantic:
                        kb["dynamic_knowledge_semantic"] = semantic
                        print(f"[DynamicKB] 语义检索命中 {sum(len(v) for v in semantic.values())} 条动态知识")
                except Exception as e:
                    print(f"[DynamicKB] 语义检索失败，回退全量模式: {e}")
        except Exception as e:
            print(f"[DynamicKB] 注入动态知识失败: {e}")
        return kb

    def _get_previous_chapter_scene_continuity(self, novel_id: str) -> Optional[Dict[str, Any]]:
        """获取上一章的场景连续性状态，用于跨章场景追踪

        如果上一章的场景尚未结束（scene_span_chapters > 1 且 scene_phase != "收尾"），
        返回上一章的 scene_continuity 信息，供剧情生成器作为约束。
        """
        try:
            chapters = self.data_manager.get_novel_chapters(novel_id)
            if not chapters or len(chapters) == 0:
                return None

            last_chapter = chapters[-1]
            scene_continuity = last_chapter.get("scene_continuity")
            if not scene_continuity or not isinstance(scene_continuity, dict):
                return None

            span = scene_continuity.get("scene_span_chapters", 1)
            phase = scene_continuity.get("scene_phase", "开始")

            # 如果跨章场景未结束，返回当前状态
            if span > 1 and phase not in ("收尾", "高潮"):
                return {
                    "continues_from_previous": True,
                    "scene_span_chapters": span,
                    "current_phase": phase,
                    "chapters_remaining": span - 1,  # 粗略估计
                    "time": last_chapter.get("scene_setting", {}).get("time", ""),
                    "location": last_chapter.get("scene_setting", {}).get("location", ""),
                    "atmosphere": last_chapter.get("scene_setting", {}).get("atmosphere", ""),
                }

            return None
        except Exception as e:
            print(f"[SceneContinuity] 获取上一章场景状态失败: {e}")
            return None

    def _extract_clean_content(self, raw_content: str) -> str:
        """从可能包含markdown格式的内容中提取纯文本"""
        if not raw_content:
            return ""
        
        # 如果是markdown格式的JSON，直接提取```json到```之间的内容
        if raw_content.startswith("```json"):
            try:
                import json
                # 找到```json和```的位置
                start = raw_content.find("```json") + 7  # 跳过```json
                end = raw_content.find("```", start)
                if end != -1:
                    json_str = raw_content[start:end].strip()
                    parsed = json.loads(json_str)
                    return parsed.get("content", raw_content)
            except:
                pass
        
        # 如果内容包含转义的换行符，转换为实际换行符
        if "\\n" in raw_content:
            raw_content = raw_content.replace("\\n", "\n")
        
        return raw_content
    
    
    def clear_continuation_cache(self, novel_id: str = None) -> Dict[str, Any]:
        """清除续写缓存数据"""
        print("开始清除续写缓存数据...")
        
        # 如果提供了novel_id，尝试加载现有上下文
        if novel_id:
            # 尝试加载现有上下文，如果失败就返回成功（表示没有缓存需要清除）
            if not self.load_context_by_novel_id(novel_id):
                print(f"没有找到小说 {novel_id} 的上下文，无需清除缓存")
                return {"status": "success", "message": "没有需要清除的缓存数据"}
        
        if not self.context:
            return {"status": "success", "message": "没有需要清除的缓存数据"}
        
        # 清除所有续写相关的缓存数据
        cache_keys_to_clear = [
            "next_chapter_content",
            "next_chapter_storyline", 
            "continuation_storyline_quality_assessment",
            "continuation_story_quality_assessment"
        ]
        
        for key in cache_keys_to_clear:
            if key in self.context._cache:
                del self.context._cache[key]
                print(f"已清除缓存: {key}")
        
        # 如果是续写模式，重置当前步骤到故事线生成
        if self.context.is_continuation:
            self.context.set_current_step("storyline_generation")
            print("已重置续写步骤到故事线生成")
        
        # 保存上下文
        self.save_context()
        
        return {
            "status": "success",
            "message": "续写缓存数据已清除，准备开始新的续写流程"
        }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流程状态"""
        if not self.context:
            return {
                "novel_id": None,
                "current_step": "not_started",
                "workflow_state": {}
            }
        
        return {
            "novel_id": self.context.novel_id,
            "current_step": self.context.current_step,
            "workflow_state": self.context.get_summary()
        }
    
    def get_continuation_status(self, novel_id: str = None) -> Dict[str, Any]:
        """获取续写状态"""
        # 如果提供了novel_id，确保上下文正确设置
        if novel_id and (not self.context or self.context.novel_id != novel_id):
            # 尝试加载现有上下文
            if not self.load_context_by_novel_id(novel_id):
                return {"error": f"无法加载小说 {novel_id} 的上下文，请先开始续写流程"}
        
        if not self.context or not self.context.is_continuation:
            return {
                "novel_id": novel_id,
                "is_continuation": False,
                "current_step": "not_started",
                "continuation_state": {}
            }
        
        novel_data = self.context.continuation_data.get("novel_data", {})
        novel_info = novel_data.get("novel_info", {})
        chapters = novel_data.get("chapters", [])
        
        # 根据实际数据确定当前步骤
        current_step = self.context.current_step
        
        # 检查是否有续写故事线数据
        next_chapter_storyline = self.context.get_cached_result("next_chapter_storyline")
        # 检查是否有续写章节内容
        next_chapter_content = self.context.get_cached_result("next_chapter_content")
        
        # 检查是否有已保存的续写章节
        saved_chapters = self.data_manager.get_novel_chapters(novel_id)
        current_chapter_number = len(chapters) + 1
        
        # 调试信息
        print(f"状态检测调试信息:")
        print(f"  - novel_data.chapters 数量: {len(chapters)}")
        print(f"  - saved_chapters 数量: {len(saved_chapters)}")
        print(f"  - next_chapter_content 存在: {bool(next_chapter_content)}")
        print(f"  - next_chapter_storyline 存在: {bool(next_chapter_storyline)}")
        
        # 根据实际数据重新确定当前步骤
        # 优先级：上下文当前步骤（如果是续写模式）> 已保存章节 > 缓存内容 > 默认状态
        
        # 如果是续写模式且上下文中有明确的步骤，优先信任上下文
        if self.context.is_continuation and current_step and current_step != "not_started":
            print(f"  - 续写模式：信任上下文中的当前步骤: {current_step}")
            
            # 对于续写模式，尝试从数据文件恢复缓存数据
            if current_step != "storyline_generation":
                # 尝试恢复故事线数据
                if not next_chapter_storyline:
                    saved_storyline = self.data_manager.load_novel_data(self.context.novel_id, "next_chapter_storyline")
                    if saved_storyline:
                        self.context.cache_result("next_chapter_storyline", saved_storyline)
                        next_chapter_storyline = saved_storyline
                        print(f"  - 从文件恢复故事线数据")
                
                # 尝试恢复章节内容数据
                if not next_chapter_content:
                    saved_content = self.data_manager.load_novel_data(self.context.novel_id, "next_chapter_content")
                    if saved_content:
                        self.context.cache_result("next_chapter_content", saved_content)
                        next_chapter_content = saved_content
                        print(f"  - 从文件恢复章节内容数据")
                        
                # 尝试恢复质量评估数据
                storyline_quality = self.data_manager.load_novel_data(self.context.novel_id, "continuation_storyline_quality_assessment")
                if storyline_quality:
                    self.context.cache_quality_assessment("storyline", storyline_quality)
                    print(f"  - 从文件恢复故事线质量评估数据")
                    
                chapter_quality = self.data_manager.load_novel_data(self.context.novel_id, "continuation_chapter_quality_assessment")
                if chapter_quality:
                    self.context.cache_quality_assessment("story", chapter_quality)
                    print(f"  - 从文件恢复章节质量评估数据")
        else:
            # 非续写模式或没有明确步骤时，使用原来的推断逻辑
            print(f"  - 使用数据推断逻辑确定步骤")
            
            # 检查是否有续写章节文件（续写章节会保存为独立的文件）
            continuation_chapter_files = [ch for ch in saved_chapters if ch.get("chapter_number", 0) > 1]
            
            if continuation_chapter_files:
                # 有续写章节文件，说明续写已完成
                current_step = "chapter_completed"
                print(f"  - 检测到续写章节文件 {[ch.get('chapter_number') for ch in continuation_chapter_files]}，设置状态为: {current_step}")
            elif next_chapter_content:
                # 有章节内容，说明章节写作已完成
                current_step = "chapter_completed"
                print(f"  - 检测到 next_chapter_content，设置状态为: {current_step}")
            elif next_chapter_storyline:
                # 有故事线但没有章节内容，说明故事线生成已完成，下一步是章节写作
                current_step = "chapter_writing"
                print(f"  - 检测到 next_chapter_storyline，设置状态为: {current_step}")
            else:
                # 没有故事线数据，说明需要生成故事线
                current_step = "storyline_generation"
                print(f"  - 没有检测到相关数据，设置状态为: {current_step}")
        
        # 更新上下文中的当前步骤（只有在步骤确实改变时才更新）
        if self.context.current_step != current_step:
            print(f"  - 更新步骤: {self.context.current_step} → {current_step}")
            self.context.set_current_step(current_step)
            self.save_context()  # 保存上下文以持久化状态变更
        else:
            print(f"  - 步骤未改变，保持: {current_step}")
        
        # 构建续写状态数据
        continuation_state = {
            "novel_data": novel_data,
            "knowledge_base": self.context.continuation_data.get("knowledge_base", {}),
            "user_requirements": self.context.user_requirements
        }
        
        # 添加续写故事线数据（如果存在）
        if next_chapter_storyline:
            continuation_state["next_chapter_storyline"] = next_chapter_storyline
        
        # 添加续写章节内容数据（如果存在）
        if next_chapter_content:
            continuation_state["next_chapter_content"] = next_chapter_content
        
        return {
            "novel_id": self.context.novel_id,
            "is_continuation": True,
            "current_step": current_step,
            "novel_title": novel_info.get("title", "未知标题"),
            "chapter_count": len(saved_chapters),  # 返回实际保存的章节数量
            "user_requirements": self.context.user_requirements,
            "continuation_state": continuation_state
        }
    
    def continue_workflow(self) -> Dict[str, Any]:
        """继续工作流程"""
        if not self.context:
            return {"error": "没有活跃的工作流程"}
        
        current_step = self.context.current_step
        
        if current_step == "tag_selection":
            return self.select_tags()
        elif current_step == "character_creation":
            return self.create_characters()
        elif current_step == "storyline_generation":
            if self.context.is_continuation:
                return self.generate_continuation_storyline()
            else:
                return self.generate_storyline()
        elif current_step == "knowledge_graph_creation":
            return self.create_knowledge_graph()
        elif current_step == "chapter_writing":
            if self.context.is_continuation:
                return self.write_continuation_chapter()
            else:
                return self.write_first_chapter()
        else:
            return {"error": f"未知的工作流程步骤: {current_step}"}
    
    def save_context(self, file_path: str = None) -> bool:
        """保存工作流程上下文"""
        if not self.context:
            return False
        
        if not file_path:
            # 将workflow_context文件保存到小说目录内
            novel_dir = os.path.join(self.data_manager.novels_dir, self.context.novel_id)
            os.makedirs(novel_dir, exist_ok=True)
            file_path = os.path.join(novel_dir, "workflow_context.json")
        
        return self.context.save_to_file(file_path)
    
    def load_context(self, file_path: str) -> bool:
        """加载工作流程上下文"""
        context = WorkflowContext.load_from_file(file_path)
        if context:
            self.context = context
            return True
        return False
    
    def load_context_by_novel_id(self, novel_id: str) -> bool:
        """根据小说ID加载上下文"""
        # 从小说目录内加载workflow_context文件
        novel_dir = os.path.join(self.data_manager.novels_dir, novel_id)
        file_path = os.path.join(novel_dir, "workflow_context.json")
        return self.load_context(file_path)
    
    def validate_and_repair_context(self) -> Dict[str, Any]:
        """验证并修复上下文"""
        if not self.context:
            return {
                "is_valid": False,
                "issues": ["缺少工作流程上下文"],
                "warnings": [],
                "repair_suggestions": ["重新开始工作流程"]
            }
        
        validation_result = self.context.validate_context()
        
        # 如果上下文无效，尝试修复
        if not validation_result["is_valid"]:
            repair_suggestions = []
            
            for issue in validation_result["issues"]:
                if "缺少小说ID" in issue:
                    repair_suggestions.append("重新创建小说项目")
                elif "缺少标签数据" in issue:
                    repair_suggestions.append("重新执行标签选择步骤")
                elif "缺少角色数据" in issue:
                    repair_suggestions.append("重新执行角色创建步骤")
                elif "缺少故事线数据" in issue:
                    repair_suggestions.append("重新执行故事线生成步骤")
                elif "缺少续写数据" in issue:
                    repair_suggestions.append("重新开始续写流程")
            
            validation_result["repair_suggestions"] = repair_suggestions
        
        return validation_result
    
    def auto_repair_context(self) -> bool:
        """自动修复上下文"""
        validation_result = self.validate_and_repair_context()
        
        if validation_result["is_valid"]:
            return True
        
        # 尝试自动修复
        if "缺少小说ID" in validation_result["issues"]:
            return False  # 无法自动修复
        
        # 重置到合适的步骤
        if "缺少标签数据" in validation_result["issues"]:
            return self.context.reset_to_step("tag_selection")
        elif "缺少角色数据" in validation_result["issues"]:
            return self.context.reset_to_step("character_creation")
        elif "缺少故事线数据" in validation_result["issues"]:
            return self.context.reset_to_step("storyline_generation")
        
        return False
    
    def start_quick_continuation_fixed(self, chapter_count: int = 1, requirements: str = "") -> bool:
        """启动指定章节数的快速续写"""
        print(f"启动快速续写（指定章节数）: {chapter_count}章")
        print(f"续写需求: {requirements}")
        
        try:
            # 更新用户需求（如果有提供）
            if requirements:
                self.context.user_requirements = requirements
                self.context.save_context()
            
            # 启动续写流程
            print(f"开始启动续写流程，小说ID: {self.context.novel_id}")
            result = self.start_novel_continuation(self.context.novel_id, requirements)
            print(f"续写流程启动结果: {result}")
            
            if not result.get("success", False):
                error_msg = result.get('error', '未知错误')
                print(f"启动续写流程失败: {error_msg}")
                return False
            
            # 开始自动执行续写流程
            return self._execute_quick_continuation_loop(chapter_count, mode='fixed')
            
        except Exception as e:
            print(f"快速续写启动失败: {e}")
            return False
    
    def start_quick_continuation_continuous(self, continuous_mode: str = 'auto', requirements: str = "") -> bool:
        """启动持续写作模式的快速续写"""
        print(f"启动快速续写（持续模式）: {continuous_mode}")
        print(f"续写需求: {requirements}")
        
        try:
            # 更新用户需求（如果有提供）
            if requirements:
                self.context.user_requirements = requirements
                self.context.save_context()
            
            # 启动续写流程
            result = self.start_novel_continuation(self.context.novel_id, requirements)
            if not result.get("success", False):
                print(f"启动续写流程失败: {result.get('error', '未知错误')}")
                return False
            
            # 开始自动执行续写流程
            return self._execute_quick_continuation_loop(max_chapters=50, mode='continuous', continuous_mode=continuous_mode)
            
        except Exception as e:
            print(f"快速续写启动失败: {e}")
            return False
    
    def _execute_quick_continuation_loop(self, max_chapters: int = 1, mode: str = 'fixed', continuous_mode: str = 'auto') -> bool:
        """执行快速续写循环"""
        print(f"开始执行快速续写循环: max_chapters={max_chapters}, mode={mode}")
        
        chapters_completed = 0
        
        try:
            while chapters_completed < max_chapters:
                print(f"\n=== 开始续写第 {chapters_completed + 1} 章 ===")
                
                # 步骤1: 生成续写故事线
                print("步骤1: 生成续写故事线...")
                storyline_result = self.generate_continuation_storyline()
                if not storyline_result.get("success", False):
                    print(f"故事线生成失败: {storyline_result.get('error', '未知错误')}")
                    break
                
                # 步骤2: 改进故事线（可选）
                print("步骤2: 改进故事线...")
                improve_result = self.improve_continuation_storyline()
                if not improve_result.get("success", False):
                    print(f"故事线改进失败: {improve_result.get('error', '未知错误')}")
                    # 继续执行，改进失败不是致命错误
                
                # 步骤3: 评估故事线质量
                print("步骤3: 评估故事线质量...")
                quality_result = self.assess_continuation_quality(content_type="storyline")
                if not quality_result.get("success", False):
                    print(f"故事线质量评估失败: {quality_result.get('error', '未知错误')}")
                    # 继续执行，质量评估失败不是致命错误
                
                # 步骤4: 写作章节
                print("步骤4: 写作章节...")
                chapter_result = self.write_continuation_chapter()
                if not chapter_result.get("success", False):
                    print(f"章节写作失败: {chapter_result.get('error', '未知错误')}")
                    break
                
                # 步骤5: 保存章节
                print("步骤5: 保存章节...")
                save_result = self.save_continuation_chapter()
                if not save_result.get("success", False):
                    print(f"章节保存失败: {save_result.get('error', '未知错误')}")
                    break
                
                chapters_completed += 1
                print(f"第 {chapters_completed} 章完成！")
                
                # 如果是持续模式且为手动模式，需要用户确认是否继续
                if mode == 'continuous' and continuous_mode == 'manual':
                    print("手动模式：请在前端界面确认是否继续下一章...")
                    # 这里可以设置一个标志，让前端知道需要用户确认
                    break
                
                # 如果是自动模式，检查是否应该停止
                if mode == 'continuous' and continuous_mode == 'auto':
                    # 检查故事是否达到自然结束点
                    if self._should_stop_continuous_writing():
                        print("检测到故事自然结束点，停止续写")
                        break
            
            print(f"\n快速续写完成！总共完成 {chapters_completed} 章")
            return True
            
        except Exception as e:
            print(f"快速续写循环执行失败: {e}")
            return False
    
    def _should_stop_continuous_writing(self) -> bool:
        """判断是否应该停止持续写作"""
        try:
            # 获取最新的故事线内容
            storyline_data = self.context.continuation_data.get("next_chapter_storyline", {})
            storyline_content = storyline_data.get("content", "")
            
            # 简单的结束点检测逻辑
            end_indicators = [
                "完结", "结束", "大结局", "尾声", "后记",
                "故事结束", "全文完", "全剧终"
            ]
            
            for indicator in end_indicators:
                if indicator in storyline_content:
                    return True
            
            # 检查章节数量是否过多（防止无限循环）
            current_chapters = len(self.context.novel_data.get("chapters", []))
            if current_chapters > 100:  # 最多100章
                return True
            
            return False
            
        except Exception as e:
            print(f"检查是否停止持续写作时出错: {e}")
            return False
