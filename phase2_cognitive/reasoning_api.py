from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import time

app = FastAPI(title="Healing Agent Cognitive API")

# Pydantic models
class AnomalyEvent(BaseModel):
    event_id: str
    started_at: str
    region: str
    site_id: str
    metrics_snapshot: Dict
    suspected_symptom: str
    confidence: float
    trace_id: str

class DiagnosisBundle(BaseModel):
    event_id: str
    region: str
    site_id: str
    likely_cause: str
    evidence: List[str]
    alternative_causes: List[str] = []
    confidence: float
    ttl: int = 300
    trace_id: str
    explanation: str

class ActionItem(BaseModel):
    action: str
    params: Dict = {}
    mode: str

class RecommendationPlan(BaseModel):
    event_id: str
    region: str
    site_id: str
    actions: List[ActionItem]
    risks: List[str] = []
    rollback: List[str]
    trace_id: str

class SimulationRequest(BaseModel):
    event_id: str
    region: str
    site_id: str
    levers: Dict
    trace_id: str

class SimulationResult(BaseModel):
    pred_packet_loss_pct: float
    pred_latency_ms: float
    pred_blocking_prob: float
    assumptions: List[str]
    trace_id: str

@app.post("/diagnose", response_model=DiagnosisBundle)
def diagnose(event: AnomalyEvent):
    """
    Accepts AnomalyEvent, returns DiagnosisBundle.
    
    Example cURL:
    curl -X POST http://localhost:7002/diagnose \
      -H "Content-Type: application/json" \
      -d @schemas/anomaly_example.json
    """
    # Mock diagnosis logic (replace with LLM call)
    return DiagnosisBundle(
        event_id=event.event_id,
        region=event.region,
        site_id=event.site_id,
        likely_cause=event.suspected_symptom,
        evidence=[
            f"Backhaul utilization at {event.metrics_snapshot['backhaul_util_pct']}%",
            f"Packet loss at {event.metrics_snapshot['packet_loss_pct']}%",
            f"Latency at {event.metrics_snapshot['latency_ms']}ms"
        ],
        alternative_causes=["fiber_cut"],
        confidence=event.confidence,
        trace_id=event.trace_id,
        explanation="Mock diagnosis explanation for testing purposes. Replace with LLM-generated content."
    )

@app.post("/recommend", response_model=RecommendationPlan)
def recommend(payload: Dict):
    """
    Accepts { event: AnomalyEvent, diagnosis: DiagnosisBundle }, returns RecommendationPlan.
    
    Example cURL:
    curl -X POST http://localhost:7002/recommend \
      -H "Content-Type: application/json" \
      -d '{"event": {...}, "diagnosis": {...}}'
    """
    event = payload["event"]
    diagnosis = payload["diagnosis"]
    
    # Mock recommendation logic
    return RecommendationPlan(
        event_id=diagnosis["event_id"],
        region=diagnosis["region"],
        site_id=diagnosis["site_id"],
        actions=[
            ActionItem(action="reroute_traffic", params={"target_region": "MidWest", "share_pct": 30}, mode="safe")
        ],
        risks=["May increase latency by 8-12ms"],
        rollback=["Revert traffic split to original distribution"],
        trace_id=diagnosis["trace_id"]
    )

@app.post("/simulate", response_model=SimulationResult)
def simulate(request: SimulationRequest):
    """
    Accepts SimulationRequest, returns SimulationResult.
    
    Example cURL:
    curl -X POST http://localhost:7002/simulate \
      -H "Content-Type: application/json" \
      -d '{"event_id":"evt_123","region":"NorthEast","site_id":"NE_SITE_003","levers":{"traffic_multiplier":2.0},"trace_id":"trace_123"}'
    """
    # Mock simulation (replace with actual M/M/c model)
    multiplier = request.levers.get("traffic_multiplier", 1.0)
    
    return SimulationResult(
        pred_packet_loss_pct=2.5 * multiplier,
        pred_latency_ms=50.0 * (1 + 0.3 * multiplier),
        pred_blocking_prob=0.01 * multiplier,
        assumptions=["M/M/c queueing model", "Service rate: 1000 req/s", "Current load: 800 req/s"],
        trace_id=request.trace_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7002)
