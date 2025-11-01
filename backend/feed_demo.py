# feed_demo.py
#
# Sends fake telemetry into /telemetry/push on a loop
# so the dashboard shows live updates and occasional incidents.
#
# HOW TO USE:
#   1. In one terminal: uvicorn main:app --reload
#   2. In another terminal: python feed_demo.py
#   3. Open dashboard.html in Chrome and talk to judges.
#
# HACKATHON REALITY:
# - This script replaces AWS Kinesis/OpenTelemetry streaming.
#
# ROADMAP STORY:
# - "In production, this feeder is replaced by a streaming pipeline
#    powered by Kinesis and OpenTelemetry from real RAN / packet core nodes."

import time
import random
import requests
from datetime import datetime

BACKEND_URL = "http://localhost:8000/telemetry/push"

REGIONS = ["northwest", "central", "south"]
CELLS = {
    "northwest": ["cell_12", "cell_15"],
    "central": ["cell_21", "cell_22"],
    "south": ["cell_30", "cell_31"]
}

def normal_payload(region: str, cell_id: str):
    return {
        "region": region,
        "cell_id": cell_id,
        "packet_loss_pct": round(random.uniform(0.3, 0.9), 2),  # healthy: <1%
        "latency_ms": round(random.uniform(45, 70), 1),        # healthy: ~50-70ms
        "throughput_mbps": round(random.uniform(100, 200), 1),
        "timestamp": datetime.utcnow().isoformat()
    }

def spike_payload():
    # simulate congestion / backhaul saturation in northwest / cell_12
    return {
        "region": "northwest",
        "cell_id": "cell_12",
        "packet_loss_pct": 6.3,        # ~6% loss, bad
        "latency_ms": 180.0,           # ~180ms latency, bad
        "throughput_mbps": 120.0,
        "timestamp": datetime.utcnow().isoformat()
    }

print("[feed_demo] starting telemetry loop against", BACKEND_URL)

while True:
    # send normal readings for each region+cell
    for r in REGIONS:
        for c in CELLS[r]:
            try:
                requests.post(BACKEND_URL, json=normal_payload(r, c), timeout=2.0)
            except Exception as e:
                print("[feed_demo] normal post failed:", e)

    # ~10% of loops, inject a spike to trigger incident/AI
    if random.random() < 0.1:
        try:
            print("[feed_demo] injecting spike to northwest/cell_12")
            requests.post(BACKEND_URL, json=spike_payload(), timeout=2.0)
        except Exception as e:
            print("[feed_demo] spike post failed:", e)

    time.sleep(2)
