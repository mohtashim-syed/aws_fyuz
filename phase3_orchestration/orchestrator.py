import json
import time
from datetime import datetime, timezone
from typing import Dict, Optional

class HealingOrchestrator:
    """
    Deterministic pipeline: Detection → Diagnosis → Recommendation → Approval → Execution → Simulation
    """
    
    def __init__(self):
        self.state_vector = {
            "packet_loss_pct": 0.0,
            "latency_ms": 0.0,
            "backhaul_util_pct": 0.0,
            "cpu_load_pct": 0.0,
            "jitter_ms": 0.0,
            "corr_hint": False,
            "prior_action_id": None
        }
        self.audit_log = []
    
    def process_anomaly(self, anomaly_event: Dict) -> Dict:
        """
        Orchestration Flow:
        Step A: Detector emits AnomalyEvent
        Step B: /diagnose returns DiagnosisBundle
        Step C: /recommend returns RecommendationPlan
        Step D: Human taps "Approve Safe Plan" in UI
        Step E: Planner sends intent payload to mock executor
        Step F: /simulate runs "what-if" to preview results
        """
        trace_id = anomaly_event["trace_id"]
        
        # Step A: Anomaly received
        self._log_audit("anomaly_received", anomaly_event["event_id"], trace_id)
        
        # Step B: Diagnosis (mock - replace with API call)
        diagnosis = self._mock_diagnose(anomaly_event)
        self._log_audit("diagnosis_completed", anomaly_event["event_id"], trace_id, 
                       {"likely_cause": diagnosis["likely_cause"]})
        
        # Step C: Recommendation (mock - replace with API call)
        recommendation = self._mock_recommend(anomaly_event, diagnosis)
        self._log_audit("recommendation_generated", anomaly_event["event_id"], trace_id,
                       {"actions": len(recommendation["actions"])})
        
        return {
            "anomaly": anomaly_event,
            "diagnosis": diagnosis,
            "recommendation": recommendation,
            "status": "awaiting_approval"
        }
    
    def approve_plan(self, event_id: str, user_id: str, plan_hash: str) -> Dict:
        """
        Step D: Human approval with safety checks
        """
        # Safety rule: No execution without explicit approval
        if not self._validate_approval(event_id, plan_hash):
            return {"status": "rejected", "reason": "invalid_plan_hash"}
        
        # Log audit entry
        self._log_audit("plan_approved", event_id, f"approval_{event_id}", 
                       {"user_id": user_id, "plan_hash": plan_hash})
        
        # Step E: Send to mock executor
        execution_result = self._mock_execute(event_id)
        
        return {
            "status": "approved",
            "execution": execution_result
        }
    
    def _validate_approval(self, event_id: str, plan_hash: str) -> bool:
        """Safety rule: Verify plan integrity"""
        # Mock validation
        return True
    
    def _mock_diagnose(self, anomaly: Dict) -> Dict:
        """Mock diagnosis - replace with API call"""
        return {
            "event_id": anomaly["event_id"],
            "region": anomaly["region"],
            "site_id": anomaly["site_id"],
            "likely_cause": anomaly["suspected_symptom"],
            "evidence": ["Mock evidence"],
            "confidence": anomaly["confidence"],
            "trace_id": anomaly["trace_id"],
            "explanation": "Mock explanation"
        }
    
    def _mock_recommend(self, anomaly: Dict, diagnosis: Dict) -> Dict:
        """Mock recommendation - replace with API call"""
        return {
            "event_id": anomaly["event_id"],
            "region": anomaly["region"],
            "site_id": anomaly["site_id"],
            "actions": [
                {"action": "reroute_traffic", "params": {"target_region": "MidWest", "share_pct": 30}, "mode": "safe"}
            ],
            "risks": ["May increase latency"],
            "rollback": ["Revert traffic split"],
            "trace_id": anomaly["trace_id"]
        }
    
    def _mock_execute(self, event_id: str) -> Dict:
        """Mock executor - no real changes"""
        return {
            "event_id": event_id,
            "status": "mitigating",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _log_audit(self, action: str, event_id: str, trace_id: str, metadata: Optional[Dict] = None):
        """Log audit entry with trace_id"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "event_id": event_id,
            "trace_id": trace_id,
            "metadata": metadata or {}
        }
        self.audit_log.append(entry)
        print(json.dumps(entry))
