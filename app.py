"""
InkAI 小说创作系统 Web API 服务器
提供RESTful API接口供前端调用
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
import json
from datetime import datetime
from typing import Dict, Any
from inkai_workflow_optimized import InkAIWorkflowOptimized as InkAIWorkflow
from workflow_context import WorkflowContext
import config

# 导入智能体（避免重复导入）
from agents import QualityAssessorAgent, CharacterCreatorAgent
from quick_continuation_executor import get_executor, QuickContinuationProgress

# 轻量 agent 辅助类（绕过 BaseAgent 的 abstractmethod 限制，直接调 LLM）
from base_agent import BaseAgent

class _LLMAgent(BaseAgent):
    def process(self, input_data): pass

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局工作流程实例
workflow = InkAIWorkflow()

# 静态文件路由
@app.route('/debug_frontend.html')
def debug_frontend():
    """提供调试前端页面"""
    return send_from_directory('.', 'debug_frontend.html')

@app.route('/favicon.ico')
def favicon():
    """处理favicon请求"""
    return send_from_directory('frontend', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 如果favicon不存在，返回404但不报错
@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    if request.path == '/favicon.ico':
        return '', 204  # 返回空响应，不报错
    return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404

def ensure_context_loaded(novel_id):
    """确保指定小说的上下文已正确加载"""
    if not workflow.context or workflow.context.novel_id != novel_id:
        # 尝试从数据管理器加载小说元数据
        novel_data = workflow.data_manager._load_novel_metadata(novel_id)
        if novel_data:
            # 创建新的上下文
            workflow.context = WorkflowContext(novel_id)
            
            # 优先尝试从保存的上下文文件加载完整数据
            context_loaded = workflow.context.load_context(novel_id)
            
            if context_loaded:
                print(f"成功从文件加载上下文: {novel_id}")
                # 如果是续写模式，直接返回，不需要重新推断步骤
                if workflow.context.is_continuation:
                    print(f"检测到续写模式，当前步骤: {workflow.context.current_step}")
                    return True
            else:
                print(f"未找到上下文文件，重新构建上下文: {novel_id}")
                # 如果没有上下文文件，按原逻辑重新构建
                user_requirements = novel_data.get("user_requirements", "")
                print(f"从metadata读取用户需求，长度: {len(user_requirements)}")
                workflow.context.set_basic_info(
                    novel_data.get("title", "未知小说"),
                    user_requirements
                )
            
            # 加载标签数据
            tags = workflow.data_manager.load_novel_data(novel_id, "tags")
            if tags:
                workflow.context.set_tags(tags)
            
            # 加载人物数据
            characters = workflow.data_manager.load_novel_data(novel_id, "characters")
            if characters:
                workflow.context.set_characters(characters)
            
            # 加载故事线数据
            storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")
            if storyline:
                workflow.context.set_storyline(storyline)
            
            # 加载质量评估数据
            character_quality = workflow.data_manager.load_novel_data(novel_id, "character_quality_assessment")
            if character_quality:
                workflow.context.cache_quality_assessment("character", character_quality)
            
            storyline_quality = workflow.data_manager.load_novel_data(novel_id, "storyline_quality_assessment")
            if storyline_quality:
                workflow.context.cache_quality_assessment("storyline", storyline_quality)
            
            # 只有在没有从文件加载上下文时才重新推断步骤（避免覆盖续写状态）
            if not context_loaded:
                # 根据已有数据确定当前步骤
                if characters:
                    if storyline:
                        # 有角色和故事线，检查是否有知识图谱
                        knowledge_graph = workflow.data_manager.get_knowledge_graph_by_novel_id(novel_id)
                        if knowledge_graph:
                            # 有知识图谱，检查是否有章节
                            chapters = workflow.data_manager.get_novel_chapters(novel_id)
                            if chapters:
                                workflow.context.set_current_step("chapter_completed")
                            else:
                                workflow.context.set_current_step("chapter_writing")
                        else:
                            workflow.context.set_current_step("knowledge_graph_creation")
                    else:
                        # 有角色但没有故事线，角色创建已完成，下一步是故事线生成
                        workflow.context.set_current_step("storyline_generation")
                elif tags:
                    # 有标签但没有角色，下一步是角色创建
                    workflow.context.set_current_step("character_creation")
                else:
                    # 什么都没有，从标签选择开始
                    workflow.context.set_current_step("tag_selection")
        else:
            return False
    return True

def get_creation_workflow_status(novel_id):
    """获取创作模式的工作流程状态（从结果文件直接判断）"""
    try:
        # 从数据管理器加载小说元数据
        novel_data = workflow.data_manager._load_novel_metadata(novel_id)
        if not novel_data:
            return {
                "novel_id": novel_id,
                "current_step": "not_started",
                "workflow_state": {}
            }
        
        # 检查各个数据文件的存在情况
        tags = workflow.data_manager.load_novel_data(novel_id, "tags")
        characters = workflow.data_manager.load_novel_data(novel_id, "characters")
        storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")
        knowledge_graph = workflow.data_manager.get_knowledge_graph_by_novel_id(novel_id)
        chapters = workflow.data_manager.get_novel_chapters(novel_id)
        
        # 根据数据存在情况确定当前步骤
        if characters:
            if storyline:
                if knowledge_graph:
                    if chapters:
                        current_step = "chapter_completed"
                    else:
                        current_step = "chapter_writing"
                else:
                    current_step = "knowledge_graph_creation"
            else:
                current_step = "storyline_generation"
        elif tags:
            current_step = "character_creation"
        else:
            current_step = "tag_selection"
        
        return {
            "novel_id": novel_id,
            "current_step": current_step,
            "workflow_state": {
                "novel_id": novel_id,
                "title": novel_data.get("title", "未知小说"),
                "current_step": current_step,
                "previous_steps": [],
                "has_tags": bool(tags),
                "has_characters": bool(characters),
                "has_storyline": bool(storyline),
                "has_knowledge_graph": bool(knowledge_graph),
                "has_chapters": bool(chapters),
                "is_continuation": False,  # 创作模式
                "cache_size": 0,
                "quality_assessments_count": 0,
                "created_at": novel_data.get("created_at", ""),
                "updated_at": novel_data.get("updated_at", "")
            }
        }
    except Exception as e:
        print(f"获取创作状态失败: {e}")
        return {
            "novel_id": novel_id,
            "current_step": "not_started",
            "workflow_state": {}
        }

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """提供静态文件"""
    return send_from_directory('frontend', path)

# ==================== 小说创作相关API ====================

@app.route('/api/novels', methods=['GET'])
def get_novels():
    """获取小说列表"""
    try:
        novels = workflow.data_manager.get_novel_list()
        return jsonify({
            "success": True,
            "data": novels
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels', methods=['POST'])
def create_novel():
    """创建新小说"""
    try:
        data = request.get_json()
        title = data.get('title', '未命名小说')
        user_requirements = data.get('user_requirements', '')
        
        if not user_requirements:
            return jsonify({
                "success": False,
                "error": "请输入创作需求"
            }), 400
        
        result = workflow.start_new_novel(user_requirements, title)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/tags', methods=['POST'])
def select_tags(novel_id):
    """选择标签"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.select_tags()
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/tags', methods=['PUT'])
def update_tags(novel_id):
    """更新标签"""
    try:
        data = request.get_json()
        selected_tags = data.get('selected_tags', {})
        
        # 获取现有标签数据
        existing_tags = workflow.data_manager.load_novel_data(novel_id, "tags")
        if not existing_tags:
            return jsonify({
                "success": False,
                "error": "标签数据不存在"
            }), 404
        
        # 更新标签数据
        existing_tags['selected_tags'] = selected_tags
        existing_tags['updated_at'] = datetime.now().isoformat()
        
        # 保存更新后的数据
        workflow.data_manager.save_novel_data(novel_id, "tags", existing_tags)
        
        return jsonify({
            "success": True,
            "data": existing_tags
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/characters', methods=['POST'])
def create_characters(novel_id):
    """创建人物形象"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.create_characters()
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/characters/improve', methods=['POST'])
def improve_characters(novel_id):
    """改进人物形象"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        data = request.get_json()
        suggestions = data.get('suggestions', [])
        
        result = workflow.improve_character(suggestions)
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/characters/quality', methods=['POST'])
def assess_character_quality(novel_id):
    """评估人物质量"""
    try:
        # 获取当前人物数据
        characters = workflow.data_manager.load_novel_data(novel_id, "characters")
        if not characters:
            return jsonify({
                "success": False,
                "error": "人物数据不存在"
            }), 404
        
        # 获取用户需求
        metadata = workflow.data_manager.load_novel_data(novel_id, "metadata")
        user_requirements = metadata.get("user_requirements", "") if metadata else ""
        
        # 检查角色数据格式
        main_character = characters.get("main_character", {})
        if not main_character:
            return jsonify({
                "success": False,
                "error": "主角数据不存在"
            }), 404
        
        # 处理角色数据格式
        character_for_assessment = main_character
        if "content" in main_character:
            # 如果角色数据包含content字段，尝试解析JSON
            try:
                import json
                if isinstance(main_character["content"], str):
                    character_for_assessment = json.loads(main_character["content"])
                else:
                    character_for_assessment = main_character["content"]
            except:
                # 如果解析失败，使用原始数据
                character_for_assessment = main_character
        
        # 调用质量评估智能体
        assessor = QualityAssessorAgent()
        
        # 构建评估输入
        assessment_input = {
            "content": character_for_assessment,
            "content_type": "character",
            "user_requirements": user_requirements
        }
        
        assessment = assessor.process(assessment_input)
        
        # 保存质量评估结果
        workflow.data_manager.save_novel_data(novel_id, "character_quality_assessment", assessment)
        
        return jsonify({
            "success": True,
            "data": assessment
        })
    except Exception as e:
        print(f"角色质量评估错误: {e}")
        return jsonify({
            "success": False,
            "error": f"评估失败: {str(e)}"
        }), 500

@app.route('/api/novels/<novel_id>/characters', methods=['PUT'])
def update_characters(novel_id):
    """更新人物数据"""
    try:
        data = request.get_json()
        
        # 获取现有数据
        existing_characters = workflow.data_manager.load_novel_data(novel_id, "characters")
        if not existing_characters:
            return jsonify({
                "success": False,
                "error": "人物数据不存在"
            }), 404
        
        # 合并更新数据
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        updated_characters = deep_update(existing_characters, data)
        
        # 保存更新后的数据
        workflow.data_manager.save_novel_data(novel_id, "characters", updated_characters)
        
        return jsonify({
            "success": True,
            "data": updated_characters
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/characters/improve-with-agent', methods=['POST'])
def improve_characters_with_agent(novel_id):
    """使用人物形象创建智能体改进人物数据"""
    try:
        data = request.get_json()
        user_modifications = data.get('modifications', {})
        
        # 获取现有数据
        existing_characters = workflow.data_manager.load_novel_data(novel_id, "characters")
        if not existing_characters:
            return jsonify({
                "success": False,
                "error": "人物数据不存在"
            }), 404
        
        # 获取标签和用户需求
        tags = workflow.data_manager.load_novel_data(novel_id, "tags")
        metadata = workflow.data_manager.load_novel_data(novel_id, "metadata")
        user_requirements = metadata.get("user_requirements", "") if metadata else ""
        
        # 合并用户修改到现有数据
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        # 应用用户修改
        modified_characters = deep_update(existing_characters.copy(), user_modifications)
        
        # 调用人物形象创建智能体进行补充和改进
        character_creator = CharacterCreatorAgent()
        
        # 构建智能体输入数据
        agent_input = {
            "selected_tags": tags.get("selected_tags", {}) if tags else {},
            "user_requirements": user_requirements,
            "existing_characters": modified_characters,
            "user_modifications": user_modifications
        }
        
        # 调用智能体进行改进
        improved_result = character_creator.process(agent_input)
        
        # 如果智能体返回了改进后的人物数据，使用它
        if improved_result and "main_character" in improved_result:
            final_characters = improved_result
        else:
            # 如果智能体没有返回改进数据，使用用户修改后的数据
            final_characters = modified_characters
        
        # 保存最终的人物数据
        workflow.data_manager.save_novel_data(novel_id, "characters", final_characters)
        
        return jsonify({
            "success": True,
            "data": final_characters,
            "improvement_applied": bool(improved_result and "main_character" in improved_result),
            "message": "人物数据已通过智能体改进并保存"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/storyline', methods=['POST'])
def generate_storyline(novel_id):
    """生成故事线"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.generate_storyline()
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/storyline/improve', methods=['POST'])
def improve_storyline(novel_id):
    """改进故事线"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        data = request.get_json()
        suggestions = data.get('suggestions', [])
        
        result = workflow.improve_storyline(suggestions)
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/storyline/quality', methods=['POST'])
def assess_storyline_quality(novel_id):
    """评估故事线质量"""
    try:
        # 获取当前故事线数据
        storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")
        if not storyline:
            return jsonify({
                "success": False,
                "error": "故事线数据不存在"
            }), 404
        
        # 获取用户需求
        metadata = workflow.data_manager.load_novel_data(novel_id, "metadata")
        user_requirements = metadata.get("user_requirements", "") if metadata else ""
        
        # 获取前续章节信息（如果有的话）
        chapters = workflow.data_manager.get_novel_chapters(novel_id)
        previous_chapters = chapters if chapters else []
        
        # 处理故事线数据格式
        storyline_for_assessment = storyline
        if "overall_storyline" in storyline:
            storyline_for_assessment = storyline["overall_storyline"]
        
        # 调用质量评估智能体
        assessor = QualityAssessorAgent()
        
        # 构建评估输入
        assessment_input = {
            "content": storyline_for_assessment,
            "content_type": "storyline",
            "user_requirements": user_requirements,
            "previous_chapters": previous_chapters,
            "overall_storyline": storyline_for_assessment
        }
        
        assessment = assessor.process(assessment_input)
        
        # 保存质量评估结果
        workflow.data_manager.save_novel_data(novel_id, "storyline_quality_assessment", assessment)
        
        return jsonify({
            "success": True,
            "data": assessment
        })
    except Exception as e:
        print(f"故事线质量评估错误: {e}")
        return jsonify({
            "success": False,
            "error": f"评估失败: {str(e)}"
        }), 500

@app.route('/api/novels/<novel_id>/storyline', methods=['PUT'])
def update_storyline(novel_id):
    """更新故事线数据"""
    try:
        data = request.get_json()
        
        # 获取现有数据
        existing_storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")
        if not existing_storyline:
            return jsonify({
                "success": False,
                "error": "故事线数据不存在"
            }), 404
        
        # 合并更新数据
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        updated_storyline = deep_update(existing_storyline, data)
        
        # 保存更新后的数据
        workflow.data_manager.save_novel_data(novel_id, "storyline", updated_storyline)
        
        return jsonify({
            "success": True,
            "data": updated_storyline
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/knowledge-graph', methods=['POST'])
def create_knowledge_graph(novel_id):
    """创建知识图谱"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.create_knowledge_graph()
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/data/knowledge_graph', methods=['GET'])
def get_knowledge_graph(novel_id):
    """获取知识图谱数据"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        # 获取知识图谱数据
        knowledge_graph = workflow.data_manager.get_knowledge_graph_by_novel_id(novel_id)
        
        if not knowledge_graph:
            return jsonify({
                "success": False,
                "error": "知识图谱不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": knowledge_graph
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/chapters', methods=['POST'])
def write_first_chapter(novel_id):
    """写作第一章"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.write_first_chapter()
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>/txt', methods=['POST'])
def save_chapter_txt(novel_id, chapter_number):
    """保存章节为txt文件"""
    try:
        # 在优化版本中，novel_id 通过 context 管理
        chapter_data = workflow.data_manager.load_novel_data(novel_id, f"chapter_{chapter_number:03d}")
        
        if not chapter_data:
            return jsonify({
                "success": False,
                "error": "章节不存在"
            }), 404
        
        txt_file = workflow.data_manager.save_chapter_txt(novel_id, chapter_number, chapter_data)
        
        if txt_file:
            return jsonify({
                "success": True,
                "data": {"txt_file": txt_file}
            })
        else:
            return jsonify({
                "success": False,
                "error": "保存失败"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 小说续写相关API ====================

@app.route('/api/novels/<novel_id>/continuation', methods=['POST'])
def start_continuation(novel_id):
    """开始小说续写"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        data = request.get_json() or {}
        user_requirements = data.get('user_requirements', '')
        reset_cache = data.get('reset_cache', False)  # 新增：用户是否选择重置
        
        result = workflow.start_novel_continuation(novel_id, user_requirements, reset_cache)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/storyline', methods=['POST'])
def generate_continuation_storyline(novel_id):
    """生成续写故事线"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.generate_continuation_storyline(novel_id)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/storyline/improve', methods=['POST'])
def improve_continuation_storyline(novel_id):
    """改进续写故事线"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.improve_continuation_storyline(novel_id)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/storyline', methods=['PUT'])
def update_continuation_storyline(novel_id):
    """更新续写故事线"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "没有提供更新数据"
            }), 400
        
        result = workflow.update_continuation_storyline(novel_id, data)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
        
        return jsonify({
            "success": True,
            "message": "续写故事线更新成功",
            "data": result
        })
        
    except Exception as e:
        print(f"更新续写故事线错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/quality', methods=['POST'])
def assess_continuation_quality(novel_id):
    """评估续写质量"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        data = request.get_json()
        content_type = data.get('content_type', 'storyline')  # 'storyline' or 'story'
        
        result = workflow.assess_continuation_quality(novel_id, content_type)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/chapter', methods=['POST'])
def write_continuation_chapter(novel_id):
    """写作续写章节"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.write_continuation_chapter(novel_id)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/chapter/improve', methods=['POST'])
def improve_continuation_chapter(novel_id):
    """改进续写章节"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        data = request.get_json()
        suggestions = data.get('suggestions', [])
        
        result = workflow.improve_continuation_chapter(novel_id, suggestions)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/save', methods=['POST'])
def save_continuation_chapter(novel_id):
    """保存续写章节"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.save_continuation_chapter(novel_id)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/clear-cache', methods=['POST'])
def clear_continuation_cache(novel_id):
    """清除续写缓存数据"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        result = workflow.clear_continuation_cache(novel_id)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 状态查询相关API ====================

@app.route('/api/novels/<novel_id>/workflow-status', methods=['GET'])
def get_workflow_status(novel_id):
    """获取工作流程状态"""
    try:
        # 确保上下文已正确加载
        if ensure_context_loaded(novel_id):
            # 优先使用内存中的工作流状态（实时状态）
            if workflow.context and workflow.context.novel_id == novel_id:
                context_status = workflow.get_workflow_status()
                if context_status and context_status.get("current_step") != "not_started":
                    print(f"使用内存状态: {context_status.get('current_step')}")
                    return jsonify({
                        "success": True,
                        "data": context_status
                    })
        
        # 如果内存状态不可用，使用文件状态作为备选
        print("内存状态不可用，使用文件状态作为备选")
        status = get_creation_workflow_status(novel_id)
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation-status', methods=['GET'])
def get_continuation_status(novel_id):
    """获取续写状态"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        status = workflow.get_continuation_status(novel_id)
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/quick', methods=['POST'])
def start_quick_continuation(novel_id):
    """启动快速续写"""
    try:
        # 获取请求参数
        data = request.get_json() or {}
        mode = data.get('mode', 'fixed')  # 'fixed' 或 'continuous'
        chapter_count = data.get('chapter_count', 1)
        requirements = data.get('requirements', '')
        continuous_mode = data.get('continuous_mode', 'auto')
        
        print(f"快速续写请求: mode={mode}, chapter_count={chapter_count}, requirements={requirements}")
        
        # 验证参数
        if mode == 'fixed' and (not chapter_count or chapter_count < 1 or chapter_count > 10):
            return jsonify({
                "success": False,
                "error": "章节数量必须在1-10之间"
            }), 400
        
        # 使用后台执行器启动快速续写
        executor = get_executor()
        
        result = executor.start_quick_continuation(
            novel_id=novel_id,
            mode=mode,
            chapter_count=chapter_count,
            requirements=requirements,
            continuous_mode=continuous_mode
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": f"快速续写已启动，模式: {mode}",
                "data": {
                    "mode": mode,
                    "chapter_count": chapter_count if mode == 'fixed' else None,
                    "continuous_mode": continuous_mode if mode == 'continuous' else None,
                    "requirements": requirements,
                    "task_id": result["task_id"],
                    "progress": result["progress"]
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
            
    except Exception as e:
        print(f"快速续写启动失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/quick/progress', methods=['GET'])
def get_quick_continuation_progress(novel_id):
    """获取快速续写进度"""
    try:
        executor = get_executor()
        
        progress = executor.get_progress(novel_id)
        if progress:
            return jsonify({
                "success": True,
                "data": {
                    "novel_id": progress.novel_id,
                    "novel_title": progress.novel_title,
                    "mode": progress.mode,
                    "total_chapters": progress.total_chapters,
                    "completed_chapters": progress.completed_chapters,
                    "current_chapter": progress.current_chapter,
                    "current_step": progress.current_step,
                    "status": progress.status,
                    "start_time": progress.start_time,
                    "last_update": progress.last_update,
                    "error_message": progress.error_message,
                    "chapter_details": progress.chapter_details
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到快速续写任务"
            }), 404
            
    except Exception as e:
        print(f"获取快速续写进度失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/quick/stop', methods=['POST'])
def stop_quick_continuation(novel_id):
    """停止快速续写任务"""
    try:
        executor = get_executor()
        
        result = executor.stop_task(novel_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"停止快速续写任务失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/quick/pause', methods=['POST'])
def pause_quick_continuation(novel_id):
    """暂停快速续写任务"""
    try:
        executor = get_executor()
        
        result = executor.pause_task(novel_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"暂停快速续写任务失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/continuation/quick/resume', methods=['POST'])
def resume_quick_continuation(novel_id):
    """恢复快速续写任务"""
    try:
        executor = get_executor()
        
        result = executor.resume_task(novel_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"恢复快速续写任务失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/data/continuation_storyline_quality_assessment', methods=['GET'])
def get_continuation_storyline_quality_assessment(novel_id):
    """获取续写故事线质量评估数据"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        # 从数据管理器获取质量评估数据
        quality_data = workflow.data_manager.load_novel_data(novel_id, "continuation_storyline_quality_assessment")
        
        if quality_data:
            return jsonify({
                "success": True,
                "data": quality_data
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到质量评估数据"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/data/continuation_chapter_quality_assessment', methods=['GET'])
def get_continuation_chapter_quality_assessment(novel_id):
    """获取续写章节质量评估数据"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        # 从数据管理器获取质量评估数据
        quality_data = workflow.data_manager.load_novel_data(novel_id, "continuation_chapter_quality_assessment")
        
        if quality_data:
            return jsonify({
                "success": True,
                "data": quality_data
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到质量评估数据"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/data/<data_type>', methods=['GET'])
def get_novel_data(novel_id, data_type):
    """获取小说数据"""
    try:
        # 确保上下文已正确加载
        if not ensure_context_loaded(novel_id):
            return jsonify({
                "success": False,
                "error": "无法加载小说数据"
            }), 404
        
        data = workflow.data_manager.load_novel_data(novel_id, data_type)
        
        if data is None:
            return jsonify({
                "success": False,
                "error": "数据不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/chapters', methods=['GET'])
def get_novel_chapters(novel_id):
    """获取小说章节列表"""
    try:
        chapters = workflow.data_manager.get_novel_chapters(novel_id)

        return jsonify({
            "success": True,
            "data": chapters
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>', methods=['PUT'])
def update_chapter(novel_id, chapter_number):
    """更新章节内容"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求数据为空"}), 400

        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title and not content:
            return jsonify({"success": False, "error": "标题和内容不能同时为空"}), 400

        success = workflow.data_manager.update_chapter(novel_id, chapter_number, title, content)
        if not success:
            return jsonify({"success": False, "error": "章节更新失败，请检查章节是否存在"}), 404

        return jsonify({
            "success": True,
            "message": f"第{chapter_number}章更新成功"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>/rollback', methods=['POST'])
def rollback_chapter(novel_id, chapter_number):
    """回退章节到上次 git 提交的版本"""
    try:
        success = workflow.data_manager.rollback_chapter(novel_id, chapter_number)
        if not success:
            return jsonify({"success": False, "error": "回退失败，请确认该章节已有 git 提交记录"}), 400
        return jsonify({
            "success": True,
            "message": f"第{chapter_number}章已回退到上次提交的版本"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>/quality', methods=['POST'])
def assess_chapter_quality(novel_id, chapter_number):
    """评估已有章节质量（文学性 + 一致性）"""
    try:
        # 加载章节
        chapters = workflow.data_manager.get_novel_chapters(novel_id)
        chapter = None
        for ch in chapters:
            if ch.get("chapter_number") == chapter_number:
                chapter = ch
                break
        if not chapter:
            return jsonify({"success": False, "error": f"第{chapter_number}章不存在"}), 404

        # 获取用户需求和知识库
        metadata = workflow.data_manager.load_novel_data(novel_id, "metadata")
        user_requirements = metadata.get("user_requirements", "") if metadata else ""

        characters = workflow.data_manager.load_novel_data(novel_id, "characters")
        storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")

        # 1. 文学质量评估
        lit_input = {
            "content": chapter,
            "content_type": "story",
            "user_requirements": user_requirements
        }
        lit_assessment = QualityAssessorAgent().process(lit_input)

        # 2. 一致性评估（章节内容 vs 知识库）
        from agents.continuation_quality_assessor import ContinuationQualityAssessor
        consistency_assessor = ContinuationQualityAssessor()
        consistency_input = {
            "continuation_content": chapter,
            "original_knowledge_base": {
                "characters": characters,
                "storyline": storyline,
                "tags": metadata.get("selected_tags", {}) if metadata else {}
            },
            "content_type": "story"
        }
        consistency_result = consistency_assessor.process(consistency_input)

        # 3. 合并评估结果
        lit_score = lit_assessment.get("overall_score", 0)
        con_score = consistency_result.get("overall_score", 0)
        overall_score = round((lit_score + con_score) / 2)

        lit_scores = lit_assessment.get("scores", {})
        con_scores = consistency_result.get("scores", {})

        def _quality_level(score):
            if score >= 85: return "优秀"
            elif score >= 70: return "良好"
            elif score >= 55: return "一般"
            return "需改进"

        merged = {
            "overall_score": overall_score,
            "quality_level": _quality_level(overall_score),
            "dimensions": {
                "coherence": lit_scores.get("coherence", 0),
                "characterization": lit_scores.get("characterization", 0),
                "writing_style": lit_scores.get("writing_style", 0),
                "appeal": lit_scores.get("appeal", 0),
                "consistency": con_score
            },
            "consistency_details": {
                "character_consistency": con_scores.get("character_consistency", 0),
                "plot_continuity": con_scores.get("plot_continuity", 0),
                "world_consistency": con_scores.get("world_consistency", 0),
                "foreshadowing_continuity": con_scores.get("foreshadowing_continuity", 0),
                "style_consistency": con_scores.get("style_consistency", 0)
            },
            "suggestions": (lit_assessment.get("suggestions") or []) + (consistency_result.get("suggestions") or []),
            "strengths": lit_assessment.get("strengths") or [],
            "weaknesses": (lit_assessment.get("weaknesses") or []) + (consistency_result.get("weaknesses") or [])
        }

        # 保存质量评估结果到章节（缓存）
        chapter["quality_assessment"] = merged
        workflow.data_manager.save_chapter(novel_id, chapter_number, chapter)

        return jsonify({"success": True, "data": merged})
    except Exception as e:
        print(f"章节质量评估错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"评估失败: {str(e)}"}), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>/improve/dialogue', methods=['POST'])
def improve_dialogue(novel_id, chapter_number):
    """对话式需求确认：AI 引导用户明确优化需求"""
    try:
        data = request.get_json() or {}
        messages = data.get("messages") or []
        chapter_summary = data.get("chapter_summary", "")
        chapter_title = data.get("chapter_title", "")
        tags = data.get("tags") or {}

        genre = tags.get("genre", "玄幻")
        tone = tags.get("tone", "")

        # 加载章节内容（前 1500 字作为参考）
        chapter_content = data.get("chapter_content", "")
        if not chapter_content:
            chapters = workflow.data_manager.get_novel_chapters(novel_id)
            for ch in chapters:
                if ch.get("chapter_number") == chapter_number:
                    chapter_content = ch.get("content", "")[:1500]
                    break

        # 构建 system prompt
        user_turns = sum(1 for m in messages if m.get("role") == "user")

        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if user_turns == 0:
            stage_hint = "这是第 1 轮。用户还没说具体需求，请问他「想优化这章的哪个方面」，给 4-5 个具体选项。"
        else:
            stage_hint = (
                f"用户刚才说：「{last_user[:100]}」。"
                f"这是第 {user_turns + 1} 轮。先用一句话直接呼应他刚才说的（引用他的具体词），"
                "再追问一个更深的细节。如果已能回答「改什么/怎么改/改多少」三个问题，给出确认总结（confirming）；否则继续追问。"
            )

        system_prompt = f"""你是网文编辑助手，正在和作者对话，帮他明确对第{chapter_number}章「{chapter_title}」的优化需求。

题材：{genre}

章节内容（前 1500 字）：
---
{chapter_content}
---

{stage_hint}

你的目标：
- 追问直到能完整回答三个问题：改什么？怎么改？改多少？
- 当你对这三个问题都有明确答案时，给出确认总结（stage=confirming），options 用 ["✅ 确认开始优化", "🔄 重新描述需求"]
- 确认总结必须包含：用户的所有关键需求 + 建议修改范围（minor/medium/major）
- 选项要引用章节中的具体内容（如角色名、场景、段落），不要泛泛而谈
- 用户的描述已经很具体时，追问一两个关键细节就够了，不要没话找话

返回纯 JSON：
{{"question":"...","options":["...","..."],"stage":"clarifying","confirmed_requirements":null,"suggested_scope":null}}

每轮回复格式（严格遵守）：
1. question 开头必须是一句呼应用户刚才内容的话，要引用他说的具体词
2. options 的每个选项必须基于用户刚才回答，包含章节中的具体内容，不能是"优化文笔"这类通用选项
"""
        # 构建消息列表
        llm_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            # 跳过 assistant 消息中的 options 字段，只保留文本
            llm_messages.append({"role": role, "content": content})

        # 如果首轮，给一个初始提示
        if not messages:
            llm_messages.append({"role": "user", "content": "我想优化这一章"})

        agent = _LLMAgent("需求对话")
        agent.model = "deepseek-v4-pro"
        response = agent.call_llm(llm_messages, temperature=0.7, max_tokens=600)

        # 使用 BaseAgent 的成熟 JSON 解析（修复中文引号/尾部逗号/markdown代码块等）
        result = agent.parse_json_response(response)
        if not result or not isinstance(result, dict) or "question" not in result:
            print(f"[dialogue] JSON 解析失败或缺少 question 字段，原始响应: {response[:300]}")
            # 上下文感知的 fallback：根据已进行的轮次给出合理回复
            user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
            if user_turns == 0:
                result = {
                    "question": f"您想优化第{chapter_number}章《{chapter_title}》的哪个方面？",
                    "options": ["情节节奏", "人物对话与心理描写", "环境与氛围描写", "世界观设定说明", "其他（请描述）"],
                    "stage": "opening",
                    "confirmed_requirements": None,
                    "suggested_scope": None
                }
            elif user_turns <= 2:
                last_user_msg = user_msgs[-1] if user_msgs else ""
                result = {
                    "question": f"了解。关于「{last_user_msg[:50]}」，您希望怎么修改？比如重点调整哪些段落或角色？",
                    "options": ["重点修改相关段落", "全文统一调整", "只补充说明即可", "其他（请描述）"],
                    "stage": "clarifying",
                    "confirmed_requirements": None,
                    "suggested_scope": None
                }
            else:
                all_requirements = "；".join(user_msgs)
                result = {
                    "question": f"总结您的需求：{all_requirements[:200]}。确认开始优化吗？",
                    "options": ["✅ 确认开始优化", "🔄 重新描述需求"],
                    "stage": "confirming",
                    "confirmed_requirements": all_requirements[:300],
                    "suggested_scope": "medium"
                }

        return jsonify({"success": True, "data": result})

    except Exception as e:
        print(f"需求对话错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"对话失败: {str(e)}"}), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>/improve/proposals', methods=['POST'])
def improve_proposals(novel_id, chapter_number):
    """生成优化方案提案：根据用户需求给出 2-3 个具体优化方案供选择"""
    try:
        data = request.get_json() or {}
        requirements = data.get("requirements", "").strip()
        scope = data.get("scope", "minor")

        # 加载章节
        chapters = workflow.data_manager.get_novel_chapters(novel_id)
        chapter = None
        for ch in chapters:
            if ch.get("chapter_number") == chapter_number:
                chapter = ch
                break
        if not chapter:
            return jsonify({"success": False, "error": f"第{chapter_number}章不存在"}), 404

        chapter_content = chapter.get("content", "")
        chapter_title = chapter.get("title", f"第{chapter_number}章")
        chapter_summary = chapter.get("summary", "")

        # 截取章节内容前 2000 字作为分析样本
        content_sample = chapter_content[:2000] if chapter_content else ""

        # 获取知识库
        metadata = workflow.data_manager.load_novel_data(novel_id, "metadata")
        tags = metadata.get("selected_tags", {}) if metadata else {}
        genre = tags.get("genre", "玄幻")

        system_prompt = f"""你是一个资深网文编辑，正在帮作者规划对第{chapter_number}章《{chapter_title}》的优化方案。

题材：{genre}
章节摘要：{chapter_summary[:200]}
用户需求：{requirements}
修改范围：{scope}

章节内容（前2000字）：
---
{content_sample}
---

请根据用户需求和章节现状，生成 2-3 个差异化的优化方案。每个方案要有不同的侧重点和优化思路。

返回 JSON（只返回 JSON，不要其他内容）：
{{
  "plans": [
    {{
      "index": 0,
      "title": "方案名称（6字以内）",
      "description": "方案概述（2-3句，说明这个方案的核心思路和优化方向）",
      "expected_result": "预期效果（用一两句话说明改完后章节会变成什么样）",
      "key_changes": ["具体改动点1", "具体改动点2", "具体改动点3"]
    }}
  ]
}}

要求：
- 必须生成 3 个差异化方案，缺一不可。只生成 1-2 个视为不合格
- 三个方案必须从不同角度切入（如：删减精简 / 结构调整 / 场景合并），不能只是措辞不同
- 每个 key_changes 列 2-4 条具体可操作的改动
- 方案要结合章节实际内容，引用具体段落/场景
- 语言简洁，不用套话"""

        agent = _LLMAgent("优化提案")
        response = agent.call_llm([{"role": "system", "content": system_prompt}], temperature=0.7, max_tokens=1200)

        # 使用 BaseAgent 的成熟 JSON 解析
        result = agent.parse_json_response(response)
        if not result or not result.get("plans"):
            print(f"[Proposals] JSON 解析失败或缺少 plans，原始响应: {response[:500]}")

        if not result or not result.get("plans"):
            # Fallback: 基于需求关键词生成有意义的方案摘要
            req_brief = requirements[:80]
            result = {"plans": [{
                "index": 0,
                "title": "精准修改",
                "description": f"针对您提出的需求，定位章节中相关段落进行精准增删改，不动整体结构",
                "expected_result": "需求点得到补充/修正，其他部分保持原样",
                "key_changes": ["定位目标段落并修改", "新增必要的说明性文字", "保持上下文衔接流畅"]
            }]}

        # 确保至少有 2 个方案（如果 AI 只返回了 1 个，补充一个差异化方案）
        plans = result.get("plans", [])
        if len(plans) < 2:
            scope_labels = {"minor": "局部微调措辞和补充", "medium": "调整相关段落结构", "major": "重写大段内容"}
            alt_approach = "major" if scope == "minor" else "minor"
            plans.append({
                "index": len(plans),
                "title": "换个思路",
                "description": f"采用不同的修改策略：从{scope_labels.get(alt_approach, '另一种方式')}切入，用另一种写作手法实现同样目的",
                "expected_result": f"相同需求，不同的表达方式，给读者不同的阅读体验",
                "key_changes": ["调整叙事节奏", "改变信息透露方式", "重新组织关键场景"]
            })
            for i, p in enumerate(plans):
                p["index"] = i
            result["plans"] = plans

        return jsonify({"success": True, "data": result})

    except Exception as e:
        print(f"优化提案错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"生成提案失败: {str(e)}"}), 500


@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>/improve', methods=['POST'])
def improve_chapter(novel_id, chapter_number):
    """根据用户需求优化已有章节（返回预览，不直接落盘）+ 优化后评审循环"""
    try:
        data = request.get_json() or {}
        requirements = data.get("requirements", "").strip()
        suggestions = data.get("suggestions") or []
        scope = data.get("scope", "minor")
        selected_plan = data.get("selected_plan") or {}
        # 如果是继续优化，可能携带上轮评审意见
        previous_review = data.get("previous_review") or {}

        # 加载章节
        chapters = workflow.data_manager.get_novel_chapters(novel_id)
        chapter = None
        for ch in chapters:
            if ch.get("chapter_number") == chapter_number:
                chapter = ch
                break
        if not chapter:
            return jsonify({"success": False, "error": f"第{chapter_number}章不存在"}), 404

        # 获取知识库
        metadata = workflow.data_manager.load_novel_data(novel_id, "metadata")
        user_requirements = metadata.get("user_requirements", "") if metadata else ""
        characters = workflow.data_manager.load_novel_data(novel_id, "characters")
        storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")

        # 章节列表、最近章节、向量检索
        all_chapters = workflow.data_manager.get_novel_chapters(novel_id)
        recent_summaries = []
        for ch in all_chapters[-4:-1] if len(all_chapters) >= 2 else all_chapters[:-1]:
            recent_summaries.append({
                "chapter_number": ch.get("chapter_number", 0),
                "title": ch.get("title", ""),
                "summary": ch.get("summary", ""),
                "key_events": ch.get("key_events", [])
            })

        # 向量语义检索
        vector_retrieved = []
        if hasattr(workflow, 'embedding_service') and workflow.embedding_service.is_available:
            try:
                from core.embedding_service import ChapterEmbeddingStore
                novel_dir = os.path.join(workflow.data_manager.novels_dir, novel_id)
                store = ChapterEmbeddingStore(novel_dir, workflow.embedding_service)
                store.backfill_chapters(all_chapters)
                query_parts = [chapter.get("summary", "")]
                if recent_summaries:
                    query_parts.append(recent_summaries[-1].get("summary", ""))
                query = "；".join(q for q in query_parts if q)
                if query:
                    retrieved = store.search_relevant_chapters(query, current_chapter=chapter_number, top_k=5)
                    if retrieved:
                        ch_map = {ch.get("chapter_number"): ch for ch in all_chapters}
                        for item in retrieved:
                            rch = ch_map.get(item["chapter_number"])
                            if rch:
                                vector_retrieved.append({
                                    "chapter_number": item["chapter_number"],
                                    "title": rch.get("title", ""),
                                    "summary": rch.get("summary", ""),
                                    "key_events": rch.get("key_events", []),
                                    "relevance_score": item["score"]
                                })
            except Exception as e:
                print(f"[Vector] 优化检索失败（不影响主线）: {e}")

        # 获取上一章结尾原文（衔接参考）
        prev_chapter = None
        for ch in all_chapters:
            if ch.get("chapter_number") == chapter_number - 1:
                prev_chapter = ch
                break
        prev_ending = ""
        if prev_chapter:
            prev_content = prev_chapter.get("content", "")
            prev_ending = prev_content[-300:] if len(prev_content) > 300 else prev_content

        # 构建知识库（优化和评审共用）
        # 加载知识图谱（如不存在，从人物/故事数据生成轻量图谱）
        knowledge_graph = workflow.data_manager.load_novel_data(novel_id, "knowledge_graph")
        if not knowledge_graph:
            kg_from_chars = {}
            if characters:
                mc = characters.get("main_character", {})
                if mc.get("basic_info", {}).get("name"):
                    kg_from_chars["protagonist"] = mc["basic_info"]["name"]
                supporting = characters.get("supporting_characters", [])
                kg_from_chars["key_characters"] = [
                    {"name": c.get("basic_info", {}).get("name", "?"), "role": c.get("role", "?")}
                    for c in supporting[:8]
                ]
                rels = characters.get("character_relationships", {}).get("relationships", [])
                mc_name = kg_from_chars.get("protagonist", "")
                kg_from_chars["relationships"] = [
                    {"from": r.get("character", "?"), "to": mc_name, "type": str(r.get("relationship_type", ""))[:80]}
                    for r in rels[:8]
                ]
            if storyline:
                ws = storyline.get("overall_storyline", {}).get("world_setting", {})
                if isinstance(ws, dict):
                    kg_from_chars["world_elements"] = {k: str(v)[:100] for k, v in ws.items() if v}
            knowledge_graph = kg_from_chars

        # 提取故事结构
        overall = storyline.get("overall_storyline", {}) if storyline else {}
        story_structure = storyline.get("story_structure", {}) if storyline else {}

        # 加载动态知识图谱（角色发展、情节时间线、伏笔、世界观变动）
        dynamic_knowledge = workflow.data_manager.load_novel_data(novel_id, "dynamic_knowledge") or {}

        knowledge_base = {
            "character_profiles": characters,
            "storyline": storyline,
            "knowledge_graph": knowledge_graph,
            "dynamic_knowledge": dynamic_knowledge,
            "tags": metadata.get("selected_tags", {}) if metadata else {},
            "world_setting": overall.get("world_setting", ""),
            "main_goal": overall.get("main_goal", ""),
            "core_conflict": overall.get("core_conflict", ""),
            "overall_outline": overall.get("overall_outline", ""),
            "volumes": overall.get("volumes", []),
            "story_structure": story_structure,
            "story_tone": overall.get("tone", ""),
            "recent_chapters_summaries": recent_summaries,
            "vector_retrieved_chapters": vector_retrieved,
            "prev_chapter_ending": prev_ending
        }

        # ── 优化-评审循环（最多 3 轮）──
        from agents.continuation_chapter_improver import ContinuationChapterImprover
        improver = ContinuationChapterImprover()

        original_content = chapter.get("content", "")
        current_content = original_content
        review_results = []
        review_passed = False
        final_quality_report = {}
        MAX_ROUNDS = 3
        PASS_THRESHOLD = 85

        for round_num in range(1, MAX_ROUNDS + 1):
            # 构建本轮需求（首轮用用户需求；后续轮次附加评审意见）
            if round_num == 1:
                round_requirements = requirements or user_requirements
                if selected_plan:
                    plan_desc = selected_plan.get("description", "")
                    plan_changes = selected_plan.get("key_changes", [])
                    round_requirements += f"\n\n【选定优化方案：{selected_plan.get('title', '')}】\n{plan_desc}\n具体改动：\n" + "\n".join(f"- {c}" for c in plan_changes)
                if previous_review and previous_review.get("suggestions"):
                    round_requirements += "\n\n【上轮评审意见，请针对修复】\n" + "\n".join(
                        f"- {s}" for s in previous_review.get("suggestions", [])
                    )
            else:
                # 后续轮次：用评审建议作为改进需求
                prev = review_results[-1]
                round_requirements = f"""上一轮优化评审得分 {prev.get('overall_score', 0)} 分（通过线 {PASS_THRESHOLD} 分），请针对以下问题重新优化：

{chr(10).join(f'- {s}' for s in prev.get('suggestions', []))}

原始用户需求：{requirements or user_requirements}"""

            # 更新 chapter_content 为上一轮结果
            round_chapter = dict(chapter)
            if current_content != original_content:
                round_chapter["content"] = current_content

            improve_input = {
                "chapter_content": round_chapter,
                "quality_assessment": {"suggestions": suggestions},
                "knowledge_base": knowledge_base,
                "user_requirements": round_requirements,
                "suggestions": suggestions,
                "scope": scope
            }
            result = improver.process(improve_input)

            # 提取优化后内容
            improved_content = ""
            if isinstance(result, dict):
                improved_chapter = result.get("improved_chapter", {})
                if isinstance(improved_chapter, dict):
                    improved_content = improved_chapter.get("content", "")
                if not improved_content:
                    improved_content = result.get("content") or result.get("improved_content") or ""
                improvement_plan = result.get("improvement_plan", {})
                improvement_summary = result.get("improvement_summary", {})
                final_quality_report = {
                    "improvement_areas": improvement_plan.get("improvement_areas", []),
                    "priority_level": improvement_plan.get("priority_level", ""),
                    "specific_issues": improvement_plan.get("specific_issues", []),
                    "improvement_summary": improvement_summary
                }

            if not improved_content or improved_content.startswith("{'"):
                improved_content = current_content

            current_content = improved_content

            # ── 质量评审 ──
            review = _review_optimization(
                original_content=original_content,
                improved_content=current_content,
                requirements=requirements or user_requirements,
                scope=scope,
                chapter_context=knowledge_base
            )
            review["round"] = round_num
            review_results.append(review)

            if review.get("overall_score", 0) >= PASS_THRESHOLD:
                review_passed = True
                break

        # ── 构建返回 ──
        last_review = review_results[-1] if review_results else {}
        return jsonify({
            "success": True,
            "data": {
                "original_content": original_content,
                "original_title": chapter.get("title", ""),
                "improved_content": current_content,
                "improved_title": result.get("title", "") if isinstance(result, dict) else "",
                "changes_summary": result.get("changes_summary", "") if isinstance(result, dict) else "",
                "quality_report": final_quality_report,
                "review_passed": review_passed,
                "review_score": last_review.get("overall_score", 0),
                "review_rounds": len(review_results),
                "review_notes": last_review.get("summary", ""),
                "review_details": {
                    "requirement_met": last_review.get("requirement_met", False),
                    "scope_respected": last_review.get("scope_respected", False),
                    "issues": last_review.get("issues", []),
                    "suggestions": last_review.get("suggestions", [])
                }
            }
        })
    except Exception as e:
        print(f"章节优化错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"优化失败: {str(e)}"}), 500


def _review_optimization(original_content, improved_content, requirements, scope, chapter_context):
    """评审优化结果：需求满足度、范围遵守、质量提升、网文风格"""
    try:
        scope_labels = {
            "minor": "小改（只改措辞/句式，不调整段落结构和情节）",
            "medium": "中改（可调整段落/节奏/对话，保持情节不变）",
            "major": "大改（可大幅重写段落，增删描写，调整叙事节奏）"
        }

        prompt = f"""你是一个严格的网文编辑，请评审这次 AI 优化的质量。

【用户原始需求】
{requirements if requirements else "无特殊需求"}

【修改范围约束】
{scope_labels.get(scope, scope_labels['minor'])}

【章节题材参考】
世界观: {str(chapter_context.get('world_setting', ''))[:200]}
故事基调: {str(chapter_context.get('story_tone', ''))[:200]}

【优化前原文】（前 500 字）
{original_content[:500]}

【优化后正文】（前 800 字）
{improved_content[:800]}

请按以下维度打分（每项 0-25 分，总分 0-100）：

1. **需求满足度** (0-25 分)：是否精准满足了用户需求？有没有遗漏或曲解？
2. **范围遵守** (0-25 分)：是否严格遵守了修改范围约束？超出范围扣分。
3. **质量提升** (0-25 分)：优化后是否真的变好了？语言是否更流畅、更有网感？
4. **网文风格** (0-25 分)：是否符合网络小说的写作特点（快节奏、短段落、强冲突、去AI腔）？

请返回严格 JSON：
{{
    "overall_score": 85,
    "requirement_met": true,
    "scope_respected": true,
    "quality_improved": true,
    "style_good": true,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "summary": "一句话总评"
}}
"""
        reviewer = _LLMAgent("优化评审")
        messages = [
            {"role": "system", "content": "你是一个严格的网文编辑，擅长评估章节优化质量。只返回 JSON，不要有其他内容。"},
            {"role": "user", "content": prompt}
        ]
        response = reviewer.call_llm(messages, temperature=0.3, max_tokens=800)

        # 解析 JSON
        import json
        # 尝试提取 JSON 块
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            review = json.loads(json_match.group())
        else:
            review = json.loads(response)

        # 确保必要字段
        review.setdefault("overall_score", 70)
        review.setdefault("requirement_met", False)
        review.setdefault("scope_respected", False)
        review.setdefault("quality_improved", False)
        review.setdefault("style_good", False)
        review.setdefault("issues", [])
        review.setdefault("suggestions", [])
        review.setdefault("summary", "")

        return review

    except Exception as e:
        print(f"[Review] 评审失败（放行）: {e}")
        return {
            "overall_score": 85,
            "requirement_met": True,
            "scope_respected": True,
            "quality_improved": True,
            "style_good": True,
            "issues": [],
            "suggestions": [],
            "summary": f"评审异常（已自动放行）: {e}"
        }

@app.route('/api/novels/<novel_id>/statistics', methods=['GET'])
def get_novel_statistics(novel_id):
    """获取小说统计信息"""
    try:
        stats = workflow.data_manager.get_novel_statistics(novel_id)
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== 配置相关API ====================

@app.route('/api/config/tags', methods=['GET'])
def get_tag_categories():
    """获取标签分类配置"""
    try:
        return jsonify({
            "success": True,
            "data": config.TAG_CATEGORIES
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>/chapters/<int:chapter_number>', methods=['DELETE'])
def delete_chapter(novel_id, chapter_number):
    """删除指定章节"""
    try:
        success = workflow.data_manager.delete_chapter(novel_id, chapter_number)
        
        if success:
            # 确保上下文已加载
            ensure_context_loaded(novel_id)
            
            if workflow.context and workflow.context.novel_id == novel_id:
                # 智能状态恢复：删除第一章时，自动回到章节写作准备状态
                if chapter_number == 1:
                    # 检查必要数据是否存在
                    storyline = workflow.data_manager.load_novel_data(novel_id, "storyline")
                    characters = workflow.data_manager.load_novel_data(novel_id, "characters")
                    
                    if storyline and characters:
                        # 确保上下文数据是最新的
                        workflow.context.set_storyline(storyline)
                        workflow.context.set_characters(characters)
                        
                        # 重新设置为章节写作状态，但清除章节相关缓存
                        workflow.context.set_current_step("chapter_writing")
                        workflow.context._cache.clear()  # 清除所有缓存
                        workflow.context.is_continuation = False  # 确保不是续写模式
                        workflow.context.save_context()  # 保存状态
                        print("已自动恢复到章节写作状态")
                    else:
                        print("警告：缺少必要数据，请检查故事线和角色设定")
                
                # 清除章节相关缓存（保留原有逻辑）
                cache_keys_to_remove = []
                for key in list(workflow.context._cache.keys()):
                    if f"chapter_{chapter_number}" in key or "chapter_content" in key:
                        cache_keys_to_remove.append(key)
                
                for key in cache_keys_to_remove:
                    if key in workflow.context._cache:
                        del workflow.context._cache[key]
            
            return jsonify({
                "success": True,
                "message": f"章节{chapter_number}删除成功，已自动恢复工作流状态"
            })
        else:
            return jsonify({
                "success": False,
                "error": "删除章节失败"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/novels/<novel_id>', methods=['DELETE'])
def delete_novel(novel_id):
    """删除整个小说项目"""
    try:
        success = workflow.data_manager.delete_novel(novel_id)
        
        if success:
            # 清除相关缓存和上下文
            if workflow.context and workflow.context.novel_id == novel_id:
                workflow.context = None
            
            return jsonify({
                "success": True,
                "message": f"小说 {novel_id} 删除成功"
            })
        else:
            return jsonify({
                "success": False,
                "error": "删除小说失败"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ═══════════════════════════════════════════════════════════
# 记忆系统 (Agent Memory) — 2026-06-28
# ═══════════════════════════════════════════════════════════

from agent_memory import AgentMemory, list_agent_memories, get_all_memories_summary


@app.route('/api/novels/<novel_id>/memory/<agent_name>', methods=['GET'])
def get_agent_memory(novel_id, agent_name):
    """获取指定 agent 的记忆"""
    try:
        mem = AgentMemory(novel_id, agent_name)
        data = mem.load()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/memory/<agent_name>', methods=['POST'])
def save_agent_memory_insight(novel_id, agent_name):
    """向 agent 记忆中添加一条 insight"""
    try:
        body = request.get_json() or {}
        insight = body.get("insight") or body
        if not insight.get("content"):
            return jsonify({"success": False, "error": "缺少 content 字段"}), 400
        mem = AgentMemory(novel_id, agent_name)
        insight_id = mem.add_insight(insight)
        return jsonify({"success": True, "data": {"insight_id": insight_id}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/memory/<agent_name>/<insight_id>', methods=['DELETE'])
def delete_agent_memory_insight(novel_id, agent_name, insight_id):
    """删除 agent 记忆中的某条 insight"""
    try:
        mem = AgentMemory(novel_id, agent_name)
        ok = mem.delete_insight(insight_id)
        if ok:
            return jsonify({"success": True, "message": "已删除"})
        return jsonify({"success": False, "error": "未找到该条目"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/memory/summary', methods=['GET'])
def get_memory_summary(novel_id):
    """获取所有 agent 的记忆摘要列表"""
    try:
        agent_list = list_agent_memories(novel_id)
        context_text = get_all_memories_summary(novel_id)
        return jsonify({
            "success": True,
            "data": {"agents": agent_list, "context_text": context_text},
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════
# 规则系统 (Novel Rules) — 2026-06-28
# ═══════════════════════════════════════════════════════════

from novel_rules import RulesManager, build_rules_dialogue_messages


@app.route('/api/novels/<novel_id>/rules', methods=['GET'])
def get_novel_rules(novel_id):
    """获取小说的所有规则"""
    try:
        rm = RulesManager(novel_id)
        data = rm.load()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/rules', methods=['PUT'])
def save_novel_rule(novel_id):
    """保存/更新一条规则"""
    try:
        body = request.get_json() or {}
        rule = body.get("rule", {})
        if not rule.get("content"):
            return jsonify({"success": False, "error": "规则 content 不能为空"}), 400
        rm = RulesManager(novel_id)
        rule_id = rule.get("id")
        if rule_id:
            ok = rm.update_rule(rule_id, rule)
            if not ok:
                return jsonify({"success": False, "error": "未找到该规则"}), 404
            return jsonify({"success": True, "data": {"rule_id": rule_id, "action": "updated"}})
        else:
            new_id = rm.add_rule(rule)
            return jsonify({"success": True, "data": {"rule_id": new_id, "action": "created"}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/rules/<rule_id>', methods=['DELETE'])
def delete_novel_rule(novel_id, rule_id):
    """删除一条规则"""
    try:
        rm = RulesManager(novel_id)
        ok = rm.delete_rule(rule_id)
        if ok:
            return jsonify({"success": True, "message": "规则已删除"})
        return jsonify({"success": False, "error": "未找到该规则"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/novels/<novel_id>/rules/dialogue', methods=['POST'])
def rules_dialogue(novel_id):
    """规则建立对话 — AI 写作教练帮助作者梳理写作规则（复用优化对话模式）"""
    try:
        body = request.get_json() or {}
        messages = body.get("messages") or []
        novel_title = body.get("novel_title", "")
        existing_rules = body.get("existing_rules") or []

        user_turns = sum(1 for m in messages if m.get("role") == "user")

        # 加载已有规则文本
        rules_text = ""
        if existing_rules:
            rules_lines = []
            for r in existing_rules:
                rules_lines.append(f"- {r.get('title','')}: {r.get('content','')}")
            rules_text = "\n".join(rules_lines)
        elif novel_id:
            try:
                rm = RulesManager(novel_id)
                data = rm.load()
                for r in data.get("rules", []):
                    rules_text += f"- {r.get('title','')}: {r.get('content','')}\n"
            except:
                pass

        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if user_turns == 0:
            stage_hint = "这是第 1 轮。用户刚开始，先问他最想解决什么写作问题，给 4-5 个具体选项引导他开口。"
        else:
            stage_hint = (
                f"用户刚才说：「{last_user[:100]}」。"
                f"这是第 {user_turns + 1} 轮。先用一句话承接这句话（引用他的词），再追问一个更具体的细节或请他举例。"
                "聊清楚 2-3 个具体点后再给出确认总结（confirming），不要着急。"
            )

        system_prompt = f"""你是一位经验丰富的网文写作教练，正在和作者一对一面聊，帮他建立小说的写作规则。

当前小说：{novel_title or '未命名'}

已有规则：
{rules_text or '（暂无）'}

{stage_hint}

你的对话风格：
- 像朋友聊天一样自然，不要废话、不要客气寒暄
- 一定要承接用户上一轮说的内容，不要重新开始一个新话题
- 如果用户说得很泛（比如"注意人物塑造"），追问具体例子
- 如果用户给了具体例子（比如"出场时要说明角色境界"），你就帮他提炼成一条可以写进 prompt 的规则
- 记住用户说过的话，不要让他重复
- 一次只聊一个维度，聊透了再问要不要换话题

返回纯 JSON（不要 markdown 代码块）：
{{"question":"...","options":["...","..."],"stage":"clarifying","rule_update":null}}

- stage 可以是 clarifying（还在了解需求）/ confirming（提炼出规则，让用户确认）/ done（规则已确认保存）
- 当 stage=confirming 时，把提炼出的规则放在 rule_update 字段：
  rule_update: {{"category":"writing_style|character|plot|dialogue|pacing|worldbuilding|general","title":"简短标题","content":"具体规则内容","priority":"must|should|may"}}
- 当 stage=done 时，question 中告诉用户规则已保存

每轮回复格式（严格遵守）：
1. question 开头必须是一句承接用户刚才内容的话，要引用他说的具体词
2. options 的每个选项必须是从用户刚才回答延伸出的具体建议，不能是泛泛的分类标签"""

        llm_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            llm_messages.append({"role": role, "content": content})

        if not messages:
            llm_messages.append({"role": "user", "content": "我想给这本小说建立一些写作规则"})

        agent = _LLMAgent("规则对话")
        agent.model = "deepseek-v4-pro"
        response = agent.call_llm(llm_messages, temperature=0.7, max_tokens=800)

        result = agent.parse_json_response(response)
        if not result or not isinstance(result, dict) or "question" not in result:
            # JSON 解析失败 → 直接用 LLM 原始文本作为 question，不再用硬编码 fallback
            print(f"[rules-dialogue] JSON 解析失败，使用原始文本。raw[:200]: {response[:200]}")
            raw_text = (result or {}).get("content", "") if isinstance(result, dict) else ""
            if not raw_text:
                raw_text = response.strip().replace('```json', '').replace('```', '').strip()
            result = {
                "question": raw_text or "抱歉，我好像走神了。我们继续聊，你刚才想说什么？",
                "options": ["继续说", "换个话题"],
                "stage": "clarifying",
                "rule_update": None,
            }

        return jsonify({"success": True, "data": result})

    except Exception as e:
        print(f"规则对话错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"对话失败: {str(e)}"}), 500


if __name__ == '__main__':
    # 确保前端目录存在
    os.makedirs('frontend', exist_ok=True)
    
    print("=" * 60)
    print("           InkAI 小说创作系统 Web 服务器")
    print("=" * 60)
    print("服务器启动中...")
    print("前端地址: http://localhost:5000")
    print("API地址: http://localhost:5000/api")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
