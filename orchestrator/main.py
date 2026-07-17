import agentscope
from state.venture_state_manager import VentureStateManager
from agents.market_research import MarketResearchAgent
from agents.opportunity_scoring import OpportunityScoringAgent
from agents.critic import CriticAgent
import json
import time

class Orchestrator:
    def __init__(self):
        self.state_manager = VentureStateManager()
        
    def run(self):
        state = self.state_manager.state
        
        # Check human checkpoints
        if state.human_checkpoints_pending:
            print(f"Orchestrator paused. Waiting on human checkpoints: {state.human_checkpoints_pending}")
            return
            
        print(f"--- Starting Orchestrator Loop (Current Phase: {state.phase}) ---")
        
        if state.phase == "bootstrap":
            print("Bootstrapping complete. Moving to discovery.")
            self.state_manager.update_phase("discovery")
            self.state_manager.log_decision("bootstrap", "Moved to discovery automatically", "agent")
            self.run()
            
        elif state.phase == "discovery":
            print("Running Phase 1: Discovery")
            research_agent = MarketResearchAgent()
            
            # TODO: Add seed area dynamically via CLI or input, hardcoded for now
            msg = research_agent.reply({"seed_area": "software development tools", "target_count": 3})
            
            if "error" in msg.content:
                print(f"Error in discovery: {msg.content['error']}")
                return
                
            opportunities = msg.content.get("opportunities", [])
            print(f"Found {len(opportunities)} opportunities. Updating state.")
            
            self.state_manager.state.opportunities = opportunities
            self.state_manager.update_phase("scoring")
            self.state_manager.log_decision("discovery", f"Found {len(opportunities)} candidates", "agent")
            self.state_manager.save()
            self.run()
            
        elif state.phase == "scoring":
            print("Running Phase 2: Opportunity Scoring & Shortlisting")
            scoring_agent = OpportunityScoringAgent()
            critic_agent = CriticAgent()
            
            candidates = self.state_manager.state.opportunities
            
            if not candidates:
                print("No candidates to score. Reverting to discovery.")
                self.state_manager.update_phase("discovery")
                return
                
            msg = scoring_agent.reply({"candidates": candidates})
            if "error" in msg.content:
                print(f"Error in scoring: {msg.content['error']}")
                return
                
            scores = msg.content.get("scores", [])
            
            print("Running Critic on scored output...")
            critic_msg = critic_agent.reply({
                "context": "Reviewing candidate opportunity scores for validity.",
                "agent_output": json.dumps(scores, indent=2)
            })
            
            # Simplified check: if blocking flags exist, halt.
            flags = critic_msg.content.get("flags", [])
            blocking_flags = [f for f in flags if f.get("type") == "blocking"]
            
            if blocking_flags:
                print(f"Critic blocked scoring output! {len(blocking_flags)} blocking flags found.")
                for flag in blocking_flags:
                    print(f"- {flag.get('issue')}: {flag.get('reason')}")
                # Log and pause
                self.state_manager.log_decision("scoring", "Critic blocked output", "agent")
                return
                
            print("Critic approved scoring. Saving scores and requesting human checkpoint.")
            
            # Apply scores to state
            for score_entry in scores:
                for opp in self.state_manager.state.opportunities:
                    if opp['id'] == score_entry.get('id'):
                        opp['score'] = score_entry.get('scores', {})
                        break
                        
            # Enforce checkpoint
            self.state_manager.add_human_checkpoint("shortlist_approval")
            self.state_manager.log_decision("scoring", "Scoring complete, waiting on human approval for deep validation", "agent")
            self.state_manager.save()
            
        elif state.phase == "validation":
            print("Running Phase 3: Deep Validation (Competitor Intel)")
            from agents.competitor_intel import CompetitorIntelAgent
            
            # Assume human picked the top scoring opportunity (we just pick the first for now)
            # In a real scenario, the human checkpoint handler would set this.
            if not state.opportunities:
                print("No opportunities to validate.")
                return
                
            active_opp = state.opportunities[0]
            
            intel_agent = CompetitorIntelAgent()
            msg = intel_agent.reply({"opportunity": active_opp})
            
            if "error" in msg.content:
                print(f"Error in validation: {msg.content['error']}")
                return
                
            competitor_data = msg.content
            print(f"Found {len(competitor_data.get('competitors', []))} competitors.")
            
            # Save to active venture state
            state.active_venture.business_model["competitor_intel"] = competitor_data
            
            self.state_manager.update_phase("business_model")
            self.state_manager.log_decision("validation", "Competitor intel gathered.", "agent")
            self.state_manager.save()
            self.run()
            
        elif state.phase == "business_model":
            print("Running Phase 4: Business Model & Unit Economics")
            from agents.business_model import BusinessModelAgent
            from agents.financial_modeling import FinancialModelingAgent
            
            active_opp = state.opportunities[0]
            intel = state.active_venture.business_model.get("competitor_intel", {})
            
            # 1. Business Model
            bm_agent = BusinessModelAgent()
            bm_msg = bm_agent.reply({
                "opportunity": active_opp,
                "competitor_intel": intel
            })
            
            if "error" in bm_msg.content:
                print(f"Error in business model: {bm_msg.content['error']}")
                return
                
            state.active_venture.business_model["canvas"] = bm_msg.content
            print("Business model generated.")
            
            # 2. Financial Modeling
            fm_agent = FinancialModelingAgent()
            fm_msg = fm_agent.reply({"business_model": bm_msg.content})
            
            if "error" in fm_msg.content:
                print(f"Error in financial modeling: {fm_msg.content['error']}")
                return
                
            state.active_venture.unit_economics = fm_msg.content
            print("Unit economics calculated.")
            
            self.state_manager.update_phase("mvp_spec")
            self.state_manager.log_decision("business_model", "Business and financial models created.", "agent")
            self.state_manager.save()
            self.run()
            
        elif state.phase == "mvp_spec":
            print("Running Phase 5: MVP / Product Spec")
            from agents.mvp_spec import MVPSpecAgent
            
            bm_agent_output = state.active_venture.business_model.get("canvas", {})
            spec_agent = MVPSpecAgent()
            msg = spec_agent.reply({"business_model": bm_agent_output})
            
            if "error" in msg.content:
                print(f"Error in MVP spec: {msg.content['error']}")
                return
                
            state.active_venture.mvp_spec = msg.content
            print("MVP spec generated.")
            
            self.state_manager.add_human_checkpoint("mvp_scope_approval")
            self.state_manager.update_phase("build")
            self.state_manager.log_decision("mvp_spec", "MVP scoped, waiting for human approval.", "agent")
            self.state_manager.save()
            
        elif state.phase == "build":
            print("Running Phase 6: Build Handoff")
            from agents.builder import BuilderAgent
            from agents.legal_compliance import LegalComplianceAgent
            
            # Legal Check before build
            legal_agent = LegalComplianceAgent()
            legal_msg = legal_agent.reply({"business_model": state.active_venture.business_model.get("canvas", {})})
            
            if "error" not in legal_msg.content:
                flags = legal_msg.content.get("risk_flags", [])
                if flags:
                    print("Legal risks flagged. Please review manually.")
                    for f in flags:
                        print(f"- [{f.get('severity')}] {f.get('risk')}")
            
            builder_agent = BuilderAgent()
            msg = builder_agent.reply({
                "venture_id": state.venture_id,
                "mvp_spec": state.active_venture.mvp_spec
            })
            
            if "error" in msg.content:
                print(f"Error in Builder: {msg.content['error']}")
                return
                
            state.active_venture.build_status = msg.content
            
            self.state_manager.add_human_checkpoint("public_deployment_approval")
            self.state_manager.update_phase("gtm")
            self.state_manager.log_decision("build", "Handoff prompt created, ready for deployment.", "agent")
            self.state_manager.save()
            
        elif state.phase == "gtm":
            print("Running Phase 7: Go-To-Market")
            from agents.growth_gtm import GrowthGTMAgent
            
            gtm_agent = GrowthGTMAgent()
            msg = gtm_agent.reply({"mvp_spec": state.active_venture.mvp_spec})
            
            if "error" in msg.content:
                print(f"Error in GTM: {msg.content['error']}")
                return
                
            state.active_venture.gtm_plan = msg.content
            print("Launch plan created.")
            
            self.state_manager.add_human_checkpoint("public_post_approval")
            self.state_manager.update_phase("metrics")
            self.state_manager.log_decision("gtm", "Launch plan created.", "agent")
            self.state_manager.save()
            
        elif state.phase == "metrics":
            print("Phase 8: Metrics loop is ongoing. Factory pipeline complete.")
            
        else:
            print(f"Phase {state.phase} is not yet implemented in orchestrator.")

if __name__ == "__main__":
    agentscope.init()
    orch = Orchestrator()
    orch.run()
