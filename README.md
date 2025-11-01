# Healing Agent - Telecom Outage Triage System

AI-Agentic Network Operations Assistant for autonomous detection, diagnosis, and remediation of telecom network anomalies.

## Architecture

- **Observability Layer**: Simulated telemetry → anomaly detection
- **Cognitive Layer**: LLM reasoning → diagnosis, recommendation, explanation
- **Planning Layer**: Lightweight simulator → "what-if" outcomes
- **Interface Layer**: Dashboard + chat → approvals, exports

## Project Structure

```
aws_fyuz/
├── phase1_data/          # Foundation & Data (Person A)
├── phase2_cognitive/     # Cognitive & Reasoning (Person B)
├── phase3_orchestration/ # Decision & Orchestration (Person B + C)
├── phase4_interface/     # Interface & Demo (Person C)
├── config/               # YAML configurations
├── schemas/              # JSON schemas
├── out/                  # Output logs
└── tests/                # Test hooks
```

## Quick Start

### ⚠️ IMPORTANT: You need 4 services for live metrics!

### Automated (Windows) - RECOMMENDED
```bash
start_all_with_forwarder.bat
```

### Manual (4 terminals required)
```bash
# Terminal 1 - Telemetry Stream
python phase1_data/telemetry_stream.py

# Terminal 2 - Cognitive API
python phase2_cognitive/reasoning_api.py

# Terminal 3 - UI Broker
python phase4_interface/ui_broker.py

# Terminal 4 - Forwarder (REQUIRED for live metrics!)
python phase1_data/forwarder.py

# Browser
http://localhost:7003
```

**Without the forwarder (Terminal 4), dashboard will show static numbers!**

**See `QUICKSTART.md` for detailed instructions or `TROUBLESHOOTING.md` if metrics don't update.**

## Demo Script

See `DEMO_SCRIPT.md` for the 10-step walkthrough.
