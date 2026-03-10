/**
 * 组件懒加载系统 - Digital Twin SG
 * 国际定价前端设计大师 + 顶级用户体验专家设计
 * 生成时间: 2026-03-08
 * 
 * 功能:
 * 1. 组件按需加载 (Intersection Observer)
 * 2. 智能预加载 (Viewport预测)
 * 3. 缓存管理 (LocalStorage + Memory)
 * 4. 性能监控 (加载时间跟踪)
 * 5. 错误处理 (优雅降级)
 */

class LazyLoadingSystem {
    constructor(options = {}) {
        // 默认配置
        this.config = {
            rootMargin: '50px 0px',
            threshold: 0.1,
            preloadDistance: 200, // 像素
            cacheTTL: 5 * 60 * 1000, // 5分钟
            maxCacheSize: 10, // 最大缓存组件数
            debug: false,
            ...options
        };

        // 状态管理
        this.observers = new Map();
        this.cache = new Map();
        this.loading = new Set();
        this.metrics = {
            totalComponents: 0,
            loadedComponents: 0,
            cachedHits: 0,
            loadTimes: [],
            errors: 0
        };

        // 初始化
        this.init();
    }

    /**
     * 初始化系统
     */
    init() {
        console.log('🚀 LazyLoadingSystem initialized');
        
        // 清理过期缓存
        this.cleanupCache();
        
        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.resumeLoading();
            }
        });

        // 监听网络状态变化
        window.addEventListener('online', () => this.handleNetworkOnline());
        window.addEventListener('offline', () => this.handleNetworkOffline());

        // 性能监控
        this.startPerformanceMonitoring();
    }

    /**
     * 注册组件进行懒加载
     * @param {string} containerId - 容器元素ID
     * @param {string} componentUrl - 组件URL
     * @param {Object} options - 加载选项
     */
    registerComponent(containerId, componentUrl, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container not found: ${containerId}`);
            return;
        }

        const componentId = `${containerId}-${componentUrl}`;
        this.metrics.totalComponents++;

        // 检查缓存
        if (this.checkCache(componentId)) {
            this.loadFromCache(componentId, container);
            return;
        }

        // 创建观察器
        const observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries, componentId, container, componentUrl, options),
            this.config
        );

        observer.observe(container);
        this.observers.set(componentId, { observer, container, componentUrl, options });

        // 预加载如果接近视口
        this.checkPreload(container, componentId, componentUrl, options);
    }

    /**
     * 处理交叉观察
     */
    handleIntersection(entries, componentId, container, componentUrl, options) {
        entries.forEach(entry => {
            if (entry.isIntersecting && !this.loading.has(componentId)) {
                this.loadComponent(componentId, container, componentUrl, options);
                
                // 停止观察已加载的组件
                const observerData = this.observers.get(componentId);
                if (observerData) {
                    observerData.observer.unobserve(container);
                    this.observers.delete(componentId);
                }
            }
        });
    }

    /**
     * 加载组件
     */
    async loadComponent(componentId, container, componentUrl, options) {
        const startTime = performance.now();
        this.loading.add(componentId);

        try {
            // 检查网络状态
            if (!navigator.onLine && !options.offlineSupport) {
                this.showOfflineMessage(container);
                return;
            }

            // 显示加载状态
            this.showLoadingState(container);

            // 获取组件
            const response = await fetch(componentUrl, {
                signal: AbortSignal.timeout(10000), // 10秒超时
                headers: {
                    'Accept': 'text/html',
                    'Cache-Control': 'max-age=300' // 5分钟缓存
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const html = await response.text();
            const loadTime = performance.now() - startTime;

            // 更新容器内容
            container.innerHTML = html;
            
            // 缓存组件
            this.cacheComponent(componentId, html);
            
            // 执行组件脚本
            this.executeComponentScripts(container);
            
            // 触发加载完成事件
            this.triggerComponentLoaded(componentId, container, loadTime);
            
            // 更新指标
            this.updateMetrics(componentId, loadTime, true);

            if (this.config.debug) {
                console.log(`✅ Component loaded: ${componentId} (${loadTime.toFixed(2)}ms)`);
            }

        } catch (error) {
            this.handleLoadError(error, componentId, container, options);
            this.updateMetrics(componentId, performance.now() - startTime, false);
        } finally {
            this.loading.delete(componentId);
        }
    }

    /**
     * 检查并预加载组件
     */
    checkPreload(container, componentId, componentUrl, options) {
        const rect = container.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        // 如果组件在预加载距离内
        if (rect.top < viewportHeight + this.config.preloadDistance) {
            if (this.config.debug) {
                console.log(`🔍 Preloading component: ${componentId}`);
            }
            
            // 低优先级预加载
            requestIdleCallback(() => {
                if (!this.loading.has(componentId) && !this.cache.has(componentId)) {
                    this.preloadComponent(componentId, componentUrl);
                }
            });
        }
    }

    /**
     * 预加载组件
     */
    async preloadComponent(componentId, componentUrl) {
        try {
            const response = await fetch(componentUrl, {
                priority: 'low',
                headers: { 'Accept': 'text/html' }
            });
            
            if (response.ok) {
                const html = await response.text();
                this.cacheComponent(componentId, html);
                
                if (this.config.debug) {
                    console.log(`📦 Component preloaded: ${componentId}`);
                }
            }
        } catch (error) {
            // 静默失败，预加载不影响主流程
            if (this.config.debug) {
                console.warn(`⚠️ Preload failed: ${componentId}`, error);
            }
        }
    }

    /**
     * 缓存组件
     */
    cacheComponent(componentId, html) {
        const cacheEntry = {
            html,
            timestamp: Date.now(),
            size: new Blob([html]).size
        };

        // 内存缓存
        this.cache.set(componentId, cacheEntry);

        // 本地存储缓存 (如果支持)
        if (typeof localStorage !== 'undefined') {
            try {
                const cacheKey = `lazy-component-${componentId}`;
                localStorage.setItem(cacheKey, JSON.stringify(cacheEntry));
            } catch (e) {
                // 本地存储可能已满，清理旧缓存
                this.cleanupLocalStorage();
            }
        }

        // 限制缓存大小
        if (this.cache.size > this.config.maxCacheSize) {
            this.evictOldestCache();
        }
    }

    /**
     * 检查缓存
     */
    checkCache(componentId) {
        // 检查内存缓存
        if (this.cache.has(componentId)) {
            const entry = this.cache.get(componentId);
            if (Date.now() - entry.timestamp < this.config.cacheTTL) {
                return true;
            } else {
                this.cache.delete(componentId);
            }
        }

        // 检查本地存储缓存
        if (typeof localStorage !== 'undefined') {
            try {
                const cacheKey = `lazy-component-${componentId}`;
                const cached = localStorage.getItem(cacheKey);
                
                if (cached) {
                    const entry = JSON.parse(cached);
                    if (Date.now() - entry.timestamp < this.config.cacheTTL) {
                        this.cache.set(componentId, entry);
                        return true;
                    } else {
                        localStorage.removeItem(cacheKey);
                    }
                }
            } catch (e) {
                // 忽略本地存储错误
            }
        }

        return false;
    }

    /**
     * 从缓存加载
     */
    loadFromCache(componentId, container) {
        const entry = this.cache.get(componentId);
        if (!entry) return;

        const startTime = performance.now();
        
        // 更新容器内容
        container.innerHTML = entry.html;
        
        // 执行组件脚本
        this.executeComponentScripts(container);
        
        // 触发加载完成事件
        const loadTime = performance.now() - startTime;
        this.triggerComponentLoaded(componentId, container, loadTime);
        
        // 更新指标
        this.metrics.cachedHits++;
        this.metrics.loadedComponents++;
        this.metrics.loadTimes.push(loadTime);

        if (this.config.debug) {
            console.log(`⚡ Component loaded from cache: ${componentId} (${loadTime.toFixed(2)}ms)`);
        }
    }

    /**
     * 执行组件内的脚本
     */
    executeComponentScripts(container) {
        const scripts = container.querySelectorAll('script');
        scripts.forEach(script => {
            const newScript = document.createElement('script');
            
            // 复制所有属性
            Array.from(script.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            
            // 复制内容
            if (script.textContent) {
                newScript.textContent = script.textContent;
            }
            
            // 替换原脚本
            script.parentNode.replaceChild(newScript, script);
        });
    }

    /**
     * 显示加载状态
     */
    showLoadingState(container) {
        const loadingHtml = `
            <div class="lazy-loading-state">
                <div class="loading-spinner"></div>
                <div class="loading-text">Loading component...</div>
            </div>
        `;
        
        // 只在容器为空时显示加载状态
        if (!container.innerHTML.trim()) {
            container.innerHTML = loadingHtml;
        }
    }

    /**
     * 显示离线消息
     */
    showOfflineMessage(container) {
        const offlineHtml = `
            <div class="lazy-offline-state">
                <div class="offline-icon">📶</div>
                <div class="offline-text">You're offline. Component will load when connection is restored.</div>
            </div>
        `;
        
        container.innerHTML = offlineHtml;
    }

    /**
     * 处理加载错误
     */
    handleLoadError(error, componentId, container, options) {
        console.error(`❌ Failed to load component ${componentId}:`, error);
        this.metrics.errors++;

        const errorHtml = `
            <div class="lazy-error-state">
                <div class="error-icon">⚠️</div>
                <div class="error-title">Component Load Failed</div>
                <div class="error-message">${error.message}</div>
                ${options.retryable !== false ? `
                    <button class="retry-button" onclick="window.lazyLoader.retryComponent('${componentId}')">
                        Retry Loading
                    </button>
                ` : ''}
            </div>
        `;
        
        container.innerHTML = errorHtml;
    }

    /**
     * 重试加载组件
     */
    retryComponent(componentId) {
        const observerData = this.observers.get(componentId);
        if (observerData) {
            this.loadComponent(componentId, observerData.container, observerData.componentUrl, observerData.options);
        }
    }

    /**
     * 触发组件加载完成事件
     */
    triggerComponentLoaded(componentId, container, loadTime) {
        const event = new CustomEvent('component:loaded', {
            detail: {
                componentId,
                container,
                loadTime,
                timestamp: Date.now()
            }
        });
        
        container.dispatchEvent(event);
        document.dispatchEvent(event);
    }

    /**
     * 更新性能指标
     */
    updateMetrics(componentId, loadTime, success) {
        if (success) {
            this.metrics.loadedComponents++;
            this.metrics.loadTimes.push(loadTime);
        }
    }

    /**
     * 清理过期缓存
     */
    cleanupCache() {
        const now = Date.now();
        
        // 清理内存缓存
        for (const [key, entry] of this.cache.entries()) {
            if (now - entry.timestamp > this.config.cacheTTL) {
                this.cache.delete(key);
            }
        }
        
        // 清理本地存储缓存
        if (typeof localStorage !== 'undefined') {
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('lazy-component-')) {
                        const cached = localStorage.getItem(key);
                        if (cached) {
                            const entry = JSON.parse(cached);
                            if (now - entry.timestamp > this.config.cacheTTL) {
                                localStorage.removeItem(key);
                            }
                        }
                    }
                }
            } catch (e) {
                // 忽略本地存储错误
            }
        }
    }

    /**
     * 清理本地存储
     */
    cleanupLocalStorage() {
        if (typeof localStorage !== 'undefined') {
            try {
                // 删除最旧的缓存项
                const cacheKeys = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('lazy-component-')) {
                        cacheKeys.push(key);
                    }
                }
                
                // 按时间排序并删除最旧的
                cacheKeys.sort((a, b) => {
                    const aData = JSON.parse(localStorage.getItem(a));
                    const bData = JSON.parse(localStorage.getItem(b));
                    return aData.timestamp - bData.timestamp;
                });
                
                // 保留最新的5个
                while (cacheKeys.length > 5) {
                    const oldestKey = cacheKeys.shift();
                    localStorage.removeItem(oldestKey);
                }
            } catch (e) {
                // 忽略错误
            }
        }
    }

    /**
     * 淘汰最旧的缓存
     */
    evictOldestCache() {
        let oldestKey = null;
        let oldestTime = Infinity;
        
        for (const [key, entry] of this.cache.entries()) {
            if (entry.timestamp < oldestTime) {
                oldestTime = entry.timestamp;
                oldestKey = key;
            }
        }
        
        if (oldestKey) {
            this.cache.delete(oldestKey);
        }
    }

    /**
     * 处理网络在线
     */
    handleNetworkOnline() {
        console.log('🌐 Network is back online');
        
        // 重试所有失败的加载
        document.querySelectorAll('.lazy-error-state .retry-button').forEach(button => {
            button.click();
        });
    }

    /**
     * 处理网络离线
     */
    handleNetworkOffline() {
        console.log('📴 Network is offline');
        
        // 暂停所有正在进行的加载
        this.loading.clear();
    }

    /**
     * 恢复加载
     */
    resumeLoading() {
        // 重新观察所有未加载的组件
        for (const [componentId, data] of this.observers.entries()) {
            if (!this.loading.has(componentId)) {
                data.observer.observe(data.container);
            }
        }
    }

    /**
     * 开始性能监控
     */
    startPerformanceMonitoring() {
        // 定期报告性能指标
        setInterval(() => {
            if (this.metrics.loadTimes.length > 0) {
                const avgLoadTime = this.metrics.loadTimes.reduce((a, b) => a + b, 0) / this.metrics.loadTimes.length;
                const cacheHitRate = this.metrics.cachedHits / this.metrics.loadedComponents * 100;
                
                if (this.config.debug) {
                    console.log('📊 Performance Metrics:', {
                        totalComponents: this.metrics.totalComponents,
                        loadedComponents: this.metrics.loadedComponents,
                        cacheHitRate: `${cacheHitRate.toFixed(1)}%`,
                        avgLoadTime: `${avgLoadTime.toFixed(2)}ms`,
                        errors: this.metrics.errors
                    });
                }
            }
        }, 30000); // 每30秒报告一次
    }

    /**
     * 获取性能报告
     */
    getPerformanceReport() {
        const avgLoadTime = this.metrics.loadTimes.length > 0 
            ? this.metrics.loadTimes.reduce((a, b) => a + b, 0) / this.metrics.loadTimes.length 
            : 0;
        
        const cacheHitRate = this.metrics.loadedComponents > 0
            ? (this.metrics.cachedHits / this.metrics.loadedComponents * 100)
            : 0;
        
        return {
            totalComponents: this.metrics.totalComponents,
            loadedComponents: this.metrics.loadedComponents,
            cacheHitRate: cacheHitRate,
            avgLoadTime: avgLoadTime,
            errors: this.metrics.errors,
            cacheSize: this.cache.size,
            loadingCount: this.loading.size
        };
    }

    /**
     * 销毁系统
     */
    destroy() {
        // 停止所有观察器
        for (const [_, data] of this.observers.entries()) {
            data.observer.disconnect();
        }
        
        this.observers.clear();
        this.loading.clear();
        
        // 移除事件监听器
        document.removeEventListener('visibilitychange', this.resume