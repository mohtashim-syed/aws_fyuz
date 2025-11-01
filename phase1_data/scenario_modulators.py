import time

def backhaul_congestion(rec: dict, severity: float) -> dict:
    """
    Severity: 0.0 (none) to 1.0 (extreme)
    Boosts packet_loss_pct, latency_ms, backhaul_util_pct
    
    Parameter ranges:
    - Adds [0, 15] to packet_loss_pct
    - Multiplies latency by [1.0, 3.5]
    - Adds [0, 35] to backhaul_util_pct
    """
    rec = rec.copy()
    rec["packet_loss_pct"] = min(100.0, rec["packet_loss_pct"] + severity * 15.0)
    rec["latency_ms"] = rec["latency_ms"] * (1.0 + severity * 2.5)
    rec["backhaul_util_pct"] = min(100.0, rec["backhaul_util_pct"] + severity * 35.0)
    return rec

def radio_overload(rec: dict, severity: float) -> dict:
    """
    Severity: 0.0 (none) to 1.0 (extreme)
    Raises calls_dropped, cpu_load_pct, jitter_ms
    
    Parameter ranges:
    - Adds [0, 25] calls_dropped
    - Adds [0, 30] to cpu_load_pct
    - Multiplies jitter by [1.0, 5.0]
    """
    rec = rec.copy()
    rec["calls_dropped"] = rec["calls_dropped"] + int(severity * 25)
    rec["cpu_load_pct"] = min(100.0, rec["cpu_load_pct"] + severity * 30.0)
    rec["jitter_ms"] = rec["jitter_ms"] * (1.0 + severity * 4.0)
    return rec

def dns_flap(rec: dict, severity: float) -> dict:
    """
    Severity: 0.0 (none) to 1.0 (extreme)
    Spikes latency_ms with sawtooth pattern based on time
    
    Parameter ranges:
    - Adds [0, 120] ms to latency in sawtooth wave (30s period)
    """
    rec = rec.copy()
    t = time.time()
    phase = (t % 30.0) / 30.0  # 30-second cycle
    sawtooth = abs(2.0 * phase - 1.0)  # 0 → 1 → 0
    rec["latency_ms"] = rec["latency_ms"] + severity * 120.0 * sawtooth
    return rec
