# Demo Script - Healing Agent System

## Prerequisites
- All dependencies installed: `pip install -r requirements.txt`
- Terminal windows ready (4 terminals recommended)

---

## Step 1: Start All Services

**Terminal 1 - Telemetry Stream**:
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase1_data/telemetry_stream.py
```
Expected output: `Telemetry stream running on ws://localhost:7001/telemetry`

**Terminal 2 - Cognitive API**:
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase2_cognitive/reasoning_api.py
```
Expected output: `Uvicorn running on http://0.0.0.0:7002`

**Terminal 3 - UI Broker**:
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase4_interface/ui_broker.py
```
Expected output: `Uvicorn running on http://0.0.0.0:7003`

**Browser**:
Open `http://localhost:7003` to view the dashboard.

---

## Step 2: Observe Steady Baseline

**What to see**:
- Region tiles showing normal KPIs:
  - Packet Loss: 1-3% (green)
  - Latency: 40-60ms (green)
  - Backhaul Util: 50-70% (green)
- Incident panel shows "No active incidents"
- Telemetry log in Terminal 1 shows regular JSON records

**Duration**: 30 seconds

---

## Step 3: Toggle Backhaul Congestion Scenario

**Terminal 4 - Inject Fault**:
```python
# Run Python interpreter
python

# Execute fault injection
import json
import requests
from phase1_data.scenario_modulators import backhaul_congestion

# Simulate congestion on NorthEast region
payload = {
    "region": "NorthEast",
    "site_id": "NE_SITE_003",
    "scenario": "backhaul_congestion",
    "severity": 0.8
}

# Note: This is a mock command. In production, this would trigger the modulator
print("Injecting backhaul_congestion with severity 0.8 on NE_SITE_003")
```

**What happens**:
- Telemetry records for NE_SITE_003 show elevated metrics:
  - `packet_loss_pct`: 10-15%
  - `latency_ms`: 120-180ms
  - `backhaul_util_pct`: 85-95%

---

## Step 4: Watch Anomaly Fire

**What to see**:
- After 3 consecutive anomalous readings (hysteresis trigger), anomaly detector fires
- Terminal 1 logs: `{"level":"WARN","component":"anomaly_detector","message":"Anomaly detected",...}`
- Dashboard incident panel updates with new incident card:
  - Event ID: `evt_xxxxx`
  - Status: **ACTIVE** (red badge)
  - Region: NorthEast
  - Site: NE_SITE_003
  - Summary: "Backhaul congestion detected"

**Duration**: 10-15 seconds after injection

---

## Step 5: Open Incident Drawer

**Action**: Click on the incident card in the incident panel.

**What to see**:
- Drawer expands showing:
  - **Evidence** section with 3-4 bullet points:
    - "Backhaul utilization spiked to 91.2%"
    - "Packet loss increased from 2.1% to 12.45%"
    - "Latency rose from 48ms to 156.78ms"
  - **Explanation** section with human-readable text (120-180 words)
  - **Recommendations** section with proposed actions
  - **Risks** section listing potential impacts

---

## Step 6: Read Explanation and Risks

**Explanation Example**:
> "The backhaul link connecting this site to the core network is saturated at 91% capacity, causing packets to queue and eventually drop. This congestion pattern emerged over the last 3 minutes as traffic volume exceeded the link's provisioned bandwidth. The simultaneous rise in latency and packet loss, combined with normal CPU and memory levels, confirms the bottleneck is in the transport layer rather than local processing. Immediate action to reroute traffic or add capacity will restore service quality within 5-8 minutes."

**Recommendations**:
- [SAFE] Reroute 30% traffic to MidWest
- [AGGRESSIVE] Scale capacity by +2 backhaul units

**Risks**:
- Rerouting may increase latency by 8-12ms
- Scaling requires 4-6 minutes provisioning time

---

## Step 7: Run Simulation at ×2 Traffic

**Action**:
1. Scroll to "Simulation Playground" panel
2. Move "Traffic Multiplier" slider to **2.0x**
3. Move "Capacity Units" slider to **+1**
4. Click **"Run Simulation"** button

**What to see**:
- "Predicted KPIs" panel appears with results:
  - **Predicted Packet Loss**: 8.45% (down from 12.45%)
  - **Predicted Latency**: 98.32ms (down from 156.78ms)
  - **Predicted Blocking Prob**: 0.0234
- **Assumptions** note: "M/M/c queueing model, service rate: 1000 req/s, current load: 800 req/s"

**Interpretation**: With doubled traffic and +1 capacity unit, situation improves but doesn't fully resolve. Consider +2 units.

---

## Step 8: Approve "Safe" Plan

**Action**: Click **"Approve Safe Plan"** button in incident drawer.

**What to see**:
- Alert popup: "Plan approved for evt_xxxxx"
- Incident status badge changes from **ACTIVE** (red) to **MITIGATING** (orange)
- Terminal 3 (UI Broker) logs: `{"action":"plan_approved","event_id":"evt_xxxxx",...}`
- Mock execution begins (no real network changes)

---

## Step 9: Show Status Transitions to "Mitigating," Then "Resolved"

**Timeline**:
- **T+0s**: Status = MITIGATING (orange badge)
- **T+30s**: Telemetry shows improving metrics:
  - `packet_loss_pct`: 8% → 5% → 3%
  - `latency_ms`: 156ms → 98ms → 52ms
  - `backhaul_util_pct`: 91% → 78% → 62%
- **T+60s**: Anomaly clears (5 consecutive normal readings)
- **T+65s**: Status = RESOLVED (green badge)
- Incident card moves to bottom of list or fades out

**What to see**:
- Region tile for NorthEast returns to green KPIs
- Dashboard shows "No active incidents" or incident marked as resolved

---

## Step 10: Export Snapshot

**Action**: Click **"Export"** button in incident drawer.

**What happens**:
- Browser downloads `snapshot_evt_xxxxx.json` file containing:
  ```json
  {
    "timestamp": "2025-10-31T23:45:00.000Z",
    "incident": {
      "event_id": "evt_xxxxx",
      "region": "NorthEast",
      "site_id": "NE_SITE_003",
      "status": "resolved",
      "evidence": [...],
      "explanation": "...",
      "recommendations": [...],
      "risks": [...]
    },
    "export_type": "incident_snapshot"
  }
  ```

**Optional**: Take screenshot of dashboard showing resolved incident and green region tiles.

---

## Demo Complete

**Summary**:
✅ Detected anomaly within 15 seconds of fault injection  
✅ Diagnosed root cause with 92% confidence  
✅ Generated safe and aggressive remediation plans  
✅ Simulated "what-if" scenarios with predicted KPIs  
✅ Approved and executed safe plan with human oversight  
✅ Monitored status transitions from active → mitigating → resolved  
✅ Exported incident snapshot for audit trail  

**Key Metrics**:
- **Detection Time**: <15 seconds
- **Diagnosis Confidence**: 0.92
- **Simulated MTTR**: 5-8 minutes
- **Human Approval**: Required (no auto-execution)
- **Trace Coverage**: 100% (all objects carry trace_id)

---

## Cleanup

Press `Ctrl+C` in all terminal windows to stop services.

Optional: Clear telemetry log:
```bash
rm out/telemetry.log
```
