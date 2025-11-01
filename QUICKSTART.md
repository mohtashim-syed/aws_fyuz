# Quick Start Guide - Healing Agent

## Prerequisites

- Python 3.8 or higher
- pip package manager
- 4 terminal windows (or use tmux/screen)

## Installation

### 1. Install Dependencies

Open a terminal in the project directory:

```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
pip install -r requirements.txt
```

This will install:
- fastapi
- uvicorn
- websockets
- pydantic
- pyyaml
- numpy
- prometheus-client
- aiofiles

### 2. Verify Installation

```bash
python -c "import fastapi, websockets, pydantic; print('All dependencies installed!')"
```

---

## Running the System

### Option A: Manual Start (Recommended for Demo)

Open **4 separate terminal windows** and run each command:

#### Terminal 1 - Telemetry Stream
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase1_data/telemetry_stream.py
```
✅ You should see: `Telemetry stream running on ws://localhost:7001/telemetry`

#### Terminal 2 - Cognitive API
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase2_cognitive/reasoning_api.py
```
✅ You should see: `Uvicorn running on http://0.0.0.0:7002`

#### Terminal 3 - UI Broker & Dashboard
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase4_interface/ui_broker.py
```
✅ You should see: `Uvicorn running on http://0.0.0.0:7003`

#### Terminal 4 - Telemetry Forwarder (REQUIRED for live metrics)
```bash
cd "c:\Users\hamma\Desktop\Github Projects\aws_fyuz"
python phase1_data/forwarder.py
```
✅ You should see: `✓ Connected to telemetry stream`

**Note:** The forwarder is essential for live metric updates. Without it, dashboard tiles will remain static.

---

### Option B: Quick Start Script (Windows)

**With Live Metrics (Recommended):**
```bash
start_all_with_forwarder.bat
```

**Basic (without live metrics):**
```bash
start_all.bat
```

The forwarder version starts all 4 services and enables real-time metric updates.

---

## Access the Dashboard

Once all services are running, open your browser:

```
http://localhost:7003
```

You should see:
- 🏥 **Healing Agent Dashboard** header
- **4 Region Tiles** (NorthEast, SouthEast, MidWest, West) with green KPIs
- **Active Incidents** panel (empty initially)
- **Simulation Playground** with sliders
- **Chat Assistant** panel

---

## Testing the System

### Test 1: Check Telemetry Stream

Open a new terminal and test the WebSocket:

```bash
python -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:7001/telemetry') as ws:
        for i in range(5):
            msg = await ws.recv()
            data = json.loads(msg)
            print(f'Received: {data[\"site_id\"]} - Loss: {data[\"packet_loss_pct\"]}%')

asyncio.run(test())
"
```

✅ You should see 5 telemetry records printed.

### Test 2: Check Cognitive API

```bash
curl http://localhost:7002/docs
```

✅ Opens FastAPI Swagger UI in browser showing `/diagnose`, `/recommend`, `/simulate` endpoints.

### Test 3: Simulate an Anomaly

In Terminal 4, create a test anomaly:

```bash
python
```

Then in Python:

```python
import requests
import json

# Create a mock anomaly event
anomaly = {
    "event_id": "evt_test_001",
    "started_at": "2025-10-31T23:50:00.000Z",
    "region": "NorthEast",
    "site_id": "NE_SITE_003",
    "metrics_snapshot": {
        "packet_loss_pct": 12.45,
        "latency_ms": 156.78,
        "backhaul_util_pct": 91.2,
        "cpu_load_pct": 68.5,
        "calls_dropped": 3
    },
    "suspected_symptom": "backhaul_congestion",
    "confidence": 0.85,
    "trace_id": "trace_test_001"
}

# Send to UI broker
response = requests.post(
    "http://localhost:7003/api/incident",
    json=anomaly
)

print(response.json())
```

✅ Check the dashboard - you should see a new incident appear in the "Active Incidents" panel!

### Test 4: Run a Simulation

In the dashboard:
1. Move **Traffic Multiplier** slider to **2.0x**
2. Move **Capacity Units** slider to **+1**
3. Click **"Run Simulation"**

✅ You should see predicted KPIs appear below the button.

---

## Stopping the System

Press `Ctrl+C` in each terminal window to stop the services.

Or if using the batch file, close all command windows.

---

## Troubleshooting

### Port Already in Use

If you see `Address already in use` errors:

**Windows:**
```bash
netstat -ano | findstr :7001
netstat -ano | findstr :7002
netstat -ano | findstr :7003
```

Kill the process using the PID shown:
```bash
taskkill /PID <PID> /F
```

### Module Not Found

If you see `ModuleNotFoundError`:
```bash
pip install --upgrade -r requirements.txt
```

### WebSocket Connection Failed

1. Ensure telemetry stream is running first
2. Check firewall isn't blocking localhost connections
3. Try restarting the UI broker

### Dashboard Not Loading

1. Verify UI broker is running on port 7003
2. Check browser console for errors (F12)
3. Try accessing `http://127.0.0.1:7003` instead

---

## Next Steps

Once everything is running:

1. **Follow the Demo Script**: See `DEMO_SCRIPT.md` for a complete 10-step walkthrough
2. **Explore the API**: Visit `http://localhost:7002/docs` for interactive API documentation
3. **Check Metrics**: Visit `http://localhost:7002/metrics` for Prometheus metrics
4. **Inject Faults**: Use the scenario modulators to test different failure scenarios

---

## File Structure Reference

```
aws_fyuz/
├── phase1_data/
│   ├── telemetry_stream.py      ← Start this first
│   ├── anomaly_detector.py
│   ├── scenario_modulators.py
│   └── metrics_server.py
├── phase2_cognitive/
│   ├── reasoning_api.py          ← Start this second
│   ├── feature_builder.py
│   ├── heuristic_classifier.py
│   └── simulator.py
├── phase4_interface/
│   ├── ui_broker.py              ← Start this third
│   ├── dashboard.html
│   └── dashboard.js
├── config/                        ← Configuration files
├── schemas/                       ← JSON schemas
├── out/                           ← Logs (auto-created)
└── requirements.txt
```

---

## Support

For issues or questions, check:
- `DEMO_SCRIPT.md` - Complete walkthrough
- `README.md` - Architecture overview
- `phase3_orchestration/observability.md` - Metrics and monitoring
