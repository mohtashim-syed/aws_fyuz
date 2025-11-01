import math

def simulate(levers: dict) -> dict:
    """
    Lightweight M/M/c queueing model simulator for "what-if" analysis.
    
    SimulationRequest levers:
    - traffic_multiplier: float (e.g., 2.0 = double traffic)
    - capacity_delta: dict with 'units' (e.g., {'units': 2})
    - routing_change: dict (placeholder for future routing logic)
    
    Returns: dict with pred_packet_loss_pct, pred_latency_ms, pred_blocking_prob
    
    M/M/c Model:
    - λ (lambda): arrival rate
    - μ (mu): service rate per server
    - c: number of servers
    - ρ (rho): utilization = λ / (c * μ)
    """
    # Baseline parameters
    baseline_arrival_rate = 800.0  # requests/sec
    service_rate_per_server = 250.0  # requests/sec per server
    baseline_servers = 4
    
    # Apply levers
    traffic_multiplier = levers.get("traffic_multiplier", 1.0)
    capacity_delta = levers.get("capacity_delta", {})
    additional_units = capacity_delta.get("units", 0)
    
    # Adjusted parameters
    arrival_rate = baseline_arrival_rate * traffic_multiplier
    num_servers = baseline_servers + additional_units
    
    # Calculate utilization
    total_capacity = num_servers * service_rate_per_server
    utilization = arrival_rate / total_capacity
    
    # Bounds checking
    if utilization >= 1.0:
        # System overload
        return {
            "pred_packet_loss_pct": 100.0,
            "pred_latency_ms": 9999.0,
            "pred_blocking_prob": 1.0
        }
    
    # Simplified M/M/c approximations
    # Packet loss approximation (Erlang C formula simplified)
    if utilization < 0.7:
        packet_loss = utilization * 0.5  # Low utilization
    elif utilization < 0.85:
        packet_loss = (utilization - 0.7) * 10 + 0.35
    else:
        packet_loss = (utilization - 0.85) * 50 + 1.85
    
    # Latency approximation (Little's Law + queueing delay)
    base_latency = 1000.0 / service_rate_per_server  # ms per request
    queue_factor = utilization / (1.0 - utilization)
    latency = base_latency * (1.0 + queue_factor * 0.5)
    
    # Blocking probability (Erlang B approximation)
    blocking_prob = min(0.99, utilization ** num_servers / math.factorial(num_servers))
    
    return {
        "pred_packet_loss_pct": round(min(100.0, packet_loss), 2),
        "pred_latency_ms": round(min(9999.0, latency), 2),
        "pred_blocking_prob": round(blocking_prob, 4)
    }
