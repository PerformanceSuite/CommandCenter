"""
Cost Budget for Long-Running Agent Orchestrator

Tracks daily spending and prevents runaway costs.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


class CostBudget:
    """
    Daily cost budget tracker.

    Features:
    - Daily spending limit
    - Automatic reset at midnight UTC
    - Persistent state across restarts
    - Per-task cost tracking
    """

    def __init__(
        self,
        daily_limit: float = 50.0,
        state_file: str | Path = ".budget_state.json"
    ):
        self.daily_limit = daily_limit
        self.state_file = Path(state_file)
        self._load_state()

    def _load_state(self):
        """Load state from disk"""
        if self.state_file.exists():
            try:
                state = json.loads(self.state_file.read_text())
                self.spent_today = state.get("spent_today", 0.0)
                self.last_reset = datetime.fromisoformat(state.get("last_reset", datetime.utcnow().isoformat()))
                self.task_costs = state.get("task_costs", {})
            except (json.JSONDecodeError, KeyError):
                self._init_state()
        else:
            self._init_state()

    def _init_state(self):
        """Initialize fresh state"""
        self.spent_today = 0.0
        self.last_reset = datetime.utcnow()
        self.task_costs = {}

    def _save_state(self):
        """Persist state to disk"""
        state = {
            "spent_today": self.spent_today,
            "last_reset": self.last_reset.isoformat(),
            "task_costs": self.task_costs,
            "daily_limit": self.daily_limit,
        }
        self.state_file.write_text(json.dumps(state, indent=2))

    def _check_reset(self):
        """Reset if we've passed midnight UTC"""
        now = datetime.utcnow()
        if now.date() > self.last_reset.date():
            print(f"🔄 Budget reset (new day: {now.date()})")
            self.spent_today = 0.0
            self.last_reset = now
            self.task_costs = {}
            self._save_state()

    def record_cost(self, amount: float, task_id: str = "unknown"):
        """Record spending from a task"""
        self._check_reset()

        self.spent_today += amount
        self.task_costs[task_id] = self.task_costs.get(task_id, 0.0) + amount

        self._save_state()

        print(f"💰 Cost recorded: ${amount:.2f} (task: {task_id})")
        print(f"💰 Daily total: ${self.spent_today:.2f} / ${self.daily_limit:.2f}")

    def can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford a task without exceeding budget"""
        self._check_reset()
        return (self.spent_today + estimated_cost) <= self.daily_limit

    def exhausted(self) -> bool:
        """Check if budget is exhausted"""
        self._check_reset()
        return self.spent_today >= self.daily_limit

    def remaining(self) -> float:
        """Get remaining budget"""
        self._check_reset()
        return max(0.0, self.daily_limit - self.spent_today)

    def reset_time(self) -> datetime:
        """When does the budget reset?"""
        tomorrow = (self.last_reset + timedelta(days=1)).date()
        return datetime.combine(tomorrow, datetime.min.time())

    def status(self) -> dict:
        """Get current budget status"""
        self._check_reset()
        return {
            "daily_limit": self.daily_limit,
            "spent_today": self.spent_today,
            "remaining": self.remaining(),
            "exhausted": self.exhausted(),
            "reset_time": self.reset_time().isoformat(),
            "task_count": len(self.task_costs),
            "task_costs": self.task_costs,
        }

    def __str__(self) -> str:
        self._check_reset()
        return f"Budget: ${self.spent_today:.2f} / ${self.daily_limit:.2f} ({self.remaining():.2f} remaining)"
