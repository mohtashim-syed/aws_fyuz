# main.py
#
# AINOA Core Service (Hackathon Version)
#
# WHAT'S REAL (hackathon / works today):
# - FastAPI app with in-memory telemetry store
# - /telemetry/push ingests telemetry
# - Simple anomaly detection (packet_loss_pct >5 OR latency_ms >150)
# - Cognitive Layer: analyze_incident() builds LLM prompt and returns structured JSON
# - Decision Layer: converts AI suggestion into machine-actionable policy JSON
# - Planning Agent: simulates before/after QoS impact
# - /status returns everything for the dashboard
#
# WHAT'S ROADMAP (what we tell judges is next):
# - Replace manual POST ingestion with AWS Kinesis / OpenTelemetry
# - Swap mock LLM for Bedrock/SageMaker-tuned telco model
# - Replace rule-based policy with RLlib-trained policy agent
# - Replace math hack forecast with ns-3 / RAN simulator
#
# Local dev:
#   1. Activate venv
#   2. python -m uvicorn main:app --reload --port 8000
#   3. In a second terminal: python feed_demo.py
#
# Demo story:
#   - feed_demo sends mostly healthy telemetry, plus spikes in northwest/cell_12
#   - spike triggers anomaly -> AI diagnosis -> policy action -> forecast
#   - /status exposes that whole brain to the frontend dashboard

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import random
import json

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------

app = FastAPI(
    title="AINOA Core Service",
    description="AI-Agentic Network Operations Assistant (Hackathon Version)",
    version="0.1-hackathon"
)

# CORS so dashboard.html (running in browser) can hit http://localhost:8000/status
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Hackathon mode: allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# In-memory runtime state (hackathon-real, not production)
# -----------------------------------------------------------------------------

# raw rolling telemetry samples (we keep last ~200)
TELEMETRY_HISTORY: List[Dict[str, Any]] = []

# snapshot of most recent reading per cell
# key: "region:cell_id" -> value: latest TelemetryEvent as dict
LATEST_BY_CELL: Dict[str, Dict[str, Any]] = {}

# active incident (only most recent, 1 at a time for demo simplicity)
ACTIVE_INCIDENT: Optional[Dict[str, Any]] = None

# cached cognitive layer output for ACTIVE_INCIDENT
AI_DIAGNOSIS: Optional[Dict[str, Any]] = None

# cached decision layer output
POLICY_ACTION: Optional[Dict[str, Any]] = None

# cached planning agent output
PLANNING_PROJECTION: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Pydantic models
# -----------------------------------------------------------------------------

class TelemetryEvent(BaseModel):
    region: str = Field(..., example="northwest")
    cell_id: str = Field(..., example="cell_12")
    packet_loss_pct: float = Field(..., example=6.3)
    latency_ms: float = Field(..., example=182.0)
    throughput_mbps: float = Field(..., example=125.4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IncidentSummary(BaseModel):
    incident_id: str
    region: str
    cell_id: str
    timestamp: datetime
    packet_loss_pct: float
    latency_ms: float
    throughput_mbps: float
    rule_triggered: str
    severity: str  # "warning" | "critical"


class AIDiagnosis(BaseModel):
    issue_summary: str
    probable_cause: str
    suggested_action: str
    risk_level: str  # "low" | "medium" | "high" | "critical"


class PolicyAction(BaseModel):
    action_type: str               # e.g. "TRAFFIC_OFFLOAD"
    source_cell: str
    target_cell: str
    offload_percent: float
    rationale: str
    can_execute_automatically: bool
    confidence: float              # pretend RLlib policy confidence


class PlanningProjection(BaseModel):
    before: Dict[str, float]
    after: Dict[str, float]
    explanation: str


class RegionHealth(BaseModel):
    region: str
    avg_latency_ms: float
    avg_packet_loss_pct: float
    avg_throughput_mbps: float
    cells: List[Dict[str, Any]]


class StatusResponse(BaseModel):
    regions: List[RegionHealth]
    active_incident: Optional[IncidentSummary]
    ai_diagnosis: Optional[AIDiagnosis]
    proposed_action: Optional[PolicyAction]
    predicted_outcome: Optional[PlanningProjection]


# -----------------------------------------------------------------------------
# Observability Layer: anomaly detection
#
# Rule: anomaly if packet_loss_pct > 5 OR latency_ms > 150.
# Severity: "critical" if both rules fired, else "warning".
# -----------------------------------------------------------------------------

def detect_anomaly(event: TelemetryEvent) -> Optional[IncidentSummary]:
    triggered_rules = []
    if event.packet_loss_pct > 5.0:
        triggered_rules.append("high_packet_loss_pct")
    if event.latency_ms > 150.0:
        triggered_rules.append("high_latency_ms")

    if not triggered_rules:
        return None

    severity = "critical" if len(triggered_rules) > 1 else "warning"

    return IncidentSummary(
        incident_id=str(uuid.uuid4()),
        region=event.region,
        cell_id=event.cell_id,
        timestamp=event.timestamp,
        packet_loss_pct=event.packet_loss_pct,
        latency_ms=event.latency_ms,
        throughput_mbps=event.throughput_mbps,
        rule_triggered=",".join(triggered_rules),
        severity=severity
    )


# -----------------------------------------------------------------------------
# Cognitive Layer: analyze_incident()
#
# For hackathon:
# - We build a prompt with telemetry context.
# - We call call_llm(), which is mocked here to return deterministic JSON.
#
# For roadmap:
# - call_llm() would call Bedrock/SageMaker with a telco-tuned model.
# -----------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    """
    MOCK LLM CALL for hackathon.
    Returns a JSON string. In prod: replace with Bedrock/Anthropic/OpenAI call.
    """
    fake = {
        "issue_summary": "Severe congestion detected in northwest / cell_12 causing high latency (~180ms) and elevated packet loss (~6%).",
        "probable_cause": "Backhaul saturation due to heavy user load and limited available capacity.",
        "suggested_action": "Offload ~20% traffic from cell_12 to neighboring cell_15 to relieve congestion.",
        "risk_level": "critical"
    }
    return json.dumps(fake)


def analyze_incident(incident: IncidentSummary) -> AIDiagnosis:
    # Grab recent telemetry for that cell/region to give LLM context
    recent_context = [
        t for t in TELEMETRY_HISTORY
        if t["region"] == incident.region and t["cell_id"] == incident.cell_id
    ][-5:]

    prompt = f"""
You are AINOA, an AI network operations assistant for a telecom.
Return a JSON with keys: issue_summary, probable_cause, suggested_action, risk_level.

Telemetry (recent samples):
{recent_context}

Incident:
region={incident.region}
cell_id={incident.cell_id}
packet_loss_pct={incident.packet_loss_pct}
latency_ms={incident.latency_ms}
throughput_mbps={incident.throughput_mbps}
severity={incident.severity}

Explain likely root cause and recommend an action like traffic offload, capacity add,
or backhaul relief.
""".strip()

    raw_llm = call_llm(prompt)

    try:
        parsed = json.loads(raw_llm)
    except json.JSONDecodeError:
        parsed = {
            "issue_summary": "Network degradation detected.",
            "probable_cause": "Unknown cause.",
            "suggested_action": "Escalate to NOC engineer.",
            "risk_level": "high"
        }

    return AIDiagnosis(
        issue_summary=parsed.get("issue_summary", "Network degradation detected."),
        probable_cause=parsed.get("probable_cause", "Unknown cause."),
        suggested_action=parsed.get("suggested_action", "Escalate to NOC engineer."),
        risk_level=parsed.get("risk_level", "high")
    )


# -----------------------------------------------------------------------------
# Decision Layer / Policy Agent
#
# Hackathon reality:
# - We parse the AI suggestion. If it says "offload", we emit TRAFFIC_OFFLOAD.
#
# Roadmap story:
# - This becomes an RLlib-trained policy agent that autonomously chooses
#   offload vs. capacity add vs. spectrum shift, etc.
# -----------------------------------------------------------------------------

def decision_layer_policy(diagnosis: AIDiagnosis, incident: IncidentSummary) -> PolicyAction:
    action_type = "NO_ACTION"
    source_cell = incident.cell_id
    target_cell = "cell_15"  # pretend known neighbor
    offload_percent = 0.0
    rationale = "No automated mitigation required."
    can_execute_automatically = False
    confidence = 0.5

    if "offload" in diagnosis.suggested_action.lower():
        action_type = "TRAFFIC_OFFLOAD"
        offload_percent = 20.0
        rationale = diagnosis.suggested_action
        can_execute_automatically = True
        confidence = 0.82  # pretend RL policy Q-value

    return PolicyAction(
        action_type=action_type,
        source_cell=source_cell,
        target_cell=target_cell,
        offload_percent=offload_percent,
        rationale=rationale,
        can_execute_automatically=can_execute_automatically,
        confidence=confidence
    )


# -----------------------------------------------------------------------------
# Planning Agent / Capacity Forecaster
#
# Hackathon:
# - We simulate improved KPIs after offload.
#
# Roadmap:
# - We'd drive ns-3 / TIP OpenRAN to predict KPI after reroute/scale.
# -----------------------------------------------------------------------------

def planning_agent_forecast(incident: IncidentSummary, action: PolicyAction) -> PlanningProjection:
    before_loss = incident.packet_loss_pct
    before_latency = incident.latency_ms

    # default (no improvement)
    after_loss = before_loss
    after_latency = before_latency

    if action.action_type == "TRAFFIC_OFFLOAD" and action.offload_percent >= 10.0:
        # pretend offload drops congestion dramatically
        after_loss = max(0.5, before_loss * 0.2)       # e.g. 6.3 -> ~1.26
        after_latency = max(60.0, before_latency - 60) # e.g. 180 -> ~120, floor 60ms

    explanation = (
        f"By offloading {action.offload_percent}% of traffic from {action.source_cell} "
        f"to {action.target_cell}, we reduce congestion and predict improved QoS "
        f"(loss {before_loss:.1f}%→{after_loss:.1f}%, "
        f"latency {before_latency:.0f}ms→{after_latency:.0f}ms)."
    )

    return PlanningProjection(
        before={
            "packet_loss_pct": before_loss,
            "latency_ms": before_latency,
            "throughput_mbps": incident.throughput_mbps
        },
        after={
            "packet_loss_pct": after_loss,
            "latency_ms": after_latency,
            "throughput_mbps": incident.throughput_mbps
        },
        explanation=explanation
    )


# -----------------------------------------------------------------------------
# Region health snapshot for /status
# -----------------------------------------------------------------------------

def compute_region_health() -> List[RegionHealth]:
    regions: Dict[str, Dict[str, Any]] = {}

    # Group latest cells by region
    for _, cell_data in LATEST_BY_CELL.items():
        rname = cell_data["region"]
        if rname not in regions:
            regions[rname] = {"cells": []}
        regions[rname]["cells"].append(cell_data)

    result: List[RegionHealth] = []
    for region_name, data in regions.items():
        cells = data["cells"]
        if not cells:
            continue

        avg_latency = sum(c["latency_ms"] for c in cells) / len(cells)
        avg_loss = sum(c["packet_loss_pct"] for c in cells) / len(cells)
        avg_tp = sum(c["throughput_mbps"] for c in cells) / len(cells)

        region_health = RegionHealth(
            region=region_name,
            avg_latency_ms=round(avg_latency, 2),
            avg_packet_loss_pct=round(avg_loss, 2),
            avg_throughput_mbps=round(avg_tp, 2),
            cells=[
                {
                    "cell_id": c["cell_id"],
                    "latency_ms": c["latency_ms"],
                    "packet_loss_pct": c["packet_loss_pct"],
                    "throughput_mbps": c["throughput_mbps"],
                    "timestamp": c["timestamp"].isoformat()
                }
                for c in cells
            ]
        )
        result.append(region_health)

    return result


# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    """
    Quick heartbeat. Use this in browser to verify server is up.
    """
    return {
        "status": "AINOA online",
        "telemetry_samples": len(TELEMETRY_HISTORY),
        "active_incident": ACTIVE_INCIDENT["incident_id"] if ACTIVE_INCIDENT else None
    }


@app.post("/telemetry/push")
def push_telemetry(event: TelemetryEvent = Body(...)):
    """
    Observability Layer ingress.
    (Prod version could be Kinesis consumer / OpenTelemetry receiver.)

    Steps:
    1. Store telemetry
    2. Update per-cell snapshot
    3. Run anomaly detection
    4. If anomaly: run Cognitive, Decision, Planning → cache results
    """
    global TELEMETRY_HISTORY, LATEST_BY_CELL
    global ACTIVE_INCIDENT, AI_DIAGNOSIS, POLICY_ACTION, PLANNING_PROJECTION

    # 1. append to rolling history
    event_dict = event.dict()
    TELEMETRY_HISTORY.append(event_dict)

    # keep history bounded
    if len(TELEMETRY_HISTORY) > 200:
        TELEMETRY_HISTORY = TELEMETRY_HISTORY[-200:]

    # 2. update snapshot for this cell
    cell_key = f"{event.region}:{event.cell_id}"
    LATEST_BY_CELL[cell_key] = event_dict

    # 3. anomaly detection
    incident_obj = detect_anomaly(event)

    if incident_obj:
        # set ACTIVE_INCIDENT
        ACTIVE_INCIDENT = incident_obj.dict()

        # console log for live demo narration
        print("[AINOA] Incident detected:",
              ACTIVE_INCIDENT["region"],
              ACTIVE_INCIDENT["cell_id"],
              "loss=", ACTIVE_INCIDENT["packet_loss_pct"],
              "latency=", ACTIVE_INCIDENT["latency_ms"],
              "severity=", ACTIVE_INCIDENT["severity"])

        # 4a. Cognitive Layer
        diagnosis = analyze_incident(incident_obj)
        AI_DIAGNOSIS = diagnosis.dict()

        # 4b. Decision Layer / Policy Agent
        policy = decision_layer_policy(diagnosis, incident_obj)
        POLICY_ACTION = policy.dict()

        # 4c. Planning Agent / Capacity Forecaster
        forecast = planning_agent_forecast(incident_obj, policy)
        PLANNING_PROJECTION = forecast.dict()

    return {
        "status": "ok",
        "stored": event_dict,
        "anomaly_detected": bool(incident_obj),
        "active_incident_id": ACTIVE_INCIDENT.get("incident_id") if ACTIVE_INCIDENT else None
    }


@app.get("/status", response_model=StatusResponse)
def get_status():
    """
    Powers the AINOA Console dashboard.
    Frontend polls this every ~2s.

    Returns:
    - regions: snapshot health per region
    - active_incident: most recent triggered incident
    - ai_diagnosis: Cognitive Layer human-readable reasoning
    - proposed_action: Decision Layer machine-actionable intent
    - predicted_outcome: Planning Agent forecast
    """
    regions_health = compute_region_health()

    active_incident_model: Optional[IncidentSummary] = None
    if ACTIVE_INCIDENT:
        active_incident_model = IncidentSummary(**ACTIVE_INCIDENT)

    ai_diag_model: Optional[AIDiagnosis] = None
    if AI_DIAGNOSIS:
        ai_diag_model = AIDiagnosis(**AI_DIAGNOSIS)

    policy_model: Optional[PolicyAction] = None
    if POLICY_ACTION:
        policy_model = PolicyAction(**POLICY_ACTION)

    planning_model: Optional[PlanningProjection] = None
    if PLANNING_PROJECTION:
        planning_model = PlanningProjection(**PLANNING_PROJECTION)

    return StatusResponse(
        regions=regions_health,
        active_incident=active_incident_model,
        ai_diagnosis=ai_diag_model,
        proposed_action=policy_model,
        predicted_outcome=planning_model
    )


@app.post("/demo/spike")
def demo_spike():
    """
    Force a high-latency / high-loss reading for northwest/cell_12.
    Useful on stage if you need to trigger an incident NOW.
    """
    spike_event = TelemetryEvent(
        region="northwest",
        cell_id="cell_12",
        packet_loss_pct=6.3,       # >5% = bad
        latency_ms=180.0,          # >150ms = bad
        throughput_mbps=120.0,
    )
    return push_telemetry(spike_event)


@app.post("/demo/normal")
def demo_normal():
    """
    Push a normal healthy reading.
    This keeps /status populated for regions with no issues.
    """
    normal_event = TelemetryEvent(
        region=random.choice(["northwest", "central", "south"]),
        cell_id=random.choice(["cell_12", "cell_15", "cell_21", "cell_22", "cell_30"]),
        packet_loss_pct=0.7,
        latency_ms=55.0,
        throughput_mbps=150.0,
    )
    return push_telemetry(normal_event)
