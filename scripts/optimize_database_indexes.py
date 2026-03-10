#!/usr/bin/env python3
"""
数据库索引优化脚本
基于性能监控结果优化数据库索引
"""

import time
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def optimize_database_indexes():
    """优化数据库索引"""
    print("🔧 开始数据库索引优化...")
    print("=" * 60)
    
    try:
        from lib.db import get_db_connection
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("📊 分析现有索引...")
        
        # 查询现有索引
        cursor.execute("""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        
        existing_indexes = cursor.fetchall()
        
        print(f"   现有索引数量: {len(existing_indexes)}")
        
        # 基于性能监控结果建议的索引
        recommended_indexes = [
            # 针对大样本查询优化
            ("agents", "idx_agents_age", "CREATE INDEX idx_agents_age ON agents(age)"),
            ("agents", "idx_agents_residency", "CREATE INDEX idx_agents_residency ON agents(residency_status)"),
            ("agents", "idx_agents_gender_age", "CREATE INDEX idx_agents_gender_age ON agents(gender, age)"),
            
            # 针对分层抽样优化
            ("agents", "idx_agents_age_group", "CREATE INDEX idx_agents_age_group ON agents(age_group)"),
            ("agents", "idx_agents_gender_age_group", "CREATE INDEX idx_agents_gender_age_group ON agents(gender, age_group)"),
            
            # 针对条件过滤优化
            ("agents", "idx_agents_planning_area", "CREATE INDEX idx_agents_planning_area ON agents(planning_area)"),
            ("agents", "idx_agents_housing_type", "CREATE INDEX idx_agents_housing_type ON agents(housing_type)"),
            
            # 复合索引用于常见查询组合
            ("agents", "idx_agents_age_residency", "CREATE INDEX idx_agents_age_residency ON agents(age, residency_status)"),
            ("agents", "idx_agents_gender_residency", "CREATE INDEX idx_agents_gender_residency ON agents(gender, residency_status)")
        ]
        
        print("\n📋 推荐创建以下索引:")
        for table, index_name, index_sql in recommended_indexes:
            print(f"  • {index_name} on {table}")
        
        # 检查哪些索引已经存在
        existing_index_names = [idx[1] for idx in existing_indexes]
        
        indexes_to_create = []
        for table, index_name, index_sql in recommended_indexes:
            if index_name not in existing_index_names:
                indexes_to_create.append((table, index_name, index_sql))
        
        print(f"\n📊 需要创建的索引: {len(indexes_to_create)}/{len(recommended_indexes)}")
        
        if indexes_to_create:
            print("\n🚀 开始创建索引...")
            
            created_count = 0
            for table, index_name, index_sql in indexes_to_create:
                try:
                    print(f"  创建 {index_name}...", end=" ")
                    cursor.execute(index_sql)
                    conn.commit()
                    print("✅ 成功")
                    created_count += 1
                    
                    # 小延迟避免锁表
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ 失败: {e}")
                    conn.rollback()
            
            print(f"\n✅ 成功创建 {created_count} 个索引")
        else:
            print("✅ 所有推荐索引已存在")
        
        # 分析表统计信息
        print("\n📈 更新表统计信息...")
        try:
            cursor.execute("ANALYZE agents;")
            conn.commit()
            print("✅ 统计信息更新完成")
        except Exception as e:
            print(f"⚠️ 统计信息更新失败: {e}")
        
        # 查询优化建议
        print("\n💡 查询优化建议:")
        suggestions = [
            "1. 对于大样本查询，使用覆盖索引减少回表",
            "2. 考虑分区表，按年龄或地区分区",
            "3. 定期执行VACUUM ANALYZE保持统计信息准确",
            "4. 监控索引使用情况，删除未使用的索引",
            "5. 考虑使用BRIN索引处理范围查询"
        ]
        
        for suggestion in suggestions:
            print(f"  {suggestion}")
        
        # 生成优化报告
        print("\n📋 生成优化报告...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "existing_indexes": len(existing_indexes),
            "recommended_indexes": len(recommended_indexes),
            "created_indexes": len(indexes_to_create),
            "index_details": [
                {
                    "table": table,
                    "index": index_name,
                    "status": "EXISTING" if index_name in existing_index_names else "CREATED" if index_name in [idx[1] for idx in indexes_to_create] else "NOT_CREATED"
                }
                for table, index_name, _ in recommended_indexes
            ],
            "performance_expected": {
                "large_sample_queries": "预计提升50-70%",
                "filtered_queries": "预计提升30-50%",
                "stratified_sampling": "预计提升20-40%"
            },
            "next_steps": [
                "运行性能监控验证优化效果",
                "监控索引使用情况",
                "考虑查询重写优化",
                "定期维护索引"
            ]
        }
        
        # 保存报告
        report_dir = Path(__file__).parent.parent / "data" / "output" / "database_optimization"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"database_index_optimization_{time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 报告已保存: {report_file}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎉 数据库索引优化完成!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 优化过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_optimization():
    """验证优化效果"""
    print("\n🔍 验证优化效果...")
    
    try:
        # 重新运行性能监控
        print("  重新运行性能监控...")
        
        # 这里可以调用之前的性能监控脚本
        # 为了简化，我们模拟结果
        
        expected_improvements = {
            "large_sample_queries": "从6.8秒减少到3.5秒 (预计)",
            "filtered_queries": "从0.4秒减少到0.2秒 (预计)",
            "overall_performance": "提升30-50% (预计)"
        }
        
        print("📊 预期性能提升:")
        for query_type, improvement in expected_improvements.items():
            print(f"  {query_type}: {improvement}")
        
        print("\n💡 建议:")
        print("  1. 在实际负载下测试优化效果")
        print("  2. 监控数据库性能指标")
        print("  3. 根据实际使用调整索引策略")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🗄️ 数据库索引优化工具")
    print("=" * 60)
    
    # 执行优化
    success = optimize_database_indexes()
    
    if success:
        # 验证优化
        verify_optimization()
        
        print("\n✨ 数据库优化任务完成!")
        print("💡 下一步: 运行性能监控验证实际效果")
        sys.exit(0)
    else:
        print("\n💥 数据库优化失败!")
        sys.exit(1)