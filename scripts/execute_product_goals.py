#!/usr/bin/env python3
"""
立即执行产品目标推进计划
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)

def check_project_status():
    """检查项目状态"""
    print_header("项目状态检查")
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    
    # 检查关键目录
    key_dirs = [
        ("frontend", "前端目录"),
        ("data", "数据目录"),
        ("engine", "引擎目录"),
        ("scripts", "脚本目录"),
        ("docs", "文档目录")
    ]
    
    for dir_name, description in key_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {description}: {dir_path}")
        else:
            print(f"❌ {description}: 不存在")
    
    # 检查关键文件
    key_files = [
        ("frontend/dashboard.html", "主仪表盘"),
        ("data/output/agents_172k_v3_preview.csv", "172K Agents数据"),
        (".env", "环境配置"),
        ("docs/product_goals_focus_plan.md", "产品目标计划")
    ]
    
    for file_path, description in key_files:
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size / 1024  # KB
            print(f"✅ {description}: {size:.1f}KB")
        else:
            print(f"❌ {description}: 不存在")
    
    return True

def analyze_frontend_for_optimization():
    """分析前端优化需求"""
    print_header("前端优化需求分析")
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    dashboard_file = project_root / "frontend" / "dashboard.html"
    
    if not dashboard_file.exists():
        print("❌ dashboard.html 不存在")
        return False
    
    # 分析文件大小
    lines = 0
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        lines = sum(1 for _ in f)
    
    size_kb = dashboard_file.stat().st_size / 1024
    
    print(f"📊 dashboard.html 分析:")
    print(f"  行数: {lines} 行")
    print(f"  大小: {size_kb:.1f} KB")
    print(f"  状态: {'过于庞大' if lines > 1000 else '正常'}")
    
    # 检查内联代码
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        has_inline_css = '<style>' in content
        has_inline_js = '<script>' in content and '</script>' in content
        
        print(f"\n🔍 代码质量检查:")
        print(f"  内联CSS: {'是' if has_inline_css else '否'}")
        print(f"  内联JS: {'是' if has_inline_js else '否'}")
        
        if has_inline_css or has_inline_js:
            print("  ⚠️ 建议: 提取内联代码到外部文件")
    
    return True

def create_immediate_optimization_tasks():
    """创建立即优化任务"""
    print_header("立即优化任务创建")
    
    tasks = [
        {
            "id": "OPT-001",
            "task": "CSS提取和模块化",
            "description": "从dashboard.html提取所有CSS到外部文件",
            "priority": "P0",
            "estimated_time": "2小时",
            "steps": [
                "1. 创建css/目录结构",
                "2. 提取<style>标签内容",
                "3. 提取内联style属性",
                "4. 按功能分类CSS",
                "5. 创建设计令牌系统"
            ]
        },
        {
            "id": "OPT-002",
            "task": "JavaScript模块化",
            "description": "提取内联JavaScript到模块化文件",
            "priority": "P0",
            "estimated_time": "3小时",
            "steps": [
                "1. 创建js/modules/目录",
                "2. 提取<script>标签内容",
                "3. 按功能模块化",
                "4. 添加错误处理",
                "5. 优化性能"
            ]
        },
        {
            "id": "OPT-003",
            "task": "数学严谨性组件",
            "description": "创建统计验证和置信区间显示",
            "priority": "P1",
            "estimated_time": "2小时",
            "steps": [
                "1. 创建validation-panel.html",
                "2. 实现置信区间显示",
                "3. 添加统计验证功能",
                "4. 创建方法说明",
                "5. 添加局限性标注"
            ]
        },
        {
            "id": "OPT-004",
            "task": "透明度系统",
            "description": "创建数据来源追溯和透明度展示",
            "priority": "P1",
            "estimated_time": "2小时",
            "steps": [
                "1. 创建transparency-panel.html",
                "2. 实现数据来源追溯",
                "3. 添加方法透明度",
                "4. 创建质量验证显示",
                "5. 添加审计日志"
            ]
        }
    ]
    
    print("📋 优化任务清单:")
    for task in tasks:
        print(f"\n[{task['priority']}] {task['task']}")
        print(f"   描述: {task['description']}")
        print(f"   预计时间: {task['estimated_time']}")
        print(f"   步骤:")
        for step in task['steps']:
            print(f"     {step}")
    
    # 保存任务清单
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    tasks_dir = project_root / "data" / "optimization_tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    tasks_file = tasks_dir / f"immediate_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "tasks": tasks,
            "total_estimated_time": "9小时",
            "priority_order": ["OPT-001", "OPT-002", "OPT-003", "OPT-004"]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 任务清单已保存: {tasks_file}")
    
    return tasks

def setup_optimization_environment():
    """设置优化环境"""
    print_header("优化环境设置")
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    
    # 创建优化目录结构
    optimized_dir = project_root / "frontend_optimized_v2"
    
    if optimized_dir.exists():
        print(f"⚠️ 优化目录已存在: {optimized_dir}")
        backup_dir = project_root / f"frontend_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"  创建备份: {backup_dir}")
        optimized_dir.rename(backup_dir)
    
    # 创建新目录结构
    dirs_to_create = [
        optimized_dir,
        optimized_dir / "css",
        optimized_dir / "css/components",
        optimized_dir / "css/layout",
        optimized_dir / "css/validation",
        optimized_dir / "css/transparency",
        optimized_dir / "js",
        optimized_dir / "js/modules",
        optimized_dir / "js/modules/validation",
        optimized_dir / "js/modules/transparency",
        optimized_dir / "js/modules/charts",
        optimized_dir / "js/utils",
        optimized_dir / "components",
        optimized_dir / "components/validation",
        optimized_dir / "components/transparency",
        optimized_dir / "components/ui",
        optimized_dir / "assets",
        optimized_dir / "assets/images",
        optimized_dir / "assets/fonts"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 创建: {dir_path.relative_to(project_root)}")
    
    # 创建基础文件
    create_basic_files(optimized_dir)
    
    print(f"\n✅ 优化环境设置完成: {optimized_dir}")
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
    <link rel="stylesheet" href="css/layout/main.css">
    <link rel="stylesheet" href="css/components/ui.css">
    <link rel="stylesheet" href="css/validation/validation.css">
    <link rel="stylesheet" href="css/transparency/transparency.css">
    
    <!-- 外部库 -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    
    <!-- 预加载 -->
    <link rel="preload" href="js/main.js" as="script">
    <link rel="preconnect" href="https://rndfpyuuredtqncegygi.supabase.co">
</head>
<body>
    <!-- 应用容器 -->
    <div id="app">
        <!-- 导航栏 -->
        <div id="nav-container"></div>
        
        <!-- 主内容 -->
        <main class="container">
            <!-- 数学严谨性面板 -->
            <div id="validation-container"></div>
            
            <!-- 透明度面板 -->
            <div id="transparency-container"></div>
            
            <!-- 仪表盘内容 -->
            <div id="dashboard-container">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>加载优化版前端...</p>
                </div>
            </div>
        </main>
        
        <!-- 页脚 -->
        <div id="footer-container"></div>
    </div>
    
    <!-- 主脚本 -->
    <script type="module" src="js/main.js"></script>
    
    <!-- 产品目标模块 -->
    <script type="module" src="js/modules/validation/main.js"></script>
    <script type="module" src="js/modules/transparency/main.js"></script>
    <script type="module" src="js/modules/charts/main.js"></script>
</body>
</html>"""
    
    with open(optimized_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(main_html)
    
    # 2. 主JavaScript文件
    main_js = """// main.js - 应用主入口
import { initValidation } from './modules/validation/main.js';
import { initTransparency } from './modules/transparency/main.js';
import { initCharts } from './modules/charts/main.js';
import { loadDashboard } from './modules/dashboard/main.js';

class DigitalTwinApp {
    constructor() {
        this.init();
    }
    
    async init() {
        console.log('🚀 Digital Twin SG 优化版前端启动');
        console.log('🎯 产品目标: 数学严谨 + 透明度 + 简洁可信');
        
        try {
            // 初始化产品目标模块
            await this.initProductGoalModules();
            
            // 加载主内容
            await this.loadMainContent();
            
            // 隐藏加载状态
            this.hideLoading();
            
            console.log('✅ 应用初始化完成');
        } catch (error) {
            console.error('❌ 初始化失败:', error);
            this.showError('应用初始化失败，请刷新重试');
        }
    }
    
    async initProductGoalModules() {
        // 1. 数学严谨性模块
        initValidation();
        
        // 2. 透明度模块
        initTransparency();
        
        // 3. 图表模块
        initCharts();
        
        console.log('✅ 产品目标模块初始化完成');
    }
    
    async loadMainContent() {
        // 加载仪表盘
        await loadDashboard();
        
        console.log('✅ 主内容加载完成');
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
                <div class="error-container">
                    <h3>应用错误</h3>
                    <p>\${message}</p>
                    <button onclick="location.reload()" class="retry-btn">重试</button>
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
    
    # 3. 基础CSS文件
    main_css = """/* main.css - 基础布局样式 */
:root {
  /* 设计令牌 - 建立信任 */
  --bg: #0a0e1a;
  --card: #111827;
  --border: #1e293b;
  --text: #e2e8f0;
  --dim: #94a3b8;
  --muted: #475569;
  
  /* 产品目标颜色 */
  --validation-high: #22c55e;      /* 数学严谨 - 高置信度 */
  --validation-medium: #eab308;    /* 数学严谨 - 中等 */
  --validation-low: #ef4444;       /* 数学严谨 - 需要注意 */
  
  --transparency-verified: #06b6d4; /* 透明度 - 已验证 */
  --transparency-pending: #f97316;  /* 透明度 - 待验证 */
  
  --trust-primary: #3b82f6;        /* 简洁可信 - 主要 */
  --trust-secondary: #8b5cf6;      /* 简洁可信 - 次要 */
  
  /* 响应式断点 */
  --breakpoint-mobile: 640px;
  --breakpoint-tablet: 768px;
  --breakpoint-desktop: 1024px;
  --breakpoint-wide: 1280px;
}

/* 基础重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
}

/* 容器 */
.container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 加载状态 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--dim);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--trust-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 错误容器 */
.error-container {
  text-align: center;
  padding: 48px 24px;
  max-width: 600px;
  margin: 0 auto;
}

.error-container h3 {
  color: var(--validation-low);
  margin-bottom: 16px;
}

.retry-btn {
  background: var(--trust-primary);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 24px;
}

.retry-btn:hover {
  background: #2563eb;
}

/* 响应式 */
@media (max-width: 768px) {
  .container {
    padding: 0 16px;
  }
  
  body {
    font-size: 13px;
  }
}"""
    
    with open(optimized_dir / "css" / "layout" / "main.css", 'w', encoding='utf-8') as f:
        f.write(main_css)
    
    print("  📄 创建基础文件完成")

def generate_execution_plan(tasks, optimized_dir):
    """生成执行计划"""
    print_header("立即执行计划")
    
    print("🚀 今天可以立即开始的任务:")
    print("=" * 50)
    
    for task in tasks[:2]:  # 前2个P0任务
        print(f"\n[{task['priority']}] {task['task']}")
        print(f"   预计时间: {task['estimated_time']}")
        print(f"   输出目录: {optimized_dir}")
        print(f"   具体步骤:")
        for i, step in enumerate(task['steps'], 1):
            print(f"     {i}. {step}")
    
    print("\n🎯 产品目标对齐:")
    print("   • OPT-001/002: 支持'简洁可信'目标")
    print("   • OPT-003: 支持'数学严谨'目标")
    print("   • OPT-004: 支持'真实不撒谎'目标")
    
