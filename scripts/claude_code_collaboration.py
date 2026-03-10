#!/usr/bin/env python3
"""
Claude Code协同工作计划 - 高效前端优化
"""

import json
from pathlib import Path
from datetime import datetime

def create_claude_code_tasks():
    """创建Claude Code具体任务清单"""
    
    print("🤝 Claude Code协同工作计划")
    print("=" * 60)
    print("策略: 我制定计划 + Claude Code高效执行")
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    frontend_dir = project_root / "frontend"
    
    # 分析dashboard.html
    dashboard_file = frontend_dir / "dashboard.html"
    
    if not dashboard_file.exists():
        print("❌ 未找到dashboard.html")
        return
    
    # 读取文件基本信息
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.count('\n') + 1
    
    print(f"📊 分析目标: dashboard.html ({lines}行)")
    
    # 创建Claude Code任务清单
    tasks = {
        "project": "Digital Twin SG 前端优化",
        "strategy": "Claude Code协同开发",
        "created_at": datetime.now().isoformat(),
        "claude_code_tasks": [],
        "my_tasks": [],
        "collaboration_workflow": []
    }
    
    # Claude Code任务 (高效代码生成)
    tasks["claude_code_tasks"] = [
        {
            "id": "CC-001",
            "task": "CSS提取和模块化",
            "description": "从dashboard.html提取所有内联CSS到外部文件",
            "claude_prompt": """请从提供的dashboard.html文件中提取所有内联CSS样式。

要求:
1. 提取所有<style>标签内的CSS
2. 提取所有内联style属性
3. 按功能分类: 布局、组件、图表、工具类
4. 创建以下文件:
   - main.css: 基础布局和重置
   - components.css: 所有UI组件样式
   - charts.css: 图表相关样式
   - utilities.css: 工具类和响应式
5. 使用CSS Custom Properties (设计令牌)
6. 确保响应式设计
7. 添加详细注释

请分步骤进行，先分析，再提取，最后优化。""",
            "input_files": ["frontend/dashboard.html"],
            "output_files": ["css/main.css", "css/components.css", "css/charts.css", "css/utilities.css"],
            "estimated_time": "2小时",
            "priority": "P0"
        },
        {
            "id": "CC-002",
            "task": "JavaScript模块化",
            "description": "提取内联JavaScript到模块化文件",
            "claude_prompt": """请从dashboard.html提取所有内联JavaScript代码。

要求:
1. 提取所有<script>标签内的JavaScript
2. 提取所有内联事件处理程序 (onclick等)
3. 按功能模块化:
   - dashboard.js: 主仪表盘逻辑
   - charts.js: 图表初始化和更新
   - filters.js: 筛选器功能
   - api.js: Supabase API通信
   - utils.js: 工具函数
4. 使用ES6模块语法 (import/export)
5. 添加错误处理和加载状态
6. 优化性能 (防抖、节流、缓存)
7. 添加JSDoc注释

请确保代码可维护性和性能。""",
            "input_files": ["frontend/dashboard.html"],
            "output_files": ["js/dashboard.js", "js/charts.js", "js/filters.js", "js/api.js", "js/utils.js"],
            "estimated_time": "3小时",
            "priority": "P0"
        },
        {
            "id": "CC-003",
            "task": "HTML组件化",
            "description": "创建可复用的HTML组件",
            "claude_prompt": """请从dashboard.html识别和创建可复用HTML组件。

要求:
1. 识别重复的HTML模式
2. 创建以下组件:
   - header.html: 导航栏和标题
   - sidebar.html: 侧边栏筛选器
   - stats-cards.html: 统计卡片
   - agent-grid.html: 代理网格
   - chart-container.html: 图表容器
3. 每个组件应该是独立的HTML片段
4. 使用语义化HTML标签
5. 添加ARIA属性用于无障碍访问
6. 确保响应式设计
7. 添加组件使用说明

组件应该可以通过JavaScript动态加载。""",
            "input_files": ["frontend/dashboard.html"],
            "output_files": ["components/header.html", "components/sidebar.html", "components/stats-cards.html", "components/agent-grid.html", "components/chart-container.html"],
            "estimated_time": "2小时",
            "priority": "P1"
        },
        {
            "id": "CC-004",
            "task": "数学严谨性组件",
            "description": "创建统计验证和置信区间显示",
            "claude_prompt": """请创建数学严谨性展示组件。

要求:
1. 创建统计验证组件:
   - 显示置信区间 (如: 99.9% ±0.25%)
   - 显示统计功效
   - 显示样本代表性
   - 验证状态指示器
2. 创建方法说明组件:
   - 统计方法描述
   - 假设说明
   - 局限性标注
3. 创建敏感性分析显示
4. 使用专业但易懂的UI
5. 支持中英文切换
6. 添加工具提示解释术语

组件应该专业、可信、透明。""",
            "input_files": [],
            "output_files": ["components/validation-panel.html", "js/modules/validation.js", "css/validation.css"],
            "estimated_time": "1.5小时",
            "priority": "P1"
        },
        {
            "id": "CC-005",
            "task": "透明度系统",
            "description": "创建数据来源追溯和透明度展示",
            "claude_prompt": """请创建透明度展示系统。

要求:
1. 数据来源追溯组件:
   - 显示数据来源 (政府API、调查等)
   - 显示收集时间
   - 显示处理方法
   - 质量验证状态
2. 方法透明度组件:
   - 算法说明
   - 参数设置
   - 验证过程
   - 替代方法
3. 结果透明度组件:
   - 置信区间强制显示
   - 局限性明确标注
   - 不确定性量化
   - 替代解读
4. 创建透明度徽章系统
5. 支持渐进式信息披露

目标是建立用户信任。""",
            "input_files": [],
            "output_files": ["components/transparency-panel.html", "js/modules/transparency.js", "css/transparency.css"],
            "estimated_time": "1.5小时",
            "priority": "P1"
        }
    ]
    
    # 我的任务 (策略、验证、集成)
    tasks["my_tasks"] = [
        {
            "id": "MY-001",
            "task": "项目架构设计",
            "description": "设计优化后的前端架构",
            "deliverables": ["架构图", "技术选型", "目录结构"],
            "estimated_time": "2小时",
            "priority": "P0"
        },
        {
            "id": "MY-002", 
            "task": "Claude Code任务管理",
            "description": "准备任务、提供上下文、验证结果",
            "deliverables": ["任务清单", "验证报告", "进度跟踪"],
            "estimated_time": "持续",
            "priority": "P0"
        },
        {
            "id": "MY-003",
            "task": "代码审查和测试",
            "description": "审查Claude生成的代码，编写测试",
            "deliverables": ["代码审查报告", "测试用例", "性能测试"],
            "estimated_time": "持续",
            "priority": "P0"
        },
        {
            "id": "MY-004",
            "task": "产品目标对齐验证",
            "description": "确保优化符合五大产品目标",
            "deliverables": ["目标对齐报告", "用户测试计划", "质量检查表"],
            "estimated_time": "持续",
            "priority": "P0"
        },
        {
            "id": "MY-005",
            "task": "部署和监控",
            "description": "部署优化版本，建立监控",
            "deliverables": ["部署计划", "监控仪表板", "用户反馈系统"],
            "estimated_time": "4小时",
            "priority": "P1"
        }
    ]
    
    # 协同工作流程
    tasks["collaboration_workflow"] = [
        {
            "phase": "准备阶段",
            "steps": [
                "我: 分析现状，制定策略",
                "我: 创建Claude Code任务清单",
                "我: 准备开发环境和上下文"
            ]
        },
        {
            "phase": "代码生成阶段", 
            "steps": [
                "Claude: 根据任务生成代码",
                "我: 提供反馈和调整要求",
                "Claude: 优化和调整代码",
                "我: 验证生成结果"
            ]
        },
        {
            "phase": "集成测试阶段",
            "steps": [
                "我: 集成生成的代码",
                "我: 编写测试用例",
                "我: 运行性能测试",
                "我: 修复集成问题"
            ]
        },
        {
            "phase": "优化迭代阶段",
            "steps": [
                "我: 收集用户反馈",
                "Claude: 根据反馈优化",
                "我: A/B测试优化效果",
                "我们: 持续改进"
            ]
        }
    ]
    
    # 时间计划
    tasks["timeline"] = {
        "day1": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tasks": [
                "CC-001: CSS提取 (上午)",
                "CC-002: JavaScript模块化开始 (下午)",
                "MY-001: 架构设计 (全天)"
            ]
        },
        "day2": {
            "date": (datetime.now().timestamp() + 86400),  # 明天
            "tasks": [
                "CC-002: JavaScript模块化完成 (上午)",
                "CC-003: HTML组件化 (下午)",
                "MY-002/003: 任务管理和测试 (全天)"
            ]
        },
        "day3": {
            "date": (datetime.now().timestamp() + 172800),  # 后天
            "tasks": [
                "CC-004: 数学严谨性组件 (上午)",
                "CC-005: 透明度系统 (下午)",
                "MY-004: 产品目标验证 (全天)"
            ]
        },
        "day4": {
            "date": (datetime.now().timestamp() + 259200),  # 大后天
            "tasks": [
                "集成测试 (上午)",
                "性能优化 (下午)",
                "MY-005: 部署准备 (全天)"
            ]
        }
    }
    
    # 成功指标
    tasks["success_metrics"] = {
        "efficiency": {
            "code_generation_speed": "> 75% faster than manual",
            "task_completion_rate": "> 90% on schedule",
            "bug_reduction": "> 50% fewer bugs"
        },
        "quality": {
            "lighthouse_score": "> 90",
            "code_maintainability": "> 80% improvement",
            "user_satisfaction": "> 4.5/5"
        },
        "product_goals": {
            "mathematical_rigor": "100% implemented",
            "transparency": "100% implemented",
            "simplicity_trust": "> 90% user trust"
        }
    }
    
    # 保存任务清单
    reports_dir = project_root / "data" / "claude_collaboration"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    tasks_file = reports_dir / f"claude_code_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Claude Code任务清单已保存: {tasks_file}")
    
    # 打印摘要
    print_summary(tasks)
    
    return tasks

def print_summary(tasks):
    """打印任务摘要"""
    print("\n📋 任务摘要")
    print("=" * 60)
    
    print(f"Claude Code任务: {len(tasks['claude_code_tasks'])}个")
    print(f"我的任务: {len(tasks['my_tasks'])}个")
    
    total_claude_hours = sum(float(t['estimated_time'].replace('小时', '')) for t in tasks['claude_code_tasks'])
    total_my_hours = sum(float(t['estimated_time'].replace('小时', '')) if isinstance(t['estimated_time'], str) and '小时' in t['estimated_time'] else 0 for t in tasks['my_tasks'])
    
    print(f"预计时间: Claude Code {total_claude_hours}小时 + 我 {total_my_hours}小时")
    print(f"效率提升: 预计 {total_claude_hours/(total_claude_hours+total_my_hours)*100:.1f}% 代码由Claude生成")
    
    print("\n🚀 今天可以开始的Claude Code任务:")
    for task in tasks['claude_code_tasks'][:2]:  # 前2个任务
        print(f"  [{task['priority']}] {task['task']} ({task['estimated_time']})")
    
    print("\n🎯 我的立即行动:")
    for task in tasks['my_tasks'][:2]:  # 前2个任务
        print(f"  [{task['priority']}] {task['task']} ({task['estimated_time']})")
    
    print("\n🤝 协同工作流程:")
    for phase in tasks['collaboration_workflow']:
        print(f"  {phase['phase']}:")
        for step in phase['steps'][:2]:  # 前2个步骤
            print(f"    • {step}")

def create_claude_ready_prompts(tasks):
    """创建Claude可用的提示模板"""
    print("\n📝 创建Claude Code提示模板...")
    print("=" * 60)
    
    project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
    prompts_dir = project_root / "docs" / "claude_prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # 为每个Claude任务创建详细提示
    for task in tasks['claude_code_tasks']:
        prompt_file = prompts_dir / f"{task['id']}_{task['task'].replace(' ', '_')}.md"
        
        prompt_content = f"""# Claude Code任务: {task['task']}

## 任务ID
{task['id']}

## 任务描述
{task['description']}

## 详细要求
{task['claude_prompt']}

## 输入文件
{chr(10).join(f'- {f}' for f in task['input_files']) if task['input_files'] else '无特定输入文件'}

## 输出文件
{chr(10).join(f'- {f}' for f in task['output_files'])}

## 项目背景
这是"新加坡数字孪生(Digital Twin SG)"项目的前端优化任务。项目有172K AI Agents，需要优化前端以符合五大产品目标:
1. 对标全球领先产品
2. 数学严谨
3. 预测尽最大努力最准  
4. 真实不撒谎
5. 前端客户界面简洁可信

## 技术栈
- HTML5, CSS3, JavaScript (ES6+)
- Chart.js v4 (已集成)
- Supabase JavaScript客户端
- 响应式设计，暗色主题

## 代码风格要求
- 使用语义化HTML标签
- CSS使用Custom Properties设计令牌
- JavaScript使用ES6模块语法
- 添加详细注释
- 确保无障碍访问(ARIA)
- 优化性能(懒加载、缓存等)

## 质量要求
- 代码可维护性高
- 浏览器兼容性好
- 性能优化充分
- 符合产品目标

请分步骤完成这个任务，先分析，再生成，最后优化。如果需要更多上下文，请询问。
"""
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        print(f"  ✅ 创建提示: {prompt_file.name}")
    
    print(f"\n🎯 Claude Code提示模板已创建在: {prompts_dir}")
    print("💡 使用建议: 在Claude桌面应用中打开这些文件，复制提示内容")

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 Claude Code协同前端优化计划")
    print("=" * 60)
    print("目标: 结合Claude Code高效开发和我的策略制定")
    
    try:
        # 创建任务清单
        tasks = create_claude_code_tasks()
        
        if tasks:
            # 创建Claude提示模板
            create_claude_ready_prompts(tasks)
            
            print("\n" + "=" * 60)
            print("🎉 Claude Code协同计划创建完成!")
            print("=" * 60)
            
            print("\n🚀 立即开始:")
            print("1. 打开Claude桌面应用")
            print("2. 打开 docs/claude_prompts/CC-001_CSS提取和模块化.md")
            print("3. 复制提示内容到Claude")
            print("4. 上传 dashboard.html 文件")
            print("5. 开始第一个任务!")
            
            print("\n📊 预期效果:")
            print("• 75%