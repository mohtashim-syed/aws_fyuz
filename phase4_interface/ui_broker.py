from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict
from collections import defaultdict

app = FastAPI(title="Healing Agent UI Broker")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket clients
clients: List[WebSocket] = []

# Real-time metrics aggregation by region
region_metrics: Dict[str, Dict] = defaultdict(lambda: {
    "packet_loss_pct": 0.0,
    "latency_ms": 0.0,
    "backhaul_util_pct": 0.0,
    "throughput_mbps": 0.0,
    "sample_count": 0
})

# Mock data store
ui_state = {
    "regions": [
        {
            "name": "NorthEast",
            "kpis": {
                "packet_loss_pct": 2.3,
                "latency_ms": 45.2,
                "backhaul_util_pct": 58.5,
                "throughput_mbps": 487.3
            }
        },
        {
            "name": "SouthEast",
            "kpis": {
                "packet_loss_pct": 1.8,
                "latency_ms": 42.1,
                "backhaul_util_pct": 52.3,
                "throughput_mbps": 512.7
            }
        },
        {
            "name": "MidWest",
            "kpis": {
                "packet_loss_pct": 2.1,
                "latency_ms": 48.5,
                "backhaul_util_pct": 61.2,
                "throughput_mbps": 465.8
            }
        },
        {
            "name": "West",
            "kpis": {
                "packet_loss_pct": 1.5,
                "latency_ms": 39.8,
                "backhaul_util_pct": 49.7,
                "throughput_mbps": 534.2
            }
        }
    ],
    "incidents": [],
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "trace_id": f"trace_ui_{int(datetime.now().timestamp())}"
}

@app.websocket("/ws/ui")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time UI updates.
    Sends UiPayload objects with regions, incidents, and metadata.
    """
    await websocket.accept()
    clients.append(websocket)
    
    try:
        # Send initial state
        await websocket.send_json(ui_state)
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(0.5)  # Update every 500ms for smooth motion
            ui_state["last_updated"] = datetime.now(timezone.utc).isoformat()
            await websocket.send_json(ui_state)
    except WebSocketDisconnect:
        clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in clients:
            clients.remove(websocket)

@app.post("/api/approve")
async def approve_plan(payload: dict):
    """
    Mock approval endpoint.
    Accepts { event_id: str, approval: bool }
    """
    event_id = payload.get("event_id")
    approval = payload.get("approval", False)
    
    if approval:
        # Update incident status
        for incident in ui_state["incidents"]:
            if incident["event_id"] == event_id:
                incident["status"] = "mitigating"
        
        # Broadcast update
        await broadcast_update()
        
        return {
            "status": "approved",
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return {"status": "rejected", "event_id": event_id}

@app.post("/api/ingest/telemetry")
async def ingest_telemetry(record: dict):
    """
    Ingest telemetry record and update region metrics.
    Called by forwarder for each telemetry record.
    """
    region = record.get("region")
    if not region:
        return {"status": "error", "message": "Missing region"}
    
    # Update running average for this region
    metrics = region_metrics[region]
    n = metrics["sample_count"]
    
    # Exponential moving average (weight recent samples more)
    alpha = 0.3  # Smoothing factor
    metrics["packet_loss_pct"] = alpha * record["packet_loss_pct"] + (1 - alpha) * metrics["packet_loss_pct"]
    metrics["latency_ms"] = alpha * record["latency_ms"] + (1 - alpha) * metrics["latency_ms"]
    metrics["backhaul_util_pct"] = alpha * record["backhaul_util_pct"] + (1 - alpha) * metrics["backhaul_util_pct"]
    metrics["throughput_mbps"] = alpha * record["throughput_mbps"] + (1 - alpha) * metrics["throughput_mbps"]
    metrics["sample_count"] = n + 1
    
    # Update UI state with latest metrics
    for region_data in ui_state["regions"]:
        if region_data["name"] == region:
            region_data["kpis"] = {
                "packet_loss_pct": round(metrics["packet_loss_pct"], 2),
                "latency_ms": round(metrics["latency_ms"], 1),
                "backhaul_util_pct": round(metrics["backhaul_util_pct"], 1),
                "throughput_mbps": round(metrics["throughput_mbps"], 1)
            }
            break
    
    # Debug logging every 50 records
    if n % 50 == 0:
        print(f"[INGEST] {region}: Loss={metrics['packet_loss_pct']:.2f}% Latency={metrics['latency_ms']:.1f}ms (samples={n})")
    
    return {"status": "ingested", "region": region}

@app.post("/api/incident")
async def add_incident(incident: dict):
    """
    Add new incident to UI state (called by orchestrator).
    """
    ui_state["incidents"].append(incident)
    await broadcast_update()
    return {"status": "added", "event_id": incident["event_id"]}

async def broadcast_update():
    """Broadcast UI state to all connected clients"""
    ui_state["last_updated"] = datetime.now(timezone.utc).isoformat()
    for client in clients:
        try:
            await client.send_json(ui_state)
        except:
            pass

@app.get("/")
async def serve_dashboard():
    """Serve the dashboard HTML"""
    return FileResponse("phase4_interface/dashboard.html")

@app.get("/dashboard.js")
async def serve_js():
    """Serve the dashboard JavaScript"""
    return FileResponse("phase4_interface/dashboard.js")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7003)
