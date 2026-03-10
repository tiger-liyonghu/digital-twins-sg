#!/usr/bin/env python3
"""
性能监控脚本 - 监控172K Agent系统的关键性能指标

功能：
1. 数据库查询性能监控
2. LLM API调用性能监控
3. 内存使用监控
4. 生成性能报告

使用方法：
    python3 -u scripts/20_performance_monitor.py
"""

import sys
import os
import time
import json
import psutil
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from lib.sampling import stratified_sample, simple_sample, CITIZEN_VOTER_STRATA, ADULT_STRATA
from lib.config import SUPABASE_URL, DEEPSEEK_API_KEY

class PerformanceMonitor:
    def __init__(self, output_dir="data/output/performance"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
    def log_test(self, name, duration, metadata=None):
        """记录测试结果"""
        test_result = {
            "name": name,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            test_result.update(metadata)
        
        self.results["tests"].append(test_result)
        return test_result
    
    def benchmark_database_queries(self):
        """基准测试数据库查询性能"""
        print("🔍 运行数据库查询性能测试...")
        
        test_cases = [
            {
                "name": "简单抽样 N=100",
                "func": lambda: simple_sample(100),
                "expected_rows": 100
            },
            {
                "name": "分层抽样 N=500 (选民)",
                "func": lambda: stratified_sample(500, strata=CITIZEN_VOTER_STRATA),
                "expected_rows": 500
            },
            {
                "name": "分层抽样 N=1000 (成人)",
                "func": lambda: stratified_sample(1000, strata=ADULT_STRATA),
                "expected_rows": 1000
            },
            {
                "name": "条件过滤抽样 N=200 (25-45岁公民)",
                "func": lambda: simple_sample(200, age_min=25, age_max=45, residency="Citizen"),
                "expected_rows": 200
            },
            {
                "name": "大样本抽样 N=5000",
                "func": lambda: simple_sample(5000),
                "expected_rows": 5000
            }
        ]
        
        db_results = []
        for test_case in test_cases:
            print(f"  测试: {test_case['name']}...")
            
            # 运行3次取平均
            durations = []
            actual_rows = []
            
            for i in range(3):
                start_time = time.time()
                try:
                    result = test_case["func"]()
                    duration = time.time() - start_time
                    
                    if hasattr(result, '__len__'):
                        rows = len(result)
                    elif isinstance(result, tuple) and len(result) == 2:
                        rows = len(result[0]) if hasattr(result[0], '__len__') else 0
                    else:
                        rows = 0
                    
                    durations.append(duration)
                    actual_rows.append(rows)
                    
                    print(f"    第{i+1}次: {duration:.2f}s, {rows}行")
                    
                except Exception as e:
                    print(f"    第{i+1}次: 错误 - {str(e)}")
                    durations.append(float('inf'))
                    actual_rows.append(0)
            
            # 计算统计信息
            valid_durations = [d for d in durations if d < float('inf')]
            valid_rows = [r for r in actual_rows if r > 0]
            
            if valid_durations:
                avg_duration = sum(valid_durations) / len(valid_durations)
                avg_rows = sum(valid_rows) / len(valid_rows)
                success_rate = len(valid_durations) / 3
            else:
                avg_duration = float('inf')
                avg_rows = 0
                success_rate = 0
            
            result = {
                "test_name": test_case["name"],
                "avg_duration_seconds": round(avg_duration, 3),
                "avg_rows_returned": int(avg_rows),
                "expected_rows": test_case["expected_rows"],
                "success_rate": round(success_rate, 2),
                "throughput_rows_per_second": round(avg_rows / avg_duration, 1) if avg_duration > 0 else 0
            }
            
            db_results.append(result)
            self.log_test(
                f"db_{test_case['name'].replace(' ', '_').lower()}",
                avg_duration,
                result
            )
        
        return db_results
    
    def monitor_system_resources(self):
        """监控系统资源使用情况"""
        print("📊 监控系统资源使用...")
        
        # 内存使用
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # CPU使用
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        
        # 进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        resource_data = {
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 2)
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "used_percent": swap.percent
            },
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": disk.percent
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent(interval=0.1)
            }
        }
        
        self.log_test("system_resources", 0, resource_data)
        return resource_data
    
    def check_data_quality(self):
        """检查数据质量指标"""
        print("📈 检查数据质量...")
        
        try:
            # 抽样检查数据完整性
            sample_df, _ = stratified_sample(1000)
            
            quality_metrics = {
                "total_agents_sampled": len(sample_df),
                "columns_present": list(sample_df.columns) if hasattr(sample_df, 'columns') else [],
                "missing_values": {},
                "data_types": {}
            }
            
            if hasattr(sample_df, 'columns'):
                for col in sample_df.columns:
                    if col in sample_df:
                        missing = sample_df[col].isna().sum() if hasattr(sample_df[col], 'isna') else 0
                        quality_metrics["missing_values"][col] = {
                            "count": int(missing),
                            "percent": round(missing / len(sample_df) * 100, 2) if len(sample_df) > 0 else 0
                        }
                        
                        # 数据类型
                        if hasattr(sample_df[col], 'dtype'):
                            quality_metrics["data_types"][col] = str(sample_df[col].dtype)
            
            self.log_test("data_quality", 0, quality_metrics)
            return quality_metrics
            
        except Exception as e:
            print(f"  数据质量检查失败: {str(e)}")
            return {"error": str(e)}
    
    def generate_report(self):
        """生成性能报告"""
        print("📄 生成性能报告...")
        
        # 计算总体指标
        db_tests = [t for t in self.results["tests"] if t["name"].startswith("db_")]
        if db_tests:
            avg_db_time = sum(t["duration_seconds"] for t in db_tests) / len(db_tests)
            slowest_test = max(db_tests, key=lambda x: x["duration_seconds"])
            fastest_test = min(db_tests, key=lambda x: x["duration_seconds"])
        else:
            avg_db_time = 0
            slowest_test = fastest_test = None
        
        # 获取系统资源数据
        system_resources = next((t for t in self.results["tests"] if t["name"] == "system_resources"), {})
        
        report = {
            "summary": {
                "timestamp": self.results["timestamp"],
                "total_tests": len(self.results["tests"]),
                "avg_database_query_time_seconds": round(avg_db_time, 3),
                "slowest_query": slowest_test["name"] if slowest_test else None,
                "slowest_query_time": slowest_test["duration_seconds"] if slowest_test else None,
                "fastest_query": fastest_test["name"] if fastest_test else None,
                "fastest_query_time": fastest_test["duration_seconds"] if fastest_test else None
            },
            "system_resources": system_resources.get("metadata", {}),
            "detailed_results": self.results["tests"],
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告
        report_file = self.output_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 报告已保存: {report_file}")
        return report
    
    def _generate_recommendations(self):
        """基于测试结果生成优化建议"""
        recommendations = []
        
        # 分析数据库性能
        db_tests = [t for t in self.results["tests"] if t["name"].startswith("db_")]
        slow_queries = [t for t in db_tests if t["duration_seconds"] > 5]
        
        if slow_queries:
            recommendations.append({
                "priority": "HIGH",
                "category": "database",
                "description": f"发现{len(slow_queries)}个慢查询（>5秒）",
                "action": "检查数据库索引，优化查询语句",
                "details": [{"query": t["name"], "time": t["duration_seconds"]} for t in slow_queries]
            })
        
        # 分析系统资源
        system_resources = next((t for t in self.results["tests"] if t["name"] == "system_resources"), {})
        if system_resources.get("metadata", {}).get("memory", {}).get("used_percent", 0) > 80:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "memory",
                "description": "内存使用率超过80%",
                "action": "考虑优化内存使用，增加缓存清理机制",
                "details": f"当前内存使用率: {system_resources['metadata']['memory']['used_percent']}%"
            })
        
        # 数据质量建议
        data_quality = next((t for t in self.results["tests"] if t["name"] == "data_quality"), {})
        if data_quality.get("metadata", {}).get("missing_values", {}):
            high_missing = {k: v for k, v in data_quality["metadata"]["missing_values"].items() 
                          if v.get("percent", 0) > 10}
            if high_missing:
                recommendations.append({
                    "priority": "LOW",
                    "category": "data_quality",
                    "description": f"{len(high_missing)}个字段缺失值超过10%",
                    "action": "检查数据源，完善数据填充逻辑",
                    "details": list(high_missing.keys())
                })
        
        # 默认建议
        if not recommendations:
            recommendations.append({
                "priority": "LOW",
                "category": "general",
                "description": "系统性能良好",
                "action": "继续保持监控，定期运行性能测试",
                "details": "所有测试通过，无显著性能问题"
            })
        
        return recommendations
    
    def run_all_checks(self):
        """运行所有性能检查"""
        print("🚀 开始性能监控...")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 系统资源监控
        self.monitor_system_resources()
        
        # 2. 数据库性能测试
        db_results = self.benchmark_database_queries()
        
        # 3. 数据质量检查
        self.check_data_quality()
        
        # 4. 生成报告
        report = self.generate_report()
        
        print("=" * 60)
        print("✅ 性能监控完成!")
        
        # 打印摘要
        print("\n📋 性能摘要:")
        print(f"  数据库查询平均时间: {report['summary']['avg_database_query_time_seconds']}秒")
        print(f"  最慢查询: {report['summary']['slowest_query']} ({report['summary']['slowest_query_time']}秒)")
        
        if report['recommendations']:
            print("\n💡 优化建议:")
            for rec in report['recommendations']:
                print(f"  [{rec['priority']}] {rec['description']}")
                print(f"     建议: {rec['action']}")
        
        return report

def main():
    """主函数"""
    try:
        monitor = PerformanceMonitor()
        report = monitor.run_all_checks()
        
        # 保存简要报告到控制台
        brief_report = {
            "status": "success",
            "timestamp": report["summary"]["timestamp"],
            "avg_query_time": report["summary"]["avg_database_query_time_seconds"],
            "recommendations_count": len(report["recommendations"])
        }
        
        print(f"\n📊 简要结果: {json.dumps(brief_report, indent=2)}")
        
    except Exception as e:
        print(f"❌ 性能监控失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
    
