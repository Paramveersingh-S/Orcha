import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from orchestrator.router import ModelRouter

class OpportunityScoringAgent(AgentBase):
    def __init__(self, name: str = "OpportunityScoringAgent"):
        super().__init__(name=name)
        self.router = ModelRouter()
        
        # Load prompt
        prompt_path = Path("prompts/opportunity_scoring.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def reply(self, x: dict = None) -> dict:
        """
        Receives a list of candidate opportunities and scores them.
        """
        if x is None:
            return Msg(self.name, content={"error": "No candidates provided"}, role="assistant")
            
        candidates = x.get("candidates", [])
        if not candidates:
            return Msg(self.name, content={"error": "Empty candidates list"}, role="assistant")
        
        print(f"[{self.name}] Scoring {len(candidates)} opportunities...")
        
        # Build payload for LLM
        candidates_text = json.dumps(candidates, indent=2)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Candidates to score:\n{candidates_text}\n\nProvide your JSON scores array."}
        ]
        
        print(f"[{self.name}] Routing task to LLM (reasoning_heavy)...")
        response_text = self.router.route(task_type="reasoning_heavy", messages=messages)
        
        # Parse JSON
        try:
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            parsed_data = json.loads(clean_text)
            
            # Validation
            scores = parsed_data.get("scores", [])
            msg = Msg(self.name, content={"scores": scores}, role="assistant")
            return msg
            
        except json.JSONDecodeError as e:
            print(f"[{self.name}] Failed to parse JSON: {e}\nRaw output: {response_text}")
            return Msg(self.name, content={"error": "JSON Decode Error", "raw": response_text}, role="assistant")
        except Exception as e:
            print(f"[{self.name}] Validation error: {e}")
            return Msg(self.name, content={"error": str(e)}, role="assistant")
