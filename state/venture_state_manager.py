import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .schema import VentureState, Decision

STATE_FILE = Path("state/venture_state.json")

class VentureStateManager:
    def __init__(self):
        self.state_dir = STATE_FILE.parent
        if not self.state_dir.exists():
            self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state = self._load_state()

    def _load_state(self) -> VentureState:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                return VentureState(**data)
        
        # Initialize new state
        return self._initialize_state()

    def _initialize_state(self) -> VentureState:
        new_state = VentureState(venture_id=str(uuid.uuid4()))
        self._save_state(new_state)
        return new_state

    def _save_state(self, state: Optional[VentureState] = None):
        if state is None:
            state = self.state
        with open(STATE_FILE, "w") as f:
            f.write(state.model_dump_json(indent=4))

    def update_phase(self, new_phase: str):
        self.state.phase = new_phase
        self._save_state()

    def log_decision(self, phase: str, decision: str, made_by: str):
        log_entry = Decision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            phase=phase,
            decision=decision,
            made_by=made_by
        )
        self.state.decision_log.append(log_entry)
        self._save_state()

    def add_human_checkpoint(self, checkpoint_name: str):
        if checkpoint_name not in self.state.human_checkpoints_pending:
            self.state.human_checkpoints_pending.append(checkpoint_name)
            self._save_state()

    def clear_human_checkpoint(self, checkpoint_name: str):
        if checkpoint_name in self.state.human_checkpoints_pending:
            self.state.human_checkpoints_pending.remove(checkpoint_name)
            self._save_state()

    def save(self):
        self._save_state()
