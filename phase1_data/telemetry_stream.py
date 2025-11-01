import asyncio
import websockets
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from itertools import cycle

random.seed(424242)

REGIONS = ["NorthEast", "SouthEast", "MidWest", "West"]
SITES = [f"{r[:2].upper()}_SITE_{str(i).zfill(3)}" 
         for r in REGIONS for i in range(1, 4)]

site_cycle = cycle(SITES)
clients = set()

def generate_record():
    site_id = next(site_cycle)
    region = next(r for r in REGIONS if site_id.startswith(r[:2].upper()))
    
    # Add wiggle for visible motion
    wiggle = random.uniform(-0.15, 0.15)
    base_loss = random.uniform(0.1, 3.5)
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "region": region,
        "site_id": site_id,
        "packet_loss_pct": round(max(0.0, base_loss + 0.8 + wiggle), 2),
        "latency_ms": round(random.uniform(30.0, 55.0) + 5 * random.random(), 1),
        "jitter_ms": round(random.uniform(1.0, 8.0), 2),
        "cpu_load_pct": round(random.uniform(40.0, 75.0), 1),
        "mem_used_pct": round(random.uniform(50.0, 80.0), 1),
        "calls_dropped": random.randint(0, 2),
        "throughput_mbps": round(random.uniform(400.0, 550.0), 1),
        "backhaul_util_pct": round(random.uniform(48.0, 75.0) + 2 * random.random(), 1),
        "trace_id": f"trace_{int(time.time()*1000)}_{random.randint(1000,9999)}"
    }

async def handler(websocket):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

async def broadcast():
    Path("./out").mkdir(exist_ok=True)
    with open("./out/telemetry.log", "a") as log:
        while True:
            rec = generate_record()
            msg = json.dumps(rec)
            log.write(msg + "\n")
            log.flush()
            
            if clients:
                await asyncio.gather(
                    *[ws.send(msg) for ws in clients],
                    return_exceptions=True
                )
            await asyncio.sleep(0.1)

async def main():
    async with websockets.serve(handler, "localhost", 7001, 
                                  path="/telemetry"):
        print("Telemetry stream running on ws://localhost:7001/telemetry")
        await broadcast()

if __name__ == "__main__":
    asyncio.run(main())
