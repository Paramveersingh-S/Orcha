import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from orchestrator.router import ModelRouter

class BusinessModelAgent(AgentBase):
    def __init__(self, name: str = "BusinessModelAgent"):
        super().__init__(name=name)
        self.router = ModelRouter()
        
        prompt_path = Path("prompts/business_model.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def reply(self, x: dict = None) -> dict:
        if x is None: return Msg(self.name, content={"error": "No input"}, role="assistant")
            
        opportunity = x.get("opportunity", {})
        competitor_intel = x.get("competitor_intel", {})
        
        print(f"[{self.name}] Designing business model for: {opportunity.get('title')}")
            
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Opportunity:\n{json.dumps(opportunity, indent=2)}\n\nCompetitor Intel:\n{json.dumps(competitor_intel, indent=2)}\n\nProvide the JSON business model."}
        ]
        
        response_text = self.router.route(task_type="reasoning_heavy", messages=messages)
        
        try:
            clean_text = response_text.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.startswith("```"): clean_text = clean_text[3:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
                
            parsed_data = json.loads(clean_text)
            return Msg(self.name, content=parsed_data, role="assistant")
            
        except Exception as e:
            return Msg(self.name, content={"error": str(e)}, role="assistant")
