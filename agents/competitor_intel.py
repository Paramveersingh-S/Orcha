import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from orchestrator.router import ModelRouter
from tools.search import SearchTool

class CompetitorIntelAgent(AgentBase):
    def __init__(self, name: str = "CompetitorIntelAgent"):
        super().__init__(name=name)
        self.router = ModelRouter()
        self.search_tool = SearchTool()
        
        prompt_path = Path("prompts/competitor_intel.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def reply(self, x: dict = None) -> dict:
        if x is None:
            return Msg(self.name, content={"error": "No input provided"}, role="assistant")
            
        opportunity = x.get("opportunity", {})
        if not opportunity:
            return Msg(self.name, content={"error": "No opportunity provided"}, role="assistant")
            
        print(f"[{self.name}] Analyzing competitors for: {opportunity.get('title')}")
        
        # Search for competitors
        query = f"{opportunity.get('title')} {opportunity.get('problem_statement')} alternatives competitors"
        search_results = self.search_tool.search(query, max_results=5)
        
        context_str = "Search Results:\n"
        for res in search_results:
            context_str += f"URL: {res['url']}\nTitle: {res['title']}\nSnippet: {res['content']}\n\n"
            
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Opportunity:\n{json.dumps(opportunity, indent=2)}\n\n{context_str}\n\nProvide the JSON analysis."}
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
            print(f"[{self.name}] Error: {e}")
            return Msg(self.name, content={"error": str(e)}, role="assistant")
