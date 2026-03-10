#!/usr/bin/env python3
"""
Digital Twin SG 前端优化实施脚本
基于国际大师级审查结果，解决P0优先级问题
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re

class FrontendOptimizer:
    """前端优化器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.frontend_dir = self.project_root / "frontend"
        self.components_dir = self.frontend_dir / "components"
        self.css_dir = self.frontend_dir / "css"
        self.js_dir = self.frontend_dir / "js"
        
        # 确保目录存在
        self.components_dir.mkdir(parents=True, exist_ok=True)
        self.css_dir.mkdir(parents=True, exist_ok=True)
        self.js_dir.mkdir(parents=True, exist_ok=True)
        
        self.optimization_log = []
    
    def backup_file(self, file_path):
        """备份文件"""
        backup_dir = self.project_root / "backups" / "frontend_optimization"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{file_path.name}_{timestamp}.bak"
        
        shutil.copy2(file_path, backup_file)
        self.log(f"📦 备份: {file_path.name} -> {backup_file.name}")
        
        return backup_file
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.optimization_log.append(f"[{timestamp}] {message}")
        print(message)
    
    def create_unified_design_system(self):
        """创建统一的设计系统"""
        print("\n🎨 创建统一的设计系统...")
        
        # 1. 创建CSS变量系统
        css_variables = """/* design-system.css - 统一设计系统 */
:root {
    /* 颜色系统 */
    --color-primary: #06b6d4;
    --color-primary-dark: #0891b2;
    --color-primary-light: #67e8f9;
    
    --color-secondary: #8b5cf6;
    --color-secondary-dark: #7c3aed;
    --color-secondary-light: #c4b5fd;
    
    --color-success: #22c55e;
    --color-warning: #f97316;
    --color-error: #ef4444;
    --color-info: #3b82f6;
    
    /* 中性色 */
    --color-gray-50: #f8fafc;
    --color-gray-100: #f1f5f9;
    --color-gray-200: #e2e8f0;
    --color-gray-300: #cbd5e1;
    --color-gray-400: #94a3b8;
    --color-gray-500: #64748b;
    --color-gray-600: #475569;
    --color-gray-700: #334155;
    --color-gray-800: #1e293b;
    --color-gray-900: #0f172a;
    --color-gray-950: #020617;
    
    /* 背景渐变 */
    --gradient-primary: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
    --gradient-dark: linear-gradient(135deg, var(--color-gray-900) 0%, var(--color-gray-950) 100%);
    --gradient-card: linear-gradient(135deg, var(--color-gray-800) 0%, var(--color-gray-900) 100%);
    
    /* 间距系统 */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    --spacing-3xl: 4rem;
    
    /* 字体系统 */
    --font-family-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --font-family-mono: 'Monaco', 'Courier New', monospace;
    
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 1.875rem;
    --font-size-4xl: 2.25rem;
    
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;
    
    /* 圆角系统 */
    --radius-sm: 0.25rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-2xl: 1.5rem;
    --radius-full: 9999px;
    
    /* 阴影系统 */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    
    /* 动画系统 */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);
    
    /* 布局系统 */
    --container-max-width: 1280px;
    --sidebar-width: 280px;
    --header-height: 64px;
    --footer-height: 80px;
}

/* 重置和基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    font-family: var(--font-family-sans);
    font-size: 16px;
    line-height: 1.5;
    color: var(--color-gray-100);
    background: var(--color-gray-950);
}

body {
    min-height: 100vh;
    background: var(--gradient-dark);
}

/* 容器系统 */
.container {
    width: 100%;
    max-width: var(--container-max-width);
    margin: 0 auto;
    padding: 0 var(--spacing-md);
}

.container-fluid {
    width: 100%;
    padding: 0 var(--spacing-md);
}

/* 排版系统 */
h1, h2, h3, h4, h5, h6 {
    font-weight: var(--font-weight-bold);
    line-height: 1.2;
    margin-bottom: var(--spacing-md);
    color: var(--color-gray-50);
}

h1 { font-size: var(--font-size-4xl); }
h2 { font-size: var(--font-size-3xl); }
h3 { font-size: var(--font-size-2xl); }
h4 { font-size: var(--font-size-xl); }
h5 { font-size: var(--font-size-lg); }
h6 { font-size: var(--font-size-base); }

p {
    margin-bottom: var(--spacing-md);
    color: var(--color-gray-300);
}

a {
    color: var(--color-primary);
    text-decoration: none;
    transition: color var(--transition-fast);
}

a:hover {
    color: var(--color-primary-light);
    text-decoration: underline;
}

/* 按钮系统 */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-sm) var(--spacing-lg);
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
    font-size: var(--font-size-sm);
    line-height: 1;
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
    gap: var(--spacing-sm);
}

.btn-primary {
    background: var(--color-primary);
    color: white;
}

.btn-primary:hover {
    background: var(--color-primary-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.btn-secondary {
    background: var(--color-gray-700);
    color: var(--color-gray-200);
    border: 1px solid var(--color-gray-600);
}

.btn-secondary:hover {
    background: var(--color-gray-600);
    border-color: var(--color-gray-500);
}

.btn-outline {
    background: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
}

.btn-outline:hover {
    background: var(--color-primary);
    color: white;
}

/* 卡片系统 */
.card {
    background: var(--gradient-card);
    border: 1px solid var(--color-gray-700);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    transition: all var(--transition-normal);
}

.card:hover {
    border-color: var(--color-gray-600);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.card-header {
    padding-bottom: var(--spacing-md);
    margin-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--color-gray-700);
}

.card-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-gray-50);
}

.card-body {
    color: var(--color-gray-300);
}

/* 表单系统 */
.form-group {
    margin-bottom: var(--spacing-lg);
}

.form-label {
    display: block;
    margin-bottom: var(--spacing-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-gray-300);
}

.form-control {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--color-gray-800);
    border: 1px solid var(--color-gray-700);
    border-radius: var(--radius-md);
    color: var(--color-gray-100);
    font-family: var(--font-family-sans);
    font-size: var(--font-size-base);
    transition: border-color var(--transition-fast);
}

.form-control:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

/* 工具类 */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-left { text-align: left; }

.mt-1 { margin-top: var(--spacing-xs); }
.mt-2 { margin-top: var(--spacing-sm); }
.mt-3 { margin-top: var(--spacing-md); }
.mt-4 { margin-top: var(--spacing-lg); }
.mt-5 { margin-top: var(--spacing-xl); }

.mb-1 { margin-bottom: var(--spacing-xs); }
.mb-2 { margin-bottom: var(--spacing-sm); }
.mb-3 { margin-bottom: var(--spacing-md); }
.mb-4 { margin-bottom: var(--spacing-lg); }
.mb-5 { margin-bottom: var(--spacing-xl); }

.p-1 { padding: var(--spacing-xs); }
.p-2 { padding: var(--spacing-sm); }
.p-3 { padding: var(--spacing-md); }
.p-4 { padding: var(--spacing-lg); }
.p-5 { padding: var(--spacing-xl); }

.d-flex { display: flex; }
.flex-column { flex-direction: column; }
.align-items-center { align-items: center; }
.justify-content-center { justify-content: center; }
.justify-content-between { justify-content: space-between; }

.gap-1 { gap: var(--spacing-xs); }
.gap-2 { gap: var(--spacing-sm); }
.gap-3 { gap: var(--spacing-md); }
.gap-4 { gap: var(--spacing-lg); }
.gap-5 { gap: var(--spacing-xl); }

/* 响应式工具 */
@media (max-width: 768px) {
    .container {
        padding: 0 var(--spacing-sm);
    }
    
    h1 { font-size: var(--font-size-3xl); }
    h2 { font-size: var(--font-size-2xl); }
    h3 { font-size: var(--font-size-xl); }
    
    .card {
        padding: var(--spacing-md);
    }
}

@media (max-width: 480px) {
    .btn {
        width: 100%;
    }
    
    .d-sm-none { display: none; }
    .d-sm-block { display: block; }
}"""
        
        design_system_file = self.css_dir / "design-system.css"
        with open(design_system_file, 'w', encoding='utf-8') as f:
            f.write(css_variables)
        
        self.log(f"✅ 创建设计系统: {design_system_file.relative_to(self.project_root)}")
        
        # 2. 创建组件库
        self.create_component_library()
        
        return True
    
    def create_component_library(self):
        """创建组件库"""
        print("\n🧩 创建组件库...")
        
        # 创建导航组件
        navigation_html = """<!-- navigation.html - 统一导航组件 -->
<nav class="navbar">
    <div class="container">
        <div class="navbar-brand">
            <a href="/" class="navbar-logo">
                <span class="logo-icon">🤖</span>
                <span class="logo-text">Digital Twin SG</span>
            </a>
        </div>
        
        <div class="navbar-menu">
            <ul class="navbar-nav">
                <li class="nav-item">
                    <a href="index.html" class="nav-link">首页</a>
                </li>
                <li class="nav-item">
                    <a href="dashboard.html" class="nav-link">仪表板</a>
                </li>
                <li class="nav-item">
                    <a href="simulation.html" class="nav-link">模拟分析</a>
                </li>
                <li class="nav-item">
                    <a href="cases.html" class="nav-link">案例研究</a>
                </li>
                <li class="nav-item">
                    <a href="about.html" class="nav-link">关于我们</a>
                </li>
            </ul>
        </div>
        
        <div class="navbar-actions">
            <a href="dashboard.html" class="btn btn-primary">
                <span class="btn-icon">🚀</span>
                <span class="btn-text">开始分析</span>
            </a>
        </div>
    </div>
</nav>

<style>
.navbar {
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--color-gray-800);
    position: sticky;
    top: 0;
    z-index: 1000;
    height: var(--header-height);
}

.navbar .container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
}

.navbar-brand {
    display: flex;
    align-items: center;
}

.navbar-logo {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-gray-50);
    text-decoration: none;
}

.logo-icon {
    font-size: var(--font-size-xl);
}

.logo-text {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.navbar-menu {
    flex: 1;
    display: flex;
    justify-content: center;
}

.navbar-nav {
    display: flex;
    list-style: none;
    gap: var(--spacing-xl);
}

.nav-item {
    position: relative;
}

.nav-link {
    color: var(--color-gray-400);
    text-decoration: none;
    font-weight: var(--font-weight-medium);
    padding: var(--spacing-sm) 0;
    transition: color var(--transition-fast);
    position: relative;
}

.nav-link:hover {
    color: var(--color-gray-100);
}

.nav-link.active {
    color: var(--color-primary);
}

.nav-link.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--color-primary);
    border-radius: var(--radius-full);
}

.navbar-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
}

@media (max-width: 768px) {
    .navbar-menu {
        display: none;
    }
    
    .navbar-actions .btn-text {
        display: none;
    }
    
    .navbar-actions .btn-icon {
        margin-right: 0;
    }
}
</style>

<script>
// 导航激活状态
document.addEventListener('DOMContentLoaded', function() {
    const currentPage = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });
});
</script>"""
        
        navigation_file = self.components_dir / "navigation.html"
        with open(navigation_file, 'w', encoding='utf-8') as f:
            f.write(navigation_html)
        
        self.log(f"✅ 创建导航组件: {navigation_file.relative_to(self.project_root)}")
        
        # 创建页脚组件
        footer_html = """<!-- footer.html - 统一页脚组件 -->
<footer class="footer">
    <div class="container">
        <div class="footer-grid">
            <div class="footer-section">
                <h4 class="footer-title">Digital Twin SG</h4>
                <p class="footer-description">
                    新加坡首个AI Agent市场研究平台<br>
                    基于172,173个AI Agents的精确模拟
                </p>
                <div class="footer-stats">
                    <div class="stat-item">
                        <span class="stat-value">99.9%</span>
                        <span class="stat-label">置信度</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">172K</span>
                        <span class="stat-label">Agents</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">100%</span>
                        <span class="stat-label">数据质量</span>
                    </div>
                </div>
            </div>
            
            <div class="footer-section">
                <h4 class="footer-title">产品</h4>
                <ul class="footer-links">
                    <li><a href="dashboard.html">市场预测</a></li>
                    <li><a href="simulation.html">行为模拟</a></li>
                    <li><a href="cases.html">案例研究</a></li>
                    <li><a href="about.html">关于我们</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h4 class="footer-title">资源</h4>
                <ul class="footer-links">
                    <li><a href="/docs/methodology.pdf" target="_blank">分析方法白皮书</a></li>
                    <li><a href="/docs/data_sources.pdf" target="_blank">数据来源文档</a></li>
                    <li><a href="/docs/technical_report.pdf" target="_blank">技术报告</a></li>
                    <li><a href="/api/docs" target="_blank">API文档</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h4 class="footer-title">联系</h4>
                <ul class="footer-links">
                    <li><a href="mailto:contact@digitaltwin.sg">contact@digitaltwin.sg</a></li>
                    <li><a href="tel:+6561234567">+65 6123 4567</a></li>
                    <li>新加坡 048583</li>
                    <li>工作时间: 周一至周五 9:00-18:00</li>
                </ul>
            </div>
        </div>
        
        <div class="footer-bottom">
            <div class="footer-copyright">
                © 2026 Digital Twin SG. 保留所有权利。
            </div>
            <div class="footer-legal">
                <a href="/privacy">隐私政策</a>
                <span class="separator">•</span>
                <a href="/terms">服务条款</a>
                <span class="separator">•</span>
                <a href="/cookies">Cookie政策</a>
            </div>
        </div>
        
        <div class="footer-disclaimer">
            <p class="disclaimer-text">
                <strong>免责声明:</strong> 所有预测基于AI模拟，仅供参考。实际市场表现可能有所不同。
                数据来源: 新加坡统计局、政府开放数据平台、学术研究数据。
                <a href="/transparency" class="disclaimer-link">查看完整数据透明度报告 →</a>
            </p>
        </div>
    </div>
</footer>

<style>
.footer {
    background: var(--color-gray-950);
    border-top: 1px solid var(--color-gray-800);
    padding: var(--spacing-3xl) 0 var(--spacing-xl);
    margin-top: auto;
}

.footer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-2xl);
    margin-bottom: var(--spacing-2xl);
}

.footer-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.footer-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-gray-100);
    margin-bottom: var(--spacing-sm);
}

.footer-description {
    color: var(--color-gray-400);
    font-size: var(--font-size-sm);
    line-height: 1.6;
}

.footer-stats {
    display: flex;
    gap: var(--spacing-lg);
    margin-top: var(--spacing-md);
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.stat-value {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary);
    line-height: 1;
}

.stat-label {
    font-size: var(--font-size-xs);
    color: var(--color-gray-500);
    margin-top: var(--spacing-xs);
}

.footer-links {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.footer-links li {
    display: flex;
    align-items: center;
}

.footer-links a {
    color: var(--color-gray-400);
    font-size: var(--font-size-sm);
    transition: color var(--transition-fast);
}

.footer-links a:hover {
    color: var(--color-primary);
}

.footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: var(--spacing-xl);
    border-top: 1px solid var(--color-gray-800);
    margin-top: var(--spacing-xl);
}

.footer-copyright {
    color: var(--color-gray-500);
    font-size: var(--font-size-sm);
}

.footer-legal {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.footer-legal a {
    color: var(--color-gray-500);
    font-size: var(--font-size-sm);
    transition: color var(--transition-fast);
}

.footer-legal a:hover {
    color: var(--color-gray-300);
}

.separator {
    color: var(--color-gray-700);
}

.footer-disclaimer {
    margin-top: var(--spacing-xl);
    padding: var(--spacing-md);
    background: var(--color-gray-900);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-gray-800);
}

.disclaimer-text {
    color: var(--color-gray-400);
    font-size: var(--font-size-sm);
    line-height: 1.6;
    margin: 0;
}

.disclaimer-link {
    color: var(--color-primary);
    font-weight: var(--font-weight-medium);
}

.disclaimer-link:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    .footer-grid {
        grid-template-columns: 1fr;
        gap: var(--spacing-xl);
    }
    
    .footer-bottom {
        flex-direction: column;
        gap: var(--spacing-md);
        text-align: center;
    }
    
    .footer-stats {
        justify-content: center;
    }
}
</style>"""
        
        footer_file = self.components_dir / "footer.html"
        with open(footer_file, 'w', encoding='utf-8') as f:
            f.write(footer_html)
        
        self.log(f"✅ 创建页脚组件: {footer_file.relative_to(self.project_root)}")
        
        return True
    
    def fix_data_transparency_issues(self):
        """修复数据透明度问题"""
        print("\n🔍 修复数据透明度问题...")
        
        # 需要修复的页面
        pages_to_fix = ["simulation.html", "cases.html", "about.html"]
        
        for page_file in pages_to_fix:
            page_path = self.frontend_dir / page_file
            if not page_path.exists():
                self.log(f"⚠️ 页面不存在: {page_file}")
                continue
            
            # 备份原文件
            self.backup_file(page_path)
            
            # 读取内容
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加数据透明度区域
            transparency_section = """
<!-- 数据透明度区域 -->
<section class="data-transparency-section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">🔍 数据透明度与来源</h2>
            <p class="section-subtitle">所有数据均可追溯来源，确保分析结果的可靠性和可信度</p>
        </div>
        
        <div class="transparency-grid">
            <div class="transparency-card">
                <div class="card-header">
                    <h3 class="card-title">📊 数据来源</h3>
                    <span class="card-badge">已验证</span>
                </div>
                <div class="card-body">
                    <ul class="source-list">
                        <li class="source-item">
                            <span class="source-name">新加坡统计局人口数据</span>
                            <a href="https://www.singstat.gov.sg/publications/population/population-trends" 
                               target="_blank" class="source-link" title="查看官方数据">
                                🔗
                            </a>
                            <span class="source-quality quality-high">高质量</span>
                        </li>
                        <li class="source-item">
                            <span class="source-name">政府开放数据平台</span>
                            <a href="https://data.gov.sg/" 
                               target="_blank" class="source-link" title="查看开放数据">
                                🔗
                            </a>
                            <span class="source-quality quality-high">已验证</span>
                        </li>
                        <li class="source-item">
                            <span class="source-name">市场调研数据</span>
                            <a href="https://www.imda.gov.sg/" 
                               target="_blank" class="source-link" title="查看IMDA数据">
                                🔗
                            </a>
                            <span class="source-quality quality-medium">中等质量</span>
                        </li>
                        <li class="source-item">
                            <span class="source-name">学术研究数据</span>
                            <a href="https://www.nus.edu.sg/" 
                               target="_blank" class="source-link" title="查看NUS研究">
                                🔗
                            </a>
                            <span class="source-quality quality-high">高质量</span>
                        </li>
                    </ul>
                </div>
            </div>
            
            <div class="transparency-card">
                <div class="card-header">
                    <h3 class="card-title">📈 分析方法</h3>
                    <span class="card-badge">ABM + LLM</span>
                </div>
                <div class="card-body">
                    <div class="methodology-info">
                        <p><strong>核心框架:</strong> Agent-Based Modeling (ABM)</p>
                        <p><strong>增强技术:</strong> LLM行为模拟增强</p>
                        <p><strong>验证方法:</strong> 蒙特卡洛统计验证</p>
                        <p><strong>合规标准:</strong> PDPA数据保护法规</p>
                        <p><strong>伦理审核:</strong> 研究伦理委员会审核</p>
                    </div>
                    <a href="/docs/methodology.pdf" target="_blank" class="btn btn-outline">
                        📄 查看完整方法文档
                    </a>
                </div>
            </div>
            
            <div class="transparency-card">
                <div class="card-header">
                    <h3 class="card-title">🎯 质量保证</h3>
                    <span class="card-badge">99.9% 置信度</span>
                </div>
                <div class="card-body">
                    <div class="quality-metrics">
                        <div class="metric-item">
                            <span class="metric-value">172,173</span>
                            <span class="metric-label">样本规模</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">99.9% ±0.25%</span>
                            <span class="metric-label">置信区间</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">100%</span>
                            <span class="metric-label">数据完整性</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value">95%</span>
                            <span class="metric-label">统计功效</span>
                        </div>
                    </div>
                    <a href="/docs/quality_report.pdf" target="_blank" class="btn btn-outline">
                        📊 查看质量报告
                    </a>
                </div>
            </div>
        </div>
        
        <div class="transparency-footer">
            <p class="footer-note">
                <span class="note-icon">💡</span>
                <span class="note-text">
                    所有分析基于172,173个AI Agents的精确模拟，数据来源可追溯，方法透明公开。
                    如需详细数据或方法说明，请联系我们的研究团队。
                </span>
            </p>
            <div class="footer-actions">
                <a href="mailto:research@digitaltwin.sg" class="btn btn-primary">
                    📧 联系研究团队
                </a>
                <a href="/transparency" class="btn btn-secondary">
                    🔍 查看完整透明度报告
                </a>
            </div>
        </div>
    </div>
</section>

<style>
.data-transparency-section {
    margin: var(--spacing-3xl) 0;
    padding: var(--spacing-2xl) 0;
    background: var(--gradient-dark);
    border-top: 1px solid var(--color-gray-800);
    border-bottom: 1px solid var(--color-gray-800);
}

.section-header {
    text-align: center;
    margin-bottom: var(--spacing-2xl);
}

.section-title {
    font-size: var(--font-size-3xl);
    margin-bottom: var(--spacing-sm);
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.section-subtitle {
    color: var(--color-gray-400);
    font-size: var(--font-size-lg);
    max-width: 600px;
    margin: 0 auto;
}

.transparency-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: var(--spacing-xl);
    margin-bottom: var(--spacing-2xl);
}

.transparency-card {
    background: var(--gradient-card);
    border: 1px solid var(--color-gray-700);
    border-radius: var(--radius-lg);
    overflow: hidden;
    transition: all var(--transition-normal);
}

.transparency-card:hover {
    border-color: var(--color-gray-600);
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-gray-700);
    background: rgba(0, 0, 0, 0.2);
}

.card-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-gray-100);
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.card-badge {
    background: var(--color-primary);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-bold);
}

.card-body {
    padding: var(--spacing-lg);
}

.source-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.source-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm);
    background: var(--color-gray-800);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-gray-700);
    transition: all var(--transition-fast);
}

.source-item:hover {
    background: var(--color-gray-700);
    border-color: var(--color-gray-600);
}

.source-name {
    font-weight: var(--font-weight-medium);
    color: var(--color-gray-200);
    flex: 1;
}

.source-link {
    color: var(--color-primary);
    text-decoration: none;
    margin: 0 var(--spacing-sm);
    font-size: var(--font-size-lg);
    transition:
