import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from orchestrator.router import ModelRouter

class MVPSpecAgent(AgentBase):
    def __init__(self, name: str = "MVPSpecAgent"):
        super().__init__(name=name)
        self.router = ModelRouter()
        
        prompt_path = Path("prompts/mvp_spec.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def reply(self, x: dict = None) -> dict:
        if x is None: return Msg(self.name, content={"error": "No input"}, role="assistant")
            
        business_model = x.get("business_model", {})
        
        print(f"[{self.name}] Scoping MVP...")
            
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Business Model:\n{json.dumps(business_model, indent=2)}\n\nProvide the JSON MVP spec."}
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
