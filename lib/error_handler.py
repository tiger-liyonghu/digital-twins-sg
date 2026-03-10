#!/usr/bin/env python3
"""
错误处理模块 - 提供统一的错误处理、重试和降级机制

功能：
1. 断路器模式（Circuit Breaker）
2. 重试机制（Retry）
3. 优雅降级（Graceful Degradation）
4. 错误监控和报警
5. 性能监控

使用方法：
    from lib.error_handler import (
        circuit_breaker, retry_on_failure, 
        fallback_on_error, ErrorMonitor
    )
    
    @circuit_breaker(failure_threshold=3, recovery_timeout=60)
    @retry_on_failure(max_attempts=3, delay=1)
    @fallback_on_error(default_value={"error": "fallback"})
    def critical_function():
        # 受保护的函数
        pass
"""

import time
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# 配置日志
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "LOW"      # 可恢复，不影响核心功能
    MEDIUM = "MEDIUM" # 部分功能受影响
    HIGH = "HIGH"    # 核心功能受影响
    CRITICAL = "CRITICAL" # 系统不可用

@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: datetime
    function_name: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "function_name": self.function_name,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "resolved": self.resolved
        }

class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.errors: List[ErrorRecord] = []
        self.metrics = {
            "total_errors": 0,
            "errors_by_severity": {sev.value: 0 for sev in ErrorSeverity},
            "errors_by_function": {},
            "last_error_time": None
        }
    
    def record_error(
        self,
        function_name: str,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ) -> ErrorRecord:
        """记录错误"""
        
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            function_name=function_name,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            context=context or {},
            stack_trace=stack_trace
        )
        
        # 添加到错误列表
        self.errors.append(error_record)
        
        # 维护列表大小
        if len(self.errors) > self.max_records:
            self.errors = self.errors[-self.max_records:]
        
        # 更新指标
        self.metrics["total_errors"] += 1
        self.metrics["errors_by_severity"][severity.value] += 1
        self.metrics["errors_by_function"][function_name] = \
            self.metrics["errors_by_function"].get(function_name, 0) + 1
        self.metrics["last_error_time"] = error_record.timestamp.isoformat()
        
        # 根据严重程度记录日志
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"严重错误 [{severity.value}]: {function_name} - {error}")
            # 这里可以添加报警逻辑（邮件、Slack等）
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"中等错误: {function_name} - {error}")
        else:
            logger.info(f"轻微错误: {function_name} - {error}")
        
        return error_record
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        recent = self.errors[-limit:] if self.errors else []
        return [err.to_dict() for err in recent]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        summary = self.metrics.copy()
        
        # 添加时间窗口统计
        now = datetime.now()
        hour_ago = now.timestamp() - 3600
        day_ago = now.timestamp() - 86400
        
        recent_hour = [e for e in self.errors 
                      if e.timestamp.timestamp() > hour_ago]
        recent_day = [e for e in self.errors 
                     if e.timestamp.timestamp() > day_ago]
        
        summary.update({
            "errors_last_hour": len(recent_hour),
            "errors_last_day": len(recent_day),
            "unresolved_errors": len([e for e in self.errors if not e.resolved]),
            "total_records": len(self.errors)
        })
        
        return summary
    
    def mark_resolved(self, error_index: int) -> bool:
        """标记错误为已解决"""
        if 0 <= error_index < len(self.errors):
            self.errors[error_index].resolved = True
            return True
        return False
    
    def clear_resolved_errors(self):
        """清理已解决的错误"""
        self.errors = [e for e in self.errors if not e.resolved]
    
    def save_to_file(self, filepath: str):
        """保存错误记录到文件"""
        data = {
            "errors": [e.to_dict() for e in self.errors],
            "metrics": self.metrics,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"错误记录已保存到: {filepath}")
    
    def load_from_file(self, filepath: str) -> bool:
        """从文件加载错误记录"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复错误记录
            self.errors = []
            for err_dict in data.get("errors", []):
                error_record = ErrorRecord(
                    timestamp=datetime.fromisoformat(err_dict["timestamp"]),
                    function_name=err_dict["function_name"],
                    error_type=err_dict["error_type"],
                    error_message=err_dict["error_message"],
                    severity=ErrorSeverity(err_dict["severity"]),
                    context=err_dict.get("context", {}),
                    stack_trace=err_dict.get("stack_trace"),
                    resolved=err_dict.get("resolved", False)
                )
                self.errors.append(error_record)
            
            # 恢复指标
            self.metrics = data.get("metrics", self.metrics)
            
            logger.info(f"从文件加载了 {len(self.errors)} 条错误记录")
            return True
            
        except Exception as e:
            logger.error(f"加载错误记录失败: {str(e)}")
            return False

# 全局错误监控器实例
global_monitor = ErrorMonitor()

class CircuitBreaker:
    """断路器模式实现"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        monitor: Optional[ErrorMonitor] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.monitor = monitor or global_monitor
    
    def can_execute(self) -> bool:
        """检查是否允许执行"""
        now = time.time()
        
        if self.state == "OPEN":
            if self.last_failure_time and (now - self.last_failure_time > self.recovery_timeout):
                self.state = "HALF_OPEN"
                logger.info("断路器进入半开状态")
                return True
            return False
        
        return True
    
    def record_success(self):
        """记录成功"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failures = 0
            logger.info("断路器关闭，恢复正常")
    
    def record_failure(self, error: Optional[Exception] = None):
        """记录失败"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if error:
            self.monitor.record_error(
                function_name="circuit_breaker",
                error=error,
                severity=ErrorSeverity.HIGH,
                context={
                    "failures": self.failures,
                    "state": self.state,
                    "threshold": self.failure_threshold
                }
            )
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"断路器打开，失败次数: {self.failures}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取断路器状态"""
        return {
            "state": self.state,
            "failures": self.failures,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }

def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    monitor: Optional[ErrorMonitor] = None
):
    """断路器装饰器"""
    
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(failure_threshold, recovery_timeout, monitor)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        
        # 添加状态访问方法
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    monitor: Optional[ErrorMonitor] = None
):
    """重试装饰器"""
    
    def decorator(func: Callable) -> Callable:
        monitor_instance = monitor or global_monitor
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # 记录错误
                    monitor_instance.record_error(
                        function_name=func.__name__,
                        error=e,
                        severity=ErrorSeverity.LOW,
                        context={
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "args": str(args)[:100],
                            "kwargs": str(kwargs)[:100]
                        }
                    )
                    
                    # 如果是最后一次尝试，抛出异常
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} 重试{max_attempts}次后失败: {e}")
                        raise
                    
                    # 计算延迟时间
                    wait_time = delay * (backoff_factor ** (attempt - 1))
                    logger.warning(f"{func.__name__} 第{attempt}次失败，{wait_time:.1f}秒后重试: {e}")
                    
                    time.sleep(wait_time)
            
            # 理论上不会执行到这里
            raise last_exception
        
        return wrapper
    
    return decorator

def fallback_on_error(
    default_value: Any = None,
    exceptions: tuple = (Exception,),
    monitor: Optional[ErrorMonitor] = None
):
    """优雅降级装饰器"""
    
    def decorator(func: Callable) -> Callable:
        monitor_instance = monitor or global_monitor
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # 记录错误
                monitor_instance.record_error(
                    function_name=func.__name__,
                    error=e,
                    severity=ErrorSeverity.MEDIUM,
                    context={
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                        "fallback_used": True,
                        "default_value": str(default_value)[:200]
                    }
                )
                
                logger.warning(f"{func.__name__} 失败，使用降级值: {default_value}")
                return default_value
        
        return wrapper
    
    return decorator

def timeout(
    timeout_seconds: float = 30.0,
    default_value: Any = None,
    monitor: Optional[ErrorMonitor] = None
):
    """超时装饰器"""
    
    def decorator(func: Callable) -> Callable:
        monitor_instance = monitor or global_monitor
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            
            # 设置信号处理器
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消警报
                return result
            except TimeoutError as e:
                # 记录超时错误
                monitor_instance.record_error(
                    function_name=func.__name__,
                    error=e,
                    severity=ErrorSeverity.MEDIUM,
                    context={
                        "timeout_seconds": timeout_seconds,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100]
                    }
                )
                
                logger.warning(f"{func.__name__} 超时，使用默认值")
                return default_value
            finally:
                signal.alarm(0)  # 确保取消警报
        
        return wrapper
    
    return decorator

class ErrorHandler:
    """错误处理器（组合模式）"""
    
    def __init__(
        self,
        func: Callable,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        fallback_value: Any = None,
        timeout_seconds: Optional[float] = None,
        monitor: Optional[ErrorMonitor] = None
    ):
        self.func = func
        self.max_retries = max_retries
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.fallback_value = fallback_value
        self.timeout_seconds = timeout_seconds
        self.monitor = monitor or global_monitor
        
        # 构建装饰链
        self.decorated_func = self._decorate_function()
    
    def _decorate_function(self) -> Callable:
        """应用所有装饰器"""
        func = self.func
        
        # 应用超时装饰器
        if self.timeout_seconds:
            func = timeout(
                timeout_seconds=self.timeout_seconds,
                default_value=self.fallback_value,
                monitor=self.monitor
            )(func)
        
        # 应用断路器装饰器
        func = circuit_breaker(
            failure_threshold=self.circuit_breaker_threshold,
            monitor=self.monitor
        )(func)
        
        # 应用重试装饰器
        func = retry_on_failure(
            max_attempts=self.max_retries,
            monitor=self.monitor
        )(func)
        
        # 应用降级装饰器
        func = fallback_on_error(
            default_value=self.fallback_value,
            monitor=self.monitor
        )(func)
        
        return func
    
    def __call__(self, *args, **kwargs):
        """调用装饰后的函数"""
        return self.decorated_func(*args, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        status = {
            "function_name": self.func.__name__,
            "max_retries": self.max_retries,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "has_fallback": self.fallback_value is not None,
            "timeout_seconds": self.timeout_seconds
        }
        
        # 获取断路器状态
        if hasattr(self.decorated_func, 'circuit_breaker'):
            status["circuit_breaker"] = self.decorated_func.circuit_breaker.get_status()
        
        return status

# 使用示例
def example_usage():
    """使用示例"""
    
    # 创建错误监控器
    monitor = ErrorMonitor()
    
    # 示例1：使用装饰器组合
    @circuit_breaker(failure_threshold=3)
    @retry_on_failure(max_attempts=2)
    @fallback_on_error(default_value={"status": "error"})
    def risky_function(x):
        if x < 0:
            raise ValueError("Negative value not allowed")
        return {"result": x * 2}
    
    # 示例2：使用ErrorHandler类
    def another_risky_function(y):
        if y == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return 100 / y
    
    handler = ErrorHandler(
        func=another_risky_function,
        max_retries=2,
        circuit_breaker_threshold=3,
        fallback_value=0,
        timeout_seconds=5,
        monitor=monitor
    )
    
    # 测试
    print("测试risky_function:")
    try:
        result = risky_function(5)
        print(f"  成功: {result}")
    except Exception as e:
        print(f"  失败: {e}")
    
    try:
        result = risky_function(-1)
        print(f"  成功（降级）: {result}")
    except Exception as e:
        print(f"  失败: {e}")
    
    print("\n测试ErrorHandler:")
    try:
        result = handler(10)
        print(f"  成功: {result}")
    except Exception as e:
        print(f"  失败: {e}")
    
    try:
        result = handler(0)
        print(f"  成功（降级）: {result}")
    except Exception as e:
        print(f"  失败: {e}")
    
    # 查看错误摘要
    print(f"\n错误摘要:")
    summary = monitor.get_error_summary()
    print(f"  总错误数: {summary['total_errors']}")
    print(f"  未解决错误: {summary['unresolved_errors']}")
    
    # 查看处理器状态
    print(f"\n处理器状态:")
    print(f"  {handler.get_status()}")

# 集成到现有系统的示例
def integrate_with_existing_system():
    """集成到现有系统的示例"""
    
    from lib.llm import ask_agent  # 假设这是现有的LLM函数
    
    # 包装现有的ask_agent函数
    protected_ask_agent = ErrorHandler(
        func=ask_agent,
        max_retries=3,
        circuit_breaker_threshold=5,
        fallback_value={
            "choice": "不确定",
            "reasoning": "系统暂时不可用",
            "willingness_score": 5,
            "fallback": True
        },
        timeout_seconds=30,
        monitor=global_monitor
    )
    
    # 现在可以安全地使用protected_ask_agent
    # 它会自动处理错误、重试、降级
    
    return protected_ask_agent

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("错误处理模块示例")
    print("=" * 50)
    
    example_usage()
    
    print("\n" + "=" * 50)
    print("全局监控器状态:")
    print(json.dumps(global_monitor.get_error_summary(), indent=2))