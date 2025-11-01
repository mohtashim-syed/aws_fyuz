"""
Real-time metrics watcher - Shows live updates from the dashboard
"""
import asyncio
import websockets
import json
import os
from datetime import datetime

async def watch():
    print("=" * 70)
    print("HEALING AGENT - LIVE METRICS WATCHER")
    print("=" * 70)
    print()
    print("Connecting to dashboard WebSocket...")
    print()
    
    try:
        async with websockets.connect('ws://localhost:7003/ws/ui') as ws:
            print("✓ Connected! Watching for updates...\n")
            
            update_count = 0
            last_values = {}
            
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                update_count += 1
                
                # Clear screen every 10 updates for readability
                if update_count % 10 == 0:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("=" * 70)
                    print("HEALING AGENT - LIVE METRICS WATCHER")
                    print("=" * 70)
                    print()
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Update #{update_count}")
                print("-" * 70)
                
                for region in data.get('regions', []):
                    name = region['name']
                    kpis = region['kpis']
                    
                    # Check if values changed
                    changed = ""
                    if name in last_values:
                        old = last_values[name]
                        if (abs(old['packet_loss_pct'] - kpis['packet_loss_pct']) > 0.01 or
                            abs(old['latency_ms'] - kpis['latency_ms']) > 0.1):
                            changed = " ← CHANGED!"
                    
                    last_values[name] = kpis.copy()
                    
                    print(f"\n{name}:{changed}")
                    print(f"  Packet Loss:  {kpis['packet_loss_pct']:6.2f}%")
                    print(f"  Latency:      {kpis['latency_ms']:6.1f} ms")
                    print(f"  Backhaul:     {kpis['backhaul_util_pct']:6.1f}%")
                    print(f"  Throughput:   {kpis['throughput_mbps']:6.1f} Mbps")
                
                print()
                
                # Show status
                if update_count == 1:
                    print("⏳ Waiting for changes... (This may take a few seconds)")
                elif update_count < 5:
                    print("⏳ Still warming up... (EMA smoothing in progress)")
                else:
                    changes = sum(1 for v in last_values.values() if v)
                    if changes > 0:
                        print(f"✓ LIVE! Metrics are updating ({changes} regions tracked)")
                    else:
                        print("⚠ No changes detected yet - check if forwarder is running")
                
                await asyncio.sleep(0.1)  # Small delay to avoid overwhelming output
                
    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocket error: {e}")
        print("\nTroubleshooting:")
        print("1. Is UI broker running? python phase4_interface/ui_broker.py")
        print("2. Is it on port 7003? Check with: netstat -ano | findstr :7003")
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    print("\nThis script watches the dashboard WebSocket for live updates.")
    print("If you see 'CHANGED!' markers, your metrics are updating!\n")
    print("Press Ctrl+C to stop.\n")
    
    asyncio.run(watch())
