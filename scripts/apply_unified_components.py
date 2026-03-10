#!/usr/bin/env python3
"""
统一组件应用脚本
将导航和页脚组件应用到所有HTML页面
"""

import os
import re
import shutil
from datetime import datetime

# 配置
PROJECT_ROOT = "/Users/tigerli/Desktop/Digital Twins Singapore"
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
COMPONENTS_DIR = os.path.join(FRONTEND_DIR, "components")

# 要处理的页面
PAGES = [
    "index.html",
    "dashboard.html", 
    "simulation.html",
    "cases.html",
    "about.html",
    "detail.html"
]

# 组件代码
NAV_COMPONENT = """<!-- 统一导航组件 -->
<div id="unified-navigation-container"></div>
<script>
// 动态加载统一导航组件
fetch("components/unified-navigation.html")
    .then(response => response.text())
    .then(html => {
        document.getElementById("unified-navigation-container").innerHTML = html;
        console.log("✅ 统一导航组件加载完成");
    })
    .catch(error => console.error("❌ 导航组件加载失败:", error));
</script>"""

FOOTER_COMPONENT = """<!-- 统一页脚组件 -->
<div id="unified-footer-container"></div>
<script>
// 动态加载统一页脚组件
fetch("components/unified-footer.html")
    .then(response => response.text())
    .then(html => {
        document.getElementById("unified-footer-container").innerHTML = html;
        console.log("✅ 统一页脚组件加载完成");
    })
    .catch(error => console.error("❌ 页脚组件加载失败:", error));
</script>"""

def backup_file(filepath):
    """备份文件"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(filepath)
    backup_path = os.path.join(BACKUP_DIR, f"{filename}_backup_{timestamp}")
    
    shutil.copy2(filepath, backup_path)
    print(f"✅ 备份: {filename} -> {backup_path}")
    return backup_path

def find_body_tag(content):
    """查找<body>标签位置"""
    body_match = re.search(r'<body[^>]*>', content)
    if body_match:
        return body_match.end()
    return -1

def find_head_tag(content):
    """查找<head>标签位置"""
    head_match = re.search(r'<head[^>]*>', content)
    if head_match:
        return head_match.end()
    return -1

def find_closing_body_tag(content):
    """查找</body>标签位置"""
    return content.find('</body>')

def remove_existing_nav(content):
    """移除现有的导航"""
    # 移除现有的导航模式
    patterns = [
        r'<!-- 数据透明度组件 -->.*?</script>',
        r'<nav[^>]*>.*?</nav>',
        r'<div[^>]*class=".*?nav.*?"[^>]*>.*?</div>',
        r'<header[^>]*>.*?</header>'
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    return content

def remove_existing_footer(content):
    """移除现有的页脚"""
    # 移除现有的页脚模式
    patterns = [
        r'<footer[^>]*>.*?</footer>',
        r'<div[^>]*class=".*?footer.*?"[^>]*>.*?</div>',
        r'<!-- 页脚 -->.*?</div>'
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    return content

def apply_navigation(content):
    """应用导航组件"""
    # 先移除现有导航
    content = remove_existing_nav(content)
    
    # 在<body>标签后插入导航
    body_pos = find_body_tag(content)
    if body_pos > 0:
        content = content[:body_pos] + '\n' + NAV_COMPONENT + '\n' + content[body_pos:]
        print("  导航组件插入位置: <body>标签后")
    else:
        # 如果找不到<body>标签，在文件开头插入
        content = NAV_COMPONENT + '\n' + content
        print("  导航组件插入位置: 文件开头")
    
    return content

def apply_footer(content):
    """应用页脚组件"""
    # 先移除现有页脚
    content = remove_existing_footer(content)
    
    # 在</body>标签前插入页脚
    body_close_pos = find_closing_body_tag(content)
    if body_close_pos > 0:
        content = content[:body_close_pos] + '\n' + FOOTER_COMPONENT + '\n' + content[body_close_pos:]
        print("  页脚组件插入位置: </body>标签前")
    else:
        # 如果找不到</body>标签，在文件末尾插入
        content = content + '\n' + FOOTER_COMPONENT
        print("  页脚组件插入位置: 文件末尾")
    
    return content

def add_css_links(content):
    """添加CSS链接到<head>"""
    css_links = """
    <!-- 统一组件CSS -->
    <link rel="stylesheet" href="css/components.css">
    """
    
    head_pos = find_head_tag(content)
    if head_pos > 0:
        content = content[:head_pos] + css_links + content[head_pos:]
        print("  CSS链接添加到<head>")
    
    return content

def process_page(page_name):
    """处理单个页面"""
    page_path = os.path.join(FRONTEND_DIR, page_name)
    
    if not os.path.exists(page_path):
        print(f"❌ 页面不存在: {page_name}")
        return False
    
    print(f"\n🔧 处理页面: {page_name}")
    
    # 备份原文件
    backup_path = backup_file(page_path)
    
    # 读取内容
    with open(page_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用导航组件
    content = apply_navigation(content)
    
    # 应用页脚组件
    content = apply_footer(content)
    
    # 添加CSS链接
    content = add_css_links(content)
    
    # 写入文件
    with open(page_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 页面更新完成: {page_name}")
    return True

def create_components_css():
    """创建组件CSS文件"""
    css_dir = os.path.join(FRONTEND_DIR, "css")
    if not os.path.exists(css_dir):
        os.makedirs(css_dir)
    
    css_path = os.path.join(css_dir, "components.css")
    
    css_content = """/* 统一组件CSS - Digital Twin SG */
/* 生成时间: 2026-03-08 */

/* 基础重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* 字体系统 */
:root {
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'SF Mono', Monaco, 'Cascadia Mono', 'Roboto Mono', monospace;
}

/* 颜色系统 */
:root {
    /* 主色调 */
    --color-primary: #06b6d4;
    --color-primary-dark: #0891b2;
    --color-primary-light: #22d3ee;
    
    /* 中性色 */
    --color-bg: #0f172a;
    --color-card: #1e293b;
    --color-border: #334155;
    --color-text: #f1f5f9;
    --color-text-dim: #94a3b8;
    --color-text-muted: #64748b;
    
    /* 语义色 */
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    --color-info: #3b82f6;
}

/* 间距系统 */
:root {
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;
}

/* 圆角系统 */
:root {
    --radius-sm: 0.25rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-full: 9999px;
}

/* 阴影系统 */
:root {
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* 过渡动画 */
:root {
    --transition-fast: 150ms ease;
    --transition-normal: 250ms ease;
    --transition-slow: 350ms ease;
}

/* 响应式断点 */
@media (max-width: 640px) {
    :root {
        --space-xl: 1.5rem;
        --space-2xl: 2rem;
    }
}

@media (max-width: 768px) {
    :root {
        --space-lg: 1rem;
        --space-xl: 1.25rem;
    }
}

/* 工具类 */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--space-md);
}

.text-center {
    text-align: center;
}

.text-right {
    text-align: right;
}

.flex {
    display: flex;
}

.flex-col {
    flex-direction: column;
}

.items-center {
    align-items: center;
}

.justify-center {
    justify-content: center;
}

.justify-between {
    justify-content: space-between;
}

.gap-sm {
    gap: var(--space-sm);
}

.gap-md {
    gap: var(--space-md);
}

.gap-lg {
    gap: var(--space-lg);
}

/* 组件基础样式 */
.component-section {
    margin: var(--space-2xl) 0;
    padding: var(--space-xl) 0;
}

.component-card {
    background: var(--color-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    transition: all var(--transition-normal);
}

.component-card:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-lg);
}

/* 按钮样式 */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-md);
    font-weight: 500;
    font-size: 0.875rem;
    line-height: 1;
    border: none;
    cursor: pointer;
    transition: all var(--transition-normal);
    gap: var(--space-sm);
    text-decoration: none;
}

.btn-primary {
    background: var(--color-primary);
    color: white;
}

.btn-primary:hover {
    background: var(--color-primary-dark);
    transform: translateY(-1px);
}

.btn-secondary {
    background: var(--color-card);
    color: var(--color-text-dim);
    border: 1px solid var(--color-border);
}

.btn-secondary:hover {
    background: var(--color-border);
    border-color: var(--color-text-dim);
}

/* 表单样式 */
.form-group {
    margin-bottom: var(--space-lg);
}

.form-label {
    display: block;
    margin-bottom: var(--space-sm);
    font-weight: 500;
    color: var(--color-text);
}

.form-input {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    background: var(--color-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text);
    font-family: var(--font-sans);
    transition: all var(--transition-normal);
}

.form-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

/* 响应式工具 */
@media (max-width: 768px) {
    .mobile-hidden {
        display: none !important;
    }
}

@media (min-width: 769px) {
    .desktop-hidden {
        display: none !important;
    }
}

/* 打印样式 */
@media print {
    .no-print {
        display: none !important;
    }
}
"""
    
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print(f"✅ 创建CSS文件: {css_path}")
    return css_path

def main():
    """主函数"""
    print("🚀 开始应用统一组件")
    print("=" * 50)
    
    # 创建CSS文件
    create_components_css()
    
    # 处理所有页面
    success_count = 0
    for page in PAGES:
        if process_page(page):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎉 处理完成!")
    print(f"✅ 成功处理: {success_count}/{len(PAGES)} 个页面")
    print(f"📁 组件位置: {COMPONENTS_DIR}")
    print(f"🎨 CSS文件: {FRONTEND_DIR}/css/components.css")
    print(f"💾 备份位置: {BACKUP_DIR}")
    
    # 生成验证命令
    print("\n🔍 验证命令:")
    print(f"  cd {FRONTEND_DIR}")
    print("  python3 -m http.server 8888")
    print("  然后访问: http://localhost:8888/index.html")
    
    return success_count == len(PAGES)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)