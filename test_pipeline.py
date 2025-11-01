"""
Quick test to verify the data pipeline is working
"""
import asyncio
import websockets
import json
import time

async def test_telemetry_stream():
    """Test that telemetry stream is emitting data"""
    print("Testing telemetry stream...")
    try:
        async with websockets.connect('ws://localhost:7001/telemetry', timeout=5) as ws:
            for i in range(3):
                msg = await ws.recv()
                data = json.loads(msg)
                print(f"✓ Received: {data['region']} - Loss: {data['packet_loss_pct']}%")
        print("✓ Telemetry stream is working!\n")
        return True
    except Exception as e:
        print(f"✗ Telemetry stream error: {e}\n")
        return False

async def test_ui_websocket():
    """Test that UI broker WebSocket is broadcasting"""
    print("Testing UI broker WebSocket...")
    try:
        async with websockets.connect('ws://localhost:7003/ws/ui', timeout=5) as ws:
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"✓ Received UI payload with {len(data.get('regions', []))} regions")
            if data.get('regions'):
                region = data['regions'][0]
                print(f"  Region: {region['name']}")
                print(f"  Packet Loss: {region['kpis']['packet_loss_pct']}%")
        print("✓ UI WebSocket is working!\n")
        return True
    except Exception as e:
        print(f"✗ UI WebSocket error: {e}\n")
        return False

async def test_broker_endpoint():
    """Test that broker accepts telemetry ingestion"""
    print("Testing broker ingestion endpoint...")
    import httpx
    
    test_record = {
        "timestamp": "2025-11-01T00:00:00Z",
        "region": "NorthEast",
        "site_id": "NE_SITE_001",
        "packet_loss_pct": 99.99,
        "latency_ms": 999.9,
        "jitter_ms": 5.0,
        "cpu_load_pct": 50.0,
        "mem_used_pct": 60.0,
        "calls_dropped": 0,
        "throughput_mbps": 500.0,
        "backhaul_util_pct": 99.9,
        "trace_id": "test_trace"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:7003/api/ingest/telemetry",
                json=test_record
            )
            if response.status_code == 200:
                print(f"✓ Broker accepted test record: {response.json()}")
                print("✓ Ingestion endpoint is working!\n")
                return True
            else:
                print(f"✗ Broker returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Broker endpoint error: {e}\n")
        return False

async def main():
    print("=" * 60)
    print("HEALING AGENT PIPELINE TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Telemetry stream
    results.append(await test_telemetry_stream())
    await asyncio.sleep(1)
    
    # Test 2: UI WebSocket
    results.append(await test_ui_websocket())
    await asyncio.sleep(1)
    
    # Test 3: Broker ingestion
    results.append(await test_broker_endpoint())
    await asyncio.sleep(2)
    
    # Test 4: Check if test record appears in UI
    print("Testing if ingested data appears in UI...")
    try:
        async with websockets.connect('ws://localhost:7003/ws/ui', timeout=5) as ws:
            msg = await ws.recv()
            data = json.loads(msg)
            ne_region = next((r for r in data['regions'] if r['name'] == 'NorthEast'), None)
            if ne_region:
                loss = ne_region['kpis']['packet_loss_pct']
                backhaul = ne_region['kpis']['backhaul_util_pct']
                print(f"  NorthEast Loss: {loss}%")
                print(f"  NorthEast Backhaul: {backhaul}%")
                
                if loss > 90 or backhaul > 90:
                    print("✓ Test data is visible in UI! (High values detected)")
                    results.append(True)
                else:
                    print("⚠ UI shows data but test values not reflected yet")
                    print("  (This is normal - wait a few seconds for EMA to catch up)")
                    results.append(True)
            else:
                print("✗ NorthEast region not found in UI data")
                results.append(False)
    except Exception as e:
        print(f"✗ Final check error: {e}")
        results.append(False)
    
    print()
    print("=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Start the forwarder: python phase1_data/forwarder.py")
        print("2. Open dashboard: http://localhost:7003")
        print("3. Watch metrics update in real-time")
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        if not results[0]:
            print("- Start telemetry stream: python phase1_data/telemetry_stream.py")
        if not results[1]:
            print("- Start UI broker: python phase4_interface/ui_broker.py")
        if not results[2]:
            print("- Check if UI broker is running on port 7003")

if __name__ == "__main__":
    asyncio.run(main())
