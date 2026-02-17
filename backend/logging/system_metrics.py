"""
System Metrics Monitoring Module

Provides system metrics logging for performance monitoring:
- RAM usage
- GPU usage
- Active tasks
- DB connections

Logs periodically to track system health and performance.
"""

import asyncio
import psutil
import time
from datetime import datetime
from typing import Dict, Optional

from backend.logging.logger import get_logger


logger = get_logger("system_metrics", component="monitoring")


class SystemMetrics:
    """
    System metrics collector for monitoring resource usage.
    
    Tracks:
    - RAM usage
    - GPU memory usage
    - Active tasks
    - DB connections
    """
    
    def __init__(self, interval: int = 30):
        """
        Initialize system metrics collector.
        
        Args:
            interval: Logging interval in seconds
        """
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_metrics: Dict = {}
    
    async def start(self) -> None:
        """Start periodic metrics collection."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info("System metrics collection started", interval=self.interval)
    
    async def stop(self) -> None:
        """Stop periodic metrics collection."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("System metrics collection stopped")
    
    async def _collect_loop(self) -> None:
        """Main collection loop."""
        while self._running:
            try:
                metrics = await self.collect_metrics()
                self._last_metrics = metrics
                self._log_metrics(metrics)
            except Exception as e:
                logger.error(
                    "Failed to collect metrics",
                    error=str(e),
                    exception=e
                )
            
            await asyncio.sleep(self.interval)
    
    async def collect_metrics(self) -> Dict:
        """
        Collect current system metrics.
        
        Returns:
            Dictionary with current metrics
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
            },
            "memory": {
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "used_mb": memory.used / (1024 * 1024),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": disk.total / (1024 * 1024 * 1024),
                "used_gb": disk.used / (1024 * 1024 * 1024),
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "percent": disk.percent,
            },
        }
        
        # GPU metrics (if available)
        try:
            import torch
            if torch.cuda.is_available():
                gpu_metrics = {
                    "available": True,
                    "device_count": torch.cuda.device_count(),
                    "current_device": torch.cuda.current_device(),
                    "memory_allocated_mb": torch.cuda.memory_allocated() / (1024 * 1024),
                    "memory_reserved_mb": torch.cuda.memory_reserved() / (1024 * 1024),
                    "max_memory_allocated_mb": torch.cuda.max_memory_allocated() / (1024 * 1024),
                }
                
                # Get memory for each device
                device_memory = []
                for i in range(torch.cuda.device_count()):
                    device_memory.append({
                        "device": i,
                        "allocated_mb": torch.cuda.memory_allocated(i) / (1024 * 1024),
                        "reserved_mb": torch.cuda.memory_reserved(i) / (1024 * 1024),
                    })
                gpu_metrics["devices"] = device_memory
                
                metrics["gpu"] = gpu_metrics
            else:
                metrics["gpu"] = {"available": False}
        except ImportError:
            metrics["gpu"] = {"available": False, "error": "PyTorch not available"}
        
        # Active tasks (if running in async context)
        try:
            loop = asyncio.get_event_loop()
            tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
            metrics["async"] = {
                "active_tasks": len(tasks),
            }
        except RuntimeError:
            metrics["async"] = {"active_tasks": 0}
        
        return metrics
    
    def _log_metrics(self, metrics: Dict) -> None:
        """Log metrics to structured logger."""
        # Log at info level for regular metrics
        logger.info(
            "System metrics snapshot",
            memory_mb=metrics["memory"]["used_mb"],
            memory_percent=metrics["memory"]["percent"],
            cpu_percent=metrics["cpu"]["percent"],
            active_tasks=metrics["async"]["active_tasks"],
            metadata=metrics,
        )
        
        # Log warnings for high usage
        if metrics["memory"]["percent"] > 90:
            logger.warning(
                "High memory usage detected",
                memory_percent=metrics["memory"]["percent"],
            )
        
        if metrics["cpu"]["percent"] > 90:
            logger.warning(
                "High CPU usage detected",
                cpu_percent=metrics["cpu"]["percent"],
            )
        
        # Check GPU if available
        if metrics.get("gpu", {}).get("available"):
            gpu = metrics["gpu"]
            if gpu.get("memory_allocated_mb", 0) > 0:
                # Log GPU memory if being used
                logger.info(
                    "GPU memory usage",
                    gpu_memory_mb=gpu["memory_allocated_mb"],
                    gpu_memory_reserved_mb=gpu["memory_reserved_mb"],
                )
    
    def get_current_metrics(self) -> Dict:
        """
        Get the last collected metrics.
        
        Returns:
            Last metrics dictionary or empty dict if not collected yet
        """
        return self._last_metrics


# Global metrics collector instance
_metrics_collector: Optional[SystemMetrics] = None


def get_metrics_collector(interval: int = 30) -> SystemMetrics:
    """
    Get the global metrics collector instance.
    
    Args:
        interval: Collection interval in seconds
    
    Returns:
        SystemMetrics instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SystemMetrics(interval=interval)
    return _metrics_collector


async def start_metrics_collection(interval: int = 30) -> None:
    """
    Start system metrics collection.
    
    Args:
        interval: Collection interval in seconds
    """
    collector = get_metrics_collector(interval)
    await collector.start()


async def stop_metrics_collection() -> None:
    """Stop system metrics collection."""
    collector = get_metrics_collector()
    await collector.stop()


def get_current_metrics() -> Dict:
    """
    Get current system metrics.
    
    Returns:
        Current metrics dictionary
    """
    collector = get_metrics_collector()
    return collector.get_current_metrics()


__all__ = [
    "SystemMetrics",
    "get_metrics_collector",
    "start_metrics_collection",
    "stop_metrics_collection",
    "get_current_metrics",
]
