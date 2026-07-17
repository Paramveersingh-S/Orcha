import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from orchestrator.router import ModelRouter

class CriticAgent(AgentBase):
    def __init__(self, name: str = "CriticAgent"):
        super().__init__(name=name)
        self.router = ModelRouter()
        
        # Load prompt
        prompt_path = Path("prompts/critic.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def reply(self, x: dict = None) -> dict:
        """
        Receives an agent's output and reviews it for flaws, citations, and logic.
        """
        if x is None:
            return Msg(self.name, content={"error": "No input provided"}, role="assistant")
            
        agent_output = x.get("agent_output", "")
        context = x.get("context", "")
        
        print(f"[{self.name}] Reviewing output for potential flaws...")
        
        # Build prompt for LLM
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nAgent Output to Review:\n{agent_output}\n\nProvide your JSON review."}
        ]
        
        # The critic uses a specific task type to ensure it uses a different provider
        # than the typical high_volume generation tasks.
        print(f"[{self.name}] Routing task to LLM (critic)...")
        response_text = self.router.route(task_type="critic", messages=messages)
        
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
            flags = parsed_data.get("flags", [])
            msg = Msg(self.name, content={"flags": flags}, role="assistant")
            
            blocking_count = sum(1 for f in flags if f.get("type") == "blocking")
            print(f"[{self.name}] Review complete. Found {len(flags)} flags ({blocking_count} blocking).")
            
            return msg
            
        except json.JSONDecodeError as e:
            print(f"[{self.name}] Failed to parse JSON: {e}\nRaw output: {response_text}")
            return Msg(self.name, content={"error": "JSON Decode Error", "raw": response_text}, role="assistant")
        except Exception as e:
            print(f"[{self.name}] Validation error: {e}")
            return Msg(self.name, content={"error": str(e)}, role="assistant")
