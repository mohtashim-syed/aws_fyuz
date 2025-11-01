"""
Telemetry Forwarder: Pipes telemetry stream to broker and anomaly detector
"""
import asyncio
import json
import websockets
import httpx
import time

TELEMETRY_WS = "ws://localhost:7001/telemetry"
BROKER_TELEMETRY = "http://localhost:7003/api/ingest/telemetry"
ANOMALY_INGEST = "http://localhost:7003/api/ingest/anomaly"

async def run():
    print("Starting telemetry forwarder...")
    print(f"Listening: {TELEMETRY_WS}")
    print(f"Forwarding to: {BROKER_TELEMETRY}")
    
    while True:
        try:
            async with websockets.connect(TELEMETRY_WS, ping_interval=20, ping_timeout=10) as ws:
                print("✓ Connected to telemetry stream")
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    async for msg in ws:
                        try:
                            rec = json.loads(msg)
                            
                            # Forward to broker for UI updates
                            await client.post(BROKER_TELEMETRY, json=rec)
                            
                            # Forward to anomaly detector (if needed)
                            # await client.post(ANOMALY_INGEST, json=rec)
                            
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {msg[:100]}")
                        except httpx.RequestError as e:
                            print(f"Forward error: {e}")
                            
        except websockets.exceptions.WebSocketException as e:
            print(f"WebSocket error: {e}. Reconnecting in 1.5s...")
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"Unexpected error: {e}. Reconnecting in 1.5s...")
            await asyncio.sleep(1.5)

if __name__ == "__main__":
    asyncio.run(run())
