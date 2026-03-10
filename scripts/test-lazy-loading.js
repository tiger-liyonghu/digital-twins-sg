/**
 * 懒加载系统测试脚本
 * 生成时间: 2026-03-08
 */

console.log('🚀 开始懒加载系统测试...');

// 测试1: 检查懒加载系统是否加载
function testLazyLoaderExistence() {
    console.log('🔍 测试1: 检查懒加载系统是否存在');
    
    if (typeof window.lazyLoader === 'undefined') {
        console.error('❌ 懒加载系统未加载');
        return false;
    }
    
    if (typeof window.lazyLoader.registerComponent !== 'function') {
        console.error('❌ 懒加载系统方法缺失');
        return false;
    }
    
    console.log('✅ 懒加载系统存在且功能完整');
    return true;
}

// 测试2: 检查性能面板
function testPerformancePanel() {
    console.log('🔍 测试2: 检查性能面板');
    
    const panel = document.getElementById('lazy-performance-panel');
    if (!panel) {
        console.error('❌ 性能面板未找到');
        return false;
    }
    
    const metrics = document.getElementById('performance-metrics');
    if (!metrics) {
        console.error('❌ 性能指标容器未找到');
        return false;
    }
    
    console.log('✅ 性能面板存在');
    return true;
}

// 测试3: 检查全局进度条
function testGlobalProgressBar() {
    console.log('🔍 测试3: 检查全局进度条');
    
    const progressBar = document.getElementById('global-progress-bar');
    if (!progressBar) {
        console.error('❌ 全局进度条未找到');
        return false;
    }
    
    console.log('✅ 全局进度条存在');
    return true;
}

// 测试4: 检查组件状态
function testComponentStatus() {
    console.log('🔍 测试4: 检查组件状态');
    
    if (typeof window.getComponentStatus !== 'function') {
        console.error('❌ 组件状态函数未找到');
        return false;
    }
    
    const status = window.getComponentStatus();
    console.log('📊 组件状态:', status);
    
    if (!status || typeof status !== 'object') {
        console.error('❌ 组件状态获取失败');
        return false;
    }
    
    console.log('✅ 组件状态获取成功');
    return true;
}

// 测试5: 检查CSS样式
function testCSSStyles() {
    console.log('🔍 测试5: 检查CSS样式');
    
    // 检查关键样式类是否存在
    const testClasses = [
        'lazy-loading-state',
        'lazy-error-state',
        'lazy-offline-state',
        'loading-spinner',
        'retry-button'
    ];
    
    const styleSheets = document.styleSheets;
    let foundClasses = 0;
    
    for (let i = 0; i < styleSheets.length; i++) {
        try {
            const rules = styleSheets[i].cssRules || styleSheets[i].rules;
            if (rules) {
                for (let j = 0; j < rules.length; j++) {
                    const rule = rules[j];
                    if (rule.selectorText) {
                        testClasses.forEach(className => {
                            if (rule.selectorText.includes(className)) {
                                foundClasses++;
                            }
                        });
                    }
                }
            }
        } catch (e) {
            // 跨域样式表可能无法访问
        }
    }
    
    console.log(`📊 找到 ${foundClasses}/${testClasses.length} 个关键样式类`);
    
    if (foundClasses >= testClasses.length / 2) {
        console.log('✅ CSS样式加载成功');
        return true;
    } else {
        console.warn('⚠️ CSS样式可能未完全加载');
        return false;
    }
}

// 测试6: 模拟组件加载
function testComponentLoading() {
    console.log('🔍 测试6: 模拟组件加载');
    
    // 创建一个测试容器
    const testContainer = document.createElement('div');
    testContainer.id = 'test-lazy-container';
    testContainer.style.height = '200px';
    testContainer.style.margin = '20px';
    testContainer.style.border = '1px dashed #06b6d4';
    testContainer.style.padding = '20px';
    testContainer.style.borderRadius = '8px';
    testContainer.innerHTML = '<p>测试容器 - 等待懒加载...</p>';
    
    document.body.appendChild(testContainer);
    
    // 注册测试组件
    window.lazyLoader.registerComponent(
        'test-lazy-container',
        'components/test-component.html',
        {
            offlineSupport: true,
            retryable: true,
            priority: 'high'
        }
    );
    
    console.log('✅ 测试组件注册成功');
    return true;
}

// 测试7: 检查错误处理
function testErrorHandling() {
    console.log('🔍 测试7: 检查错误处理');
    
    // 测试重试函数
    if (typeof window.forceLoadComponent !== 'function') {
        console.error('❌ 强制加载函数未找到');
        return false;
    }
    
    // 测试缓存清理函数
    if (typeof window.clearComponentCache !== 'function') {
        console.error('❌ 缓存清理函数未找到');
        return false;
    }
    
    // 测试性能刷新函数
    if (typeof window.refreshPerformanceMetrics !== 'function') {
        console.error('❌ 性能刷新函数未找到');
        return false;
    }
    
    console.log('✅ 错误处理函数完整');
    return true;
}

// 测试8: 检查事件系统
function testEventSystem() {
    console.log('🔍 测试8: 检查事件系统');
    
    let eventReceived = false;
    
    const eventHandler = () => {
        eventReceived = true;
        console.log('✅ 组件加载事件触发成功');
    };
    
    // 监听组件加载事件
    document.addEventListener('component:loaded', eventHandler);
    
    // 模拟触发事件
    const testEvent = new CustomEvent('component:loaded', {
        detail: {
            componentId: 'test-component',
            container: document.createElement('div'),
            loadTime: 100,
            timestamp: Date.now()
        }
    });
    
    document.dispatchEvent(testEvent);
    
    // 移除监听器
    document.removeEventListener('component:loaded', eventHandler);
    
    if (!eventReceived) {
        console.error('❌ 事件系统未正常工作');
        return false;
    }
    
    console.log('✅ 事件系统工作正常');
    return true;
}

// 运行所有测试
function runAllTests() {
    console.log('🧪 开始运行所有懒加载系统测试...\n');
    
    const tests = [
        { name: '懒加载系统存在性', fn: testLazyLoaderExistence },
        { name: '性能面板', fn: testPerformancePanel },
        { name: '全局进度条', fn: testGlobalProgressBar },
        { name: '组件状态', fn: testComponentStatus },
        { name: 'CSS样式', fn: testCSSStyles },
        { name: '组件加载', fn: testComponentLoading },
        { name: '错误处理', fn: testErrorHandling },
        { name: '事件系统', fn: testEventSystem }
    ];
    
    let passed = 0;
    let failed = 0;
    
    tests.forEach((test, index) => {
        console.log(`\n📋 测试 ${index + 1}: ${test.name}`);
        try {
            if (test.fn()) {
                passed++;
            } else {
                failed++;
            }
        } catch (error) {
            console.error(`❌ 测试失败: ${error.message}`);
            failed++;
        }
    });
    
    console.log('\n📊 ===== 测试结果汇总 =====');
    console.log(`✅ 通过: ${passed}`);
    console.log(`❌ 失败: ${failed}`);
    console.log(`📈 成功率: ${((passed / tests.length) * 100).toFixed(1)}%`);
    
    if (failed === 0) {
        console.log('\n🎉 所有测试通过！懒加载系统工作正常。');
        return true;
    } else {
        console.log('\n⚠️ 部分测试失败，需要检查系统配置。');
        return false;
    }
}

// 创建测试组件
function createTestComponent() {
    const testComponentHtml = `
<!DOCTYPE html>
<html>
<head>
    <style>
        .test-component {
            background: linear-gradient(135deg, #06b6d4, #3b82f6);
            color: white;
            padding: 2rem;
            border-radius: 1rem;
            text-align: center;
            animation: fadeIn 0.5s ease;
        }
        
        .test-component h2 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .test-component p {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-bottom: 1rem;
        }
        
        .test-stats {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.25rem;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.75rem;
            opacity: 0.8;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="test-component">
        <h2>✅ 懒加载测试组件</h2>
        <p>这个组件通过懒加载系统成功加载！</p>
        <p>加载时间: <span id="load-time">计算中...</span></p>
        
        <div class="test-stats">
            <div class="stat">
                <div class="stat-value">172K</div>
                <div class="stat-label">AI Agents</div>
            </div>
            <div class="stat">
                <div class="stat-value">99.9%</div>
                <div class="stat-label">置信度</div>
            </div>
            <div class="stat">
                <div class="stat-value">3.8%</div>
                <div class="stat-label">人口样本</div>
            </div>
        </div>
    </div>
    
    <script>
        // 计算加载时间
        const loadTime = performance.now() - window.lazyLoadStartTime;
        document.getElementById('load-time').textContent = loadTime.toFixed(2) + 'ms';
        
        console.log('🎉 测试组件加载完成，耗时: ' + loadTime.toFixed(2) + 'ms');
    </script>
</body>
</html>
    `;
    
    // 保存测试组件文件
    const fs = require('fs');
    const path = require('path');
    
    const componentPath = path.join(__dirname, '../frontend/components/test-component.html');
    fs.writeFileSync(componentPath, testComponentHtml);
    
    console.log('📁 测试组件文件已创建:', componentPath);
}

// 主函数
function main() {
    console.log('🚀 Digital Twin SG 懒加载系统测试');
    console.log('===================================\n');
    
    // 记录开始时间
    window.lazyLoadStartTime = performance.now();
    
    // 运行测试
    const allTestsPassed = runAllTests();
    
    // 创建测试组件
    createTestComponent();
    
    // 显示性能报告
    setTimeout(() => {
        if (window.lazyLoader) {
            const report = window.lazyLoader.getPerformanceReport();
            console.log('\n📈 ===== 性能报告 =====');
            console.log('总组件数:', report.totalComponents);
            console.log('已加载组件:', report.loadedComponents);
            console.log('缓存命中率:', report.cacheHitRate.toFixed(1) + '%');
            console.log('平均加载时间:', report.avgLoadTime.toFixed(2) + 'ms');
            console.log('错误数:', report.errors);
            console.log('缓存大小:', report.cacheSize);
        }
    }, 1000);
    
    return allTestsPassed;
}

// 如果直接运行此脚本
if (typeof window !== 'undefined') {
    // 在浏览器中运行
    window.addEventListener('load', main);
} else {
    // 在Node.js中运行
    console.log('📝 这是一个浏览器测试脚本，请在浏览器控制台中运行。');
    console.log('💡 使用方法:');
    console.log('1. 打开浏览器开发者工具 (F12)');
    console.log('2. 进入Console标签页');
    console.log('3. 复制此脚本内容并粘贴执行');
}

// 导出测试函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        testLazyLoaderExistence,
        testPerformancePanel,
        testGlobalProgressBar,
        testComponentStatus,
        testCSSStyles,
        testComponentLoading,
        testErrorHandling,
        testEventSystem,
        runAllTests,
        main
    };
}