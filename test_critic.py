import agentscope
from agents.critic import CriticAgent

def test():
    print("Initializing AgentScope...")
    agentscope.init()
    
    agent = CriticAgent()
    print("Running Critic Agent...")
    
    dummy_context = "Context: The market for AI agents is growing rapidly."
    dummy_output = '''
    The TAM for this idea is $100 Billion (no source). 
    This is the best startup idea ever because AI is cool! 
    There are absolutely zero competitors in this space.
    '''
    
    msg = agent.reply({"context": dummy_context, "agent_output": dummy_output})
    
    print("\n--- CRITIC RESULTS ---")
    if "error" in msg.content:
        print("Error:", msg.content["error"])
        if "raw" in msg.content:
            print("Raw response:", msg.content["raw"])
    else:
        flags = msg.content.get("flags", [])
        for f in flags:
            print(f"[{f.get('type', 'UNKNOWN').upper()}] {f.get('issue', '')}")
            print(f"Reason: {f.get('reason', '')}\n")

if __name__ == "__main__":
    test()
