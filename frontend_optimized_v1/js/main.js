// main.js - 应用主入口
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
});