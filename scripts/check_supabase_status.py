#!/usr/bin/env python3
"""
检查Supabase数据库状态和优化
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
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请安装: pip install supabase pandas numpy")
    sys.exit(1)

def connect_to_supabase():
    """连接到Supabase"""
    print("🔗 连接到Supabase数据库...")
    
    # 从.env文件读取配置
    env_file = project_root / ".env"
    supabase_url = None
    supabase_key = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith("SUPABASE_URL="):
                    supabase_url = line.strip().split("=", 1)[1]
                elif line.startswith("SUPABASE_KEY="):
                    supabase_key = line.strip().split("=", 1)[1]
    
    # 如果.env中没有，使用用户提供的
    if not supabase_url:
        supabase_url = "https://rndfpyuuredtqncegygi.supabase.co"

    if not supabase_key:
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJuZGZweXV1cmVkdHFuY2VneWdpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwODc5NDYsImV4cCI6MjA4ODY2Mzk0Nn0.J6ks7B2Vv3epXLQSeBcO3JMtgJiQaiA7WCCJCuYceqQ"
    
    print(f"📡 URL: {supabase_url}")
    print(f"🔑 Key: {supabase_key[:20]}...")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase连接成功")
        return supabase
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None

def check_database_structure(supabase):
    """检查数据库结构"""
    print("\n📊 检查数据库结构...")
    
    # 获取所有表
    try:
        # 使用SQL查询获取表信息
        query = """
        SELECT 
            table_name,
            table_type,
            (SELECT COUNT(*) FROM information_schema.columns 
             WHERE table_name = tables.table_name) as column_count
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        
        if hasattr(result, 'data'):
            tables = result.data
            print(f"📋 找到 {len(tables)} 个表:")
            
            for table in tables:
                print(f"  • {table['table_name']} ({table['column_count']}列)")
        
        return True
    except Exception as e:
        print(f"⚠️ 无法获取表信息: {e}")
        return False

def check_agents_table(supabase):
    """检查Agents表状态"""
    print("\n👥 检查Agents表...")
    
    try:
        # 获取记录数量
        count_result = supabase.table('agents').select('agent_id', count='exact').execute()
        agent_count = count_result.count if hasattr(count_result, 'count') else 0
        
        print(f"📊 Agents数量: {agent_count:,}")
        
        # 获取样本数据
        sample_result = supabase.table('agents').select('*').limit(5).execute()
        
        if hasattr(sample_result, 'data') and sample_result.data:
            print("🔍 样本数据:")
            for i, agent in enumerate(sample_result.data[:3], 1):
                print(f"  Agent {i}: ID={agent.get('agent_id', 'N/A')}, "
                      f"Age={agent.get('age', 'N/A')}, "
                      f"Gender={agent.get('gender', 'N/A')}")
        
        # 检查列信息
        print("\n📈 统计信息:")
        try:
            # 年龄分布
            age_result = supabase.table('agents').select('age').execute()
            if hasattr(age_result, 'data'):
                ages = [a['age'] for a in age_result.data if 'age' in a]
                if ages:
                    print(f"  • 年龄范围: {min(ages)}-{max(ages)}岁")
                    print(f"  • 平均年龄: {np.mean(ages):.1f}岁")
            
            # 性别分布
            gender_result = supabase.table('agents').select('gender').execute()
            if hasattr(gender_result, 'data'):
                genders = [g['gender'] for g in gender_result.data if 'gender' in g]
                if genders:
                    male_count = genders.count('M')
                    female_count = genders.count('F')
                    total = len(genders)
                    print(f"  • 性别分布: M={male_count/total*100:.1f}%, F={female_count/total*100:.1f}%")
        
        except Exception as e:
            print(f"⚠️ 统计信息获取失败: {e}")
        
        return agent_count
        
    except Exception as e:
        print(f"❌ Agents表检查失败: {e}")
        return 0

def check_performance_issues(supabase):
    """检查性能问题"""
    print("\n⚡ 检查性能问题...")
    
    issues = []
    
    try:
        # 检查索引
        query = """
        SELECT 
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
        """
        
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        
        if hasattr(result, 'data'):
            indexes = result.data
            print(f"📊 找到 {len(indexes)} 个索引")
            
            # 检查agents表索引
            agent_indexes = [idx for idx in indexes if idx['tablename'] == 'agents']
            print(f"  • agents表索引: {len(agent_indexes)}个")
            
            if len(agent_indexes) < 3:
                issues.append({
                    'type': 'performance',
                    'severity': 'high',
                    'issue': 'agents表索引不足',
                    'details': f'只有{len(agent_indexes)}个索引，建议添加更多索引优化查询'
                })
        
        # 检查表大小
        size_query = """
        SELECT 
            table_name,
            pg_size_pretty(pg_total_relation_size('"' || table_schema || '"."' || table_name || '"')) as total_size,
            pg_size_pretty(pg_relation_size('"' || table_schema || '"."' || table_name || '"')) as table_size
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY pg_total_relation_size('"' || table_schema || '"."' || table_name || '"') DESC;
        """
        
        size_result = supabase.rpc('exec_sql', {'query': size_query}).execute()
        
        if hasattr(size_result, 'data'):
            print("\n💾 表大小信息:")
            for table in size_result.data[:5]:
                print(f"  • {table['table_name']}: {table['total_size']}")
        
    except Exception as e:
        print(f"⚠️ 性能检查失败: {e}")
        issues.append({
            'type': 'connection',
            'severity': 'medium',
            'issue': '性能检查失败',
            'details': str(e)
        })
    
    return issues

def check_data_quality(supabase, agent_count):
    """检查数据质量"""
    print("\n🔍 检查数据质量...")
    
    quality_issues = []
    
    try:
        # 检查缺失值
        null_check_query = """
        SELECT 
            'agents' as table_name,
            COUNT(*) as total_rows,
            SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) as null_age,
            SUM(CASE WHEN gender IS NULL THEN 1 ELSE 0 END) as null_gender,
            SUM(CASE WHEN ethnicity IS NULL THEN 1 ELSE 0 END) as null_ethnicity,
            SUM(CASE WHEN residency_status IS NULL THEN 1 ELSE 0 END) as null_residency
        FROM agents;
        """
        
        null_result = supabase.rpc('exec_sql', {'query': null_check_query}).execute()
        
        if hasattr(null_result, 'data') and null_result.data:
            stats = null_result.data[0]
            total = stats['total_rows']
            
            print(f"📊 数据完整性检查 (共{total}行):")
            
            checks = [
                ('age', '年龄'),
                ('gender', '性别'),
                ('ethnicity', '种族'),
                ('residency_status', '居民状态')
            ]
            
            for field, name in checks:
                null_count = stats.get(f'null_{field}', 0)
                null_percent = null_count / total * 100 if total > 0 else 0
                
                if null_count > 0:
                    quality_issues.append({
                        'type': 'data_quality',
                        'severity': 'high' if null_percent > 5 else 'medium',
                        'issue': f'{name}缺失值',
                        'details': f'{null_count}行({null_percent:.1f}%)缺少{name}'
                    })
                    print(f"  ⚠️ {name}: {null_count}行缺失 ({null_percent:.1f}%)")
                else:
                    print(f"  ✅ {name}: 无缺失值")
        
        # 检查数据有效性
        validity_query = """
        SELECT 
            COUNT(*) as invalid_age_count
        FROM agents
        WHERE age < 0 OR age > 100;
        """
        
        validity_result = supabase.rpc('exec_sql', {'query': validity_query}).execute()
        
        if hasattr(validity_result, 'data') and validity_result.data:
            invalid_age = validity_result.data[0].get('invalid_age_count', 0)
            if invalid_age > 0:
                quality_issues.append({
                    'type': 'data_quality',
                    'severity': 'high',
                    'issue': '无效年龄数据',
                    'details': f'{invalid_age}行年龄不在0-100范围内'
                })
                print(f"  ⚠️ 无效年龄: {invalid_age}行")
            else:
                print(f"  ✅ 年龄有效性: 所有数据在0-100范围内")
        
    except Exception as e:
        print(f"⚠️ 数据质量检查失败: {e}")
        quality_issues.append({
            'type': 'connection',
            'severity': 'medium',
            'issue': '数据质量检查失败',
            'details': str(e)
        })
    
    return quality_issues

def generate_optimization_recommendations(agent_count, issues, quality_issues):
    """生成优化建议"""
    print("\n🎯 生成优化建议...")
    
    recommendations = []
    
    # 基于agent数量的建议
    if agent_count > 100000:
        recommendations.append({
            'priority': 'P0',
            'category': 'performance',
            'recommendation': '分区表优化',
            'reason': f'数据量巨大({agent_count:,}行)，建议按年龄组或区域分区',
            'benefit': '查询性能提升50-70%'
        })
    
    if agent_count > 50000:
        recommendations.append({
            'priority': 'P0',
            'category': 'performance',
            'recommendation': '添加复合索引',
            'reason': '大表需要优化常用查询组合',
            'benefit': '联合查询性能提升30-50%'
        })
    
    # 基于问题的建议
    for issue in issues:
        if issue['type'] == 'performance' and '索引不足' in issue['issue']:
            recommendations.append({
                'priority': 'P0',
                'category': 'performance',
                'recommendation': '创建缺失索引',
                'reason': issue['details'],
                'benefit': '查询性能显著提升'
            })
    
    for issue in quality_issues:
        if issue['type'] == 'data_quality':
            recommendations.append({
                'priority': 'P1',
                'category': 'data_quality',
                'recommendation': '数据清洗和验证',
                'reason': issue['details'],
                'benefit': '提高数据可靠性和分析准确性'
            })
    
    # 通用建议
    recommendations.extend([
        {
            'priority': 'P1',
            'category': 'monitoring',
            'recommendation': '建立性能监控',
            'reason': '监控查询性能和资源使用',
            'benefit': '及时发现和解决性能问题'
        },
        {
            'priority': 'P1',
            'category': 'backup',
            'recommendation': '定期备份策略',
            'reason': f'保护{agent_count:,}行重要数据',
            'benefit': '数据安全和灾难恢复'
        },
        {
            'priority': 'P2',
            'category': 'scalability',
            'recommendation': '读写分离考虑',
            'reason': '高并发场景下的性能优化',
            'benefit': '提高系统吞吐量'
        }
    ])
    
    # 打印建议
    print("📋 优化建议清单:")
    for rec in recommendations:
        print(f"\n[{rec['priority']}] {rec['recommendation']}")
        print(f"   类别: {rec['category']}")
        print(f"   原因: {rec['reason']}")
        print(f"   收益: {rec['benefit']}")
    
    return recommendations

def save_analysis_report(agent_count, issues, quality_issues, recommendations):
    """保存分析报告"""
    print("\n💾 保存分析报告...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_url': 'https://rndfpyuuredtqncegygi.supabase.co',
        'analysis_summary': {
            'agent_count': agent_count,
            'performance_issues': len(issues),
            'data_quality_issues': len(quality_issues),
            'recommendations': len(recommendations)
        },
        'agent_statistics': {
            'total_agents': agent_count,
            'data_scale': f'{agent_count:,}行数据'
        },
        'performance_issues': issues,
        'data_quality_issues': quality_issues,
        'optimization_recommendations': recommendations,
        'next_steps': [
            '1. 实施P0优先级优化建议',
            '2. 建立性能监控系统',
            '3. 定期运行数据质量检查',
            '4. 考虑数据分区策略'
        ]
    }
    
    # 保存报告
    reports_dir = project_root / "data" / "supabase_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / f"supabase_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分析报告已保存: {report_file}")
    
    return report_file

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 Digital Twin SG Supabase数据库分析")
    print("=" * 60)
    
    # 连接到Supabase
    supabase = connect_to_supabase()
    if not supabase:
        print("❌ 无法连接到Supabase，请检查配置")
        return
    
    try:
        # 检查数据库结构
        check_database_structure(supabase)
        
        # 检查Agents表
        agent_count = check_agents_table(supabase)
        
        # 检查性能问题
        issues = check_performance_issues(supabase)
        
        # 检查数据质量
        quality_issues = check_data_quality(supabase, agent_count)
        
        # 生成优化建议
        recommendations = generate_optimization_recommendations(agent_count, issues, quality_issues)
        
        # 保存报告
        report_file = save_analysis_report(agent_count, issues, quality_issues, recommendations)
        
        print("\n" + "=" * 60)
        print("🎉 Supabase数据库分析完成!")
        print("=" * 60)
        
        print(f"\n📊 分析摘要:")
        print(f"  • Agents数量: {agent_count:,}")
        print(f"  • 性能问题: {len(issues)}个")
        print(f"  • 数据质量问题: {len(quality_issues)}个")
        print(f"  • 优化建议: {len(recommendations)}个")
        
        print(f"\n📁 报告位置: {report_file}")
        
        print("\n🚀 立即行动建议:")
        print("  1. 查看分析报告了解详细问题")
        print("  2. 实施P0优先级优化建议")
        print("  3. 建立定期检查机制")
        
    except Exception as e:
        print(f"\n❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()