# State & Actions Definition

## State Vector
```python
state = [
    packet_loss_pct,      # Current packet loss percentage
    latency_ms,           # Current latency in milliseconds
    backhaul_util_pct,    # Backhaul utilization percentage
    cpu_load_pct,         # CPU load percentage
    jitter_ms,            # Jitter in milliseconds
    corr_hint,            # Binary correlation hint (0 or 1)
    prior_action_id       # ID of previously executed action
]
```

## Action Catalog

### 1. reroute_traffic(target_region, share_pct)
- **Description**: Redirect traffic to alternate region
- **Parameters**:
  - `target_region`: string (e.g., "MidWest")
  - `share_pct`: integer 10-50 (percentage of traffic to reroute)
- **Mode**: safe
- **Expected MTTR**: 5 minutes

### 2. scale_capacity(node_type, units)
- **Description**: Add computational/bandwidth resources
- **Parameters**:
  - `node_type`: string ("backhaul" or "radio")
  - `units`: integer 1-5 (number of capacity units)
- **Mode**: aggressive
- **Expected MTTR**: 8-10 minutes

### 3. enable_cac(threshold_pct)
- **Description**: Enable Call Admission Control
- **Parameters**:
  - `threshold_pct`: integer 90-99 (utilization threshold)
- **Mode**: safe
- **Expected MTTR**: 2 minutes

### 4. switch_dns_upstream(provider)
- **Description**: Switch to alternate DNS provider
- **Parameters**:
  - `provider`: string ("primary", "secondary", "tertiary")
- **Mode**: safe
- **Expected MTTR**: 1 minute

## Reward Goal

**Objective**: Minimize packet loss and latency within 5 minutes while penalizing oscillations and excessive capacity.

**Reward Function Components**:
1. **Primary**: Reduction in packet_loss_pct and latency_ms
2. **Penalty**: Action oscillations (frequent action changes)
3. **Penalty**: Excessive capacity provisioning (cost efficiency)
4. **Bonus**: Fast resolution (MTTR < 5 minutes)

**Formula**:
```
reward = -1.0 * (packet_loss_pct + latency_ms/100) 
         - 0.5 * oscillation_count 
         - 0.3 * excess_capacity_units
         + 10.0 * (1 if resolved_under_5min else 0)
```
