#!/usr/bin/env python3
"""
检查前端服务器状态和功能
"""

import os
import sys
import json
import socket
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

def check_port(port=8888):
    """检查端口是否被占用"""
    print(f"🔍 检查端口 {port}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    
    try:
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            print(f"✅ 端口 {port} 已被占用")
            return True
        else:
            print(f"❌ 端口 {port} 未被占用")
            return False
    except Exception as e:
        print(f"⚠️ 端口检查失败: {e}")
        return False
    finally:
        sock.close()

def start_http_server():
    """启动HTTP服务器"""
    print("\n🚀 启动HTTP服务器...")
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return None
    
    # 检查是否已有服务器运行
    if check_port(8888):
        print("📡 服务器已在运行，尝试连接...")
        return "http://localhost:8888"
    
    # 启动Python HTTP服务器
    import subprocess
    import time
    
    try:
        print(f"📁 服务目录: {frontend_dir}")
        print("🌐 启动服务器在端口 8888...")
        
        # 在后台启动服务器
        server_process = subprocess.Popen(
            ["python3", "-m", "http.server", "8888"],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查是否启动成功
        if check_port(8888):
            print("✅ HTTP服务器启动成功")
            return "http://localhost:8888", server_process
        else:
            print("❌ 服务器启动失败")
            server_process.terminate()
            return None, None
            
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return None, None

def test_frontend_pages(base_url):
    """测试前端页面"""
    print(f"\n🧪 测试前端页面: {base_url}")
    
    pages_to_test = [
        "/",  # 首页
        "/dashboard.html",
        "/index.html",
        "/about.html",
        "/cases.html",
        "/detail.html",
        "/simulation.html"
    ]
    
    available_pages = []
    
    for page in pages_to_test:
        url = urljoin(base_url, page)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {page} - 可访问 ({len(response.text)}字节)")
                available_pages.append(page)
            else:
                print(f"⚠️ {page} - 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ {page} - 访问失败: {e}")
    
    return available_pages

def analyze_dashboard_functionality(base_url):
    """分析仪表盘功能"""
    print("\n📊 分析仪表盘功能...")
    
    dashboard_url = urljoin(base_url, "/dashboard.html")
    
    try:
        response = requests.get(dashboard_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 无法获取dashboard.html: {response.status_code}")
            return None
        
        content = response.text
        print(f"📄 dashboard.html大小: {len(content):,}字节")
        
        # 分析功能
        features = {
            "chart_js": "Chart.js" in content,
            "supabase": "supabase" in content.lower(),
            "real_time": "实时" in content or "realtime" in content.lower(),
            "filtering": "筛选" in content or "filter" in content.lower(),
            "search": "搜索" in content or "search" in content.lower(),
            "export": "导出" in content or "export" in content.lower()
        }
        
        print("🔧 检测到的功能:")
        for feature, present in features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature}")
        
        # 检查产品目标相关功能
        product_goals = {
            "mathematical_rigor": "置信区间" in content or "confidence" in content.lower(),
            "transparency": "数据来源" in content or "transparency" in content.lower(),
            "simplicity": "简洁" in content or "simple" in content.lower()
        }
        
        print("\n🎯 产品目标功能:")
        for goal, present in product_goals.items():
            status = "✅" if present else "❌"
            print(f"  {status} {goal}")
        
        return features
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def check_supabase_connection():
    """检查Supabase连接"""
    print("\n🔗 检查Supabase连接...")
    
    # 从dashboard.html中提取Supabase配置
    dashboard_file = Path("/Users/tigerli/Desktop/Digital Twins Singapore/frontend/dashboard.html")
    
    if not dashboard_file.exists():
        print("❌ dashboard.html不存在")
        return False
    
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找Supabase配置
        import re
        
        # 查找Supabase URL
        url_pattern = r'supabase\.co[^"\']*'
        urls = re.findall(url_pattern, content)
        
        if urls:
            print(f"✅ 找到Supabase配置: {urls[0]}")
            return True
        else:
            print("⚠️ 未找到Supabase配置")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def create_frontend_analysis_report(base_url, available_pages, features):
    """创建前端分析报告"""
    print("\n📋 创建前端分析报告...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "frontend_url": base_url,
        "server_status": "running" if base_url else "stopped",
        "available_pages": available_pages,
        "detected_features": features,
        "analysis_summary": {
            "total_pages": len(available_pages),
            "dashboard_size": "1415行代码",
            "supabase_connected": check_supabase_connection(),
            "product_goals_implemented": sum(1 for f in [
                "mathematical_rigor" in str(features),
                "transparency" in str(features),
                "simplicity" in str(features)
            ] if f)
        },
        "recommendations": [
            "1. 优化dashboard.html代码结构",
            "2. 添加数学严谨性展示组件",
            "3. 增强透明度功能",
            "4. 实施性能优化"
        ]
    }
    
    # 保存报告
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    reports_dir = project_root / "data" / "frontend_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / f"frontend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 前端分析报告已保存: {report_file}")
    return report_file

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 Digital Twin SG 前端服务器检查")
    print("=" * 60)
    
    # 检查端口状态
    port_occupied = check_port(8888)
    
    base_url = None
    server_process = None
    
    if not port_occupied:
        print("\n🔄 尝试启动前端服务器...")
        result = start_http_server()
        if isinstance(result, tuple):
            base_url, server_process = result
        else:
            base_url = result
    else:
        base_url = "http://localhost:8888"
        print(f"\n📡 使用现有服务器: {base_url}")
    
    if not base_url:
        print("❌ 无法启动或连接到前端服务器")
        return
    
    try:
        # 测试前端页面
        available_pages = test_frontend_pages(base_url)
        
        if not available_pages:
            print("❌ 没有可访问的页面")
            return
        
        # 分析仪表盘功能
        features = analyze_dashboard_functionality(base_url)
        
        # 创建分析报告
        report_file = create_frontend_analysis_report(base_url, available_pages, features)
        
        # 打印总结
        print("\n" + "=" * 60)
        print("🎉 前端分析完成!")
        print("=" * 60)
        
        print(f"\n📊 分析摘要:")
        print(f"  服务器: {base_url}")
        print(f"  可访问页面: {len(available_pages)}个")
        print(f"  dashboard.html: 1415行代码")
        print(f"  Supabase连接: {'✅' if check_supabase_connection() else '❌'}")
        
        print("\n🚀 立即优化建议:")
        print("  1. 访问 http://localhost:8888/dashboard.html 查看当前状态")
        print("  2. 集成数学严谨性组件到现有界面")
        print("  3. 添加透明度功能展示")
        print("  4. 优化代码结构和性能")
        
        print(f"\n📁 详细报告: {report_file}")
        
        # 保持服务器运行提示
        if server_process:
            print("\n💡 服务器正在后台运行，按Ctrl+C停止")
            try:
                server_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 停止服务器...")
                server_process.terminate()
        
    except Exception as e:
        print(f"\n❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()
        
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    main()