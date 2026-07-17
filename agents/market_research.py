import json
from pathlib import Path
import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from orchestrator.router import ModelRouter
from tools.search import SearchTool
from state.schema import Opportunity

class MarketResearchAgent(AgentBase):
    def __init__(self, name: str = "MarketResearchAgent"):
        super().__init__(name=name)
        self.router = ModelRouter()
        self.search_tool = SearchTool()
        
        # Load prompt
        prompt_path = Path("prompts/market_research.md")
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()

    def reply(self, x: dict = None) -> dict:
        """
        Receives an instruction (seed area and target count) and returns a list of opportunities.
        """
        if x is None:
            x = {}
            
        seed_area = x.get("seed_area", "")
        target_count = x.get("target_count", 5)
        
        print(f"[{self.name}] Searching web for pain points related to: {seed_area if seed_area else 'general startup ideas'}")
        
        # Perform some automated search queries to gather context
        search_queries = [
            f"{seed_area} biggest complaints forums" if seed_area else "biggest startup pain points forums",
            f"{seed_area} 'I wish there was a tool that' reddit" if seed_area else "'I wish there was an app that' reddit",
            f"{seed_area} unmet needs B2B SaaS" if seed_area else "unmet needs software 2026",
        ]
        
        context_data = []
        for q in search_queries:
            results = self.search_tool.search(q, max_results=3)
            for res in results:
                context_data.append(f"URL: {res['url']}\nTitle: {res['title']}\nSnippet: {res['content']}\n")
                
        context_str = "\n".join(context_data)
        
        # Build prompt for LLM
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Seed Area: {seed_area}\nTarget Count: {target_count}\n\nSearch Context:\n{context_str}\n\nGenerate the output JSON array based on this context and your internal knowledge. ONLY OUTPUT JSON."}
        ]
        
        print(f"[{self.name}] Routing task to LLM (high_volume/reasoning)...")
        # Market research involves processing context and classification
        response_text = self.router.route(task_type="high_volume", messages=messages)
        
        # Parse JSON
        try:
            # Clean possible markdown formatting
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            parsed_data = json.loads(clean_text)
            
            # Basic validation
            valid_opportunities = []
            import uuid
            for item in parsed_data:
                # Map to schema roughly
                opp = Opportunity(
                    id=str(uuid.uuid4()),
                    title=item.get("title", "Unknown"),
                    problem_statement=item.get("problem_statement", ""),
                    sources=item.get("sources", []),
                    status="candidate"
                )
                valid_opportunities.append(opp)
                
            msg = Msg(self.name, content={"opportunities": [o.model_dump() for o in valid_opportunities]}, role="assistant")
            return msg
            
        except json.JSONDecodeError as e:
            print(f"[{self.name}] Failed to parse JSON: {e}\nRaw output: {response_text}")
            return Msg(self.name, content={"error": "JSON Decode Error", "raw": response_text}, role="assistant")
        except Exception as e:
            print(f"[{self.name}] Validation error: {e}")
            return Msg(self.name, content={"error": str(e)}, role="assistant")
