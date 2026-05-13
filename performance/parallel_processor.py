"""
并行处理管理器
负责管理智能体的并行执行，提升系统性能
"""

import asyncio
import concurrent.futures
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import time


class ParallelProcessor:
    """并行处理管理器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks = {}
        self.task_lock = threading.Lock()
    
    def execute_parallel_assessment(self, assessment_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """并行执行评估任务"""
        try:
            if not assessment_tasks:
                return {"error": "没有评估任务"}
            
            # 提交所有任务到线程池
            future_to_task = {}
            for task in assessment_tasks:
                future = self.executor.submit(self._execute_single_assessment, task)
                future_to_task[future] = task
            
            # 收集结果
            results = {}
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.get("task_id", "unknown")] = result
                except Exception as e:
                    results[task.get("task_id", "unknown")] = {"error": str(e)}
            
            return {
                "status": "success",
                "results": results,
                "total_tasks": len(assessment_tasks),
                "completed_tasks": len(results)
            }
            
        except Exception as e:
            return {"error": f"并行评估执行失败: {str(e)}"}
    
    def execute_parallel_improvement(self, improvement_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """并行执行改进任务"""
        try:
            if not improvement_tasks:
                return {"error": "没有改进任务"}
            
            # 提交所有任务到线程池
            future_to_task = {}
            for task in improvement_tasks:
                future = self.executor.submit(self._execute_single_improvement, task)
                future_to_task[future] = task
            
            # 收集结果
            results = {}
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.get("task_id", "unknown")] = result
                except Exception as e:
                    results[task.get("task_id", "unknown")] = {"error": str(e)}
            
            return {
                "status": "success",
                "results": results,
                "total_tasks": len(improvement_tasks),
                "completed_tasks": len(results)
            }
            
        except Exception as e:
            return {"error": f"并行改进执行失败: {str(e)}"}
    
    def execute_parallel_llm_calls(self, llm_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """并行执行LLM调用"""
        try:
            if not llm_tasks:
                return {"error": "没有LLM任务"}
            
            # 提交所有任务到线程池
            future_to_task = {}
            for task in llm_tasks:
                future = self.executor.submit(self._execute_single_llm_call, task)
                future_to_task[future] = task
            
            # 收集结果
            results = {}
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.get("task_id", "unknown")] = result
                except Exception as e:
                    results[task.get("task_id", "unknown")] = {"error": str(e)}
            
            return {
                "status": "success",
                "results": results,
                "total_tasks": len(llm_tasks),
                "completed_tasks": len(results)
            }
            
        except Exception as e:
            return {"error": f"并行LLM调用失败: {str(e)}"}
    
    def _execute_single_assessment(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个评估任务"""
        try:
            assessor = task.get("assessor")
            input_data = task.get("input_data", {})
            
            if not assessor:
                return {"error": "缺少评估器"}
            
            # 执行评估
            result = assessor.process(input_data)
            
            return {
                "task_id": task.get("task_id", "unknown"),
                "assessor_type": task.get("assessor_type", "unknown"),
                "result": result,
                "execution_time": time.time() - task.get("start_time", time.time())
            }
            
        except Exception as e:
            return {
                "task_id": task.get("task_id", "unknown"),
                "error": str(e),
                "execution_time": time.time() - task.get("start_time", time.time())
            }
    
    def _execute_single_improvement(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个改进任务"""
        try:
            improver = task.get("improver")
            input_data = task.get("input_data", {})
            
            if not improver:
                return {"error": "缺少改进器"}
            
            # 执行改进
            result = improver.process(input_data)
            
            return {
                "task_id": task.get("task_id", "unknown"),
                "improver_type": task.get("improver_type", "unknown"),
                "result": result,
                "execution_time": time.time() - task.get("start_time", time.time())
            }
            
        except Exception as e:
            return {
                "task_id": task.get("task_id", "unknown"),
                "error": str(e),
                "execution_time": time.time() - task.get("start_time", time.time())
            }
    
    def _execute_single_llm_call(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个LLM调用"""
        try:
            llm_client = task.get("llm_client")
            messages = task.get("messages", [])
            
            if not llm_client:
                return {"error": "缺少LLM客户端"}
            
            # 执行LLM调用
            response = llm_client.call_llm(messages)
            
            return {
                "task_id": task.get("task_id", "unknown"),
                "response": response,
                "execution_time": time.time() - task.get("start_time", time.time())
            }
            
        except Exception as e:
            return {
                "task_id": task.get("task_id", "unknown"),
                "error": str(e),
                "execution_time": time.time() - task.get("start_time", time.time())
            }
    
    def create_assessment_tasks(self, assessors: List[Any], input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建评估任务列表"""
        tasks = []
        for i, assessor in enumerate(assessors):
            task = {
                "task_id": f"assessment_{i}_{int(time.time())}",
                "assessor": assessor,
                "assessor_type": assessor.__class__.__name__,
                "input_data": input_data,
                "start_time": time.time()
            }
            tasks.append(task)
        return tasks
    
    def create_improvement_tasks(self, improvers: List[Any], input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建改进任务列表"""
        tasks = []
        for i, improver in enumerate(improvers):
            task = {
                "task_id": f"improvement_{i}_{int(time.time())}",
                "improver": improver,
                "improver_type": improver.__class__.__name__,
                "input_data": input_data,
                "start_time": time.time()
            }
            tasks.append(task)
        return tasks
    
    def create_llm_tasks(self, llm_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """创建LLM调用任务列表"""
        tasks = []
        for i, llm_call in enumerate(llm_calls):
            task = {
                "task_id": f"llm_{i}_{int(time.time())}",
                "llm_client": llm_call.get("llm_client"),
                "messages": llm_call.get("messages", []),
                "start_time": time.time()
            }
            tasks.append(task)
        return tasks
    
    def get_running_tasks_count(self) -> int:
        """获取正在运行的任务数量"""
        with self.task_lock:
            return len(self.running_tasks)
    
    def shutdown(self):
        """关闭并行处理器"""
        self.executor.shutdown(wait=True)
    
    def __del__(self):
        """析构函数"""
        self.shutdown()
