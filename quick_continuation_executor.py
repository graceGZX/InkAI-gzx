"""
快速续写后台执行器
负责完全自动化的续写流程执行，支持进度跟踪和独占模式
"""
import os
import sys
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inkai_workflow_optimized import InkAIWorkflowOptimized
from data_manager import DataManager
import config


@dataclass
class QuickContinuationProgress:
    """快速续写进度信息"""
    novel_id: str
    novel_title: str
    mode: str  # 'fixed' 或 'continuous'
    total_chapters: int
    completed_chapters: int
    current_chapter: int
    current_step: str
    status: str  # 'running', 'completed', 'failed', 'paused'
    start_time: str
    last_update: str
    error_message: str = ""
    chapter_details: List[Dict[str, Any]] = None
    word_count_retry_count: int = 0  # 字数验证重试计数
    
    def __post_init__(self):
        if self.chapter_details is None:
            self.chapter_details = []


class QuickContinuationExecutor:
    """快速续写后台执行器"""
    
    def __init__(self):
        self.workflow = InkAIWorkflowOptimized()
        self.data_manager = DataManager()
        self.running_tasks: Dict[str, QuickContinuationProgress] = {}
        self.lock = threading.Lock()
        
        # 确保状态目录存在
        self.status_dir = os.path.join(config.NOVELS_DIR, "quick_continuation_status")
        os.makedirs(self.status_dir, exist_ok=True)
    
    def start_quick_continuation(self, novel_id: str, mode: str, 
                                chapter_count: int = 1, requirements: str = "",
                                continuous_mode: str = 'auto') -> Dict[str, Any]:
        """启动快速续写任务"""
        try:
            with self.lock:
                # 检查是否已有运行中的任务
                if novel_id in self.running_tasks:
                    return {
                        "success": False,
                        "error": "该小说已有快速续写任务在运行中"
                    }
                
                # 获取小说信息
                novel_data = self.data_manager.load_novel_data(novel_id, "metadata")
                if not novel_data:
                    return {
                        "success": False,
                        "error": f"未找到小说 {novel_id}"
                    }
                
                # 创建进度对象
                progress = QuickContinuationProgress(
                    novel_id=novel_id,
                    novel_title=novel_data.get("title", "未知标题"),
                    mode=mode,
                    total_chapters=chapter_count if mode == 'fixed' else 999,
                    completed_chapters=0,
                    current_chapter=0,
                    current_step="initializing",
                    status="running",
                    start_time=datetime.now().isoformat(),
                    last_update=datetime.now().isoformat()
                )
                
                # 保存进度到文件
                self._save_progress(progress)
                
                # 启动后台线程
                thread = threading.Thread(
                    target=self._execute_continuation_task,
                    args=(progress, requirements, continuous_mode),
                    daemon=True
                )
                thread.start()
                
                # 记录运行中的任务
                self.running_tasks[novel_id] = progress
                
                return {
                    "success": True,
                    "message": "快速续写任务已启动",
                    "task_id": novel_id,
                    "progress": asdict(progress)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"启动快速续写失败: {str(e)}"
            }
    
    def _execute_continuation_task(self, progress: QuickContinuationProgress, 
                                  requirements: str, continuous_mode: str):
        """执行续写任务的后台线程"""
        try:
            # 更新状态
            progress.current_step = "starting"
            progress.status = "running"
            self._update_progress(progress)
            
            # 启动续写流程
            result = self.workflow.start_novel_continuation(progress.novel_id, requirements)
            if not result.get("success", False):
                progress.status = "failed"
                progress.error_message = result.get('error', '启动续写流程失败')
                self._update_progress(progress)
                return
            
            # 开始自动执行续写循环
            if progress.mode == 'fixed':
                self._execute_fixed_mode(progress, requirements)
            else:
                self._execute_continuous_mode(progress, requirements, continuous_mode)
                
        except Exception as e:
            progress.status = "failed"
            progress.error_message = f"执行过程中发生错误: {str(e)}"
            self._update_progress(progress)
        finally:
            # 清理运行中的任务记录
            with self.lock:
                if progress.novel_id in self.running_tasks:
                    del self.running_tasks[progress.novel_id]
    
    def _execute_fixed_mode(self, progress: QuickContinuationProgress, requirements: str):
        """执行指定章节数模式"""
        # 获取当前小说的章节数
        current_chapter_count = self._get_current_chapter_count(progress.novel_id)
        chapters_completed = 0
        
        while chapters_completed < progress.total_chapters:
            # 计算下一章的章节号（从当前章节数+1开始）
            progress.current_chapter = current_chapter_count + chapters_completed + 1
            progress.current_step = f"writing_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            # 执行单章续写流程
            success = self._execute_single_chapter_continuation(progress, requirements)
            
            if success:
                chapters_completed += 1
                progress.completed_chapters = chapters_completed
                
                # 记录章节详情
                chapter_detail = {
                    "chapter_number": progress.current_chapter,
                    "completed_at": datetime.now().isoformat(),
                    "status": "completed"
                }
                progress.chapter_details.append(chapter_detail)
                
                # 更新当前章节数，为下一章做准备
                current_chapter_count = self._get_current_chapter_count(progress.novel_id)
                
                self._update_progress(progress)
            else:
                progress.status = "failed"
                # 保留 _execute_single_chapter_continuation 中设置的具体错误信息
                if not progress.error_message:
                    progress.error_message = f"第{progress.current_chapter}章写作失败"
                self._update_progress(progress)
                return
        
        # 所有章节完成
        progress.status = "completed"
        progress.current_step = "completed"
        self._update_progress(progress)
    
    def _execute_continuous_mode(self, progress: QuickContinuationProgress, 
                                requirements: str, continuous_mode: str):
        """执行持续写作模式"""
        # 获取当前小说的章节数
        current_chapter_count = self._get_current_chapter_count(progress.novel_id)
        
        # 修复：重新计算已完成章节数，确保与实际章节数同步
        # 如果进度状态中的已完成章节数小于实际章节数，说明有章节已经完成但没有正确记录
        if progress.completed_chapters < current_chapter_count:
            print(f"检测到状态不同步：进度记录{progress.completed_chapters}章，实际已有{current_chapter_count}章")
            print("正在同步状态...")
            
            # 重新计算已完成章节数
            progress.completed_chapters = current_chapter_count
            
            # 重新构建章节详情列表
            progress.chapter_details = []
            for i in range(1, current_chapter_count + 1):
                chapter_detail = {
                    "chapter_number": i,
                    "completed_at": datetime.now().isoformat(),
                    "status": "completed"
                }
                progress.chapter_details.append(chapter_detail)
            
            print(f"状态同步完成：已完成{progress.completed_chapters}章")
        
        # 根据模式设置最大章节数限制
        if continuous_mode == 'infinite':
            max_chapters = float('inf')  # 无限续写模式
            print("启动无限续写模式，将持续写作直到故事自然结束")
        else:
            max_chapters = 50  # 普通持续写作模式的最大章节数限制
        
        # 修复：使用实际章节数作为起始点，而不是进度记录
        start_chapter_count = current_chapter_count
        
        while progress.completed_chapters < max_chapters:
            # 重新获取当前章节数，确保章节号计算正确
            current_chapter_count = self._get_current_chapter_count(progress.novel_id)
            # 计算下一章的章节号（从当前章节数+1开始）
            progress.current_chapter = current_chapter_count + 1
            progress.current_step = f"writing_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            print(f"开始写作第{progress.current_chapter}章...")
            
            # 执行单章续写流程
            success = self._execute_single_chapter_continuation(progress, requirements)
            
            if success:
                # 重新获取章节数，确认章节已保存
                new_chapter_count = self._get_current_chapter_count(progress.novel_id)
                if new_chapter_count > current_chapter_count:
                    # 章节确实已保存，更新进度
                    progress.completed_chapters = new_chapter_count
                    
                    # 记录章节详情
                    chapter_detail = {
                        "chapter_number": progress.current_chapter,
                        "completed_at": datetime.now().isoformat(),
                        "status": "completed"
                    }
                    progress.chapter_details.append(chapter_detail)
                    
                    print(f"第{progress.current_chapter}章写作完成，当前总章节数：{new_chapter_count}")
                else:
                    print(f"警告：第{progress.current_chapter}章写作完成但章节数未增加")
                
                self._update_progress(progress)
                
                # 检查是否应该停止
                if continuous_mode in ['auto', 'infinite']:
                    if self._should_stop_continuous_writing(progress):
                        progress.status = "completed"
                        progress.current_step = "completed"
                        if continuous_mode == 'infinite':
                            progress.error_message = "无限续写模式：检测到故事自然结束点"
                        else:
                            progress.error_message = "检测到故事自然结束点"
                        self._update_progress(progress)
                        return
                elif continuous_mode == 'manual':
                    # 手动模式需要用户确认，这里暂停
                    progress.status = "paused"
                    progress.current_step = "waiting_for_user_confirmation"
                    self._update_progress(progress)
                    return
            else:
                # 章节写作失败，记录失败信息
                print(f"第{progress.current_chapter}章写作失败: {progress.error_message}")
                chapter_detail = {
                    "chapter_number": progress.current_chapter,
                    "completed_at": datetime.now().isoformat(),
                    "status": "failed",
                    "error": progress.error_message
                }
                progress.chapter_details.append(chapter_detail)
                
                # 修复：失败时增加已完成章节数，避免无限循环
                progress.completed_chapters += 1
                
                self._update_progress(progress)
                
                # 检查是否应该停止
                if continuous_mode in ['auto', 'infinite']:
                    if self._should_stop_continuous_writing(progress):
                        progress.status = "completed"
                        progress.current_step = "completed"
                        if continuous_mode == 'infinite':
                            progress.error_message = "无限续写模式：检测到故事自然结束点"
                        else:
                            progress.error_message = "检测到故事自然结束点"
                        self._update_progress(progress)
                        return
                elif continuous_mode == 'manual':
                    # 手动模式需要用户确认，这里暂停
                    progress.status = "paused"
                    progress.current_step = "waiting_for_user_confirmation"
                    self._update_progress(progress)
                    return
        
        # 达到最大章节数（仅对非无限模式）
        if continuous_mode != 'infinite':
            progress.status = "completed"
            progress.current_step = "completed"
            progress.error_message = "已达到最大章节数限制"
            self._update_progress(progress)
    
    def _execute_single_chapter_continuation(self, progress: QuickContinuationProgress, 
                                           requirements: str) -> bool:
        """执行单章续写流程（包含质量评估但不包含改进）"""
        try:
            # 重置字数验证重试计数
            progress.word_count_retry_count = 0
            
            # 步骤1: 生成续写故事线
            progress.current_step = f"generating_storyline_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            storyline_result = self.workflow.generate_continuation_storyline(progress.novel_id)
            if not storyline_result.get("success", False):
                print(f"故事线生成失败: {storyline_result.get('error', '未知错误')}")
                progress.error_message = f"故事线生成失败: {storyline_result.get('error', '未知错误')}"
                return False
            
            # 步骤2: 评估故事线质量
            progress.current_step = f"assessing_storyline_quality_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            storyline_quality_result = self.workflow.assess_continuation_quality(progress.novel_id, "storyline")
            if not storyline_quality_result.get("success", False):
                print(f"故事线质量评估失败: {storyline_quality_result.get('error', '未知错误')}")
                # 继续执行，质量评估失败不是致命错误
            else:
                # 检查故事线质量分数，低于50分则进行优化
                storyline_score = storyline_quality_result.get("overall_score", 100)
                if storyline_score < 50:
                    print(f"故事线质量分数较低({storyline_score}分)，开始优化...")
                    progress.current_step = f"improving_storyline_chapter_{progress.current_chapter}"
                    self._update_progress(progress)
                    
                    improve_result = self.workflow.improve_continuation_storyline(progress.novel_id)
                    if not improve_result.get("success", False):
                        print(f"故事线优化失败: {improve_result.get('error', '未知错误')}")
                        # 继续执行，优化失败不是致命错误
                    else:
                        print(f"故事线优化完成")
                else:
                    print(f"故事线质量分数({storyline_score}分)符合要求，跳过优化")
            
            # 步骤3: 写作章节
            progress.current_step = f"writing_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            chapter_result = self.workflow.write_continuation_chapter(progress.novel_id)
            if not chapter_result.get("success", False):
                print(f"章节写作失败: {chapter_result.get('error', '未知错误')}")
                progress.error_message = f"章节写作失败: {chapter_result.get('error', '未知错误')}"
                return False
            
            # 步骤4: 评估章节质量
            progress.current_step = f"assessing_chapter_quality_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            chapter_quality_result = self.workflow.assess_continuation_quality(progress.novel_id, "story")
            if not chapter_quality_result.get("success", False):
                print(f"章节质量评估失败: {chapter_quality_result.get('error', '未知错误')}")
                # 继续执行，质量评估失败不是致命错误
            else:
                # 检查章节质量分数，低于50分则进行优化
                chapter_score = chapter_quality_result.get("overall_score", 100)
                if chapter_score < 50:
                    print(f"章节质量分数较低({chapter_score}分)，但章节优化功能暂未实现，跳过优化")
                    # TODO: 后续可以添加章节优化功能
                    # progress.current_step = f"improving_chapter_chapter_{progress.current_chapter}"
                    # self._update_progress(progress)
                    # improve_result = self.workflow.improve_continuation_chapter(progress.novel_id)
                else:
                    print(f"章节质量分数({chapter_score}分)符合要求，跳过优化")
            
            # 步骤5: 保存章节
            progress.current_step = f"saving_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            save_result = self.workflow.save_continuation_chapter(progress.novel_id)
            if not save_result.get("success", False):
                print(f"章节保存失败: {save_result.get('error', '未知错误')}")
                progress.error_message = f"章节保存失败: {save_result.get('error', '未知错误')}"
                return False
            
            # 验证章节是否真正保存成功
            # 带重试的验证，避免文件系统延迟导致的误判
            import time
            max_verify_retries = 5
            expected_chapter_count = progress.current_chapter
            new_chapter_count = 0
            for retry in range(max_verify_retries):
                time.sleep(0.3)
                new_chapter_count = self._get_current_chapter_count(progress.novel_id)
                if new_chapter_count >= expected_chapter_count:
                    break
                print(f"章节保存验证重试 {retry + 1}/{max_verify_retries}：期望{expected_chapter_count}，实际{new_chapter_count}")

            if new_chapter_count < expected_chapter_count:
                progress.error_message = f"章节保存验证失败：期望章节数{expected_chapter_count}，实际章节数{new_chapter_count}"
                self._update_progress(progress)
                print(f"第{progress.current_chapter}章保存验证失败")
                return False
            
            # 步骤6: 验证章节字数，少于2.5k字则重新生成
            if not self._validate_chapter_word_count(progress):
                # 字数不足，_validate_chapter_word_count 方法会处理重新生成
                return False
            
            # 章节保存成功，更新进度状态为章节完成
            progress.current_step = f"chapter_completed_{progress.current_chapter}"
            self._update_progress(progress)
            print(f"第{progress.current_chapter}章续写完成并保存成功，验证通过")
            
            return True
            
        except Exception as e:
            print(f"单章续写执行失败: {e}")
            return False
    
    def _get_current_chapter_count(self, novel_id: str) -> int:
        """获取当前小说的章节数"""
        try:
            # 优先从文件系统获取，确保获取到最新的章节数
            novel_dir = os.path.join(config.NOVELS_DIR, novel_id)
            if os.path.exists(novel_dir):
                chapter_files = [f for f in os.listdir(novel_dir) if f.startswith("chapter_") and f.endswith(".json")]
                file_count = len(chapter_files)
                print(f"从文件系统获取到章节数: {file_count}")
                
                # 同时检查元数据中的章节数，如果不一致则记录警告
                novel_data = self.data_manager.load_novel_data(novel_id, "metadata")
                if novel_data and "chapters" in novel_data:
                    metadata_count = len(novel_data["chapters"])
                    if metadata_count != file_count:
                        print(f"警告：元数据章节数({metadata_count})与文件系统章节数({file_count})不一致")
                
                return file_count
            
            # 如果文件系统获取失败，尝试从元数据获取
            novel_data = self.data_manager.load_novel_data(novel_id, "metadata")
            if novel_data and "chapters" in novel_data:
                metadata_count = len(novel_data["chapters"])
                print(f"从元数据获取到章节数: {metadata_count}")
                return metadata_count
            
            return 0
        except Exception as e:
            print(f"获取章节数失败: {e}")
            return 0
    
    def _should_stop_continuous_writing(self, progress: QuickContinuationProgress) -> bool:
        """判断是否应该停止持续写作"""
        try:
            # 获取最新的故事线内容
            storyline_data = self.workflow.context.continuation_data.get("next_chapter_storyline", {})
            storyline_content = storyline_data.get("content", "")
            chapter_ending = storyline_data.get("chapter_ending", "")
            next_chapter_hint = storyline_data.get("next_chapter_hint", "")
            
            # 检查所有相关文本
            all_text = f"{storyline_content} {chapter_ending} {next_chapter_hint}"
            
            # 扩展的结束点检测逻辑
            end_indicators = [
                # 明确的结束词汇
                "完结", "结束", "大结局", "尾声", "后记", "终章",
                "故事结束", "全文完", "全剧终", "剧终", "终了",
                "从此以后", "多年以后", "多年后", "时光荏苒",
                "岁月如梭", "光阴似箭", "白驹过隙",
                
                # 故事结构结束点
                "故事告一段落", "故事到此结束", "故事画上句号",
                "圆满结局", "完美结局", "幸福结局",
                "英雄归来", "王者归来", "胜利归来",
                
                # 时间跨度结束
                "十年后", "二十年后", "三十年后", "多年后",
                "晚年", "老年", "暮年", "垂暮之年",
                
                # 空间结束
                "回到故乡", "回到起点", "回到原点",
                "落叶归根", "荣归故里"
            ]
            
            # 检查是否包含结束指示词
            for indicator in end_indicators:
                if indicator in all_text:
                    print(f"检测到故事结束指示词: '{indicator}'")
                    return True
            
            # 检查章节标题是否暗示结束
            chapter_title = storyline_data.get("chapter_title", "")
            if chapter_title:
                title_end_indicators = ["终章", "尾声", "后记", "完结", "结局", "大结局"]
                for indicator in title_end_indicators:
                    if indicator in chapter_title:
                        print(f"检测到章节标题中的结束指示词: '{indicator}'")
                        return True
            
            return False
            
        except Exception as e:
            print(f"检查是否停止持续写作时出错: {e}")
            return False
    
    def get_progress(self, novel_id: str) -> Optional[QuickContinuationProgress]:
        """获取任务进度"""
        with self.lock:
            if novel_id in self.running_tasks:
                return self.running_tasks[novel_id]
            
            # 尝试从文件加载
            progress = self._load_progress(novel_id)
            
            # 如果加载到进度，检查状态是否合理
            if progress:
                progress = self._validate_and_repair_progress(progress)
            
            return progress
    
    def stop_task(self, novel_id: str) -> Dict[str, Any]:
        """停止任务"""
        with self.lock:
            if novel_id in self.running_tasks:
                progress = self.running_tasks[novel_id]
                progress.status = "stopped"
                progress.current_step = "stopped"
                self._update_progress(progress)
                del self.running_tasks[novel_id]
                
                return {
                    "success": True,
                    "message": "任务已停止"
                }
            else:
                # 尝试从文件加载进度，如果状态为运行中，则更新为停止
                progress = self._load_progress(novel_id)
                if progress and progress.status == "running":
                    print(f"检测到文件中的任务状态为运行中，正在更新为停止状态...")
                    progress.status = "stopped"
                    progress.current_step = "stopped"
                    self._update_progress(progress)
                    
                    return {
                        "success": True,
                        "message": "任务已停止（状态已修复）"
                    }
                else:
                    return {
                        "success": False,
                        "error": "未找到运行中的任务"
                    }
    
    def pause_task(self, novel_id: str) -> Dict[str, Any]:
        """暂停任务"""
        with self.lock:
            if novel_id in self.running_tasks:
                progress = self.running_tasks[novel_id]
                progress.status = "paused"
                self._update_progress(progress)
                
                return {
                    "success": True,
                    "message": "任务已暂停"
                }
            else:
                # 尝试从文件加载进度，如果状态为运行中，则更新为暂停
                progress = self._load_progress(novel_id)
                if progress and progress.status == "running":
                    print(f"检测到文件中的任务状态为运行中，正在更新为暂停状态...")
                    progress.status = "paused"
                    self._update_progress(progress)
                    
                    return {
                        "success": True,
                        "message": "任务已暂停（状态已修复）"
                    }
                else:
                    return {
                        "success": False,
                        "error": "未找到运行中的任务"
                    }
    
    def resume_task(self, novel_id: str) -> Dict[str, Any]:
        """恢复任务"""
        with self.lock:
            if novel_id in self.running_tasks:
                progress = self.running_tasks[novel_id]
                progress.status = "running"
                self._update_progress(progress)
                
                return {
                    "success": True,
                    "message": "任务已恢复"
                }
            else:
                return {
                    "success": False,
                    "error": "未找到运行中的任务"
                }
    
    def _update_progress(self, progress: QuickContinuationProgress):
        """更新进度"""
        progress.last_update = datetime.now().isoformat()
        self._save_progress(progress)
    
    def _save_progress(self, progress: QuickContinuationProgress):
        """保存进度到文件"""
        try:
            # 验证数据完整性
            if not progress.novel_id:
                print("警告: novel_id为空，无法保存进度")
                return
            
            # 确保所有必需字段都有默认值
            if not hasattr(progress, 'novel_title') or not progress.novel_title:
                progress.novel_title = "未知小说"
            if not hasattr(progress, 'mode') or not progress.mode:
                progress.mode = "fixed"
            if not hasattr(progress, 'total_chapters'):
                progress.total_chapters = 0
            if not hasattr(progress, 'completed_chapters'):
                progress.completed_chapters = 0
            if not hasattr(progress, 'current_chapter'):
                progress.current_chapter = 1
            if not hasattr(progress, 'current_step') or not progress.current_step:
                progress.current_step = "unknown"
            if not hasattr(progress, 'status') or not progress.status:
                progress.status = "unknown"
            if not hasattr(progress, 'start_time') or not progress.start_time:
                progress.start_time = datetime.now().isoformat()
            if not hasattr(progress, 'last_update'):
                progress.last_update = datetime.now().isoformat()
            if not hasattr(progress, 'error_message'):
                progress.error_message = ""
            if not hasattr(progress, 'chapter_details'):
                progress.chapter_details = []
            
            progress_file = os.path.join(self.status_dir, f"{progress.novel_id}.json")
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(progress), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存进度失败: {e}")
    
    def _load_progress(self, novel_id: str) -> Optional[QuickContinuationProgress]:
        """从文件加载进度"""
        try:
            progress_file = os.path.join(self.status_dir, f"{novel_id}.json")
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return QuickContinuationProgress(**data)
        except Exception as e:
            print(f"加载进度失败: {e}")
        return None
    
    def _validate_and_repair_progress(self, progress: QuickContinuationProgress) -> QuickContinuationProgress:
        """验证并修复进度状态"""
        try:
            # 获取实际章节数
            actual_chapter_count = self._get_current_chapter_count(progress.novel_id)
            
            # 检查状态是否合理
            if progress.status == "running":
                # 首先检查任务是否真的在内存中运行
                if progress.novel_id not in self.running_tasks:
                    print(f"检测到任务状态为运行中，但不在内存中，正在修复状态...")
                    print(f"  任务ID: {progress.novel_id}")
                    print(f"  当前状态: {progress.status}")
                    
                    # 如果任务不在内存中，说明任务已经完成或异常结束
                    # 根据章节数判断任务状态
                    if progress.completed_chapters >= actual_chapter_count:
                        # 如果已完成章节数大于等于实际章节数，说明任务已完成
                        progress.status = "completed"
                        progress.current_step = "completed"
                        print(f"  修复为: 已完成")
                    else:
                        # 否则标记为失败
                        progress.status = "failed"
                        progress.current_step = "failed"
                        progress.error_message = "任务异常结束，状态已自动修复"
                        print(f"  修复为: 失败")
                    
                    # 保存修复后的状态
                    self._update_progress(progress)
                    return progress
                
                # 如果状态是运行中，但已完成章节数小于实际章节数，说明状态不同步
                if progress.completed_chapters < actual_chapter_count:
                    print(f"检测到进度状态不同步，正在修复...")
                    print(f"  进度记录：已完成{progress.completed_chapters}章")
                    print(f"  实际状态：已有{actual_chapter_count}章")
                    
                    # 修复进度状态
                    progress.completed_chapters = actual_chapter_count
                    
                    # 重新构建章节详情
                    progress.chapter_details = []
                    for i in range(1, actual_chapter_count + 1):
                        chapter_detail = {
                            "chapter_number": i,
                            "completed_at": datetime.now().isoformat(),
                            "status": "completed"
                        }
                        progress.chapter_details.append(chapter_detail)
                    
                    # 如果当前步骤是写作章节，但该章节已经存在，说明卡住了
                    if progress.current_step.startswith("writing_chapter_"):
                        chapter_num = int(progress.current_step.split("_")[-1])
                        if chapter_num <= actual_chapter_count:
                            print(f"检测到卡在已完成的章节{chapter_num}，重置状态...")
                            progress.current_step = "storyline_generation"
                            progress.current_chapter = actual_chapter_count + 1
                    
                    print(f"进度状态修复完成：已完成{progress.completed_chapters}章")
                    
                    # 保存修复后的进度
                    self._update_progress(progress)
            
            return progress
            
        except Exception as e:
            print(f"验证和修复进度状态失败: {e}")
            return progress
    
    def cleanup_completed_tasks(self):
        """清理已完成的任务文件"""
        try:
            for filename in os.listdir(self.status_dir):
                if filename.endswith('.json'):
                    novel_id = filename[:-5]  # 移除.json后缀
                    progress = self._load_progress(novel_id)
                    if progress and progress.status in ['completed', 'failed', 'stopped']:
                        # 删除超过24小时的任务文件
                        last_update = datetime.fromisoformat(progress.last_update)
                        if (datetime.now() - last_update).total_seconds() > 24 * 3600:
                            os.remove(os.path.join(self.status_dir, filename))
        except Exception as e:
            print(f"清理任务文件失败: {e}")
    
    def _validate_chapter_word_count(self, progress: QuickContinuationProgress) -> bool:
        """验证章节字数，少于2k字则重新生成"""
        try:
            MIN_WORD_COUNT = 2000  # 最小字数要求
            MAX_RETRIES = 5  # 最大重试次数
            
            # 获取刚保存的章节
            chapters = self.data_manager.get_novel_chapters(progress.novel_id)
            if not chapters:
                print("❌ 无法获取章节数据进行字数验证")
                return False
            
            # 找到当前章节
            current_chapter = None
            for chapter in chapters:
                if chapter.get("chapter_number") == progress.current_chapter:
                    current_chapter = chapter
                    break
            
            if not current_chapter:
                print(f"❌ 无法找到第{progress.current_chapter}章进行字数验证")
                return False
            
            word_count = current_chapter.get("word_count", 0)
            print(f"📊 第{progress.current_chapter}章字数: {word_count}")
            
            if word_count >= MIN_WORD_COUNT:
                print(f"✅ 章节字数({word_count})符合要求(≥{MIN_WORD_COUNT})")
                return True
            
            print(f"❌ 章节字数({word_count})不足，要求至少{MIN_WORD_COUNT}字")
            
            # 检查重试次数
            retry_count = getattr(progress, 'word_count_retry_count', 0)
            if retry_count >= MAX_RETRIES:
                print(f"❌ 已达到最大重试次数({MAX_RETRIES})，跳过重新生成")
                progress.error_message = f"章节字数不足({word_count}字)，已达到最大重试次数"
                return False
            
            # 增加重试计数
            progress.word_count_retry_count = retry_count + 1
            print(f"🔄 开始第{progress.word_count_retry_count}次重新生成(最多{MAX_RETRIES}次)")
            
            # 删除当前字数不足的章节
            print(f"🗑️ 删除字数不足的第{progress.current_chapter}章")
            delete_success = self.data_manager.delete_chapter(progress.novel_id, progress.current_chapter)
            if not delete_success:
                print("❌ 删除字数不足的章节失败")
                return False
            
            # 清除相关缓存
            if self.workflow.context:
                cache_keys_to_remove = []
                for key in self.workflow.context._cache.keys():
                    if "next_chapter" in key or "chapter_content" in key:
                        cache_keys_to_remove.append(key)
                
                for key in cache_keys_to_remove:
                    del self.workflow.context._cache[key]
                print(f"🧹 清除了{len(cache_keys_to_remove)}个相关缓存")
            
            # 重新执行章节生成流程
            print(f"🔄 重新生成第{progress.current_chapter}章...")
            progress.current_step = f"regenerating_chapter_{progress.current_chapter}_attempt_{progress.word_count_retry_count}"
            self._update_progress(progress)
            
            # 递归调用重新生成（但不包括保存验证，避免无限递归）
            success = self._regenerate_chapter_for_word_count(progress)
            
            if success:
                # 重新验证字数
                return self._validate_chapter_word_count(progress)
            else:
                print(f"❌ 第{progress.word_count_retry_count}次重新生成失败")
                return False
                
        except Exception as e:
            print(f"❌ 章节字数验证失败: {e}")
            return False
    
    def _regenerate_chapter_for_word_count(self, progress: QuickContinuationProgress) -> bool:
        """为字数不足重新生成章节（不包括保存验证，避免递归）"""
        try:
            # 重新生成故事线（给AI更明确的字数要求）
            print(f"📝 重新生成故事线，要求字数≥2500字...")
            progress.current_step = f"regenerating_storyline_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            # 在用户需求中添加字数要求
            enhanced_requirements = f"请确保章节内容丰富详实，字数不少于2500字。要有充分的情节发展、人物对话、环境描写和心理描写。"
            
            # 临时修改用户需求
            original_requirements = self.workflow.context.user_requirements if self.workflow.context else ""
            if self.workflow.context:
                self.workflow.context.user_requirements = enhanced_requirements
            
            storyline_result = self.workflow.generate_continuation_storyline(progress.novel_id)
            
            # 恢复原始需求
            if self.workflow.context:
                self.workflow.context.user_requirements = original_requirements
                
            if not storyline_result.get("success", False):
                print(f"❌ 重新生成故事线失败: {storyline_result.get('error', '未知错误')}")
                return False
            
            # 重新写作章节
            print(f"✍️ 重新写作章节内容...")
            progress.current_step = f"rewriting_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            chapter_result = self.workflow.write_continuation_chapter(progress.novel_id)
            if not chapter_result.get("success", False):
                print(f"❌ 重新写作章节失败: {chapter_result.get('error', '未知错误')}")
                return False
            
            # 重新保存章节
            print(f"💾 重新保存章节...")
            progress.current_step = f"resaving_chapter_{progress.current_chapter}"
            self._update_progress(progress)
            
            save_result = self.workflow.save_continuation_chapter(progress.novel_id)
            if not save_result.get("success", False):
                print(f"❌ 重新保存章节失败: {save_result.get('error', '未知错误')}")
                return False
            
            print(f"✅ 第{progress.current_chapter}章重新生成完成")
            return True
            
        except Exception as e:
            print(f"❌ 重新生成章节失败: {e}")
            return False


# 全局执行器实例
_executor = None

def get_executor() -> QuickContinuationExecutor:
    """获取全局执行器实例"""
    global _executor
    if _executor is None:
        _executor = QuickContinuationExecutor()
    return _executor
