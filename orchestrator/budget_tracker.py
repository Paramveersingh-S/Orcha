import json
import os
from datetime import datetime, timezone
from pathlib import Path

BUDGET_FILE = Path("state/budget_tracker.json")

class BudgetTracker:
    def __init__(self):
        self.state_dir = BUDGET_FILE.parent
        if not self.state_dir.exists():
            self.state_dir.mkdir(parents=True, exist_ok=True)
            
        self.budget = self._load_budget()

    def _load_budget(self):
        if BUDGET_FILE.exists():
            with open(BUDGET_FILE, "r") as f:
                return json.load(f)
        return self._initialize_budget()

    def _initialize_budget(self):
        # Default limits based on spec (to be refreshed/monitored dynamically if possible)
        initial = {
            "groq": {"requests_used": 0, "requests_limit": 14000, "reset_at": datetime.now(timezone.utc).isoformat()},
            "openrouter": {"requests_used": 0, "requests_limit": 200, "reset_at": datetime.now(timezone.utc).isoformat()},
            "gemini": {"requests_used": 0, "requests_limit": 1500, "reset_at": datetime.now(timezone.utc).isoformat()},
            "cerebras": {"requests_used": 0, "requests_limit": 14000, "reset_at": datetime.now(timezone.utc).isoformat()}
        }
        self._save_budget(initial)
        return initial

    def _save_budget(self, data=None):
        if data is None:
            data = self.budget
        with open(BUDGET_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def log_usage(self, provider: str, tokens: int = 0):
        provider = provider.lower()
        if provider not in self.budget:
            self.budget[provider] = {"requests_used": 0, "requests_limit": 100, "reset_at": datetime.now(timezone.utc).isoformat()}
            
        self.budget[provider]["requests_used"] += 1
        self._save_budget()

    def is_near_cap(self, provider: str) -> bool:
        provider = provider.lower()
        if provider not in self.budget:
            return False
        
        data = self.budget[provider]
        limit = data.get("requests_limit", 1)
        used = data.get("requests_used", 0)
        
        # Consider near cap if >= 90%
        return used >= (limit * 0.9)

    def get_summary(self):
        summary = []
        for provider, data in self.budget.items():
            used = data.get('requests_used', 0)
            limit = data.get('requests_limit', 1)
            pct = (used / limit) * 100 if limit > 0 else 100
            summary.append(f"{provider.capitalize()}: {pct:.1f}%")
        return ", ".join(summary)
