"""
InkAI 小说创作系统主程序
提供命令行界面和API接口
"""
import os
import sys
import json
from typing import Dict, Any
from inkai_workflow_optimized import InkAIWorkflowOptimized as InkAIWorkflow


def save_chapter_to_txt(workflow, chapter_data: Dict[str, Any]):
    """保存章节为txt文件"""
    try:
        # 使用数据管理器保存章节
        txt_file = workflow.data_manager.save_chapter_txt(
            workflow.context.novel_id if workflow.context else None, 
            1, 
            chapter_data
        )
        
        if txt_file:
            print(f"✓ 章节已保存为: {txt_file}")
        else:
            print("✗ 保存章节失败")
        
    except Exception as e:
        print(f"✗ 保存章节失败: {e}")

def print_banner():
    """打印程序横幅"""
    print("=" * 60)
    print("           InkAI 智能小说创作系统")
    print("=" * 60)
    print("基于大语言模型的智能小说创作助手")
    print("支持从需求分析到章节生成的完整创作流程")
    print("=" * 60)


def print_menu():
    """打印主菜单"""
    print("\n请选择操作:")
    print("1. 开始创作新小说")
    print("2. 续写现有小说")
    print("3. 查看小说列表")
    print("4. 查看工作流程状态")
    print("5. 查看续写状态")
    print("6. 退出程序")
    print("-" * 40)


def start_new_novel_interactive(workflow: InkAIWorkflow):
    """交互式开始新小说创作"""
    print("\n=== 开始新小说创作 ===")
    
    # 获取用户需求
    title = input("请输入小说标题 (默认: 未命名小说): ").strip()
    if not title:
        title = "未命名小说"
    
    print("\n请输入您的创作需求:")
    print("例如: 想写一部都市悬疑小说，主角是侦探，有推理元素")
    user_requirements = input("需求描述: ").strip()
    
    if not user_requirements:
        print("错误: 请输入创作需求")
        return
    
    # 开始创作流程
    result = workflow.start_new_novel(user_requirements, title)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        return
    
    print(f"\n小说项目创建成功!")
    print(f"项目ID: {result['novel_id']}")
    print(f"下一步: {result['next_step']}")
    
    # 自动进行标签选择
    print("\n正在分析需求并推荐标签...")
    tag_result = workflow.select_tags()
    
    if "error" in tag_result:
        print(f"错误: {tag_result['error']}")
        return
    
    print("\n推荐的标签组合:")
    for category, tags in tag_result["tags"]["selected_tags"].items():
        print(f"  {category}: {', '.join(tags)}")
    
    # 询问用户是否接受推荐标签
    accept = input("\n是否接受推荐的标签? (y/n, 默认y): ").strip().lower()
    if accept in ['n', 'no']:
        print("您可以稍后手动调整标签")
    
    # 继续后续流程
    continue_creation_process(workflow)


def continue_creation_process(workflow: InkAIWorkflow):
    """继续创作流程"""
    print("\n=== 继续创作流程 ===")
    
    while True:
        status = workflow.get_workflow_status()
        current_step = status["current_step"]
        
        print(f"\n当前步骤: {current_step}")
        
        if current_step == "character_creation":
            print("正在创建人物形象...")
            result = workflow.create_characters()
            
            if result["status"] == "needs_improvement":
                print(f"人物质量评估: {result['quality_assessment']['overall_score']}分")
                print("改进建议:")
                for suggestion in result['quality_assessment']['suggestions']:
                    print(f"  - {suggestion}")
                
                improve = input("是否改进人物形象? (y/n, 默认y): ").strip().lower()
                if improve in ['n', 'no']:
                    print("跳过人物改进，继续下一步")
                    workflow.context.set_current_step("storyline_generation")
                else:
                    workflow.improve_character(result['quality_assessment']['suggestions'])
            else:
                print("人物形象创建完成!")
        
        elif current_step == "storyline_generation":
            print("正在生成故事线...")
            result = workflow.generate_storyline()
            
            if result["status"] == "needs_improvement":
                print(f"故事线质量评估: {result['quality_assessment']['overall_score']}分")
                print("改进建议:")
                for suggestion in result['quality_assessment']['suggestions']:
                    print(f"  - {suggestion}")
                
                improve = input("是否改进故事线? (y/n, 默认y): ").strip().lower()
                if improve in ['n', 'no']:
                    print("跳过故事线改进，继续下一步")
                    workflow.workflow_state["step"] = "knowledge_graph_creation"
                else:
                    workflow.improve_storyline(result['quality_assessment']['suggestions'])
            else:
                print("故事线生成完成!")
        
        elif current_step == "knowledge_graph_creation":
            print("正在创建知识图谱...")
            result = workflow.create_knowledge_graph()
            print("知识图谱创建完成!")
        
        elif current_step == "chapter_writing":
            print("正在写作第一章...")
            result = workflow.write_first_chapter()
            
            if "error" in result:
                print(f"错误: {result['error']}")
                break
            
            print("第一章写作完成!")
            print(f"章节标题: {result['chapter']['title']}")
            print(f"字数: {result['quality_assessment'].get('word_count', '未知')}")
            
            # 询问是否查看章节内容
            view = input("是否查看章节内容? (y/n, 默认n): ").strip().lower()
            if view in ['y', 'yes']:
                print("\n" + "="*50)
                print(result['chapter']['content'][:500] + "...")
                print("="*50)
            
            # 询问是否保存章节为txt文件
            save_txt = input("是否保存章节为txt文件? (y/n, 默认y): ").strip().lower()
            if save_txt in ['y', 'yes', '']:
                save_chapter_to_txt(workflow, result['chapter'])
            
            break
        
        elif current_step == "chapter_completed":
            print("第一章创作完成!")
            break
        
        else:
            print(f"未知步骤: {current_step}")
            break


def view_novel_list(workflow: InkAIWorkflow):
    """查看小说列表"""
    print("\n=== 小说列表 ===")
    
    novels = workflow.data_manager.get_novel_list()
    
    if not novels:
        print("暂无小说项目")
        return
    
    for i, novel in enumerate(novels, 1):
        print(f"{i}. {novel['title']}")
        print(f"   项目ID: {novel['novel_id']}")
        print(f"   创建时间: {novel['created_at']}")
        print(f"   状态: {novel['status']}")
        print(f"   章节数: {len(novel.get('chapters', []))}")
        print()


def start_novel_continuation_interactive(workflow: InkAIWorkflow):
    """交互式开始小说续写"""
    print("\n=== 续写现有小说 ===")
    
    # 显示小说列表
    novels = workflow.data_manager.get_novel_list()
    if not novels:
        print("暂无小说项目，请先创建新小说")
        return
    
    print("现有小说列表:")
    for i, novel in enumerate(novels, 1):
        print(f"{i}. {novel['title']} (ID: {novel['novel_id']})")
        print(f"   创建时间: {novel['created_at']}")
        print(f"   章节数: {len(novel.get('chapters', []))}")
        print()
    
    # 获取用户选择
    try:
        choice = input("请选择要续写的小说编号: ").strip()
        novel_index = int(choice) - 1
        
        if novel_index < 0 or novel_index >= len(novels):
            print("无效选择")
            return
        
        selected_novel = novels[novel_index]
        novel_id = selected_novel['novel_id']
        
    except ValueError:
        print("请输入有效的数字")
        return
    
    # 获取续写需求
    print(f"\n您选择了小说: {selected_novel['title']}")
    print("请输入续写需求 (可选，直接回车跳过):")
    print("例如: 希望加快节奏，进入高潮部分")
    user_requirements = input("续写需求: ").strip()
    
    # 开始续写流程
    result = workflow.start_novel_continuation(novel_id, user_requirements)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        return
    
    print(f"\n续写项目启动成功!")
    print(f"小说标题: {result['novel_title']}")
    print(f"当前章节数: {result['chapter_count']}")
    print(f"下一步: {result['next_step']}")
    
    # 继续续写流程
    continue_continuation_process(workflow)


def continue_continuation_process(workflow: InkAIWorkflow):
    """继续续写流程"""
    print("\n=== 继续续写流程 ===")
    
    while True:
        status = workflow.get_continuation_status()
        current_step = status["current_step"]
        
        print(f"\n当前步骤: {current_step}")
        
        if current_step == "storyline_generation":
            print("正在生成续写故事线...")
            result = workflow.generate_continuation_storyline()
            
            if "error" in result:
                print(f"错误: {result['error']}")
                break
            
            print("故事线生成完成!")
            storyline = result["storyline"]
            print(f"章节标题: {storyline.get('chapter_title', '未知')}")
            print(f"场景设定: {storyline.get('scene_setting', {}).get('location', '未知')}")
        
        elif current_step == "quality_assessment":
            print("正在评估故事线质量...")
            result = workflow.assess_continuation_quality("storyline")
            
            if "error" in result:
                print(f"错误: {result['error']}")
                break
            
            quality_assessment = result["quality_assessment"]
            print(f"故事线质量评估: {quality_assessment['overall_score']}分")
            
            if quality_assessment.get("is_high_quality", False):
                print("故事线质量评估通过，继续下一步")
            else:
                print("故事线质量评估未通过，改进建议:")
                for suggestion in quality_assessment.get("suggestions", []):
                    print(f"  - {suggestion}")
                
                improve = input("是否改进故事线? (y/n, 默认y): ").strip().lower()
                if improve in ['n', 'no']:
                    print("跳过故事线改进，继续下一步")
                    workflow.continuation_state["step"] = "chapter_writing"
                else:
                    print("正在改进故事线...")
                    improve_result = workflow.improve_continuation_storyline()
                    
                    if "error" in improve_result:
                        print(f"改进失败: {improve_result['error']}")
                        workflow.continuation_state["step"] = "chapter_writing"
                    else:
                        print("故事线改进完成!")
                        improvement_notes = improve_result["improvement_notes"]
                        print(f"原分数: {improvement_notes['original_score']}分")
                        print("主要改进:")
                        for suggestion in improvement_notes["improvement_suggestions"][:3]:  # 显示前3个建议
                            print(f"  - {suggestion}")
                        
                        # 改进后会自动重新评估，所以不需要手动设置状态
        
        elif current_step == "chapter_writing":
            print("正在写作续写章节...")
            result = workflow.write_continuation_chapter()
            
            if "error" in result:
                print(f"错误: {result['error']}")
                break
            
            print("续写章节写作完成!")
            chapter_content = result["chapter_content"]
            print(f"章节标题: {chapter_content.get('title', '未知')}")
            print(f"字数: {result['word_count']}")
            
            # 询问是否查看章节内容
            view = input("是否查看章节内容? (y/n, 默认n): ").strip().lower()
            if view in ['y', 'yes']:
                print("\n" + "="*50)
                content = chapter_content.get("content", "")
                print(content[:500] + "..." if len(content) > 500 else content)
                print("="*50)
        
        elif current_step == "chapter_quality_assessment":
            print("正在评估章节质量...")
            result = workflow.assess_continuation_quality("story")
            
            if "error" in result:
                print(f"错误: {result['error']}")
                break
            
            quality_assessment = result["quality_assessment"]
            print(f"章节质量评估: {quality_assessment['overall_score']}分")
            
            if quality_assessment.get("is_high_quality", False):
                print("章节质量评估通过，可以保存")
            else:
                print("章节质量评估未通过，改进建议:")
                for suggestion in quality_assessment.get("suggestions", []):
                    print(f"  - {suggestion}")
                
                improve = input("是否改进章节内容? (y/n, 默认y): ").strip().lower()
                if improve in ['n', 'no']:
                    print("跳过章节改进，直接保存")
                    workflow.continuation_state["step"] = "chapter_completed"
                else:
                    print("章节改进功能开发中，暂时跳过")
                    workflow.continuation_state["step"] = "chapter_completed"
        
        elif current_step == "chapter_completed":
            print("正在保存续写章节...")
            result = workflow.save_continuation_chapter()
            
            if "error" in result:
                print(f"错误: {result['error']}")
                break
            
            print("续写章节保存完成!")
            print(f"章节号: {result['chapter_number']}")
            print(f"章节标题: {result['chapter_title']}")
            
            # 询问是否继续续写
            continue_write = input("是否继续续写下一章? (y/n, 默认n): ").strip().lower()
            if continue_write in ['y', 'yes']:
                # 重新开始续写流程
                novel_id = workflow.continuation_state["novel_id"]
                user_requirements = workflow.continuation_state["user_requirements"]
                workflow.start_novel_continuation(novel_id, user_requirements)
            else:
                print("续写完成!")
                break
        
        else:
            print(f"未知步骤: {current_step}")
            break


def view_workflow_status(workflow: InkAIWorkflow):
    """查看工作流程状态"""
    print("\n=== 工作流程状态 ===")
    
    status = workflow.get_workflow_status()
    
    if not status["novel_id"]:
        print("当前没有活跃的小说项目")
        return
    
    print(f"项目ID: {status['novel_id']}")
    print(f"当前步骤: {status['current_step']}")
    
    # 显示工作流程状态详情
    workflow_state = status["workflow_state"]
    if "title" in workflow_state:
        print(f"小说标题: {workflow_state['title']}")
    if "user_requirements" in workflow_state:
        print(f"用户需求: {workflow_state['user_requirements']}")
    if "tags" in workflow_state:
        print("已选择标签:")
        for category, tags in workflow_state["tags"].get("selected_tags", {}).items():
            print(f"  {category}: {', '.join(tags)}")


def view_continuation_status(workflow: InkAIWorkflow):
    """查看续写状态"""
    print("\n=== 续写状态 ===")
    
    status = workflow.get_continuation_status()
    
    if status["status"] == "not_started":
        print("当前没有活跃的续写项目")
        return
    
    print(f"小说ID: {status['novel_id']}")
    print(f"小说标题: {status['novel_title']}")
    print(f"当前章节数: {status['chapter_count']}")
    print(f"当前步骤: {status['current_step']}")
    print(f"用户需求: {status['user_requirements']}")
    
    # 询问是否继续续写流程
    continue_work = input("是否继续续写流程? (y/n, 默认n): ").strip().lower()
    if continue_work in ['y', 'yes']:
        continue_continuation_process(workflow)


def main():
    """主程序入口"""
    print_banner()
    
    # 初始化工作流程
    workflow = InkAIWorkflow()
    
    while True:
        print_menu()
        
        try:
            choice = input("请输入选择 (1-6): ").strip()
            
            if choice == "1":
                start_new_novel_interactive(workflow)
            elif choice == "2":
                start_novel_continuation_interactive(workflow)
            elif choice == "3":
                view_novel_list(workflow)
            elif choice == "4":
                view_workflow_status(workflow)
            elif choice == "5":
                view_continuation_status(workflow)
            elif choice == "6":
                print("感谢使用 InkAI 小说创作系统!")
                break
            else:
                print("无效选择，请重新输入")
        
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print("请重试或联系技术支持")


if __name__ == "__main__":
    main()
