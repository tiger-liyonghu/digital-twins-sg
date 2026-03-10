#!/usr/bin/env python3
"""
前端优化启动脚本 - 立即开始优化已部署的前端项目
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class FrontendOptimizer:
    """前端优化器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.frontend_dir = self.project_root / "frontend"
        self.optimized_dir = self.project_root / "frontend_optimized"
        self.reports_dir = self.project_root / "data" / "frontend_reports"
        
        # 创建目录
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def run_performance_audit(self):
        """运行性能审计"""
        print("📊 运行前端性能审计...")
        print("=" * 60)
        
        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "audit_type": "frontend_performance_baseline",
            "files_analyzed": [],
            "performance_metrics": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # 分析文件结构
        html_files = list(self.frontend_dir.glob("*.html"))
        js_files = list(self.frontend_dir.glob("**/*.js"))
        css_inline = 0
        
        audit_results["files_analyzed"] = [
            {
                "file": str(f.relative_to(self.frontend_dir)),
                "size_kb": f.stat().st_size / 1024,
                "lines": self.count_lines(f)
            }
            for f in html_files + js_files
        ]
        
        # 分析dashboard.html (主要问题文件)
        dashboard_file = self.frontend_dir / "dashboard.html"
        if dashboard_file.exists():
            lines = self.count_lines(dashboard_file)
            size_kb = dashboard_file.stat().st_size / 1024
            
            audit_results["performance_metrics"]["dashboard"] = {
                "lines": lines,
                "size_kb": size_kb,
                "is_monolithic": lines > 1000,
                "has_inline_css": self.has_inline_css(dashboard_file),
                "has_inline_js": self.has_inline_js(dashboard_file)
            }
            
            if lines > 1000:
                audit_results["issues_found"].append({
                    "severity": "HIGH",
                    "issue": "dashboard.html过于庞大",
                    "details": f"{lines}行代码，{size_kb:.1f}KB",
                    "impact": "维护困难，加载性能差"
                })
                audit_results["recommendations"].append({
                    "priority": "P0",
                    "action": "拆分dashboard.html为模块化组件",
                    "reason": "代码过于庞大，影响可维护性和性能"
                })
        
        # 检查内联样式和脚本
        for html_file in html_files:
            if self.has_inline_css(html_file):
                css_inline += 1
        
        if css_inline > 0:
            audit_results["issues_found"].append({
                "severity": "MEDIUM",
                "issue": "内联样式过多",
                "details": f"{css_inline}个HTML文件包含内联样式",
                "impact": "样式难以维护，缓存效率低"
            })
            audit_results["recommendations"].append({
                "priority": "P1",
                "action": "提取内联样式到外部CSS文件",
                "reason": "提高样式可维护性和缓存效率"
            })
        
        # 保存审计报告
        report_file = self.reports_dir / f"performance_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(audit_results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 性能审计报告已保存: {report_file}")
        
        # 打印摘要
        print("\n📋 审计摘要:")
        print(f"  分析文件: {len(audit_results['files_analyzed'])}个")
        print(f"  发现问题: {len(audit_results['issues_found'])}个")
        
        for issue in audit_results["issues_found"]:
            print(f"  [{issue['severity']}] {issue['issue']}")
        
        return audit_results
    
    def count_lines(self, file_path):
        """计算文件行数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def has_inline_css(self, file_path):
        """检查是否有内联样式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return '<style>' in content
        except:
            return False
    
    def has_inline_js(self, file_path):
        """检查是否有内联脚本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return '<script>' in content and '</script>' in content
        except:
            return False
    
    def create_optimization_plan(self, audit_results):
        """创建优化计划"""
        print("\n📋 创建前端优化计划...")
        print("=" * 60)
        
        plan = {
            "timestamp": datetime.now().isoformat(),
            "project": "Digital Twin SG Frontend Optimization",
            "based_on_audit": audit_results.get("timestamp", ""),
            "phases": [],
            "immediate_actions": [],
            "success_metrics": {}
        }
        
        # 阶段1: 紧急优化 (本周)
        phase1 = {
            "name": "紧急优化 - 代码拆分和性能",
            "duration": "1周",
            "tasks": [
                {
                    "id": "T1.1",
                    "task": "拆分dashboard.html为模块化组件",
                    "priority": "P0",
                    "estimated_hours": 8,
                    "deliverables": ["模块化组件结构", "分离的CSS/JS文件"]
                },
                {
                    "id": "T1.2",
                    "task": "提取内联样式到外部CSS文件",
                    "priority": "P0",
                    "estimated_hours": 4,
                    "deliverables": ["main.css", "components.css"]
                },
                {
                    "id": "T1.3",
                    "task": "实现基础懒加载",
                    "priority": "P1",
                    "estimated_hours": 6,
                    "deliverables": ["懒加载图表", "按需加载组件"]
                }
            ]
        }
        
        # 阶段2: 核心优化 (2周)
        phase2 = {
            "name": "核心优化 - 用户体验和产品目标",
            "duration": "2周",
            "tasks": [
                {
                    "id": "T2.1",
                    "task": "实现数学严谨性展示",
                    "priority": "P1",
                    "estimated_hours": 8,
                    "deliverables": ["统计验证组件", "置信区间显示"]
                },
                {
                    "id": "T2.2",
                    "task": "增强透明度功能",
                    "priority": "P1",
                    "estimated_hours": 6,
                    "deliverables": ["数据来源追溯", "方法说明工具"]
                },
                {
                    "id": "T2.3",
                    "task": "优化响应式设计",
                    "priority": "P1",
                    "estimated_hours": 8,
                    "deliverables": ["移动端优化", "响应式组件"]
                }
            ]
        }
        
        # 阶段3: 高级优化 (3-4周)
        phase3 = {
            "name": "高级优化 - 技术栈和监控",
            "duration": "3-4周",
            "tasks": [
                {
                    "id": "T3.1",
                    "task": "考虑技术栈升级",
                    "priority": "P2",
                    "estimated_hours": 12,
                    "deliverables": ["技术评估报告", "迁移方案"]
                },
                {
                    "id": "T3.2",
                    "task": "建立性能监控",
                    "priority": "P2",
                    "estimated_hours": 8,
                    "deliverables": ["监控仪表板", "告警系统"]
                },
                {
                    "id": "T3.3",
                    "task": "创建用户体验实验室",
                    "priority": "P2",
                    "estimated_hours": 10,
                    "deliverables": ["A/B测试框架", "用户反馈系统"]
                }
            ]
        }
        
        plan["phases"] = [phase1, phase2, phase3]
        
        # 立即行动
        plan["immediate_actions"] = [
            {
                "action": "创建优化开发环境",
                "owner": "开发团队",
                "deadline": "今天"
            },
            {
                "action": "开始dashboard.html代码分析",
                "owner": "开发团队",
                "deadline": "今天"
            },
            {
                "action": "制定详细周计划",
                "owner": "项目经理",
                "deadline": "明天"
            }
        ]
        
        # 成功指标
        plan["success_metrics"] = {
            "performance": {
                "lighthouse_score": "> 90",
                "first_contentful_paint": "< 1.5s",
                "largest_contentful_paint": "< 2.5s",
                "cumulative_layout_shift": "< 0.1"
            },
            "code_quality": {
                "file_size_reduction": "> 30%",
                "modularity_score": "> 80%",
                "maintainability_index": "> 70"
            },
            "user_experience": {
                "satisfaction_score": "> 4.5/5",
                "mobile_experience": "> 4/5",
                "trust_indicator": "> 90%"
            }
        }
        
        # 保存计划
        plan_file = self.reports_dir / f"optimization_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 优化计划已保存: {plan_file}")
        
        # 打印计划摘要
        print("\n📅 优化计划摘要:")
        print(f"  总阶段: {len(plan['phases'])}个")
        print(f"  总任务: {sum(len(p['tasks']) for p in plan['phases'])}个")
        print(f"  总预计时间: {sum(sum(t['estimated_hours'] for t in p['tasks']) for p in plan['phases'])}小时")
        
        print("\n🚀 阶段1 - 紧急优化 (本周):")
        for task in phase1["tasks"]:
            print(f"  [{task['priority']}] {task['task']} ({task['estimated_hours']}小时)")
        
        print("\n🎯 立即行动 (今天):")
        for action in plan["immediate_actions"]:
            print(f"  • {action['action']} - {action['owner']} ({action['deadline']})")
        
        return plan
    
    def start_phase1_optimization(self):
        """开始阶段1优化 - 创建基础结构"""
        print("\n🚀 开始阶段1优化 - 创建基础结构...")
        print("=" * 60)
        
        # 创建优化目录结构
        optimized_structure = {
            "app": ["css", "js/modules", "js/utils", "components"],
            "assets": ["images", "fonts"],
            "docs": ["api", "design"]
        }
        
        # 创建目录
        for base_dir, subdirs in optimized_structure.items():
            dir_path = self.optimized_dir / base_dir
            dir_path.mkdir(parents=True, exist_ok=True)
            
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ 创建优化目录结构")
        
        # 创建基础文件
        self.create_base_files()
        
        print("✅ 创建基础文件")
        
        # 复制现有资源
        self.copy_existing_resources()
        
        print("✅ 复制现有资源")
        
        print(f"\n🎉 阶段1基础结构创建完成!")
        print(f"📁 优化目录: {self.optimized_dir}")
        
        return True
    
    def create_base_files(self):
        """创建基础文件"""
        
        # 1. 主HTML文件 (精简版)
        main_html = """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新加坡数字孪生 - 优化版 | Singapore Digital Twin</title>
    
    <!-- 样式文件 -->
    <link rel="stylesheet" href="app/css/main.css">
    <link rel="stylesheet" href="app/css/components.css">
    
    <!-- 外部库 -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    
    <!-- 预加载关键资源 -->
    <link rel="preload" href="app/js/main.js" as="script">
</head>
<body>
    <!-- 导航栏组件 -->
    <div id="nav-container"></div>
    
    <!-- 主内容区域 -->
    <main class="container">
        <!-- 页面将通过JavaScript动态加载 -->
        <div id="page-container">
            <div class="loading">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        </div>
    </main>
    
    <!-- 页脚组件 -->
    <div id="footer-container"></div>
    
    <!-- 全局脚本 -->
    <script type="module" src="app/js/main.js"></script>
    
    <!-- 数学严谨性验证脚本 -->
    <script type="module" src="app/js/modules/validation.js"></script>
    
    <!-- 透明度追踪脚本 -->
    <script type="module" src="app/js/modules/transparency.js"></script>
</body>
</html>"""
        
        with open(self.optimized_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(main_html)
        
        # 2. 基础CSS文件
        main_css = """/* main.css - 主样式文件 */
:root {
  /* 设计令牌 */
  --bg: #0a0e1a;
  --card: #111827;
  --border: #1e293b;
  --text: #e2e8f0;
  --dim: #94a3b8;
  --muted: #475569;
  --accent: #3b82f6;
  --green: #22c55e;
  --red: #ef4444;
  --orange: #f97316;
  --purple: #a855f7;
  --cyan: #06b6d4;
  --yellow: #eab308;
  
  /* 数学严谨性颜色 */
  --confidence-high: #22c55e;
  --confidence-medium: #eab308;
  --confidence-low: #ef4444;
  
  /* 透明度颜色 */
  --transparency-verified: #06b6d4;
  --transparency-pending: #f97316;
  
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
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式工具类 */
.mobile-only { display: none; }
.tablet-only { display: none; }
.desktop-only { display: block; }

@media (max-width: 1024px) {
  .desktop-only { display: none; }
  .tablet-only { display: block; }
}

@media (max-width: 768px) {
  .tablet-only { display: none; }
  .mobile-only { display: block; }
  .container { padding: 0 16px; }
}

/* 数学严谨性组件 */
.statistical-validation {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.validation-badge {
  display: inline-flex;
  align-items: