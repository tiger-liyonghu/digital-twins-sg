#!/usr/bin/env python3
"""
前端优化立即启动脚本
"""

import os
import json
from pathlib import Path
from datetime import datetime

def analyze_frontend():
    """分析前端现状"""
    print("🔍 分析已部署的前端项目...")
    print("=" * 60)
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        print("❌ 未找到frontend目录")
        return None
    
    # 分析主要文件
    dashboard_file = frontend_dir / "dashboard.html"
    
    if not dashboard_file.exists():
        print("❌ 未找到dashboard.html")
        return None
    
    # 读取dashboard.html大小
    file_size = dashboard_file.stat().st_size / 1024  # KB
    lines = count_lines(dashboard_file)
    
    print(f"📁 项目位置: {frontend_dir}")
    print(f"📄 主要文件: dashboard.html")
    print(f"📏 文件大小: {file_size:.1f} KB")
    print(f"📝 代码行数: {lines} 行")
    
    # 检查问题
    issues = []
    
    if lines > 1000:
        issues.append({
            "severity": "HIGH",
            "issue": "dashboard.html过于庞大",
            "impact": "维护困难，加载性能差",
            "solution": "拆分为模块化组件"
        })
    
    # 检查内联样式
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if '<style>' in content:
            issues.append({
                "severity": "MEDIUM",
                "issue": "内联样式过多",
                "impact": "样式难以维护，缓存效率低",
                "solution": "提取到外部CSS文件"
            })
    
    # 检查内联脚本
    if '<script>' in content and '</script>' in content:
        issues.append({
            "severity": "MEDIUM",
            "issue": "内联脚本过多",
            "impact": "代码组织混乱，维护困难",
            "solution": "提取到外部JS文件"
        })
    
    # 打印问题
    if issues:
        print("\n⚠️ 发现的问题:")
        for issue in issues:
            print(f"  [{issue['severity']}] {issue['issue']}")
            print(f"     影响: {issue['impact']}")
            print(f"     解决方案: {issue['solution']}")
    else:
        print("\n✅ 未发现重大问题")
    
    return {
        "frontend_dir": str(frontend_dir),
        "dashboard_size_kb": file_size,
        "dashboard_lines": lines,
        "issues": issues,
        "analysis_time": datetime.now().isoformat()
    }

def count_lines(file_path):
    """计算文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0

def create_immediate_optimization_plan(analysis):
    """创建立即优化计划"""
    print("\n📋 创建立即优化计划...")
    print("=" * 60)
    
    plan = {
        "timestamp": datetime.now().isoformat(),
        "project": "Digital Twin SG 前端立即优化",
        "analysis_based_on": analysis["analysis_time"],
        "priority_tasks": [],
        "today_tasks": [],
        "week1_tasks": [],
        "success_criteria": {}
    }
    
    # 今天可以完成的任务
    plan["today_tasks"] = [
        {
            "task": "创建优化目录结构",
            "description": "建立模块化的前端结构",
            "estimated_time": "1小时",
            "deliverables": ["优化目录结构", "基础文件"]
        },
        {
            "task": "提取dashboard.html中的CSS",
            "description": "将内联样式提取到外部文件",
            "estimated_time": "2小时",
            "deliverables": ["main.css", "components.css"]
        },
        {
            "task": "创建基础JavaScript模块",
            "description": "提取内联脚本到模块化JS文件",
            "estimated_time": "2小时",
            "deliverables": ["main.js", "dashboard.js", "charts.js"]
        }
    ]
    
    # 第一周任务
    plan["week1_tasks"] = [
        {
            "task": "实现数学严谨性展示",
            "description": "添加统计验证和置信区间显示",
            "estimated_time": "4小时",
            "deliverables": ["validation.js", "统计验证组件"]
        },
        {
            "task": "增强透明度功能",
            "description": "添加数据来源追溯和方法说明",
            "estimated_time": "3小时",
            "deliverables": ["transparency.js", "透明度组件"]
        },
        {
            "task": "优化响应式设计",
            "description": "改进移动端体验",
            "estimated_time": "4小时",
            "deliverables": ["响应式CSS", "移动端优化"]
        },
        {
            "task": "实现懒加载",
            "description": "优化图表和组件加载性能",
            "estimated_time": "3小时",
            "deliverables": ["懒加载系统", "性能优化"]
        }
    ]
    
    # 优先级任务（基于分析结果）
    if analysis["issues"]:
        for issue in analysis["issues"]:
            if issue["severity"] == "HIGH":
                plan["priority_tasks"].append({
                    "priority": "P0",
                    "task": issue["solution"],
                    "reason": issue["issue"],
                    "impact": issue["impact"]
                })
    
    # 成功标准
    plan["success_criteria"] = {
        "performance": {
            "dashboard_size_reduction": "> 50%",
            "css_extraction": "100% 内联样式提取",
            "js_modularization": "> 80% 脚本模块化"
        },
        "product_goals": {
            "mathematical_rigor": "统计验证功能实现",
            "transparency": "数据来源追溯实现",
            "simplicity": "界面复杂度降低30%"
        },
        "user_experience": {
            "loading_time": "< 2秒",
            "mobile_friendly": "移动端评分 > 80",
            "accessibility": "WCAG 2.1基础合规"
        }
    }
    
    # 保存计划
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    reports_dir = project_root / "data" / "frontend_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    plan_file = reports_dir / f"immediate_optimization_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(plan_file, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 优化计划已保存: {plan_file}")
    
    return plan

def create_optimization_structure():
    """创建优化目录结构"""
    print("\n🚀 创建优化目录结构...")
    print("=" * 60)
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    optimized_dir = project_root / "frontend_optimized_v1"
    
    # 如果目录已存在，备份
    if optimized_dir.exists():
        backup_dir = project_root / f"frontend_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"⚠️ 优化目录已存在，备份到: {backup_dir}")
        optimized_dir.rename(backup_dir)
    
    # 创建新目录结构
    dirs_to_create = [
        optimized_dir,
        optimized_dir / "css",
        optimized_dir / "js",
        optimized_dir / "js/modules",
        optimized_dir / "js/utils",
        optimized_dir / "components",
        optimized_dir / "assets",
        optimized_dir / "pages"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 创建: {dir_path.relative_to(project_root)}")
    
    # 创建基础文件
    create_basic_files(optimized_dir)
    
    print(f"\n✅ 优化目录结构创建完成!")
    print(f"📁 位置: {optimized_dir}")
    
    return optimized_dir

def create_basic_files(optimized_dir):
    """创建基础文件"""
    
    # 1. 主HTML文件
    main_html = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新加坡数字孪生 - 优化版 | Singapore Digital Twin</title>
    
    <!-- 核心样式 -->
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/components.css">
    
    <!-- 外部库 -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    
    <!-- 预加载 -->
    <link rel="preload" href="js/main.js" as="script">
</head>
<body>
    <!-- 应用容器 -->
    <div id="app">
        <div class="loading">
            <div class="spinner"></div>
            <p>加载优化版前端...</p>
        </div>
    </div>
    
    <!-- 主脚本 -->
    <script type="module" src="js/main.js"></script>
</body>
</html>"""
    
    with open(optimized_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(main_html)
    
    # 2. 基础CSS
    main_css = """/* main.css - 基础样式 */
:root {
  --bg: #0a0e1a;
  --card: #111827;
  --border: #1e293b;
  --text: #e2e8f0;
  --dim: #94a3b8;
  --muted: #475569;
  --accent: #3b82f6;
  --green: #22c55e;
  --red: #ef4444;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: var(--dim);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式基础 */
@media (max-width: 768px) {
  body { font-size: 13px; }
}"""
    
    with open(optimized_dir / "css" / "main.css", 'w', encoding='utf-8') as f:
        f.write(main_css)
    
    # 3. 主JavaScript文件
    main_js = """// main.js - 应用主入口
import { loadDashboard } from './modules/dashboard.js';
import { initCharts } from './modules/charts.js';
import { initValidation } from './modules/validation.js';

class DigitalTwinApp {
    constructor() {
        this.init();
    }
    
    async init() {
        console.log('🚀 Digital Twin SG 优化版前端启动');
        
        // 初始化模块
        await this.initModules();
        
        // 加载主页面
        await this.loadMainPage();
        
        // 隐藏加载状态
        this.hideLoading();
    }
    
    async initModules() {
        // 初始化验证模块
        initValidation();
        
        // 初始化图表模块
        initCharts();
    }
    
    async loadMainPage() {
        try {
            // 加载仪表盘
            await loadDashboard();
            
            console.log('✅ 仪表盘加载完成');
        } catch (error) {
            console.error('❌ 加载失败:', error);
            this.showError('页面加载失败，请刷新重试');
        }
    }
    
    hideLoading() {
        const loadingEl = document.querySelector('.loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
    
    showError(message) {
        const appEl = document.getElementById('app');
        if (appEl) {
            appEl.innerHTML = \`
                <div class="error">
                    <h3>错误</h3>
                    <p>\${message}</p>
                    <button onclick="location.reload()">重试</button>
                </div>
            \`;
        }
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    new DigitalTwinApp();
});"""
    
    with open(optimized_dir / "js" / "main.js", 'w', encoding='utf-8') as f:
        f.write(main_js)
    
    # 4. 创建模块占位文件
    modules = [
        ("dashboard.js", "// dashboard.js - 仪表盘模块"),
        ("charts.js", "// charts.js - 图表模块"),
        ("validation.js", "// validation.js - 数学验证模块"),
        ("transparency.js", "// transparency.js - 透明度模块"),
        ("api.js", "// api.js - API通信模块")
    ]
    
    for filename, content in modules:
        with open(optimized_dir / "js" / "modules" / filename, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("  📄 创建基础文件完成")

def generate_optimization_summary(analysis, plan, optimized_dir):
    """生成优化总结"""
    print("\n" + "=" * 60)
    print("🎯 前端优化启动总结")
    print("=" * 60)
    
    print(f"📊 分析结果:")
    print(f"  主要文件: dashboard.html ({analysis['dashboard_lines']}行)")
    print(f"  发现问题: {len(analysis['issues'])}个")
    
    print(f"\n📅 优化计划:")
    print(f"  今天任务: {len(plan['today_tasks'])}个")
    print(f"  本周任务: {len(plan['week1_tasks'])}个")
    print(f"  优先级任务: {len(plan['priority_tasks'])}个")
    
    print(f"\n📁 优化结构:")
    print(f"  位置: {optimized_dir}")
    print(f"  包含: HTML, CSS, JS模块, 组件")
    
    print(f"\n🚀 立即开始:")
    print("  1. 提取dashboard.html中的CSS到css/目录")
    print("  2. 提取内联JavaScript到js/modules/")
    print("  3. 创建组件化的HTML结构")
    
    print(f"\n🎯 成功标准:")
    for category, criteria in plan["success_criteria"].items():
        print(f"  {category}:")
        for key, value in criteria.items():
            print(f"    • {key}: {value}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Digital Twin SG 前端优化立即启动")
    print("=" * 60)
    print("目标: 优化已部署的前端项目，对齐五大产品目标")
    
    try:
        # 1. 分析现状
        analysis = analyze_frontend()
        if not analysis:
            return
        
        # 2. 创建优化计划
        plan = create_immediate_optimization_plan(analysis)
        
        # 3. 创建优化结构
        optimized_dir = create_optimization_structure()
        
        # 4. 生成总结
        generate_optimization_summary(analysis, plan, optimized_dir)
        
        print("\n" + "=" * 60)
        print("🎉 前端优化启动完成!")
        print("=" * 60)
        print("\n💡 下一步:")
        print("  1. 开始提取dashboard.html的CSS和JS")
        print("  2. 实现模块化组件")
        print("  3. 添加数学严谨性和透明度功能")
        print(f"\n📁 优化目录: {optimized_dir}")
        
    except Exception as e:
        print(f"\n❌ 优化启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()