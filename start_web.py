#!/usr/bin/env python3
"""
InkAI 小说创作系统 Web 服务器启动脚本
"""
import os
import sys
import subprocess

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import flask_cors
        print("✓ Flask 依赖检查通过")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("           InkAI 小说创作系统 Web 服务器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查必要文件
    required_files = ['app.py', 'inkai_workflow_optimized.py', 'data_manager.py', 'config.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"✗ 缺少必要文件: {file}")
            sys.exit(1)
    
    print("✓ 所有必要文件检查通过")
    
    # 确保前端目录存在
    if not os.path.exists('frontend'):
        print("✗ 前端目录不存在")
        sys.exit(1)
    
    print("✓ 前端目录检查通过")
    
    # 启动服务器
    print("\n正在启动 Web 服务器...")
    print("前端地址: http://localhost:5000")
    print("API地址: http://localhost:5000/api")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        # 导入并运行Flask应用
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except Exception as e:
        print(f"\n✗ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
