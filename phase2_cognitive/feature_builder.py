import statistics
from typing import List, Dict

def build_features(window: List[dict]) -> dict:
    """
    Build statistical features from telemetry window.
    
    Inputs: List of TelemetryRecord dicts for last N minutes
    Outputs: Means, stdevs, latest values, correlation hints
    """
    if len(window) < 10:
        return {"error": "insufficient_data"}
    
    # Extract metric arrays
    metrics = {
        "packet_loss_pct": [r["packet_loss_pct"] for r in window],
        "latency_ms": [r["latency_ms"] for r in window],
        "backhaul_util_pct": [r["backhaul_util_pct"] for r in window],
        "cpu_load_pct": [r["cpu_load_pct"] for r in window],
        "jitter_ms": [r["jitter_ms"] for r in window],
        "calls_dropped": [r["calls_dropped"] for r in window]
    }
    
    features = {}
    
    # Compute means, stdevs, latest
    for name, values in metrics.items():
        features[f"{name}_mean"] = round(statistics.mean(values), 2)
        features[f"{name}_stdev"] = round(statistics.stdev(values), 2) if len(values) > 1 else 0.0
        features[f"{name}_latest"] = values[-1]
    
    # Correlation hint: backhaul, latency, loss rising together
    backhaul_trend = metrics["backhaul_util_pct"][-5:] if len(window) >= 5 else metrics["backhaul_util_pct"]
    latency_trend = metrics["latency_ms"][-5:] if len(window) >= 5 else metrics["latency_ms"]
    loss_trend = metrics["packet_loss_pct"][-5:] if len(window) >= 5 else metrics["packet_loss_pct"]
    
    backhaul_rising = all(backhaul_trend[i] <= backhaul_trend[i+1] for i in range(len(backhaul_trend)-1))
    latency_rising = all(latency_trend[i] <= latency_trend[i+1] for i in range(len(latency_trend)-1))
    loss_rising = all(loss_trend[i] <= loss_trend[i+1] for i in range(len(loss_trend)-1))
    
    features["corr_hint"] = backhaul_rising and latency_rising and loss_rising
    
    return features
