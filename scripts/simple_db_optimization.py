#!/usr/bin/env python3
"""
简化版数据库优化 - 直接使用SQL优化
"""

import time
import json
import sys
from pathlib import Path

def generate_optimization_sql():
    """生成优化SQL脚本"""
    
    print("🔧 生成数据库优化SQL脚本...")
    print("=" * 60)
    
    optimization_sql = """
-- ============================================
-- Digital Twin SG 数据库优化脚本
-- 生成时间: {timestamp}
-- 目标: 优化172K Agent系统性能
-- ============================================

-- 1. 创建缺失的索引
CREATE INDEX IF NOT EXISTS idx_agents_age ON agents(age);
CREATE INDEX IF NOT EXISTS idx_agents_residency ON agents(residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age ON agents(gender, age);
CREATE INDEX IF NOT EXISTS idx_agents_age_group ON agents(age_group);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age_group ON agents(gender, age_group);
CREATE INDEX IF NOT EXISTS idx_agents_planning_area ON agents(planning_area);
CREATE INDEX IF NOT EXISTS idx_agents_housing_type ON agents(housing_type);
CREATE INDEX IF NOT EXISTS idx_agents_age_residency ON agents(age, residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_residency ON agents(gender, residency_status);

-- 2. 分析表统计信息
ANALYZE agents;

-- 3. 查询现有索引状态
-- SELECT * FROM pg_indexes WHERE tablename = 'agents';

-- 4. 性能监控查询
-- 检查大样本查询性能
EXPLAIN ANALYZE SELECT * FROM agents LIMIT 5000;

-- 检查条件过滤查询性能  
EXPLAIN ANALYZE SELECT * FROM agents WHERE age BETWEEN 25 AND 45 AND residency_status = 'Citizen' LIMIT 200;

-- 5. 索引使用情况监控
-- SELECT * FROM pg_stat_user_indexes WHERE relname = 'agents';
""".format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 保存SQL文件
    sql_dir = Path(__file__).parent.parent / "data" / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    
    sql_file = sql_dir / f"database_optimization_{time.strftime('%Y%m%d_%H%M%S')}.sql"
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(optimization_sql)
    
    print(f"✅ SQL脚本已生成: {sql_file}")
    
    # 生成优化报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "optimization_type": "database_indexes",
        "recommended_indexes": [
            {"name": "idx_agents_age", "table": "agents", "columns": ["age"], "purpose": "年龄过滤查询"},
            {"name": "idx_agents_residency", "table": "agents", "columns": ["residency_status"], "purpose": "居民状态过滤"},
            {"name": "idx_agents_gender_age", "table": "agents", "columns": ["gender", "age"], "purpose": "性别和年龄联合查询"},
            {"name": "idx_agents_age_group", "table": "agents", "columns": ["age_group"], "purpose": "年龄组分层抽样"},
            {"name": "idx_agents_gender_age_group", "table": "agents", "columns": ["gender", "age_group"], "purpose": "性别和年龄组联合查询"},
            {"name": "idx_agents_planning_area", "table": "agents", "columns": ["planning_area"], "purpose": "规划区域过滤"},
            {"name": "idx_agents_housing_type", "table": "agents", "columns": ["housing_type"], "purpose": "住房类型过滤"},
            {"name": "idx_agents_age_residency", "table": "agents", "columns": ["age", "residency_status"], "purpose": "年龄和居民状态联合查询"},
            {"name": "idx_agents_gender_residency", "table": "agents", "columns": ["gender", "residency_status"], "purpose": "性别和居民状态联合查询"}
        ],
        "expected_improvements": {
            "large_sample_queries": "50-70% 性能提升",
            "filtered_queries": "30-50% 性能提升", 
            "stratified_sampling": "20-40% 性能提升",
            "overall_performance": "30-50% 性能提升"
        },
        "implementation_steps": [
            "1. 在Supabase控制台执行SQL脚本",
            "2. 运行性能监控验证效果",
            "3. 监控索引使用情况",
            "4. 根据实际使用调整索引策略"
        ],
        "monitoring_metrics": [
            "查询响应时间",
            "索引使用频率",
            "数据库负载",
            "内存使用情况"
        ]
    }
    
    report_dir = Path(__file__).parent.parent / "data" / "output" / "optimization_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"db_optimization_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 优化报告已生成: {report_file}")
    
    # 打印摘要
    print("\n📋 优化摘要:")
    print(f"  推荐索引数量: {len(report['recommended_indexes'])}")
    print(f"  预期性能提升: {report['expected_improvements']['overall_performance']}")
    
    print("\n💡 执行步骤:")
    for step in report["implementation_steps"]:
        print(f"  {step}")
    
    return sql_file, report_file

def create_quick_optimization_guide():
    """创建快速优化指南"""
    
    print("\n📘 创建快速优化指南...")
    
    guide = f"""# Digital Twin SG 数据库优化指南

## 📅 优化时间
{time.strftime("%Y-%m-%d %H:%M:%S")}

## 🎯 优化目标
基于性能监控结果，优化172K Agent系统的数据库性能。

## 📊 性能问题识别
根据性能监控报告：
- 大样本查询 (5000行): 6.8秒 (需要优化)
- 条件过滤查询: 0.4秒 (良好)
- 分层抽样查询: 1.8秒 (可优化)

## 🔧 推荐优化措施

### 1. 索引优化
```sql
-- 执行以下索引创建语句
CREATE INDEX IF NOT EXISTS idx_agents_age ON agents(age);
CREATE INDEX IF NOT EXISTS idx_agents_residency ON agents(residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age ON agents(gender, age);
CREATE INDEX IF NOT EXISTS idx_agents_age_group ON agents(age_group);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age_group ON agents(gender, age_group);
CREATE INDEX IF NOT EXISTS idx_agents_planning_area ON agents(planning_area);
CREATE INDEX IF NOT EXISTS idx_agents_housing_type ON agents(housing_type);
CREATE INDEX IF NOT EXISTS idx_agents_age_residency ON agents(age, residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_residency ON agents(gender, residency_status);
```

### 2. 统计信息更新
```sql
ANALYZE agents;
```

### 3. 性能验证
运行性能监控脚本验证优化效果：
```bash
python3 -u scripts/20_performance_monitor.py
```

## 📈 预期效果

| 查询类型 | 优化前 | 优化后 | 提升幅度 |
|---------|--------|--------|----------|
| 大样本查询 | 6.8秒 | 3.5秒 | 50% |
| 条件过滤 | 0.4秒 | 0.2秒 | 50% |
| 分层抽样 | 1.8秒 | 1.2秒 | 33% |

## 🔍 监控指标

1. **查询响应时间**: 使用性能监控脚本
2. **索引使用率**: 检查pg_stat_user_indexes
3. **数据库负载**: 监控CPU和内存使用
4. **查询计划**: 使用EXPLAIN ANALYZE

## 🚀 下一步行动

1. **立即执行**: 在Supabase控制台运行优化SQL
2. **验证效果**: 运行性能监控对比结果
3. **持续监控**: 建立定期性能检查机制
4. **优化调整**: 根据实际使用调整索引策略

## 📞 技术支持
如有问题，请联系技术团队或参考性能监控报告。
"""
    
    guide_dir = Path(__file__).parent.parent / "docs"
    guide_dir.mkdir(parents=True, exist_ok=True)
    
    guide_file = guide_dir / f"database_optimization_guide_{time.strftime('%Y%m%d')}.md"
    
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"✅ 优化指南已生成: {guide_file}")
    
    return guide_file

if __name__ == "__main__":
    print("=" * 60)
    print("🗄️ 简化版数据库优化工具")
    print("=" * 60)
    
    try:
        # 生成SQL脚本和报告
        sql_file, report_file = generate_optimization_sql()
        
        # 创建优化指南
        guide_file = create_quick_optimization_guide()
        
        print("\n" + "=" * 60)
        print("🎉 数据库优化准备完成!")
        print("=" * 60)
        
        print("\n📁 生成的文件:")
        print(f"  • SQL脚本: {sql_file}")
        print(f"  • 优化报告: {report_file}")
        print(f"  • 优化指南: {guide_file}")
        
        print("\n💡 执行步骤:")
        print("  1. 登录Supabase控制台")
        print("  2. 进入SQL编辑器")
        print("  3. 复制并执行生成的SQL脚本")
        print("  4. 运行性能监控验证效果")
        
        print("\n✨ 任务完成!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ 优化准备失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)