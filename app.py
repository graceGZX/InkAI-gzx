"""
InkAI 小说创作系统 Web API 服务器
提供RESTful API接口供前端调用
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from typing import Dict, Any
from inkai_workflow_optimized import InkAIWorkflowOptimized as InkAIWorkflow
from workflow_context import WorkflowContext
import config

# 导入智能体（避免重复导入）
from agents import QualityAssessorAgent, CharacterCreatorAgent
from quick_continuation_executor import get_executor, QuickContinuationProgress

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
