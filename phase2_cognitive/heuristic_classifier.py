def heuristic_classifier(features: dict, metrics_snapshot: dict) -> tuple:
    """
    Rule-first heuristic layer for provisional diagnosis.
    
    Returns: (provisional_cause, preliminary_confidence)
    
    Signature Table:
    | Condition | Cause | Confidence |
    |-----------|-------|------------|
    | backhaul>85% AND loss>8% AND latency>100ms AND corr_hint | backhaul_congestion | 0.88 |
    | cpu>80% AND calls_dropped>10 AND jitter>15ms | radio_overload | 0.82 |
    | latency>120ms AND loss<8% AND latency_stdev>30ms | dns_flap | 0.75 |
    | backhaul>75% AND loss>5% | backhaul_congestion | 0.65 |
    | cpu>85% | radio_overload | 0.60 |
    """
    backhaul = metrics_snapshot["backhaul_util_pct"]
    loss = metrics_snapshot["packet_loss_pct"]
    latency = metrics_snapshot["latency_ms"]
    cpu = metrics_snapshot["cpu_load_pct"]
    calls_dropped = metrics_snapshot["calls_dropped"]
    jitter = features.get("jitter_ms_latest", 0)
    corr_hint = features.get("corr_hint", False)
    
    # Rule 1: Backhaul congestion (strong signal)
    if backhaul > 85.0 and loss > 8.0 and latency > 100.0 and corr_hint:
        return ("backhaul_congestion", 0.88)
    
    # Rule 2: Radio overload
    if cpu > 80.0 and calls_dropped > 10 and jitter > 15.0:
        return ("radio_overload", 0.82)
    
    # Rule 3: DNS flap (periodic latency spikes)
    if latency > 120.0 and loss < 8.0 and features.get("latency_ms_stdev", 0) > 30.0:
        return ("dns_flap", 0.75)
    
    # Rule 4: Moderate backhaul congestion
    if backhaul > 75.0 and loss > 5.0:
        return ("backhaul_congestion", 0.65)
    
    # Rule 5: Elevated CPU
    if cpu > 85.0:
        return ("radio_overload", 0.60)
    
    # Default: unknown
    return ("unknown", 0.45)
