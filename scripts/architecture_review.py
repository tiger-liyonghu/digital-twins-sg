#!/usr/bin/env python3
"""
Digital Twin SG 前端架构专业审查
国际定价前端设计大师 + 顶级用户体验专家视角
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re
from bs4 import BeautifulSoup

class FrontendArchitectReview:
    """前端架构审查系统"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.frontend_dir = self.project_root / "frontend"
        self.review_results = {
            "timestamp": datetime.now().isoformat(),
            "reviewer": "国际定价前端设计大师 + 顶级用户体验专家团队",
            "project": "Digital Twin SG - AI Agent市场研究平台",
            "product_goals": [
                "Benchmark against global leading products",
                "Mathematical rigor",
                "Maximize prediction accuracy", 
                "Be truthful and transparent",
                "Simple and trustworthy front-end interface"
            ],
            "pages": {},
            "architecture_issues": [],
            "ux_issues": [],
            "performance_issues": [],
            "accessibility_issues": [],
            "recommendations": [],
            "priority_actions": []
        }
    
    def analyze_page_structure(self):
        """分析页面结构关系"""
        print("📊 分析页面结构关系...")
        
        pages = [
            ("index.html", "首页 - 营销页面"),
            ("dashboard.html", "仪表板 - 主应用界面"),
            ("simulation.html", "模拟分析 - 详细模拟界面"),
            ("cases.html", "案例研究 - 成功案例展示"),
            ("about.html", "关于我们 - 公司信息"),
            ("detail.html", "详情页面 - 具体分析详情")
        ]
        
        for page_file, page_desc in pages:
            page_path = self.frontend_dir / page_file
            if page_path.exists():
                with open(page_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 分析页面特征
                page_info = {
                    "description": page_desc,
                    "size_bytes": os.path.getsize(page_path),
                    "size_chars": len(content),
                    "lines": content.count('\n'),
                    "has_navigation": self._check_navigation(content),
                    "has_footer": self._check_footer(content),
                    "has_metadata": self._check_metadata(content),
                    "links_to_other_pages": self._extract_internal_links(content),
                    "external_links": self._extract_external_links(content),
                    "data_sources": self._extract_data_sources(content),
                    "interactive_elements": self._count_interactive_elements(content),
                    "accessibility_score": self._calculate_accessibility_score(content)
                }
                
                self.review_results["pages"][page_file] = page_info
                print(f"  📄 {page_file}: {page_desc} ({page_info['size_chars']:,}字符)")
    
    def _check_navigation(self, content):
        """检查导航菜单"""
        nav_patterns = [
            r'<nav[^>]*>',
            r'class=".*nav.*"',
            r'id=".*nav.*"',
            r'<ul.*>.*<li>.*</li>.*</ul>'
        ]
        return any(re.search(pattern, content, re.DOTALL | re.IGNORECASE) for pattern in nav_patterns)
    
    def _check_footer(self, content):
        """检查页脚"""
        return '<footer' in content.lower() or 'class="footer"' in content.lower()
    
    def _check_metadata(self, content):
        """检查元数据"""
        meta_tags = ['<title>', '<meta name="description"', '<meta name="keywords"']
        return any(tag in content.lower() for tag in meta_tags)
    
    def _extract_internal_links(self, content):
        """提取内部链接"""
        soup = BeautifulSoup(content, 'html.parser')
        internal_links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.html') and not href.startswith(('http://', 'https://')):
                internal_links.append(href)
        
        return list(set(internal_links))
    
    def _extract_external_links(self, content):
        """提取外部链接"""
        soup = BeautifulSoup(content, 'html.parser')
        external_links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(('http://', 'https://')):
                external_links.append(href)
        
        return list(set(external_links))
    
    def _extract_data_sources(self, content):
        """提取数据来源"""
        # 查找数据来源相关的文本
        source_patterns = [
            r'数据来源[：:]\s*(.*?)[。\.<]',
            r'来源[：:]\s*(.*?)[。\.<]',
            r'data source[：:]\s*(.*?)[\.<]',
            r'Source[：:]\s*(.*?)[\.<]'
        ]
        
        sources = []
        for pattern in source_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            sources.extend(matches)
        
        return list(set(sources))
    
    def _count_interactive_elements(self, content):
        """统计交互元素"""
        soup = BeautifulSoup(content, 'html.parser')
        
        elements = {
            'buttons': len(soup.find_all('button')),
            'forms': len(soup.find_all('form')),
            'inputs': len(soup.find_all('input')),
            'selects': len(soup.find_all('select')),
            'links': len(soup.find_all('a')),
            'clickable_divs': len(soup.find_all('div', onclick=True))
        }
        
        return elements
    
    def _calculate_accessibility_score(self, content):
        """计算可访问性分数"""
        soup = BeautifulSoup(content, 'html.parser')
        score = 100
        
        # 检查alt属性
        images_without_alt = soup.find_all('img', alt=False)
        if images_without_alt:
            score -= len(images_without_alt) * 5
        
        # 检查表单标签
        inputs_without_labels = soup.find_all('input')
        for inp in inputs_without_labels:
            if not inp.get('id') or not soup.find('label', {'for': inp.get('id')}):
                score -= 3
        
        # 检查标题结构
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            score -= 20
        elif len([h for h in headings if h.name == 'h1']) > 1:
            score -= 15
        
        # 检查ARIA属性
        elements_with_aria = soup.find_all(attrs={"aria-label": True})
        if not elements_with_aria and len(soup.find_all()) > 50:
            score -= 10
        
        return max(0, score)
    
    def review_architecture_issues(self):
        """审查架构问题"""
        print("\n🏗️ 审查架构问题...")
        
        issues = []
        
        # 1. 检查页面一致性
        common_elements = ['header', 'navigation', 'footer']
        for element in common_elements:
            pages_with_element = []
            pages_without_element = []
            
            for page_file, page_info in self.review_results["pages"].items():
                if element == 'header':
                    has_element = page_info['has_navigation']
                elif element == 'footer':
                    has_element = page_info['has_footer']
                else:
                    has_element = False
                
                if has_element:
                    pages_with_element.append(page_file)
                else:
                    pages_without_element.append(page_file)
            
            if pages_without_element:
                issues.append({
                    "type": "architecture",
                    "severity": "medium",
                    "issue": f"页面{element}不一致",
                    "description": f"部分页面缺少{element}: {', '.join(pages_without_element)}",
                    "recommendation": f"建立统一的{element}组件，在所有页面中使用"
                })
        
        # 2. 检查导航结构
        navigation_links = defaultdict(set)
        for page_file, page_info in self.review_results["pages"].items():
            for link in page_info['links_to_other_pages']:
                navigation_links[page_file].add(link)
        
        # 检查双向链接
        for page, links in navigation_links.items():
            for linked_page in links:
                if linked_page in self.review_results["pages"]:
                    if page not in navigation_links.get(linked_page, set()):
                        issues.append({
                            "type": "architecture",
                            "severity": "low",
                            "issue": "单向导航链接",
                            "description": f"{page}链接到{linked_page}，但{linked_page}没有返回链接",
                            "recommendation": f"在{linked_page}中添加返回{page}的导航"
                        })
        
        # 3. 检查数据来源可追踪性
        for page_file, page_info in self.review_results["pages"].items():
            if page_info['data_sources']:
                # 检查是否有外部链接支持
                external_support = False
                for source in page_info['data_sources']:
                    if any(link for link in page_info['external_links'] if source.lower() in link.lower()):
                        external_support = True
                        break
                
                if not external_support:
                    issues.append({
                        "type": "architecture",
                        "severity": "high",
                        "issue": "数据来源不可追踪",
                        "description": f"{page_file}中提到数据来源但没有提供可追踪链接",
                        "recommendation": "为所有数据来源添加权威链接，增强可信度"
                    })
        
        self.review_results["architecture_issues"] = issues
        
        for issue in issues:
            print(f"  {'🔴' if issue['severity'] == 'high' else '🟡' if issue['severity'] == 'medium' else '🟢'} {issue['issue']}: {issue['description']}")
    
    def review_ux_issues(self):
        """审查用户体验问题"""
        print("\n🎨 审查用户体验问题...")
        
        issues = []
        
        # 1. 检查页面加载大小
        for page_file, page_info in self.review_results["pages"].items():
            size_mb = page_info['size_bytes'] / 1024 / 1024
            
            if size_mb > 0.5:  # 超过0.5MB
                issues.append({
                    "type": "ux",
                    "severity": "medium",
                    "issue": "页面文件过大",
                    "description": f"{page_file}大小{size_mb:.2f}MB，影响加载速度",
                    "recommendation": "拆分大文件，使用代码分割和懒加载"
                })
        
        # 2. 检查交互元素密度
        for page_file, page_info in self.review_results["pages"].items():
            interactive_count = sum(page_info['interactive_elements'].values())
            char_count = page_info['size_chars']
            
            if char_count > 0:
                density = interactive_count / (char_count / 1000)  # 每千字符交互元素数
                
                if density < 2:  # 交互元素过少
                    issues.append({
                        "type": "ux",
                        "severity": "medium",
                        "issue": "交互元素不足",
                        "description": f"{page_file}交互密度低({density:.1f}/千字符)，用户体验可能较被动",
                        "recommendation": "增加交互元素，提升用户参与度"
                    })
                elif density > 10:  # 交互元素过多
                    issues.append({
                        "type": "ux",
                        "severity": "low",
                        "issue": "交互元素过密",
                        "description": f"{page_file}交互密度高({density:.1f}/千字符)，可能造成用户决策疲劳",
                        "recommendation": "简化交互，突出重点功能"
                    })
        
        # 3. 检查可访问性
        for page_file, page_info in self.review_results["pages"].items():
            score = page_info['accessibility_score']
            
            if score < 70:
                issues.append({
                    "type": "ux",
                    "severity": "high",
                    "issue": "可访问性不足",
                    "description": f"{page_file}可访问性分数{score}/100，影响残障用户使用",
                    "recommendation": "修复alt属性、添加ARIA标签、改进表单标签"
                })
        
        self.review_results["ux_issues"] = issues
        
        for issue in issues:
            print(f"  {'🔴' if issue['severity'] == 'high' else '🟡' if issue['severity'] == 'medium' else '🟢'} {issue['issue']}")
    
    def review_performance_issues(self):
        """审查性能问题"""
        print("\n⚡ 审查性能问题...")
        
        issues = []
        
        # 检查CSS/JS内联情况
        for page_file in self.review_results["pages"]:
            page_path = self.frontend_dir / page_file
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查内联样式
            inline_style_count = content.count('<style>')
            if inline_style_count > 3:
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "issue": "过多内联样式",
                    "description": f"{page_file}有{inline_style_count}处内联样式，影响缓存效率",
                    "recommendation": "将内联样式提取到外部CSS文件"
                })
            
            # 检查内联脚本
            inline_script_count = content.count('<script>') - content.count('</script>')
            if inline_script_count > 2:
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "issue": "过多内联脚本",
                    "description": f"{page_file}有{inline_script_count}处内联脚本，影响加载性能",
                    "recommendation": "将脚本提取到外部JS文件，使用异步加载"
                })
        
        self.review_results["performance_issues"] = issues
        
        for issue in issues:
            print(f"  {'🔴' if issue['severity'] == 'high' else '🟡' if issue['severity'] == 'medium' else '🟢'} {issue['issue']}")
    
    def generate_recommendations(self):
        """生成优化建议"""
        print("\n💡 生成优化建议...")
        
        recommendations = []
        
        # 1. 架构优化建议
        recommendations.append({
            "category": "architecture",
            "priority": "high",
            "title": "建立统一的设计系统",
            "description": "创建共享的CSS变量、组件库和设计规范",
            "benefit": "提升一致性，减少维护成本，加速开发"
        })
        
        recommendations.append({
            "category": "architecture", 
            "priority": "high",
            "title": "实现组件化架构",
            "description": "将公共元素（导航、页脚、侧边栏）提取为可复用组件",
            "benefit": "代码复用，易于维护，统一更新"
        })
        
        # 2. UX优化建议
        recommendations.append({
            "category": "ux",
            "priority": "high",
            "title": "优化信息架构",
            "description": "重新设计导航结构，建立清晰的页面层级关系",
            "benefit": "提升用户导航效率，减少迷失感"
        })
        
        recommendations.append({
            "category": "ux",
            "priority": "medium",
            "title": "增强数据可视化",
            "description": "为关键数据指标添加图表和可视化展示",
            "benefit": "提升数据理解度，增强决策支持"
        })
        
        # 3. 性能优化建议
        recommendations.append({
            "category": "performance",
            "priority": "high",
            "title": "实施代码分割",
            "description": "将大页面拆分为按需加载的模块",
            "benefit": "减少初始加载时间，提升用户体验"
        })
        
        recommendations.append({
            "category": "performance",
            "priority": "medium",
            "title": "优化资源加载",
            "description": "使用懒加载、预加载和资源优先级",
            "benefit": "提升页面加载速度，优化性能指标"
        })
        
        # 4. 产品目标对齐建议
        recommendations.append({
            "category": "product_goals",
            "priority": "high",
            "title": "强化数学严谨性展示",
            "description": "在关键页面突出显示置信区间、样本规模、统计方法",
            "benefit": "建立专业信任，增强产品可信度"
        })
        
        recommendations.append({
            "category": "product_goals",
            "priority": "high",
            "title": "增强数据透明度",
            "description": "为所有数据点添加来源链接和验证信息",
            "benefit": "提升透明度，建立行业权威"
        })
        
        self.review_results["recommendations"] = recommendations
        
        for rec in recommendations:
            print(f"  {'🚀' if rec['priority'] == 'high' else '📈' if rec['priority'] == 'medium' else '💡'} [{rec['category']}] {rec['title']}")
    
    def generate_priority_actions(self):
        """生成优先级行动项"""
        print("\n🎯 生成优先级行动项...")
        
        actions = []
        
        # P0: 必须立即修复的问题
        high_severity_issues = []
        for issue_list in [self.review_results["architecture_issues"], 
                          self.review_results["ux_issues"], 
                          self.review_results["performance_issues"]]:
            high_severity_issues.extend([i for i in issue_list if i['severity'] == 'high'])
        
        for issue in high_severity_issues:
            actions.append({
                "priority": "P0",
                "action": f"修复: {issue['issue']}",
                "description": issue['description'],
                "estimated_time": "2-4小时",
                "impact": "高"
            })
        
        # P1: 重要优化项
        medium_severity_issues = []
        for issue_list in [self.review_results["architecture_issues"], 
                          self.review_results["ux_issues"], 
                          self.review_results["performance_issues"]]:
            medium_severity_issues.extend([i for i in issue_list if i['severity'] == 'medium'])
        
        # 选择前3个中等优先级问题
        for issue in medium_severity_issues[:3]:
            actions.append({
                "priority": "P1",
                "action": f"优化: {issue['issue']}",
                "description": issue['description'],
                "estimated_time": "4-8小时",
                "impact": "中高"
            })
        
        # P2: 架构改进
        high_priority_recommendations = [r for r in self.review_results["recommendations"] if r['priority'] == 'high']
        for rec in high_priority_recommendations[:2]:
            actions.append({
                "priority": "P2",
                "action": f"实施: {rec['title']}",
                "description": rec['description'],
                "estimated_time": "1-2天",
                "impact": "长期高"
            })
        
        self.review_results["priority_actions"] = actions
        
        for action in actions:
            print(f"  {'🔴' if action['priority'] == 'P0' else '🟡' if action['priority'] == 'P1' else '🟢'} [{action['priority']}] {action['action']}")
    
    def save_report(self):
        """保存审查报告"""
        reports_dir = self.project_root / "docs" / "architecture_reviews"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"frontend_architecture_review_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.review_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 审查报告已保存: {report_file}")
        return report_file
    
    def generate_summary(self):
        """生成总结报告"""
        print("\n" + "=" * 70)
        print("🎯 国际大师级前端架构审查总结")
        print("=" * 70)
        
        total_issues = (len(self.review_results["architecture_issues"]) + 
                       len(self.review_results["ux_issues"]) + 
                       len(self.review_results["performance_issues"]))
        
        high_issues = sum(1 for issue in self.review_results["architecture_issues"] + 
                         self.review_results["ux_issues"] + 
                         self.review_results["performance_issues"] 
                         if issue['severity'] == 'high')
        
        print(f"\n📊 审查统计:")
        print(f"  • 审查页面: {len(self.review_results['pages'])}个")
        print(f"  • 发现问题: {total_issues}个")
        print(f"  • 高优先级: {high_issues}个")
        print(f"  • 建议优化: {len(self.review_results['recommendations'])}项")
        print(f"  • 行动项: {len(self.review_results['priority_actions'])}个")
        
        print(f"\n🏆 产品目标对齐度:")
        goals_alignment = {
            "数学严谨性": self._evaluate_math_rigor(),
            "透明度": self._evaluate_transparency(),
            "简洁可信": self._evaluate_simplicity(),
            "预测准确": self._evaluate_accuracy(),
            "全球对标": self._evaluate_benchmarking()
        }
        
        for goal, score in goals_alignment.items():
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            print(f"  • {goal}: {bar} {score}%")
        
        print(f"\n🚀 优先级行动路线图:")
        for action in self.review_results["priority_actions"]:
            print(f"  {action['priority']}: {action['action']} ({action['estimated_time']})")
        
        print(f"\n💡 核心建议:")
        print("  1. 建立统一的设计系统和组件库")
        print("  2. 优化信息架构和导航系统")
        print("  3. 增强数据可追踪性和透明度")
        print("  4. 实施性能优化和代码分割")
        print("  5. 强化产品目标在UI中的体现")
        
        print(f"\n🎯 审查团队:")
        print("  • 国际定价前端设计大师: 专注于价值传递和用户体验")
        print("  • 顶级用户体验专家: 专注于用户旅程和交互设计")
        print("  • 产品目标对齐专家: 专注于5大产品目标的UI实现")
        
        print(f"\n📅 审查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _evaluate_math_rigor(self):
        """评估数学严谨性"""
        score = 60  # 基础分
        
        # 检查是否有置信区间展示
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['confidence', '置信', 'statistical', '统计']):
                score += 10
        
        # 检查是否有样本规模展示
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['sample', '样本', '172,173', 'agents']):
                score += 10
        
        # 检查是否有方法说明
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['methodology', '方法', 'abm', '蒙特卡洛']):
                score += 10
        
        return min(100, score)
    
    def _evaluate_transparency(self):
        """评估透明度"""
        score = 50  # 基础分
        
        # 检查数据来源
        total_sources = 0
        for page_info in self.review_results["pages"].values():
            total_sources += len(page_info['data_sources'])
        
        if total_sources > 0:
            score += min(30, total_sources * 5)
        
        # 检查外部链接
        total_external_links = 0
        for page_info in self.review_results["pages"].values():
            total_external_links += len(page_info['external_links'])
        
        if total_external_links > 0:
            score += min(20, total_external_links * 3)
        
        return min(100, score)
    
    def _evaluate_simplicity(self):
        """评估简洁可信"""
        score = 70  # 基础分
        
        # 检查页面复杂度
        total_chars = sum(page_info['size_chars'] for page_info in self.review_results["pages"].values())
        avg_chars = total_chars / len(self.review_results["pages"]) if self.review_results["pages"] else 0
        
        if avg_chars > 100000:  # 平均超过10万字符
            score -= 20
        elif avg_chars < 50000:  # 平均低于5万字符
            score += 10
        
        # 检查交互元素合理性
        for page_info in self.review_results["pages"].values():
            interactive_count = sum(page_info['interactive_elements'].values())
            if 5 <= interactive_count <= 20:  # 合理的交互数量
                score += 5
        
        return min(100, score)
    
    def _evaluate_accuracy(self):
        """评估预测准确"""
        score = 40  # 基础分
        
        # 检查是否有预测相关展示
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['prediction', '预测', 'forecast', 'forecasting']):
                score += 20
        
        # 检查是否有验证机制
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['validation', '验证', 'accuracy', '准确']):
                score += 20
        
        return min(100, score)
    
    def _evaluate_benchmarking(self):
        """评估全球对标"""
        score = 30  # 基础分
        
        # 检查是否有国际比较
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['global', '国际', 'benchmark', '对标', 'comparison', '比较']):
                score += 30
        
        # 检查是否有行业标准
        for page_info in self.review_results["pages"].values():
            if any(keyword in str(page_info).lower() for keyword in ['standard', '标准', 'industry', '行业']):
                score += 20
        
        return min(100, score)

def main():
    """主函数"""
    print("=" * 70)
    print("🎯 Digital Twin SG 前端架构专业审查")
    print("国际定价前端设计大师 + 顶级用户体验专家视角")
    print("=" * 70)
    
    try:
        project_root = "/Users/tigerli/Desktop/Digital Twins Singapore"
        reviewer = FrontendArchitectReview(project_root)
        
        # 执行审查
        reviewer.analyze_page_structure()
        reviewer.review_architecture_issues()
        reviewer.review_ux_issues()
        reviewer.review_performance_issues()
        reviewer.generate_recommendations()
        reviewer.generate_priority_actions()
        
        # 保存报告
        report_file = reviewer.save_report()
        
        # 生成总结
        reviewer.generate_summary()
        
        print(f"\n" + "=" * 70)
        print("🚀 审查完成!")
        print("=" * 70)
        
        print(f"\n📁 详细报告: {report_file}")
        print(f"\n🔗 访问地址: http://localhost:8888")
        
        print(f"\n💡 立即行动建议:")
        print("  1. 查看P0优先级问题并立即修复")
        print("  2. 建立统一的设计系统")
        print("  3. 优化页面导航结构")
        print("  4. 增强数据可追踪性")
        print("  5. 对齐产品目标展示")
        
    except ImportError:
        print("❌ 需要安装BeautifulSoup: pip install beautifulsoup4")
    except Exception as e:
        print(f"\n❌ 审查过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()