from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime

class Source(BaseModel):
    url: str
    claim: str
    confidence: Literal["high", "medium", "low", "unverified"]

class Score(BaseModel):
    demand_evidence: int = 0
    market_size_estimate: int = 0
    competition_density: int = 0
    buildability_on_free_tier: int = 0
    founder_fit: int = 0
    total: int = 0

class Opportunity(BaseModel):
    id: str
    title: str
    problem_statement: str
    sources: List[Source] = Field(default_factory=list)
    score: Score = Field(default_factory=Score)
    status: Literal["candidate", "shortlisted", "validating", "rejected", "active"] = "candidate"
    critic_flags: List[str] = Field(default_factory=list)

class ActiveVenture(BaseModel):
    business_model: dict = Field(default_factory=dict)
    unit_economics: dict = Field(default_factory=lambda: {"assumptions": [], "citations": []})
    mvp_spec: dict = Field(default_factory=dict)
    build_status: dict = Field(default_factory=dict)
    gtm_plan: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=lambda: {"signups": 0, "revenue": 0, "last_updated": None})

class Decision(BaseModel):
    timestamp: str
    phase: str
    decision: str
    made_by: Literal["agent", "human"]

class VentureState(BaseModel):
    venture_id: str
    phase: Literal["bootstrap", "discovery", "scoring", "validation", "business_model", "mvp_spec", "build", "gtm", "metrics"] = "bootstrap"
    opportunities: List[Opportunity] = Field(default_factory=list)
    active_venture: ActiveVenture = Field(default_factory=ActiveVenture)
    decision_log: List[Decision] = Field(default_factory=list)
    human_checkpoints_pending: List[str] = Field(default_factory=list)
