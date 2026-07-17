import agentscope
from agents.market_research import MarketResearchAgent

def test():
    print("Initializing AgentScope...")
    agentscope.init()
    
    agent = MarketResearchAgent()
    print("Running Market Research Agent...")
    msg = agent.reply({"seed_area": "Gen-Z personal finance", "target_count": 2})
    
    print("\n--- RESULTS ---")
    if "error" in msg.content:
        print("Error:", msg.content["error"])
        if "raw" in msg.content:
            print("Raw response:", msg.content["raw"])
    else:
        opportunities = msg.content["opportunities"]
        print(f"Found {len(opportunities)} opportunities.")
        for opp in opportunities:
            print(f"\nTitle: {opp['title']}")
            print(f"Problem: {opp['problem_statement']}")
            print(f"Sources: {len(opp['sources'])}")
            for src in opp['sources']:
                print(f" - {src['confidence'].upper()}: {src['url']}")

if __name__ == "__main__":
    test()
