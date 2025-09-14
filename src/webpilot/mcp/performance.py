"""
Performance optimization for WebPilot MCP operations.

Provides caching, parallelization, and optimization strategies.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import hashlib
import json
import time
from collections import deque
from functools import lru_cache, wraps
import logging


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    cache_hit: bool = False
    error: Optional[str] = None
    
    @property
    def timestamp(self) -> datetime:
        """Get timestamp of operation."""
        return datetime.fromtimestamp(self.start_time)


class OperationCache:
    """
    Intelligent caching for WebPilot operations.
    
    Caches results of expensive operations with TTL and size limits.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default TTL in seconds
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: deque = deque(maxlen=max_size)
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger(__name__)
    
    def _make_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate cache key from operation and parameters."""
        # Sort params for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        key_string = f"{operation}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached result if available and not expired.
        
        Args:
            operation: Operation name
            params: Operation parameters
            
        Returns:
            Cached result or None
        """
        key = self._make_key(operation, params)
        
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires']:
                self.hits += 1
                self.access_times.append((key, time.time()))
                self.logger.debug(f"Cache hit for {operation}")
                return entry['result']
            else:
                # Expired entry
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, operation: str, params: Dict[str, Any], 
            result: Any, ttl: Optional[int] = None):
        """
        Cache operation result.
        
        Args:
            operation: Operation name
            params: Operation parameters
            result: Result to cache
            ttl: TTL in seconds (uses default if not specified)
        """
        key = self._make_key(operation, params)
        ttl = ttl or self.default_ttl
        
        # Enforce size limit
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = {
            'result': result,
            'expires': datetime.now() + timedelta(seconds=ttl),
            'operation': operation,
            'params': params
        }
        self.access_times.append((key, time.time()))
        self.logger.debug(f"Cached result for {operation} (TTL: {ttl}s)")
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if self.access_times:
            oldest_key = self.access_times[0][0]
            if oldest_key in self.cache:
                del self.cache[oldest_key]
                self.logger.debug(f"Evicted LRU cache entry: {oldest_key}")
    
    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.access_times.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total
        }


class ParallelExecutor:
    """
    Execute multiple WebPilot operations in parallel.
    
    Improves performance for batch operations.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum concurrent operations
        """
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def execute_parallel(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute operations in parallel.
        
        Args:
            operations: List of operations to execute
            
        Returns:
            List of results in same order as operations
        """
        tasks = []
        for op in operations:
            task = self._execute_with_limit(op)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "operation": operations[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_with_limit(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation with concurrency limit."""
        async with self.semaphore:
            return await self._execute_operation(operation)
    
    async def _execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single operation."""
        start_time = time.time()
        
        try:
            # Import WebPilot dynamically to avoid circular imports
            from ..core import WebPilot
            
            tool_name = operation.get('tool')
            params = operation.get('params', {})
            
            # This would be replaced with actual tool execution
            # For now, simulate with delay
            await asyncio.sleep(0.1)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "tool": tool_name,
                "duration_ms": duration_ms,
                "data": {"simulated": True}
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "tool": operation.get('tool'),
                "duration_ms": duration_ms,
                "error": str(e)
            }


class PerformanceOptimizer:
    """
    Main performance optimization coordinator.
    
    Combines caching, parallelization, and performance tracking.
    """
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.cache = OperationCache()
        self.parallel_executor = ParallelExecutor()
        self.metrics: List[PerformanceMetrics] = []
        self.logger = logging.getLogger(__name__)
        
        # Optimization settings
        self.enable_cache = True
        self.enable_parallel = True
        self.enable_metrics = True
    
    def cached_operation(self, ttl: int = 300):
        """
        Decorator for caching operation results.
        
        Args:
            ttl: Cache TTL in seconds
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enable_cache:
                    return await func(*args, **kwargs)
                
                # Create cache key from function name and arguments
                operation = func.__name__
                params = {"args": args, "kwargs": kwargs}
                
                # Check cache
                cached = self.cache.get(operation, params)
                if cached is not None:
                    self.logger.debug(f"Using cached result for {operation}")
                    return cached
                
                # Execute and cache
                result = await func(*args, **kwargs)
                self.cache.set(operation, params, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    def track_performance(self, operation: str):
        """
        Decorator for tracking operation performance.
        
        Args:
            operation: Operation name for metrics
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enable_metrics:
                    return await func(*args, **kwargs)
                
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    metric = PerformanceMetrics(
                        operation=operation,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        success=success,
                        error=error
                    )
                    self.metrics.append(metric)
                    
                    # Keep only last 1000 metrics
                    if len(self.metrics) > 1000:
                        self.metrics = self.metrics[-1000:]
            
            return wrapper
        return decorator
    
    async def batch_execute(self, operations: List[Dict[str, Any]], 
                           parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Execute batch of operations with optimization.
        
        Args:
            operations: List of operations to execute
            parallel: Whether to execute in parallel
            
        Returns:
            List of results
        """
        if parallel and self.enable_parallel:
            return await self.parallel_executor.execute_parallel(operations)
        else:
            # Sequential execution
            results = []
            for op in operations:
                result = await self.parallel_executor._execute_operation(op)
                results.append(result)
            return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.metrics:
            return {
                "total_operations": 0,
                "cache_stats": self.cache.get_stats()
            }
        
        # Calculate statistics
        total_ops = len(self.metrics)
        successful_ops = sum(1 for m in self.metrics if m.success)
        failed_ops = total_ops - successful_ops
        
        durations = [m.duration_ms for m in self.metrics]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Group by operation
        op_stats = {}
        for metric in self.metrics:
            if metric.operation not in op_stats:
                op_stats[metric.operation] = {
                    "count": 0,
                    "success": 0,
                    "failed": 0,
                    "total_ms": 0
                }
            
            stats = op_stats[metric.operation]
            stats["count"] += 1
            stats["total_ms"] += metric.duration_ms
            if metric.success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        # Calculate per-operation averages
        for op, stats in op_stats.items():
            stats["avg_ms"] = stats["total_ms"] / stats["count"]
            stats["success_rate"] = (stats["success"] / stats["count"] * 100)
        
        return {
            "total_operations": total_ops,
            "successful": successful_ops,
            "failed": failed_ops,
            "success_rate": f"{(successful_ops / total_ops * 100):.1f}%",
            "performance": {
                "avg_duration_ms": f"{avg_duration:.2f}",
                "min_duration_ms": f"{min_duration:.2f}",
                "max_duration_ms": f"{max_duration:.2f}"
            },
            "by_operation": op_stats,
            "cache_stats": self.cache.get_stats()
        }
    
    def optimize_for_scenario(self, scenario: str):
        """
        Optimize settings for specific scenarios.
        
        Args:
            scenario: Optimization scenario
        """
        scenarios = {
            "speed": {
                "enable_cache": True,
                "enable_parallel": True,
                "cache_ttl": 600
            },
            "accuracy": {
                "enable_cache": False,
                "enable_parallel": False,
                "cache_ttl": 0
            },
            "balanced": {
                "enable_cache": True,
                "enable_parallel": True,
                "cache_ttl": 300
            },
            "batch": {
                "enable_cache": True,
                "enable_parallel": True,
                "cache_ttl": 60
            }
        }
        
        if scenario in scenarios:
            settings = scenarios[scenario]
            self.enable_cache = settings["enable_cache"]
            self.enable_parallel = settings["enable_parallel"]
            self.cache.default_ttl = settings["cache_ttl"]
            self.logger.info(f"Optimized for {scenario} scenario")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()