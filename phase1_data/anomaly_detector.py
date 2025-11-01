from collections import deque
import statistics
import time
import random

class AnomalyDetector:
    def __init__(self, window_size=120, z_threshold=3.0, 
                 trigger_consecutive=3, clear_consecutive=5):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.trigger_consecutive = trigger_consecutive
        self.clear_consecutive = clear_consecutive
        
        self.windows = {
            "packet_loss_pct": deque(maxlen=window_size),
            "latency_ms": deque(maxlen=window_size),
            "backhaul_util_pct": deque(maxlen=window_size)
        }
        self.trigger_counts = {}
        self.clear_counts = {}
        self.active_anomaly = None
    
    def detect(self, rec: dict) -> dict:
        """
        Detect anomalies using rolling z-scores and absolute thresholds.
        
        Returns AnomalyEvent dict or None
        """
        site_id = rec["site_id"]
        
        # Update rolling windows
        for metric in self.windows:
            self.windows[metric].append(rec[metric])
        
        # Need minimum samples for statistics
        if len(self.windows["packet_loss_pct"]) < 30:
            return None
        
        # Calculate z-scores
        z_loss = self._z_score("packet_loss_pct", rec["packet_loss_pct"])
        z_latency = self._z_score("latency_ms", rec["latency_ms"])
        backhaul = rec["backhaul_util_pct"]
        
        # Detection logic: z-score exceedance or absolute threshold
        anomalous = (z_loss > self.z_threshold or 
                     z_latency > self.z_threshold or 
                     backhaul > 85.0)
        
        # Hysteresis logic
        if anomalous:
            self.trigger_counts[site_id] = self.trigger_counts.get(site_id, 0) + 1
            self.clear_counts[site_id] = 0
            
            if self.trigger_counts[site_id] >= self.trigger_consecutive and not self.active_anomaly:
                self.active_anomaly = self._create_event(rec, z_loss, z_latency, backhaul)
                return self.active_anomaly
        else:
            self.clear_counts[site_id] = self.clear_counts.get(site_id, 0) + 1
            self.trigger_counts[site_id] = 0
            
            if self.clear_counts[site_id] >= self.clear_consecutive:
                self.active_anomaly = None
        
        return None
    
    def _z_score(self, metric, value):
        data = list(self.windows[metric])
        if len(data) < 2:
            return 0.0
        mean = statistics.mean(data)
        stdev = statistics.stdev(data)
        return abs(value - mean) / stdev if stdev > 0 else 0.0
    
    def _create_event(self, rec, z_loss, z_latency, backhaul):
        # Symptom classification heuristics
        if backhaul > 85.0 and z_loss > 2.0 and z_latency > 2.0:
            symptom = "backhaul_congestion"
            confidence = 0.85
        elif rec["cpu_load_pct"] > 80.0 and rec["calls_dropped"] > 10:
            symptom = "radio_overload"
            confidence = 0.78
        elif z_latency > 3.5 and z_loss < 2.0:
            symptom = "dns_flap"
            confidence = 0.72
        else:
            symptom = "unknown"
            confidence = 0.50
        
        return {
            "event_id": f"evt_{int(time.time()*1000)}_{random.randint(1000,9999)}",
            "started_at": rec["timestamp"],
            "region": rec["region"],
            "site_id": rec["site_id"],
            "metrics_snapshot": {
                "packet_loss_pct": rec["packet_loss_pct"],
                "latency_ms": rec["latency_ms"],
                "backhaul_util_pct": rec["backhaul_util_pct"],
                "cpu_load_pct": rec["cpu_load_pct"],
                "calls_dropped": rec["calls_dropped"]
            },
            "suspected_symptom": symptom,
            "confidence": confidence,
            "trace_id": rec["trace_id"]
        }
