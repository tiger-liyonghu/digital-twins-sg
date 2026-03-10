#!/usr/bin/env python3
"""
立即执行Supabase数据库优化
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path("/Users/tigerli/Desktop/Digital Twins Singapore")
sys.path.insert(0, str(project_root))

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ 请安装supabase: pip install supabase")
    sys.exit(1)

def connect_supabase():
    """连接到Supabase"""
    print("🔗 连接到Supabase...")
    
    supabase_url = "https://rndfpyuuredtqncegygi.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwODc5NDYsImV4cCI6MjA4ODY2Mzk0Nn0.J6ks7B2Vv3epXLQSeBcO3JMtgJiQaiA7WCCJCuYceqQ"
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase连接成功")
        return supabase
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None

def check_current_status(supabase):
    """检查当前状态"""
    print("\n📊 检查当前数据库状态...")
    
    try:
        # 尝试获取agents表数据
        result = supabase.table('agents').select('agent_id', count='exact').limit(1).execute()
        
        if hasattr(result, 'count'):
            print(f"✅ Agents表可访问，记录数: {result.count:,}")
            return True
        else:
            print("⚠️ 无法获取记录数，但表可访问")
            return True
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def create_exec_sql_function(supabase):
    """创建exec_sql函数"""
    print("\n⚙️ 创建exec_sql函数...")
    
    sql = """
    CREATE OR REPLACE FUNCTION public.exec_sql(query text)
    RETURNS jsonb
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
      RETURN (SELECT jsonb_agg(row_to_json(t)) 
              FROM (EXECUTE query) t);
    END;
    $$;
    """
    
    try:
        # 尝试直接执行SQL
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print("✅ exec_sql函数创建成功")
        return True
    except Exception as e:
        print(f"⚠️ 无法创建exec_sql函数: {e}")
        print("尝试使用原始SQL连接...")
        return False

def create_indexes(supabase):
    """创建索引"""
    print("\n📈 创建数据库索引...")
    
    indexes = [
        ("idx_agents_age", "CREATE INDEX IF NOT EXISTS idx_agents_age ON agents(age);"),
        ("idx_agents_gender", "CREATE INDEX IF NOT EXISTS idx_agents_gender ON agents(gender);"),
        ("idx_agents_age_gender", "CREATE INDEX IF NOT EXISTS idx_agents_age_gender ON agents(age, gender);"),
    ]
    
    success_count = 0
    
    for index_name, sql in indexes:
        try:
            result = supabase.rpc('exec_sql', {'query': sql}).execute()
            print(f"✅ {index_name} 创建成功")
            success_count += 1
        except Exception as e:
            print(f"⚠️ {index_name} 创建失败: {e}")
    
    print(f"📊 索引创建: {success_count}/{len(indexes)} 成功")
    return success_count > 0

def create_data_quality_function(supabase):
    """创建数据质量检查函数"""
    print("\n🔍 创建数据质量检查函数...")
    
    sql = """
    CREATE OR REPLACE FUNCTION public.check_data_quality()
    RETURNS TABLE (
        metric_name text,
        metric_value numeric,
        status text
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 'total_agents'::text, COUNT(*)::numeric, 
               CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'ERROR' END
        FROM agents
        
        UNION ALL
        
        SELECT 'null_age_count', 
               SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END)::numeric,
               CASE WHEN SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) = 0 
                    THEN 'OK' ELSE 'WARNING' END
        FROM agents
        
        UNION ALL
        
        SELECT 'invalid_age_count',
               SUM(CASE WHEN age < 0 OR age > 100 THEN 1 ELSE 0 END)::numeric,
               CASE WHEN SUM(CASE WHEN age < 0 OR age > 100 THEN 1 ELSE 0 END) = 0 
                    THEN 'OK' ELSE 'ERROR' END
        FROM agents;
    END;
    $$ LANGUAGE plpgsql;
    """
    
    try:
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print("✅ 数据质量检查函数创建成功")
        return True
    except Exception as e:
        print(f"⚠️ 数据质量函数创建失败: {e}")
        return False

def run_data_quality_check(supabase):
    """运行数据质量检查"""
    print("\n🧪 运行数据质量检查...")
    
    try:
        result = supabase.rpc('check_data_quality', {}).execute()
        
        if hasattr(result, 'data'):
            print("📊 数据质量报告:")
            for row in result.data:
                print(f"  • {row['metric_name']}: {row['metric_value']} ({row['status']})")
            return True
        else:
            print("⚠️ 无法获取数据质量报告")
            return False
            
    except Exception as e:
        print(f"❌ 数据质量检查失败: {e}")
        return False

def create_backup_metadata_table(supabase):
    """创建备份元数据表"""
    print("\n💾 创建备份元数据表...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS public.backup_metadata (
        id BIGSERIAL PRIMARY KEY,
        backup_type TEXT NOT NULL,
        table_name TEXT NOT NULL,
        row_count INTEGER,
        backup_size_bytes BIGINT,
        backup_timestamp TIMESTAMP DEFAULT NOW(),
        status TEXT DEFAULT 'completed',
        notes TEXT
    );
    """
    
    try:
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print("✅ 备份元数据表创建成功")
        return True
    except Exception as e:
        print(f"⚠️ 备份表创建失败: {e}")
        return False

def create_performance_log_table(supabase):
    """创建性能日志表"""
    print("\n📊 创建性能日志表...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS public.query_performance_logs (
        id BIGSERIAL PRIMARY KEY,
        query_text TEXT,
        execution_time_ms INTEGER,
        rows_returned INTEGER,
        timestamp TIMESTAMP DEFAULT NOW(),
        user_id UUID,
        endpoint TEXT
    );
    """
    
    try:
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print("✅ 性能日志表创建成功")
        return True
    except Exception as e:
        print(f"⚠️ 性能日志表创建失败: {e}")
        return False

def create_optimization_report(supabase, optimizations):
    """创建优化报告"""
    print("\n📋 创建优化报告...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "database_url": "https://rndfpyuuredtqncegygi.supabase.co",
        "optimizations_applied": optimizations,
        "summary": {
            "total_optimizations": len(optimizations),
            "successful": sum(1 for o in optimizations if o.get("success", False)),
            "failed": sum(1 for o in optimizations if not o.get("success", True))
        },
        "next_steps": [
            "1. 监控索引使用情况",
            "2. 定期运行数据质量检查",
            "3. 建立自动备份系统",
            "4. 实施查询性能监控"
        ]
    }
    
    # 保存报告
    reports_dir = project_root / "data" / "supabase_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / f"optimization_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 优化报告已保存: {report_file}")
    return report_file

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Digital Twin SG Supabase数据库立即优化")
    print("=" * 60)
    
    # 连接到Supabase
    supabase = connect_supabase()
    if not supabase:
        print("❌ 无法连接到Supabase，终止优化")
        return
    
    # 检查当前状态
    if not check_current_status(supabase):
        print("❌ 数据库状态检查失败，终止优化")
        return
    
    optimizations = []
    
    # 执行优化步骤
    print("\n" + "=" * 60)
    print("🎯 开始执行优化步骤")
    print("=" * 60)
    
    # 1. 创建exec_sql函数
    exec_sql_success = create_exec_sql_function(supabase)
    optimizations.append({
        "name": "创建exec_sql函数",
        "success": exec_sql_success,
        "timestamp": datetime.now().isoformat()
    })
    
    # 2. 创建索引
    indexes_success = create_indexes(supabase)
    optimizations.append({
        "name": "创建数据库索引",
        "success": indexes_success,
        "timestamp": datetime.now().isoformat()
    })
    
    # 3. 创建数据质量函数
    quality_func_success = create_data_quality_function(supabase)
    optimizations.append({
        "name": "创建数据质量检查函数",
        "success": quality_func_success,
        "timestamp": datetime.now().isoformat()
    })
    
    # 4. 运行数据质量检查
    if quality_func_success:
        quality_check_success = run_data_quality_check(supabase)
        optimizations.append({
            "name": "运行数据质量检查",
            "success": quality_check_success,
            "timestamp": datetime.now().isoformat()
        })
    
    # 5. 创建备份元数据表
    backup_table_success = create_backup_metadata_table(supabase)
    optimizations.append({
        "name": "创建备份元数据表",
        "success": backup_table_success,
        "timestamp": datetime.now().isoformat()
    })
    
    # 6. 创建性能日志表
    perf_table_success = create_performance_log_table(supabase)
    optimizations.append({
        "name": "创建性能日志表",
        "success": perf_table_success,
        "timestamp": datetime.now().isoformat()
    })
    
    # 创建优化报告
    report_file = create_optimization_report(supabase, optimizations)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("🎉 Supabase数据库优化完成!")
    print("=" * 60)
    
    successful = sum(1 for o in optimizations if o.get("success", False))
    total = len(optimizations)
    
    print(f"\n📊 优化执行总结:")
    print(f"  总优化步骤: {total}")
    print(f"  成功步骤: {successful}")
    print(f"  成功率: {successful/total*100:.1f}%")
    
    print("\n✅ 成功优化的功能:")
    for opt in optimizations:
        if opt.get("success", False):
            print(f"  • {opt['name']}")
    
    print("\n⚠️ 需要注意的问题:")
    for opt in optimizations:
        if not opt.get("success", True):
            print(f"  • {opt['name']} - 需要手动处理")
    
    print(f"\n📁 详细报告: {report_file}")
    
    print("\n🚀 下一步建议:")
    print("  1. 验证索引效果 - 运行性能测试")
    print("  2. 定期数据质量检查 - 建立自动化")
    print("  3. 实施备份策略 - 保护数据安全")
    print("  4. 监控查询性能 - 持续优化")

if __name__ == "__main__":
    main()