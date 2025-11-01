from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response
import json
from datetime import datetime, timezone

app = FastAPI()

# Prometheus counters
telemetry_emitted = Counter('telemetry_emitted_total', 'Total telemetry records emitted', ['region'])
anomaly_emitted = Counter('anomaly_emitted_total', 'Total anomaly events emitted', ['region', 'symptom'])

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def log_json(level: str, component: str, message: str, **kwargs):
    """Structured JSON logging"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "component": component,
        "message": message,
        **kwargs
    }
    print(json.dumps(log_entry))

# Example PromQL queries:
# sum(rate(telemetry_emitted_total[5m])) by (region)
# sum(anomaly_emitted_total) by (region, symptom)
# count(anomaly_emitted_total{symptom="backhaul_congestion"})
