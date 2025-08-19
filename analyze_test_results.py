#!/usr/bin/env python3
"""
KMTI Test Results Analyzer
==========================

Advanced analysis tool for KMTI test results:
- Parses test logs and reports
- Identifies patterns in test failures
- Generates trend analysis
- Provides actionable recommendations
- Creates visual reports and charts

Usage: python analyze_test_results.py [test_report.txt] [--options]
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional

class KMTITestAnalyzer:
    """Comprehensive test results analyzer"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results_data = {}
        self.analysis_results = {}
        
    def analyze_results(self, report_file: Optional[str] = None, log_file: Optional[str] = None):
        """Run comprehensive analysis of test results"""
        
        print("📊 KMTI Test Results Analysis")
        print("=" * 50)
        
        # Load test data
        if not self._load_test_data(report_file, log_file):
            print("❌ Failed to load test data")
            return False
        
        # Run analysis modules
        self._analyze_test_summary()
        self._analyze_failure_patterns()
        self._analyze_performance_metrics()
        self._analyze_category_health()
        self._analyze_trends()
        self._generate_recommendations()
        
        # Generate reports
        self._generate_summary_report()
        self._generate_detailed_report()
        
        return True
    
    def _load_test_data(self, report_file: Optional[str], log_file: Optional[str]) -> bool:
        """Load test data from files"""
        
        # Default file locations
        if not report_file:
            report_file = self.project_root / "test_data" / "test_report.txt"
        if not log_file:
            log_file = self.project_root / "kmti_test_results.log"
        
        self.results_data = {
            'report_content': '',
            'log_content': '',
            'parsed_results': {},
            'metadata': {
                'report_file': str(report_file),
                'log_file': str(log_file),
                'analysis_time': datetime.now().isoformat()
            }
        }
        
        # Load report file
        report_path = Path(report_file)
        if report_path.exists():
            try:
                self.results_data['report_content'] = report_path.read_text()
                print(f"✅ Loaded report: {report_path.name}")
            except Exception as e:
                print(f"❌ Error reading report: {e}")
                return False
        else:
            print(f"⚠️  Report file not found: {report_path}")
        
        # Load log file
        log_path = Path(log_file)
        if log_path.exists():
            try:
                self.results_data['log_content'] = log_path.read_text()
                print(f"✅ Loaded log: {log_path.name}")
            except Exception as e:
                print(f"❌ Error reading log: {e}")
                return False
        else:
            print(f"⚠️  Log file not found: {log_path}")
        
        # Parse the data
        self._parse_test_data()
        
        return True
    
    def _parse_test_data(self):
        """Parse raw test data into structured format"""
        
        parsed = {
            'summary': {},
            'categories': {},
            'individual_tests': [],
            'performance_data': {},
            'errors': []
        }
        
        # Parse report content
        report_content = self.results_data['report_content']
        
        # Extract summary statistics
        summary_match = re.search(r'Total Tests:\s*(\d+)', report_content)
        if summary_match:
            parsed['summary']['total_tests'] = int(summary_match.group(1))
        
        passed_match = re.search(r'Passed:\s*(\d+)\s*\(([^)]+)\)', report_content)
        if passed_match:
            parsed['summary']['passed'] = int(passed_match.group(1))
            parsed['summary']['passed_percent'] = passed_match.group(2)
        
        failed_match = re.search(r'Failed:\s*(\d+)\s*\(([^)]+)\)', report_content)
        if failed_match:
            parsed['summary']['failed'] = int(failed_match.group(1))
            parsed['summary']['failed_percent'] = failed_match.group(2)
        
        errors_match = re.search(r'Errors:\s*(\d+)\s*\(([^)]+)\)', report_content)
        if errors_match:
            parsed['summary']['errors'] = int(errors_match.group(1))
            parsed['summary']['errors_percent'] = errors_match.group(2)
        
        duration_match = re.search(r'DURATION:\s*([^\n]+)', report_content)
        if duration_match:
            parsed['summary']['duration'] = duration_match.group(1).strip()
        
        # Parse category results
        category_sections = re.findall(r'📁 ([A-Z_]+):\s*(\d+)/(\d+)\s*\(([^)]+)\)', report_content)
        for category, passed, total, percentage in category_sections:
            parsed['categories'][category.lower()] = {
                'passed': int(passed),
                'total': int(total),
                'percentage': percentage,
                'failed': int(total) - int(passed)
            }
        
        # Parse individual test results
        test_results = re.findall(r'([✅❌💥])\s+([^:]+):\s*([^\n]+)\s*\(([^)]+)s\)', report_content)
        for status_icon, test_name, message, duration in test_results:
            status = 'passed' if status_icon == '✅' else 'failed' if status_icon == '❌' else 'error'
            parsed['individual_tests'].append({
                'name': test_name.strip(),
                'status': status,
                'message': message.strip(), 
                'duration': float(duration)
            })
        
        # Parse log for additional performance data and errors
        log_content = self.results_data['log_content']
        
        # Extract performance metrics
        perf_matches = re.findall(r'(\w+)\s+test.*?(\d+\.\d+)s', log_content)
        for test_type, duration in perf_matches:
            if test_type not in parsed['performance_data']:
                parsed['performance_data'][test_type] = []
            parsed['performance_data'][test_type].append(float(duration))
        
        # Extract error messages
        error_matches = re.findall(r'ERROR.*?-\s*(.+)', log_content)
        parsed['errors'] = [error.strip() for error in error_matches]
        
        self.results_data['parsed_results'] = parsed
    
    def _analyze_test_summary(self):
        """Analyze overall test summary"""
        
        print("\n1. 📊 Test Summary Analysis")
        
        parsed = self.results_data['parsed_results']
        summary = parsed.get('summary', {})
        
        analysis = {
            'overall_health': 'unknown',
            'total_tests': summary.get('total_tests', 0),
            'success_rate': 0,
            'failure_rate': 0,
            'error_rate': 0,
            'assessment': ''
        }
        
        if analysis['total_tests'] > 0:
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0) 
            errors = summary.get('errors', 0)
            
            analysis['success_rate'] = (passed / analysis['total_tests']) * 100
            analysis['failure_rate'] = (failed / analysis['total_tests']) * 100
            analysis['error_rate'] = (errors / analysis['total_tests']) * 100
            
            # Determine overall health
            if analysis['success_rate'] >= 95:
                analysis['overall_health'] = 'excellent'
                analysis['assessment'] = 'System is in excellent condition'
            elif analysis['success_rate'] >= 85:
                analysis['overall_health'] = 'good'
                analysis['assessment'] = 'System is in good condition with minor issues'
            elif analysis['success_rate'] >= 70:
                analysis['overall_health'] = 'fair'
                analysis['assessment'] = 'System has some significant issues requiring attention'
            else:
                analysis['overall_health'] = 'poor'
                analysis['assessment'] = 'System has major issues requiring immediate attention'
        
        self.analysis_results['summary'] = analysis
        
        print(f"   Overall Health: {analysis['overall_health'].upper()}")
        print(f"   Success Rate: {analysis['success_rate']:.1f}%")
        print(f"   Assessment: {analysis['assessment']}")
    
    def _analyze_failure_patterns(self):
        """Analyze patterns in test failures"""
        
        print("\n2. 🔍 Failure Pattern Analysis")
        
        parsed = self.results_data['parsed_results']
        failed_tests = [test for test in parsed.get('individual_tests', []) 
                       if test['status'] in ['failed', 'error']]
        
        analysis = {
            'total_failures': len(failed_tests),
            'failure_by_category': Counter(),
            'common_error_patterns': Counter(),
            'failure_keywords': Counter(),
            'critical_failures': []
        }
        
        for test in failed_tests:
            # Categorize by test name patterns
            test_name = test['name']
            if 'auth' in test_name.lower():
                analysis['failure_by_category']['authentication'] += 1
            elif 'file' in test_name.lower():
                analysis['failure_by_category']['file_management'] += 1
            elif 'approval' in test_name.lower():
                analysis['failure_by_category']['approval_workflow'] += 1
            elif 'admin' in test_name.lower():
                analysis['failure_by_category']['admin_panel'] += 1
            elif 'security' in test_name.lower():
                analysis['failure_by_category']['security'] += 1
            else:
                analysis['failure_by_category']['other'] += 1
            
            # Extract error patterns
            message = test['message'].lower()
            if 'permission' in message:
                analysis['common_error_patterns']['permission_errors'] += 1
            elif 'not found' in message:
                analysis['common_error_patterns']['not_found_errors'] += 1
            elif 'connection' in message or 'network' in message:
                analysis['common_error_patterns']['network_errors'] += 1
            elif 'timeout' in message:
                analysis['common_error_patterns']['timeout_errors'] += 1
            elif 'import' in message or 'module' in message:
                analysis['common_error_patterns']['import_errors'] += 1
            
            # Extract keywords
            words = re.findall(r'\w+', message)
            for word in words:
                if len(word) > 3:  # Only meaningful words
                    analysis['failure_keywords'][word] += 1
            
            # Identify critical failures
            if test['status'] == 'error' or 'critical' in message or 'fatal' in message:
                analysis['critical_failures'].append({
                    'test': test_name,
                    'message': test['message']
                })
        
        self.analysis_results['failure_patterns'] = analysis
        
        if analysis['total_failures'] > 0:
            print(f"   Total Failures: {analysis['total_failures']}")
            print("   Failure Categories:")
            for category, count in analysis['failure_by_category'].most_common(5):
                print(f"     • {category}: {count}")
            
            if analysis['common_error_patterns']:
                print("   Common Error Patterns:")
                for pattern, count in analysis['common_error_patterns'].most_common(3):
                    print(f"     • {pattern.replace('_', ' ')}: {count}")
        else:
            print("   ✅ No failures detected")
    
    def _analyze_performance_metrics(self):
        """Analyze performance metrics"""
        
        print("\n3. ⚡ Performance Analysis")
        
        parsed = self.results_data['parsed_results']
        individual_tests = parsed.get('individual_tests', [])
        
        analysis = {
            'total_duration': 0,
            'average_test_duration': 0,
            'slowest_tests': [],
            'fastest_tests': [],
            'performance_categories': {},
            'performance_issues': []
        }
        
        if individual_tests:
            durations = [test['duration'] for test in individual_tests]
            analysis['total_duration'] = sum(durations)
            analysis['average_test_duration'] = analysis['total_duration'] / len(durations)
            
            # Sort by duration
            sorted_tests = sorted(individual_tests, key=lambda x: x['duration'], reverse=True)
            analysis['slowest_tests'] = sorted_tests[:5]  # Top 5 slowest
            analysis['fastest_tests'] = sorted_tests[-5:]  # Top 5 fastest
            
            # Categorize performance by test type
            for test in individual_tests:
                test_name = test['name'].lower()
                category = 'other'
                
                if 'performance' in test_name:
                    category = 'performance'
                elif 'auth' in test_name:
                    category = 'authentication'
                elif 'file' in test_name:
                    category = 'file_operations'
                elif 'database' in test_name or 'data' in test_name:
                    category = 'database'
                
                if category not in analysis['performance_categories']:
                    analysis['performance_categories'][category] = []
                analysis['performance_categories'][category].append(test['duration'])
            
            # Calculate category averages
            for category, durations in analysis['performance_categories'].items():
                avg_duration = sum(durations) / len(durations)
                analysis['performance_categories'][category] = {
                    'average': avg_duration,
                    'count': len(durations),
                    'total': sum(durations)
                }
            
            # Identify performance issues
            slow_threshold = 5.0  # 5 seconds
            for test in individual_tests:
                if test['duration'] > slow_threshold:
                    analysis['performance_issues'].append({
                        'test': test['name'],
                        'duration': test['duration'],
                        'issue': f"Test took {test['duration']:.2f}s (>{slow_threshold}s threshold)"
                    })
        
        self.analysis_results['performance'] = analysis
        
        print(f"   Total Duration: {analysis['total_duration']:.2f}s")
        print(f"   Average Test Duration: {analysis['average_test_duration']:.3f}s")
        
        if analysis['slowest_tests']:
            print("   Slowest Tests:")
            for test in analysis['slowest_tests']:
                print(f"     • {test['name']}: {test['duration']:.3f}s")
        
        if analysis['performance_issues']:
            print(f"   Performance Issues: {len(analysis['performance_issues'])}")
        else:
            print("   ✅ No performance issues detected")
    
    def _analyze_category_health(self):
        """Analyze health of each test category"""
        
        print("\n4. 🏥 Category Health Analysis")
        
        parsed = self.results_data['parsed_results']
        categories = parsed.get('categories', {})
        
        analysis = {
            'healthy_categories': [],
            'warning_categories': [],
            'critical_categories': [],
            'category_details': {}
        }
        
        for category, data in categories.items():
            success_rate = (data['passed'] / data['total']) * 100 if data['total'] > 0 else 0
            
            category_analysis = {
                'success_rate': success_rate,
                'total_tests': data['total'],
                'passed_tests': data['passed'],
                'failed_tests': data['failed'],
                'health_status': 'unknown'
            }
            
            # Determine health status
            if success_rate >= 90:
                category_analysis['health_status'] = 'healthy'
                analysis['healthy_categories'].append(category)
            elif success_rate >= 75:
                category_analysis['health_status'] = 'warning'
                analysis['warning_categories'].append(category)
            else:
                category_analysis['health_status'] = 'critical'
                analysis['critical_categories'].append(category)
            
            analysis['category_details'][category] = category_analysis
        
        self.analysis_results['category_health'] = analysis
        
        print(f"   Healthy Categories: {len(analysis['healthy_categories'])}")
        for category in analysis['healthy_categories']:
            rate = analysis['category_details'][category]['success_rate']
            print(f"     ✅ {category}: {rate:.1f}%")
        
        if analysis['warning_categories']:
            print(f"   Warning Categories: {len(analysis['warning_categories'])}")
            for category in analysis['warning_categories']:
                rate = analysis['category_details'][category]['success_rate']
                print(f"     ⚠️  {category}: {rate:.1f}%")
        
        if analysis['critical_categories']:
            print(f"   Critical Categories: {len(analysis['critical_categories'])}")
            for category in analysis['critical_categories']:
                rate = analysis['category_details'][category]['success_rate']
                print(f"     ❌ {category}: {rate:.1f}%")
    
    def _analyze_trends(self):
        """Analyze trends (placeholder for historical data)"""
        
        print("\n5. 📈 Trend Analysis")
        
        # This would require historical test data
        # For now, provide placeholder analysis
        
        analysis = {
            'trend_available': False,
            'historical_data_points': 0,
            'recommendation': 'Run tests regularly to establish trend data'
        }
        
        # Check if we have multiple test result files
        test_data_dir = self.project_root / "test_data"
        if test_data_dir.exists():
            result_files = list(test_data_dir.glob("test_report_*.txt"))
            if len(result_files) > 1:
                analysis['trend_available'] = True
                analysis['historical_data_points'] = len(result_files)
                analysis['recommendation'] = 'Historical trend data available for analysis'
        
        self.analysis_results['trends'] = analysis
        
        if analysis['trend_available']:
            print(f"   📊 {analysis['historical_data_points']} historical data points available")
        else:
            print("   📊 No historical data available for trend analysis")
            print("   💡 Tip: Run tests regularly to build trend history")
    
    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        
        print("\n6. 💡 Generating Recommendations")
        
        recommendations = {
            'immediate_actions': [],
            'medium_term_improvements': [],
            'long_term_strategy': [],
            'priority_score': 0
        }
        
        # Analyze results to generate recommendations
        summary = self.analysis_results.get('summary', {})
        failure_patterns = self.analysis_results.get('failure_patterns', {})
        performance = self.analysis_results.get('performance', {})
        category_health = self.analysis_results.get('category_health', {})
        
        # Immediate actions based on overall health
        if summary.get('overall_health') == 'poor':
            recommendations['immediate_actions'].append(
                "CRITICAL: Review and fix major system issues - success rate is below 70%"
            )
            recommendations['priority_score'] += 10
        elif summary.get('overall_health') == 'fair':
            recommendations['immediate_actions'].append(
                "Address failing tests - success rate could be improved"
            )
            recommendations['priority_score'] += 5
        
        # Recommendations based on failure patterns
        if failure_patterns.get('total_failures', 0) > 0:
            common_patterns = failure_patterns.get('common_error_patterns', {})
            
            if 'permission_errors' in common_patterns:
                recommendations['immediate_actions'].append(
                    "Fix permission errors - check file/directory access rights"
                )
            
            if 'network_errors' in common_patterns:
                recommendations['immediate_actions'].append(
                    "Address network connectivity issues - verify network paths"
                )
            
            if 'import_errors' in common_patterns:
                recommendations['immediate_actions'].append(
                    "Resolve import/module errors - check Python dependencies"
                )
        
        # Performance recommendations
        perf_issues = performance.get('performance_issues', [])
        if len(perf_issues) > 3:
            recommendations['medium_term_improvements'].append(
                f"Optimize performance - {len(perf_issues)} tests are running slowly"
            )
        
        # Category-specific recommendations
        critical_categories = category_health.get('critical_categories', [])
        if critical_categories:
            for category in critical_categories:
                recommendations['immediate_actions'].append(
                    f"Fix critical issues in {category} tests"
                )
                recommendations['priority_score'] += 3
        
        # Long-term strategy
        recommendations['long_term_strategy'].extend([
            "Establish regular testing schedule to build trend data",
            "Consider implementing automated test runs on code changes",
            "Add more comprehensive integration tests",
            "Set up monitoring for test result trends"
        ])
        
        self.analysis_results['recommendations'] = recommendations
        
        # Print recommendations
        if recommendations['immediate_actions']:
            print(f"   🚨 Immediate Actions ({len(recommendations['immediate_actions'])}):")
            for action in recommendations['immediate_actions']:
                print(f"     • {action}")
        
        if recommendations['medium_term_improvements']:
            print(f"   📋 Medium-term Improvements:")
            for improvement in recommendations['medium_term_improvements']:
                print(f"     • {improvement}")
        
        print(f"   Priority Score: {recommendations['priority_score']} (higher = more urgent)")
    
    def _generate_summary_report(self):
        """Generate concise summary report"""
        
        print("\n" + "=" * 50)
        print("📋 ANALYSIS SUMMARY")
        print("=" * 50)
        
        summary = self.analysis_results.get('summary', {})
        
        print(f"🎯 Overall System Health: {summary.get('overall_health', 'unknown').upper()}")
        print(f"📊 Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"⚡ Average Test Duration: {self.analysis_results.get('performance', {}).get('average_test_duration', 0):.3f}s")
        
        failure_count = self.analysis_results.get('failure_patterns', {}).get('total_failures', 0)
        print(f"❌ Total Failures: {failure_count}")
        
        recommendations = self.analysis_results.get('recommendations', {})
        immediate_actions = len(recommendations.get('immediate_actions', []))
        print(f"🚨 Immediate Actions Needed: {immediate_actions}")
        
        print(f"\n📈 Key Insights:")
        print(f"   • {summary.get('assessment', 'No assessment available')}")
        
        if failure_count > 0:
            most_common_failure = max(
                self.analysis_results.get('failure_patterns', {}).get('failure_by_category', {}).items(),
                key=lambda x: x[1],
                default=('unknown', 0)
            )
            print(f"   • Most failures in: {most_common_failure[0]} ({most_common_failure[1]} failures)")
    
    def _generate_detailed_report(self):
        """Generate detailed analysis report file"""
        
        report_content = self._create_detailed_report_content()
        
        # Save to file
        report_file = self.project_root / "test_analysis_report.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Detailed analysis report saved: {report_file}")
    
    def _create_detailed_report_content(self) -> str:
        """Create detailed markdown report content"""
        
        return f"""# KMTI Test Results Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Tool:** KMTI Test Results Analyzer

## Executive Summary

{self._format_summary_section()}

## Test Results Overview  

{self._format_results_overview()}

## Failure Analysis

{self._format_failure_analysis()}

## Performance Analysis

{self._format_performance_analysis()}

## Category Health Report

{self._format_category_health()}

## Recommendations

{self._format_recommendations()}

## Technical Details

{self._format_technical_details()}

---
*Report generated by KMTI Test Results Analyzer*
"""
    
    def _format_summary_section(self) -> str:
        summary = self.analysis_results.get('summary', {})
        return f"""
- **Overall Health**: {summary.get('overall_health', 'unknown').title()}
- **Success Rate**: {summary.get('success_rate', 0):.1f}%
- **Total Tests**: {summary.get('total_tests', 0)}
- **Assessment**: {summary.get('assessment', 'No assessment available')}
"""
    
    def _format_results_overview(self) -> str:
        parsed = self.results_data['parsed_results']
        summary = parsed.get('summary', {})
        
        return f"""
| Metric | Count | Percentage |
|--------|-------|------------|
| Passed | {summary.get('passed', 0)} | {summary.get('passed_percent', 'N/A')} |
| Failed | {summary.get('failed', 0)} | {summary.get('failed_percent', 'N/A')} |  
| Errors | {summary.get('errors', 0)} | {summary.get('errors_percent', 'N/A')} |
| **Total** | **{summary.get('total_tests', 0)}** | **100%** |

**Test Duration**: {summary.get('duration', 'N/A')}
"""
    
    def _format_failure_analysis(self) -> str:
        failure_patterns = self.analysis_results.get('failure_patterns', {})
        
        content = f"**Total Failures**: {failure_patterns.get('total_failures', 0)}\n\n"
        
        if failure_patterns.get('failure_by_category'):
            content += "### Failures by Category\n\n"
            for category, count in failure_patterns['failure_by_category'].most_common():
                content += f"- **{category.title()}**: {count} failures\n"
        
        if failure_patterns.get('common_error_patterns'):
            content += "\n### Common Error Patterns\n\n"
            for pattern, count in failure_patterns['common_error_patterns'].most_common():
                content += f"- **{pattern.replace('_', ' ').title()}**: {count} occurrences\n"
        
        return content
    
    def _format_performance_analysis(self) -> str:
        performance = self.analysis_results.get('performance', {})
        
        content = f"""
**Total Duration**: {performance.get('total_duration', 0):.2f}s  
**Average Test Duration**: {performance.get('average_test_duration', 0):.3f}s  
**Performance Issues**: {len(performance.get('performance_issues', []))}
"""
        
        if performance.get('slowest_tests'):
            content += "\n### Slowest Tests\n\n"
            for test in performance['slowest_tests']:
                content += f"- **{test['name']}**: {test['duration']:.3f}s\n"
        
        return content
    
    def _format_category_health(self) -> str:
        category_health = self.analysis_results.get('category_health', {})
        
        content = ""
        
        for status, categories in [
            ('Healthy', category_health.get('healthy_categories', [])),
            ('Warning', category_health.get('warning_categories', [])),
            ('Critical', category_health.get('critical_categories', []))
        ]:
            if categories:
                content += f"\n### {status} Categories\n\n"
                for category in categories:
                    details = category_health.get('category_details', {}).get(category, {})
                    rate = details.get('success_rate', 0)
                    content += f"- **{category.title()}**: {rate:.1f}% success rate\n"
        
        return content
    
    def _format_recommendations(self) -> str:
        recommendations = self.analysis_results.get('recommendations', {})
        
        content = f"**Priority Score**: {recommendations.get('priority_score', 0)}\n\n"
        
        for section, title in [
            ('immediate_actions', 'Immediate Actions'),
            ('medium_term_improvements', 'Medium-term Improvements'),
            ('long_term_strategy', 'Long-term Strategy')
        ]:
            actions = recommendations.get(section, [])
            if actions:
                content += f"### {title}\n\n"
                for action in actions:
                    content += f"- {action}\n"
                content += "\n"
        
        return content
    
    def _format_technical_details(self) -> str:
        metadata = self.results_data.get('metadata', {})
        
        return f"""
### Analysis Metadata

- **Report File**: {metadata.get('report_file', 'N/A')}
- **Log File**: {metadata.get('log_file', 'N/A')}  
- **Analysis Time**: {metadata.get('analysis_time', 'N/A')}

### Data Sources

{len(self.results_data.get('parsed_results', {}).get('individual_tests', []))} individual test results analyzed
"""


def main():
    """Main analyzer function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='KMTI Test Results Analyzer')
    parser.add_argument('report_file', nargs='?', help='Test report file to analyze')
    parser.add_argument('--log', help='Test log file to analyze')
    parser.add_argument('--output', '-o', help='Output file for detailed report')
    
    args = parser.parse_args()
    
    try:
        analyzer = KMTITestAnalyzer()
        
        success = analyzer.analyze_results(args.report_file, args.log)
        
        if success:
            print("\n🎉 Analysis completed successfully!")
            return 0
        else:
            print("\n❌ Analysis failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 Analysis error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
