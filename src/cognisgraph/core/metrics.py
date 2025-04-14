from dataclasses import dataclass
from typing import Dict, List, Optional
import time
from datetime import datetime
import json
import os
from pathlib import Path

@dataclass
class OperationMetrics:
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class PerformanceTracker:
    def __init__(self, log_dir: str = "logs/metrics"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_operations: Dict[str, OperationMetrics] = {}
        self.operation_history: List[OperationMetrics] = []

    def start_operation(self, operation_name: str, metadata: Optional[Dict] = None) -> str:
        """Start tracking an operation and return its ID."""
        operation_id = f"{operation_name}_{int(time.time())}"
        self.current_operations[operation_id] = OperationMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            end_time=0,
            duration=0,
            success=False,
            metadata=metadata
        )
        return operation_id

    def end_operation(self, operation_id: str, success: bool = True, error: Optional[str] = None):
        """End tracking an operation."""
        if operation_id not in self.current_operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.current_operations[operation_id]
        operation.end_time = time.time()
        operation.duration = operation.end_time - operation.start_time
        operation.success = success
        operation.error = error

        self.operation_history.append(operation)
        del self.current_operations[operation_id]

        # Log the operation
        self._log_operation(operation)

    def get_operation_metrics(self, operation_id: str) -> Optional[OperationMetrics]:
        """Get metrics for a specific operation."""
        return self.current_operations.get(operation_id)

    def get_average_duration(self, operation_name: str) -> float:
        """Get average duration for a specific operation type."""
        durations = [
            op.duration for op in self.operation_history
            if op.operation_name == operation_name
        ]
        return sum(durations) / len(durations) if durations else 0

    def get_success_rate(self, operation_name: str) -> float:
        """Get success rate for a specific operation type."""
        operations = [
            op for op in self.operation_history
            if op.operation_name == operation_name
        ]
        if not operations:
            return 0
        return sum(1 for op in operations if op.success) / len(operations)

    def _log_operation(self, operation: OperationMetrics):
        """Log operation metrics to a file."""
        log_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation_name": operation.operation_name,
            "duration": operation.duration,
            "success": operation.success,
            "error": operation.error,
            "metadata": operation.metadata
        }

        if log_file.exists():
            with open(log_file, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        else:
            logs = []

        logs.append(log_entry)

        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def get_metrics_summary(self) -> Dict:
        """Get a summary of all metrics."""
        summary = {}
        for operation in self.operation_history:
            if operation.operation_name not in summary:
                summary[operation.operation_name] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_count": 0,
                    "error_count": 0
                }
            
            metrics = summary[operation.operation_name]
            metrics["count"] += 1
            metrics["total_duration"] += operation.duration
            if operation.success:
                metrics["success_count"] += 1
            else:
                metrics["error_count"] += 1

        # Calculate averages and rates
        for op_name, metrics in summary.items():
            metrics["average_duration"] = metrics["total_duration"] / metrics["count"]
            metrics["success_rate"] = metrics["success_count"] / metrics["count"]

        return summary 