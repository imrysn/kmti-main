#!/usr/bin/env python3
"""
KMTI Performance Benchmark Suite
===============================

Dedicated performance testing and benchmarking tool for the KMTI system:
- File upload/download performance testing
- Database query performance measurement
- Concurrent user simulation
- Memory usage monitoring
- Network performance testing
- System resource utilization analysis

Usage: python benchmark_kmti_performance.py [--options]
"""

import os
import sys
import time
import json
import uuid
import hashlib
import threading
import tempfile
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
import statistics

# Try to import optional performance monitoring libraries
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️  psutil not available - memory/CPU monitoring disabled")

class PerformanceBenchmark:
    """KMTI performance benchmarking suite"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.benchmark_results = {}
        self.test_data_dir = self.project_root / "benchmark_data"
        self.start_time = None
        
    def run_benchmark_suite(self, categories: Optional[List[str]] = None) -> Dict:
        """Run complete performance benchmark suite"""
        
        print("⚡ KMTI Performance Benchmark Suite")
        print("=" * 50)
        
        self.start_time = time.time()
        
        # Available benchmark categories
        available_categories = [
            'file_operations',
            'database_performance',
            'concurrent_users',
            'memory_usage',
            'network_simulation',
            'system_resources',
            'scalability_test'
        ]
        
        if categories is None:
            categories = available_categories
        
        # Setup benchmark environment
        if not self._setup_benchmark_environment():
            print("❌ Failed to setup benchmark environment")
            return {}
        
        # Run benchmarks
        for category in categories:
            if category in available_categories:
                print(f"\n🔥 Running {category} benchmark...")
                try:
                    method = getattr(self, f'_benchmark_{category}')
                    results = method()
                    self.benchmark_results[category] = results
                    self._print_category_summary(category, results)
                except Exception as e:
                    print(f"❌ Benchmark {category} failed: {e}")
                    self.benchmark_results[category] = {'error': str(e)}
        
        # Generate final report
        self._generate_benchmark_report()
        
        return self.benchmark_results
    
    def _setup_benchmark_environment(self) -> bool:
        """Setup benchmark test environment"""
        
        print("🛠️  Setting up benchmark environment...")
        
        try:
            # Create benchmark data directory
            self.test_data_dir.mkdir(exist_ok=True)
            
            # Create test files for benchmarking
            self._create_benchmark_files()
            
            # Initialize system monitoring
            if HAS_PSUTIL:
                self.process = psutil.Process()
                self.initial_memory = self.process.memory_info()
                print("   ✅ System monitoring initialized")
            
            print("   ✅ Benchmark environment ready")
            return True
            
        except Exception as e:
            print(f"   ❌ Setup failed: {e}")
            return False
    
    def _create_benchmark_files(self):
        """Create test files for benchmarking"""
        
        test_files = {
            # Small files (< 1MB)
            'small_text.txt': b'Small file content ' * 100,  # ~2KB
            'small_json.json': json.dumps({'data': list(range(1000))}).encode(),
            
            # Medium files (1-10MB)  
            'medium_document.pdf': b'PDF content simulation ' * 50000,  # ~1MB
            'medium_data.csv': b'col1,col2,col3\n' + b'data,test,value\n' * 100000,  # ~1.5MB
            
            # Large files (10MB+)
            'large_file.zip': b'Large file content for performance testing ' * 250000,  # ~10MB
            'extra_large.dat': b'X' * (50 * 1024 * 1024),  # 50MB
        }
        
        for filename, content in test_files.items():
            file_path = self.test_data_dir / filename
            with open(file_path, 'wb') as f:
                f.write(content)
        
        print("   ✅ Created benchmark test files")
    
    def _benchmark_file_operations(self) -> Dict:
        """Benchmark file operations performance"""
        
        results = {
            'file_creation': {},
            'file_reading': {},
            'file_copying': {},
            'file_deletion': {},
            'metadata_operations': {}
        }
        
        test_files = list(self.test_data_dir.glob("*"))
        
        # File Creation Benchmark
        print("     Testing file creation...")
        creation_times = []
        for i in range(10):
            start = time.time()
            test_file = self.test_data_dir / f"create_test_{i}.tmp"
            test_file.write_bytes(b"Test content " * 1000)
            end = time.time()
            creation_times.append(end - start)
            test_file.unlink()  # Clean up
        
        results['file_creation'] = {
            'average_time': statistics.mean(creation_times),
            'median_time': statistics.median(creation_times),
            'min_time': min(creation_times),
            'max_time': max(creation_times),
            'operations_per_second': 1.0 / statistics.mean(creation_times)
        }
        
        # File Reading Benchmark
        print("     Testing file reading...")
        reading_times = []
        for test_file in test_files[:5]:  # Test first 5 files
            start = time.time()
            content = test_file.read_bytes()
            end = time.time()
            reading_times.append(end - start)
            
            # Calculate throughput
            file_size = len(content)
            throughput = file_size / (end - start) / 1024 / 1024  # MB/s
            
        results['file_reading'] = {
            'average_time': statistics.mean(reading_times),
            'median_time': statistics.median(reading_times),
            'throughput_mb_per_sec': throughput if reading_times else 0
        }
        
        # File Copying Benchmark
        print("     Testing file copying...")
        copy_times = []
        for test_file in test_files[:3]:  # Test copying 3 files
            dest_file = self.test_data_dir / f"copy_{test_file.name}"
            
            start = time.time()
            import shutil
            shutil.copy2(test_file, dest_file)
            end = time.time()
            
            copy_times.append(end - start)
            dest_file.unlink()  # Clean up
        
        results['file_copying'] = {
            'average_time': statistics.mean(copy_times) if copy_times else 0,
            'operations_per_second': 1.0 / statistics.mean(copy_times) if copy_times else 0
        }
        
        return results
    
    def _benchmark_database_performance(self) -> Dict:
        """Benchmark database operations performance"""
        
        results = {
            'json_operations': {},
            'large_dataset_queries': {},
            'concurrent_access': {}
        }
        
        # JSON Operations Benchmark
        print("     Testing JSON operations...")
        
        # Create test dataset
        test_data = {}
        for i in range(10000):
            test_data[f"record_{i}"] = {
                'id': i,
                'name': f'Test Record {i}',
                'timestamp': datetime.now().isoformat(),
                'data': {'value': i * 2, 'category': f'cat_{i % 10}'}
            }
        
        # Test JSON serialization
        start = time.time()
        json_str = json.dumps(test_data)
        serialize_time = time.time() - start
        
        # Test JSON deserialization
        start = time.time()
        loaded_data = json.loads(json_str)
        deserialize_time = time.time() - start
        
        # Test file I/O
        test_db_file = self.test_data_dir / "benchmark_db.json"
        
        start = time.time()
        with open(test_db_file, 'w') as f:
            json.dump(test_data, f)
        write_time = time.time() - start
        
        start = time.time()
        with open(test_db_file, 'r') as f:
            loaded_data = json.load(f)
        read_time = time.time() - start
        
        results['json_operations'] = {
            'serialize_time': serialize_time,
            'deserialize_time': deserialize_time,
            'file_write_time': write_time,
            'file_read_time': read_time,
            'records_per_second_write': len(test_data) / write_time,
            'records_per_second_read': len(test_data) / read_time
        }
        
        # Large Dataset Query Benchmark
        print("     Testing large dataset queries...")
        
        query_times = []
        
        # Query by ID
        start = time.time()
        result = loaded_data.get('record_5000')
        query_times.append(time.time() - start)
        
        # Query by filter
        start = time.time()
        filtered = {k: v for k, v in loaded_data.items() 
                   if v.get('data', {}).get('category') == 'cat_5'}
        query_times.append(time.time() - start)
        
        # Count operation
        start = time.time()
        count = len([v for v in loaded_data.values() 
                    if v.get('id', 0) > 5000])
        query_times.append(time.time() - start)
        
        results['large_dataset_queries'] = {
            'average_query_time': statistics.mean(query_times),
            'dataset_size': len(loaded_data),
            'queries_per_second': 1.0 / statistics.mean(query_times)
        }
        
        return results
    
    def _benchmark_concurrent_users(self) -> Dict:
        """Benchmark concurrent user operations"""
        
        results = {
            'concurrent_file_operations': {},
            'concurrent_json_operations': {},
            'thread_scaling': {}
        }
        
        print("     Testing concurrent file operations...")
        
        def simulate_user_file_operation(user_id):
            """Simulate a user file operation"""
            try:
                start_time = time.time()
                
                # Create user directory
                user_dir = self.test_data_dir / f"user_{user_id}"
                user_dir.mkdir(exist_ok=True)
                
                # Create user file
                user_file = user_dir / f"file_{user_id}.txt"
                user_file.write_text(f"Content for user {user_id} " * 100)
                
                # Read file
                content = user_file.read_text()
                
                # Update file
                user_file.write_text(content + " UPDATED")
                
                # Create metadata
                metadata = {
                    'user_id': user_id,
                    'filename': f"file_{user_id}.txt", 
                    'created': datetime.now().isoformat(),
                    'size': len(content)
                }
                
                metadata_file = user_dir / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f)
                
                end_time = time.time()
                return {
                    'user_id': user_id,
                    'success': True,
                    'duration': end_time - start_time,
                    'operations': 4  # create, read, update, metadata
                }
                
            except Exception as e:
                return {
                    'user_id': user_id,
                    'success': False,
                    'error': str(e),
                    'duration': 0,
                    'operations': 0
                }
        
        # Test different numbers of concurrent users
        for num_users in [5, 10, 20, 50]:
            print(f"       Testing {num_users} concurrent users...")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [executor.submit(simulate_user_file_operation, i) 
                          for i in range(num_users)]
                results_list = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            successful_operations = [r for r in results_list if r['success']]
            failed_operations = [r for r in results_list if not r['success']]
            
            if successful_operations:
                avg_user_time = statistics.mean([r['duration'] for r in successful_operations])
                operations_per_second = sum([r['operations'] for r in successful_operations]) / total_time
            else:
                avg_user_time = 0
                operations_per_second = 0
            
            results['concurrent_file_operations'][f'{num_users}_users'] = {
                'total_time': total_time,
                'successful_users': len(successful_operations),
                'failed_users': len(failed_operations),
                'average_user_time': avg_user_time,
                'operations_per_second': operations_per_second,
                'concurrency_efficiency': (num_users * avg_user_time) / total_time if total_time > 0 else 0
            }
        
        return results
    
    def _benchmark_memory_usage(self) -> Dict:
        """Benchmark memory usage patterns"""
        
        results = {
            'baseline_memory': {},
            'memory_growth': {},
            'memory_efficiency': {}
        }
        
        if not HAS_PSUTIL:
            results['error'] = 'psutil not available for memory monitoring'
            return results
        
        print("     Testing memory usage patterns...")
        
        # Baseline memory
        initial_memory = self.process.memory_info()
        results['baseline_memory'] = {
            'rss_mb': initial_memory.rss / 1024 / 1024,
            'vms_mb': initial_memory.vms / 1024 / 1024
        }
        
        # Memory growth test
        memory_samples = []
        data_structures = []
        
        for i in range(10):
            # Create large data structure
            large_data = {f'key_{j}': f'value_{j}' * 100 for j in range(1000)}
            data_structures.append(large_data)
            
            # Sample memory
            current_memory = self.process.memory_info()
            memory_samples.append({
                'iteration': i,
                'rss_mb': current_memory.rss / 1024 / 1024,
                'vms_mb': current_memory.vms / 1024 / 1024
            })
            
            time.sleep(0.1)  # Small delay for measurement
        
        # Calculate memory growth
        initial_rss = memory_samples[0]['rss_mb']
        final_rss = memory_samples[-1]['rss_mb']
        memory_growth = final_rss - initial_rss
        
        results['memory_growth'] = {
            'initial_rss_mb': initial_rss,
            'final_rss_mb': final_rss,
            'growth_mb': memory_growth,
            'growth_per_iteration_mb': memory_growth / len(memory_samples)
        }
        
        # Memory cleanup test
        data_structures.clear()
        
        # Force garbage collection if available
        try:
            import gc
            gc.collect()
        except ImportError:
            pass
        
        time.sleep(0.5)  # Allow cleanup
        
        cleanup_memory = self.process.memory_info()
        memory_recovered = final_rss - (cleanup_memory.rss / 1024 / 1024)
        
        results['memory_efficiency'] = {
            'memory_recovered_mb': memory_recovered,
            'recovery_percentage': (memory_recovered / memory_growth * 100) if memory_growth > 0 else 0
        }
        
        return results
    
    def _benchmark_network_simulation(self) -> Dict:
        """Benchmark network-related operations (simulated)"""
        
        results = {
            'network_path_access': {},
            'file_transfer_simulation': {}
        }
        
        print("     Testing network operations simulation...")
        
        # Simulate network path access times
        network_paths = [
            r"\\TEST-NAS\Shared\data",
            r"\\TEST-SERVER\Files",
            r"\\BACKUP-NAS\Archive"
        ]
        
        access_times = []
        for path in network_paths:
            start = time.time()
            
            # Simulate network delay
            time.sleep(0.01 + (len(path) * 0.001))  # Simulate variable latency
            
            # Check if path exists (will fail, but measures time)
            try:
                Path(path).exists()
            except:
                pass  # Expected to fail
            
            end = time.time()
            access_times.append(end - start)
        
        results['network_path_access'] = {
            'average_access_time': statistics.mean(access_times),
            'max_access_time': max(access_times),
            'min_access_time': min(access_times)
        }
        
        # Simulate file transfer performance
        print("       Simulating file transfers...")
        
        test_file = self.test_data_dir / "large_file.zip"
        file_size = test_file.stat().st_size
        
        # Simulate different transfer scenarios
        transfer_scenarios = {
            'local_copy': 1.0,  # multiplier for local operations
            'network_copy_fast': 0.3,  # fast network
            'network_copy_slow': 0.1,  # slow network
        }
        
        for scenario, speed_multiplier in transfer_scenarios.items():
            start = time.time()
            
            # Simulate reading file with network delays
            with open(test_file, 'rb') as f:
                data = f.read()
                
            # Simulate network transfer time
            simulated_transfer_time = len(data) / (10 * 1024 * 1024 * speed_multiplier)  # Simulate 10MB/s base
            time.sleep(simulated_transfer_time)
            
            total_time = time.time() - start
            throughput = file_size / total_time / 1024 / 1024  # MB/s
            
            results['file_transfer_simulation'][scenario] = {
                'file_size_mb': file_size / 1024 / 1024,
                'transfer_time_seconds': total_time,
                'throughput_mb_per_second': throughput
            }
        
        return results
    
    def _benchmark_system_resources(self) -> Dict:
        """Benchmark system resource utilization"""
        
        results = {
            'cpu_usage': {},
            'disk_io': {},
            'system_limits': {}
        }
        
        if not HAS_PSUTIL:
            results['error'] = 'psutil not available for system monitoring'
            return results
        
        print("     Testing system resource utilization...")
        
        # CPU Usage Test
        cpu_samples = []
        start_time = time.time()
        
        # Perform CPU-intensive operations
        for i in range(5):
            # Hash operations (CPU intensive)
            data = b"test data " * 10000
            for j in range(100):
                hashlib.sha256(data).hexdigest()
            
            # Sample CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_percent)
        
        cpu_test_time = time.time() - start_time
        
        results['cpu_usage'] = {
            'average_cpu_percent': statistics.mean(cpu_samples),
            'max_cpu_percent': max(cpu_samples),
            'test_duration': cpu_test_time
        }
        
        # Disk I/O Test
        print("       Testing disk I/O...")
        
        io_start = psutil.disk_io_counters()
        start_time = time.time()
        
        # Perform I/O intensive operations
        for i in range(10):
            test_file = self.test_data_dir / f"io_test_{i}.tmp"
            test_file.write_bytes(b"I/O test data " * 10000)
            content = test_file.read_bytes()
            test_file.unlink()
        
        io_end = psutil.disk_io_counters()
        io_test_time = time.time() - start_time
        
        if io_start and io_end:
            bytes_read = io_end.read_bytes - io_start.read_bytes
            bytes_written = io_end.write_bytes - io_start.write_bytes
            
            results['disk_io'] = {
                'bytes_read': bytes_read,
                'bytes_written': bytes_written,
                'read_speed_mb_per_second': bytes_read / io_test_time / 1024 / 1024,
                'write_speed_mb_per_second': bytes_written / io_test_time / 1024 / 1024,
                'test_duration': io_test_time
            }
        
        # System Limits Test
        results['system_limits'] = {
            'available_memory_mb': psutil.virtual_memory().available / 1024 / 1024,
            'total_memory_mb': psutil.virtual_memory().total / 1024 / 1024,
            'available_disk_space_gb': psutil.disk_usage('.').free / 1024 / 1024 / 1024,
            'cpu_count': psutil.cpu_count(),
            'cpu_frequency_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'
        }
        
        return results
    
    def _benchmark_scalability_test(self) -> Dict:
        """Test system scalability limits"""
        
        results = {
            'file_count_limits': {},
            'data_size_limits': {},
            'concurrent_operation_limits': {}
        }
        
        print("     Testing scalability limits...")
        
        # File Count Limits Test
        print("       Testing file count scalability...")
        
        file_count_results = {}
        for file_count in [100, 500, 1000, 2000]:
            try:
                start_time = time.time()
                
                # Create many small files
                test_dir = self.test_data_dir / f"scale_test_{file_count}"
                test_dir.mkdir(exist_ok=True)
                
                for i in range(file_count):
                    test_file = test_dir / f"file_{i:04d}.txt"
                    test_file.write_text(f"Content for file {i}")
                
                creation_time = time.time() - start_time
                
                # Test directory listing performance
                start_time = time.time()
                files = list(test_dir.iterdir())
                listing_time = time.time() - start_time
                
                file_count_results[file_count] = {
                    'creation_time': creation_time,
                    'listing_time': listing_time,
                    'files_per_second_creation': file_count / creation_time,
                    'files_per_second_listing': file_count / listing_time
                }
                
                # Cleanup
                import shutil
                shutil.rmtree(test_dir)
                
            except Exception as e:
                file_count_results[file_count] = {'error': str(e)}
        
        results['file_count_limits'] = file_count_results
        
        # Data Size Limits Test
        print("       Testing data size scalability...")
        
        data_size_results = {}
        for size_mb in [1, 10, 50, 100]:
            try:
                start_time = time.time()
                
                # Create large data structure
                large_data = {'data': 'X' * (size_mb * 1024 * 1024)}
                
                # Test JSON serialization performance
                json_str = json.dumps(large_data)
                serialization_time = time.time() - start_time
                
                # Test JSON deserialization performance
                start_time = time.time()
                loaded_data = json.loads(json_str)
                deserialization_time = time.time() - start_time
                
                data_size_results[size_mb] = {
                    'serialization_time': serialization_time,
                    'deserialization_time': deserialization_time,
                    'mb_per_second_serialize': size_mb / serialization_time,
                    'mb_per_second_deserialize': size_mb / deserialization_time
                }
                
            except Exception as e:
                data_size_results[size_mb] = {'error': str(e)}
        
        results['data_size_limits'] = data_size_results
        
        return results
    
    def _print_category_summary(self, category: str, results: Dict):
        """Print summary of benchmark category results"""
        
        if 'error' in results:
            print(f"     ❌ Error: {results['error']}")
            return
        
        print(f"     ✅ {category} benchmark completed")
        
        # Print key metrics based on category
        if category == 'file_operations':
            file_ops = results.get('file_creation', {})
            avg_time = file_ops.get('average_time', 0)
            ops_per_sec = file_ops.get('operations_per_second', 0)
            print(f"       • File creation: {avg_time:.4f}s avg, {ops_per_sec:.1f} ops/sec")
            
        elif category == 'database_performance':
            json_ops = results.get('json_operations', {})
            write_speed = json_ops.get('records_per_second_write', 0)
            read_speed = json_ops.get('records_per_second_read', 0)
            print(f"       • JSON performance: {write_speed:.0f} writes/sec, {read_speed:.0f} reads/sec")
            
        elif category == 'concurrent_users':
            if '20_users' in results.get('concurrent_file_operations', {}):
                test_20_users = results['concurrent_file_operations']['20_users']
                ops_per_sec = test_20_users.get('operations_per_second', 0)
                print(f"       • 20 concurrent users: {ops_per_sec:.1f} ops/sec")
                
        elif category == 'memory_usage':
            growth = results.get('memory_growth', {})
            growth_mb = growth.get('growth_mb', 0)
            print(f"       • Memory growth: {growth_mb:.1f} MB")
    
    def _generate_benchmark_report(self):
        """Generate comprehensive benchmark report"""
        
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 50)
        print("🏁 BENCHMARK RESULTS SUMMARY")
        print("=" * 50)
        
        print(f"📊 Total Benchmark Time: {total_time:.2f} seconds")
        print(f"🧪 Categories Tested: {len(self.benchmark_results)}")
        
        # Generate performance score
        performance_score = self._calculate_performance_score()
        print(f"⭐ Overall Performance Score: {performance_score}/100")
        
        # Save detailed results to file
        results_file = self.project_root / "benchmark_results.json"
        benchmark_data = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': total_time,
            'performance_score': performance_score,
            'results': self.benchmark_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(benchmark_data, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")
        
        # Generate markdown report
        self._generate_markdown_report(benchmark_data)
    
    def _calculate_performance_score(self) -> int:
        """Calculate overall performance score (0-100)"""
        
        score = 100  # Start with perfect score
        
        # Deduct points based on performance issues
        for category, results in self.benchmark_results.items():
            if 'error' in results:
                score -= 20  # Major deduction for errors
                continue
            
            # Category-specific scoring
            if category == 'file_operations':
                file_creation = results.get('file_creation', {})
                avg_time = file_creation.get('average_time', 0)
                if avg_time > 0.1:  # Slower than 100ms per file
                    score -= 10
                elif avg_time > 0.05:  # Slower than 50ms per file
                    score -= 5
            
            elif category == 'concurrent_users':
                # Check concurrent performance
                concurrent_ops = results.get('concurrent_file_operations', {})
                if '20_users' in concurrent_ops:
                    ops_per_sec = concurrent_ops['20_users'].get('operations_per_second', 0)
                    if ops_per_sec < 50:  # Less than 50 operations per second
                        score -= 15
                    elif ops_per_sec < 100:
                        score -= 8
            
            elif category == 'memory_usage':
                if HAS_PSUTIL:
                    growth = results.get('memory_growth', {})
                    growth_per_iter = growth.get('growth_per_iteration_mb', 0)
                    if growth_per_iter > 10:  # More than 10MB growth per iteration
                        score -= 10
                    elif growth_per_iter > 5:
                        score -= 5
        
        return max(0, min(100, score))  # Ensure score is between 0-100
    
    def _generate_markdown_report(self, benchmark_data: Dict):
        """Generate markdown benchmark report"""
        
        report_content = f"""# KMTI Performance Benchmark Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Duration:** {benchmark_data['total_duration']:.2f} seconds  
**Performance Score:** {benchmark_data['performance_score']}/100

## Executive Summary

This report contains comprehensive performance benchmarks for the KMTI Data Management System, testing various aspects of system performance including file operations, database queries, concurrent user handling, memory usage, and scalability limits.

## Performance Score Breakdown

- **Overall Score:** {benchmark_data['performance_score']}/100
- **Rating:** {self._get_performance_rating(benchmark_data['performance_score'])}

## Detailed Results

{self._format_benchmark_results(benchmark_data['results'])}

## Recommendations

{self._generate_performance_recommendations(benchmark_data)}

---
*Report generated by KMTI Performance Benchmark Suite*
"""
        
        report_file = self.project_root / "benchmark_report.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"📊 Benchmark report saved to: {report_file}")
    
    def _get_performance_rating(self, score: int) -> str:
        """Get performance rating based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _format_benchmark_results(self, results: Dict) -> str:
        """Format benchmark results for markdown report"""
        
        content = ""
        
        for category, data in results.items():
            content += f"\n### {category.replace('_', ' ').title()}\n\n"
            
            if 'error' in data:
                content += f"❌ **Error:** {data['error']}\n\n"
                continue
            
            # Format category-specific results
            if category == 'file_operations':
                file_creation = data.get('file_creation', {})
                content += f"- **File Creation Average:** {file_creation.get('average_time', 0):.4f}s\n"
                content += f"- **Operations per Second:** {file_creation.get('operations_per_second', 0):.1f}\n"
                
                file_reading = data.get('file_reading', {})
                content += f"- **File Reading Throughput:** {file_reading.get('throughput_mb_per_sec', 0):.2f} MB/s\n"
            
            elif category == 'database_performance':
                json_ops = data.get('json_operations', {})
                content += f"- **JSON Write Speed:** {json_ops.get('records_per_second_write', 0):.0f} records/sec\n"
                content += f"- **JSON Read Speed:** {json_ops.get('records_per_second_read', 0):.0f} records/sec\n"
            
            elif category == 'memory_usage' and HAS_PSUTIL:
                baseline = data.get('baseline_memory', {})
                growth = data.get('memory_growth', {})
                content += f"- **Baseline Memory:** {baseline.get('rss_mb', 0):.1f} MB\n"
                content += f"- **Memory Growth:** {growth.get('growth_mb', 0):.1f} MB\n"
            
            content += "\n"
        
        return content
    
    def _generate_performance_recommendations(self, benchmark_data: Dict) -> str:
        """Generate performance recommendations"""
        
        score = benchmark_data['performance_score']
        recommendations = []
        
        if score < 60:
            recommendations.append("🚨 **Critical:** System performance is below acceptable levels")
            recommendations.append("Consider hardware upgrades or system optimization")
        
        elif score < 75:
            recommendations.append("⚠️ **Warning:** System performance could be improved")
            recommendations.append("Review slow operations and optimize bottlenecks")
        
        else:
            recommendations.append("✅ **Good:** System performance is acceptable")
            recommendations.append("Continue monitoring and maintain current performance levels")
        
        # Specific recommendations based on results
        results = benchmark_data['results']
        
        if 'memory_usage' in results and HAS_PSUTIL:
            growth = results['memory_usage'].get('memory_growth', {})
            if growth.get('growth_mb', 0) > 50:
                recommendations.append("💾 **Memory:** High memory usage detected - implement better memory management")
        
        if 'concurrent_users' in results:
            concurrent_ops = results['concurrent_users'].get('concurrent_file_operations', {})
            if '20_users' in concurrent_ops:
                ops_per_sec = concurrent_ops['20_users'].get('operations_per_second', 0)
                if ops_per_sec < 50:
                    recommendations.append("👥 **Concurrency:** Low concurrent performance - optimize for multi-user scenarios")
        
        return "\n".join([f"- {rec}" for rec in recommendations])


def main():
    """Main benchmark function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='KMTI Performance Benchmark Suite')
    parser.add_argument('--categories', nargs='*',
                       help='Specific benchmark categories to run',
                       choices=['file_operations', 'database_performance', 'concurrent_users',
                               'memory_usage', 'network_simulation', 'system_resources', 'scalability_test'])
    parser.add_argument('--iterations', type=int, default=1,
                       help='Number of benchmark iterations to run')
    parser.add_argument('--output', '-o',
                       help='Output directory for benchmark results')
    
    args = parser.parse_args()
    
    try:
        benchmark = PerformanceBenchmark()
        
        # Run benchmarks
        for iteration in range(args.iterations):
            if args.iterations > 1:
                print(f"\n🔄 Benchmark Iteration {iteration + 1}/{args.iterations}")
            
            results = benchmark.run_benchmark_suite(args.categories)
            
            if not results:
                print("❌ Benchmark failed")
                return 1
        
        print("\n🎉 Performance benchmark completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Benchmark interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 Benchmark error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
