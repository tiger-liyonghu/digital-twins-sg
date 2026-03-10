/**
 * 快速性能测试脚本
 * 测试懒加载系统的实际效果
 */

console.log('🚀 开始懒加载系统性能测试...');

// 性能测试配置
const TEST_CONFIG = {
    testUrl: 'http://localhost:8889/test-lazy-loading.html',
    iterations: 3,
    warmupIterations: 1,
    metrics: {
        firstContentfulPaint: null,
        largestContentfulPaint: null,
        firstInputDelay: null,
        cumulativeLayoutShift: null,
        totalBlockingTime: null
    }
};

// 运行性能测试
async function runPerformanceTest() {
    console.log('📊 性能测试配置:', TEST_CONFIG);
    
    try {
        // 预热
        console.log('🔥 预热运行...');
        for (let i = 0; i < TEST_CONFIG.warmupIterations; i++) {
            await loadPage();
        }
        
        // 正式测试
        console.log('🧪 开始正式性能测试...');
        const results = [];
        
        for (let i = 0; i < TEST_CONFIG.iterations; i++) {
            console.log(`\n📈 测试迭代 ${i + 1}/${TEST_CONFIG.iterations}`);
            const result = await runSingleTest();
            results.push(result);
            
            // 显示当前结果
            console.log('当前结果:', {
                loadTime: result.loadTime,
                componentCount: result.componentCount,
                cacheHits: result.cacheHits
            });
            
            // 等待一下再进行下一次测试
            await sleep(2000);
        }
        
        // 分析结果
        analyzeResults(results);
        
    } catch (error) {
        console.error('❌ 性能测试失败:', error);
    }
}

// 加载页面
async function loadPage() {
    return new Promise((resolve) => {
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = TEST_CONFIG.testUrl;
        
        iframe.onload = () => {
            console.log('✅ 页面加载完成');
            setTimeout(() => {
                document.body.removeChild(iframe);
                resolve();
            }, 1000);
        };
        
        document.body.appendChild(iframe);
    });
}

// 运行单次测试
async function runSingleTest() {
    return new Promise((resolve) => {
        const startTime = performance.now();
        
        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.top = '0';
        iframe.style.left = '0';
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.style.zIndex = '9999';
        iframe.src = TEST_CONFIG.testUrl;
        
        let loadTime = 0;
        let componentCount = 0;
        let cacheHits = 0;
        
        iframe.onload = () => {
            loadTime = performance.now() - startTime;
            console.log(`⏱️ 页面加载时间: ${loadTime.toFixed(2)}ms`);
            
            // 尝试从iframe中获取性能数据
            try {
                const iframeWindow = iframe.contentWindow;
                if (iframeWindow && iframeWindow.lazyLoader) {
                    const report = iframeWindow.lazyLoader.getPerformanceReport();
                    componentCount = report.totalComponents;
                    cacheHits = report.cachedHits;
                    
                    console.log(`📊 组件统计: ${componentCount}个组件, ${cacheHits}次缓存命中`);
                }
            } catch (e) {
                console.warn('⚠️ 无法访问iframe性能数据:', e.message);
            }
            
            // 等待组件加载
            setTimeout(() => {
                document.body.removeChild(iframe);
                resolve({
                    loadTime,
                    componentCount,
                    cacheHits,
                    timestamp: Date.now()
                });
            }, 3000);
        };
        
        document.body.appendChild(iframe);
    });
}

// 分析结果
function analyzeResults(results) {
    console.log('\n📈 ===== 性能测试结果分析 =====');
    
    // 计算平均值
    const avgLoadTime = results.reduce((sum, r) => sum + r.loadTime, 0) / results.length;
    const avgComponents = results.reduce((sum, r) => sum + r.componentCount, 0) / results.length;
    const avgCacheHits = results.reduce((sum, r) => sum + r.cacheHits, 0) / results.length;
    
    console.log(`📊 平均加载时间: ${avgLoadTime.toFixed(2)}ms`);
    console.log(`📊 平均组件数: ${avgComponents.toFixed(1)}个`);
    console.log(`📊 平均缓存命中: ${avgCacheHits.toFixed(1)}次`);
    
    // 计算标准差
    const loadTimeStdDev = Math.sqrt(
        results.reduce((sum, r) => sum + Math.pow(r.loadTime - avgLoadTime, 2), 0) / results.length
    );
    
    console.log(`📊 加载时间标准差: ${loadTimeStdDev.toFixed(2)}ms`);
    
    // 性能评估
    console.log('\n🎯 ===== 性能评估 =====');
    
    if (avgLoadTime < 1000) {
        console.log('✅ 优秀: 加载时间 < 1秒');
    } else if (avgLoadTime < 2000) {
        console.log('⚠️ 良好: 加载时间 1-2秒');
    } else {
        console.log('❌ 需要优化: 加载时间 > 2秒');
    }
    
    if (avgCacheHits > 0) {
        const cacheHitRate = (avgCacheHits / avgComponents) * 100;
        console.log(`📊 缓存命中率: ${cacheHitRate.toFixed(1)}%`);
        
        if (cacheHitRate > 50) {
            console.log('✅ 优秀: 缓存命中率 > 50%');
        } else if (cacheHitRate > 20) {
            console.log('⚠️ 良好: 缓存命中率 20-50%');
        } else {
            console.log('❌ 需要优化: 缓存命中率 < 20%');
        }
    }
    
    // 生成建议
    console.log('\n💡 ===== 优化建议 =====');
    
    if (avgLoadTime > 1500) {
        console.log('1. 🔧 考虑进一步优化组件大小');
        console.log('2. 🔧 增加预加载距离');
        console.log('3. 🔧 优化缓存策略');
    }
    
    if (avgCacheHits < avgComponents * 0.3) {
        console.log('4. 🔧 提高缓存命中率');
        console.log('5. 🔧 优化组件注册顺序');
        console.log('6. 🔧 考虑服务端渲染关键组件');
    }
    
    // 保存结果
    const testResult = {
        timestamp: new Date().toISOString(),
        config: TEST_CONFIG,
        results: results,
        summary: {
            avgLoadTime,
            avgComponents,
            avgCacheHits,
            loadTimeStdDev
        }
    };
    
    // 尝试保存到本地存储
    try {
        const history = JSON.parse(localStorage.getItem('lazyLoadTestHistory') || '[]');
        history.push(testResult);
        localStorage.setItem('lazyLoadTestHistory', JSON.stringify(history.slice(-10))); // 保留最近10次
        console.log('💾 测试结果已保存到本地存储');
    } catch (e) {
        console.warn('⚠️ 无法保存到本地存储:', e.message);
    }
    
    // 显示结果摘要
    displayResultSummary(testResult);
}

// 显示结果摘要
function displayResultSummary(result) {
    const summaryDiv = document.createElement('div');
    summaryDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        color: white;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        z-index: 10000;
        max-width: 400px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    `;
    
    const { summary } = result;
    
    summaryDiv.innerHTML = `
        <h3 style="margin: 0 0 15px 0; color: #06b6d4; font-size: 16px;">🚀 懒加载性能测试结果</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div>
                <div style="font-size: 11px; color: #94a3b8;">平均加载时间</div>
                <div style="font-size: 20px; font-weight: bold; color: ${summary.avgLoadTime < 1000 ? '#22c55e' : summary.avgLoadTime < 2000 ? '#eab308' : '#ef4444'}">
                    ${summary.avgLoadTime.toFixed(0)}ms
                </div>
            </div>
            <div>
                <div style="font-size: 11px; color: #94a3b8;">缓存命中率</div>
                <div style="font-size: 20px; font-weight: bold; color: ${summary.avgCacheHits > 0 ? '#22c55e' : '#eab308'}">
                    ${summary.avgComponents > 0 ? ((summary.avgCacheHits / summary.avgComponents) * 100).toFixed(1) : 0}%
                </div>
            </div>
        </div>
        
        <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">
            测试时间: ${new Date(result.timestamp).toLocaleTimeString()}
        </div>
        
        <div style="display: flex; gap: 10px;">
            <button onclick="runPerformanceTest()" style="
                background: #06b6d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                flex: 1;
            ">重新测试</button>
            <button onclick="this.parentElement.parentElement.remove()" style="
                background: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                flex: 1;
            ">关闭</button>
        </div>
    `;
    
    document.body.appendChild(summaryDiv);
}

// 工具函数
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 导出函数
window.runPerformanceTest = runPerformanceTest;

// 自动运行测试
console.log('⏰ 3秒后开始性能测试...');
setTimeout(() => {
    runPerformanceTest();
}, 3000);

// 添加测试页面链接
const testLink = document.createElement('a');
testLink.href = TEST_CONFIG.testUrl;
testLink.target = '_blank';
testLink.textContent = '📊 打开测试页面';
testLink.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #06b6d4;
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    z-index: 9999;
    box-shadow: 0 4px 20px rgba(6, 182, 212, 0.3);
`;

document.body.appendChild(testLink);

console.log('✅ 性能测试脚本加载完成');
console.log('💡 使用方法:');
console.log('1. 点击右下角的"打开测试页面"');
console.log('2. 等待3秒后自动开始性能测试');
console.log('3. 查看右上角的测试结果');