"""
Progress tracking service for long-running tasks
Allows frontend to poll for real-time progress updates
"""

from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressTracker:
    """
    Tracks progress of background tasks like course processing, embedding, etc.
    """
    
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}
    
    def start_task(self, task_id: str, total_steps: int, description: str = ""):
        """Start tracking a new task"""
        self._tasks[task_id] = {
            "task_id": task_id,
            "status": TaskStatus.RUNNING,
            "description": description,
            "total_steps": total_steps,
            "current_step": 0,
            "current_step_name": "",
            "progress_percentage": 0,
            "steps_log": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None
        }
    
    def update_step(self, task_id: str, step_number: int, step_name: str, details: str = ""):
        """Update current step of a task"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["current_step"] = step_number
        task["current_step_name"] = step_name
        task["progress_percentage"] = int((step_number / task["total_steps"]) * 100)
        
        # Add to log
        task["steps_log"].append({
            "step": step_number,
            "name": step_name,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_log(self, task_id: str, message: str, level: str = "info"):
        """Add a log message without updating step"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["steps_log"].append({
            "step": task["current_step"],
            "name": task["current_step_name"],
            "details": message,
            "level": level,
            "timestamp": datetime.now().isoformat()
        })
    
    def complete_task(self, task_id: str, result: Dict = None):
        """Mark task as completed"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["status"] = TaskStatus.COMPLETED
        task["progress_percentage"] = 100
        task["completed_at"] = datetime.now().isoformat()
        if result:
            task["result"] = result
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task["status"] = TaskStatus.FAILED
        task["error"] = error
        task["completed_at"] = datetime.now().isoformat()
    
    def get_task_progress(self, task_id: str) -> Optional[Dict]:
        """Get current progress of a task"""
        return self._tasks.get(task_id)
    
    def clear_task(self, task_id: str):
        """Remove task from tracker"""
        if task_id in self._tasks:
            del self._tasks[task_id]
    
    def get_all_tasks(self) -> Dict[str, Dict]:
        """Get all tracked tasks"""
        return self._tasks.copy()


# Global instance
progress_tracker = ProgressTracker()
