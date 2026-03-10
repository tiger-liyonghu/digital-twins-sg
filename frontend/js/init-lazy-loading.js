/**
 * 懒加载系统初始化脚本 - Digital Twin SG
 * 国际定价前端设计大师 + 顶级用户体验专家设计
 * 生成时间: 2026-03-08
 */

// 等待DOM完全加载
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Lazy Loading System...');
    
    // 创建全局懒加载器实例
    window.lazyLoader = new LazyLoadingSystem({
        rootMargin: '100px 0px',
        threshold: 0.05,
        preloadDistance: 300,
        cacheTTL: 10 * 60 * 1000, // 10分钟
        maxCacheSize: 15,
        debug: true // 开发模式下启用调试
    });
    
    // 自动注册所有懒加载组件
    autoRegisterComponents();
    
    // 添加性能监控面板
    addPerformancePanel();
    
    // 添加全局加载进度条
    addGlobalProgressBar();
    
    // 监听组件加载事件
    setupComponentListeners();
    
    console.log('✅ Lazy Loading System initialized successfully');
});

/**
 * 自动注册所有懒加载组件
 */
function autoRegisterComponents() {
    // 数据透明度组件
    const transparencyContainers = document.querySelectorAll('[id*="data-transparency"]');
    transparencyContainers.forEach(container => {
        if (container.id && !container.id.includes('container')) {
            window.lazyLoader.registerComponent(
                container.id,
                'components/data-transparency.html',
                {
                    offlineSupport: true,
                    retryable: true,
                    priority: 'high'
                }
            );
        }
    });
    
    // 统一导航组件
    const navContainers = document.querySelectorAll('[id*="unified-navigation"]');
    navContainers.forEach(container => {
        if (container.id && !container.id.includes('container')) {
            window.lazyLoader.registerComponent(
                container.id,
                'components/unified-navigation.html',
                {
                    offlineSupport: false, // 导航需要在线
                    retryable: true,
                    priority: 'critical'
                }
            );
        }
    });
    
    // 统一页脚组件
    const footerContainers = document.querySelectorAll('[id*="unified-footer"]');
    footerContainers.forEach(container => {
        if (container.id && !container.id.includes('container')) {
            window.lazyLoader.registerComponent(
                container.id,
                'components/unified-footer.html',
                {
                    offlineSupport: true,
                    retryable: true,
                    priority: 'low'
                }
            );
        }
    });
    
    // 手动注册的组件容器
    const manualContainers = document.querySelectorAll('[data-lazy-component]');
    manualContainers.forEach(container => {
        const componentUrl = container.getAttribute('data-lazy-component');
        const componentId = container.id || `lazy-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        if (!container.id) {
            container.id = componentId;
        }
        
        const options = {
            offlineSupport: container.getAttribute('data-offline-support') === 'true',
            retryable: container.getAttribute('data-retryable') !== 'false',
            priority: container.getAttribute('data-priority') || 'medium'
        };
        
        window.lazyLoader.registerComponent(componentId, componentUrl, options);
    });
    
    console.log(`📊 Registered ${transparencyContainers.length + navContainers.length + footerContainers.length + manualContainers.length} lazy components`);
}

/**
 * 添加性能监控面板
 */
function addPerformancePanel() {
    // 创建性能面板
    const panelHtml = `
        <div class="lazy-performance-panel" id="lazy-performance-panel">
            <div class="performance-header">
                <div class="performance-title">📊 Lazy Loading Performance</div>
                <button class="performance-toggle" onclick="togglePerformancePanel()">Hide</button>
            </div>
            <div class="performance-metrics" id="performance-metrics">
                <!-- Metrics will be populated dynamically -->
            </div>
            <div class="performance-actions">
                <button class="performance-btn" onclick="refreshPerformanceMetrics()">Refresh</button>
                <button class="performance-btn" onclick="clearComponentCache()">Clear Cache</button>
                <button class="performance-btn" onclick="exportPerformanceReport()">Export</button>
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.insertAdjacentHTML('beforeend', panelHtml);
    
    // 初始更新性能指标
    updatePerformanceMetrics();
    
    // 定期更新性能指标
    setInterval(updatePerformanceMetrics, 5000);
}

/**
 * 更新性能指标显示
 */
function updatePerformanceMetrics() {
    if (!window.lazyLoader) return;
    
    const report = window.lazyLoader.getPerformanceReport();
    const metricsContainer = document.getElementById('performance-metrics');
    
    if (!metricsContainer) return;
    
    const metricsHtml = `
        <div class="metric-item">
            <div class="metric-label">Total Components</div>
            <div class="metric-value">${report.totalComponents}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Loaded</div>
            <div class="metric-value success">${report.loadedComponents}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Cache Hit Rate</div>
            <div class="metric-value ${report.cacheHitRate > 50 ? 'success' : report.cacheHitRate > 20 ? 'warning' : 'error'}">
                ${report.cacheHitRate.toFixed(1)}%
            </div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Avg Load Time</div>
            <div class="metric-value ${report.avgLoadTime < 100 ? 'success' : report.avgLoadTime < 500 ? 'warning' : 'error'}">
                ${report.avgLoadTime.toFixed(0)}ms
            </div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Cache Size</div>
            <div class="metric-value">${report.cacheSize}</div>
        </div>
        <div class="metric-item">
            <div class="metric-label">Errors</div>
            <div class="metric-value ${report.errors === 0 ? 'success' : 'error'}">${report.errors}</div>
        </div>
    `;
    
    metricsContainer.innerHTML = metricsHtml;
}

/**
 * 切换性能面板显示
 */
function togglePerformancePanel() {
    const panel = document.getElementById('lazy-performance-panel');
    const toggleBtn = panel.querySelector('.performance-toggle');
    
    if (panel.classList.contains('hidden')) {
        panel.classList.remove('hidden');
        toggleBtn.textContent = 'Hide';
    } else {
        panel.classList.add('hidden');
        toggleBtn.textContent = 'Show';
    }
}

/**
 * 刷新性能指标
 */
function refreshPerformanceMetrics() {
    updatePerformanceMetrics();
    showPerformanceHint('Performance metrics refreshed');
}

/**
 * 清除组件缓存
 */
function clearComponentCache() {
    if (window.lazyLoader && window.lazyLoader.cache) {
        window.lazyLoader.cache.clear();
        
        // 清除本地存储缓存
        if (typeof localStorage !== 'undefined') {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.startsWith('lazy-component-')) {
                    localStorage.removeItem(key);
                }
            }
        }
        
        showPerformanceHint('Component cache cleared');
        refreshPerformanceMetrics();
    }
}

/**
 * 导出性能报告
 */
function exportPerformanceReport() {
    if (!window.lazyLoader) return;
    
    const report = window.lazyLoader.getPerformanceReport();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `lazy-loading-report-${timestamp}.json`;
    
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    // 创建下载链接
    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(dataBlob);
    downloadLink.download = filename;
    downloadLink.click();
    
    showPerformanceHint('Performance report exported');
}

/**
 * 显示性能提示
 */
function showPerformanceHint(message) {
    // 创建或获取提示元素
    let hint = document.getElementById('lazy-performance-hint');
    if (!hint) {
        hint = document.createElement('div');
        hint.id = 'lazy-performance-hint';
        hint.className = 'lazy-performance-hint';
        document.body.appendChild(hint);
    }
    
    // 更新提示内容
    hint.innerHTML = `
        <span class="hint-icon">💡</span>
        <span class="hint-text">${message}</span>
    `;
    
    // 显示提示
    hint.classList.add('show');
    
    // 3秒后隐藏
    setTimeout(() => {
        hint.classList.remove('show');
    }, 3000);
}

/**
 * 添加全局加载进度条
 */
function addGlobalProgressBar() {
    const progressBarHtml = `
        <div class="lazy-progress-bar" id="global-progress-bar"></div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', progressBarHtml);
    
    // 监听组件加载事件来更新进度条
    document.addEventListener('component:loaded', updateGlobalProgress);
}

/**
 * 更新全局加载进度
 */
function updateGlobalProgress() {
    if (!window.lazyLoader) return;
    
    const progressBar = document.getElementById('global-progress-bar');
    if (!progressBar) return;
    
    const report = window.lazyLoader.getPerformanceReport();
    const progress = report.totalComponents > 0 
        ? (report.loadedComponents / report.totalComponents) 
        : 0;
    
    // 更新进度条
    progressBar.classList.remove('loading', 'complete');
    
    if (progress === 0) {
        // 还没开始加载
    } else if (progress < 1) {
        progressBar.classList.add('loading');
        progressBar.style.transform = `scaleX(${progress * 0.7 + 0.3})`; // 留30%给完成动画
    } else {
        progressBar.classList.add('complete');
        progressBar.style.transform = 'scaleX(1)';
        
        // 3秒后隐藏进度条
        setTimeout(() => {
            progressBar.style.opacity = '0';
            setTimeout(() => {
                progressBar.style.display = 'none';
            }, 300);
        }, 3000);
    }
}

/**
 * 设置组件监听器
 */
function setupComponentListeners() {
    // 监听组件加载完成事件
    document.addEventListener('component:loaded', function(event) {
        const { componentId, container, loadTime } = event.detail;
        
        console.log(`🎉 Component loaded: ${componentId} in ${loadTime.toFixed(2)}ms`);
        
        // 添加加载完成动画
        container.classList.add('component-fade-in');
        
        // 如果是关键组件，触发特定事件
        if (componentId.includes('navigation')) {
            document.dispatchEvent(new CustomEvent('navigation:loaded'));
        } else if (componentId.includes('transparency')) {
            document.dispatchEvent(new CustomEvent('transparency:loaded'));
        } else if (componentId.includes('footer')) {
            document.dispatchEvent(new CustomEvent('footer:loaded'));
        }
    });
    
    // 监听导航加载完成
    document.addEventListener('navigation:loaded', function() {
        console.log('✅ Navigation component fully loaded');
        // 这里可以添加导航特定的初始化代码
    });
    
    // 监听透明度组件加载完成
    document.addEventListener('transparency:loaded', function() {
        console.log('✅ Transparency component fully loaded');
        // 这里可以添加透明度组件特定的初始化代码
    });
    
    // 监听页脚加载完成
    document.addEventListener('footer:loaded', function() {
        console.log('✅ Footer component fully loaded');
        // 这里可以添加页脚特定的初始化代码
    });
}

/**
 * 手动触发组件加载（用于调试）
 */
function forceLoadComponent(componentId) {
    if (window.lazyLoader) {
        const observerData = window.lazyLoader.observers.get(componentId);
        if (observerData) {
            window.lazyLoader.loadComponent(
                componentId,
                observerData.container,
                observerData.componentUrl,
                observerData.options
            );
        }
    }
}

/**
 * 获取所有组件状态
 */
function getComponentStatus() {
    if (!window.lazyLoader) return {};
    
    const status = {
        total: window.lazyLoader.metrics.totalComponents,
        loaded: window.lazyLoader.metrics.loadedComponents,
        loading: Array.from(window.lazyLoader.loading),
        cached: Array.from(window.lazyLoader.cache.keys()),
        observers: Array.from(window.lazyLoader.observers.keys())
    };
    
    return status;
}

/**
 * 预加载所有组件（用于页面可见性变化）
 */
function preloadAllComponents() {
    if (!window.lazyLoader) return;
    
    for (const [componentId, data] of window.lazyLoader.observers.entries()) {
        if (!window.lazyLoader.loading.has(componentId) && !window.lazyLoader.cache.has(componentId)) {
            window.lazyLoader.preloadComponent(componentId, data.componentUrl);
        }
    }
}

// 页面可见性变化时预加载组件
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        preloadAllComponents();
    }
});

// 导出全局函数
window.togglePerformancePanel = togglePerformancePanel;
window.refreshPerformanceMetrics = refreshPerformanceMetrics;
window.clearComponentCache = clearComponentCache;
window.exportPerformanceReport = exportPerformanceReport;
window.forceLoadComponent = forceLoadComponent;
window.getComponentStatus = getComponentStatus;
window.preloadAllComponents = preloadAllComponents;