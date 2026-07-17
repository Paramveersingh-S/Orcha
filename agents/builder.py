import os
import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg

class BuilderAgent(AgentBase):
    def __init__(self, name: str = "BuilderAgent"):
        super().__init__(name=name)

    def reply(self, x: dict = None) -> dict:
        if x is None: return Msg(self.name, content={"error": "No input"}, role="assistant")
            
        venture_id = x.get("venture_id", "default_venture")
        mvp_spec = x.get("mvp_spec", {})
        
        print(f"[{self.name}] Generating Builder prompt for venture {venture_id}...")
        
        build_prompt_md = mvp_spec.get("build_prompt_md", "")
        if not build_prompt_md:
            return Msg(self.name, content={"error": "No build_prompt_md found in mvp_spec"}, role="assistant")
            
        # Create folder
        venture_dir = Path(f"ventures/{venture_id}")
        venture_dir.mkdir(parents=True, exist_ok=True)
        
        # Write prompt.md
        prompt_file = venture_dir / "prompt.md"
        with open(prompt_file, "w") as f:
            f.write(build_prompt_md)
            
        print(f"[{self.name}] Wrote build spec to {prompt_file}")
        
        return Msg(self.name, content={
            "build_status": "ready_for_handoff",
            "prompt_path": str(prompt_file)
        }, role="assistant")
