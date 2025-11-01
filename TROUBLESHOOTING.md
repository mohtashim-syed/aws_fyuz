# Troubleshooting: Dashboard Not Updating

## Quick Diagnosis

Run this command to check what's running:
```bash
check_services.bat
```

Or manually check:
```bash
# Should show 4 Python processes
tasklist | findstr python.exe

# Should show ports in use
netstat -ano | findstr :7001
netstat -ano | findstr :7003
```

## Problem: Dashboard Shows Static Numbers

### Root Cause Checklist

✅ **Is the forwarder running?**
- The forwarder is the NEW service that pipes data from telemetry → broker
- Without it, the dashboard will NOT update
- Check: You should have **4 terminal windows** open, not 3

✅ **Are all 4 services running?**
1. Telemetry Stream (port 7001)
2. Cognitive API (port 7002)  
3. UI Broker (port 7003)
4. **Forwarder (no port - connects to 7001 and 7003)**

### Step-by-Step Fix

#### Step 1: Stop Everything
Close all terminal windows or press `Ctrl+C` in each.

#### Step 2: Start in Correct Order

**Option A: Automated**
```bash
start_all_with_forwarder.bat
```

**Option B: Manual (4 terminals)**

**Terminal 1:**
```bash
python phase1_data/telemetry_stream.py
```
Wait for: `Telemetry stream running on ws://localhost:7001/telemetry`

**Terminal 2:**
```bash
python phase2_cognitive/reasoning_api.py
```
Wait for: `Uvicorn running on http://0.0.0.0:7002`

**Terminal 3:**
```bash
python phase4_interface/ui_broker.py
```
Wait for: `Uvicorn running on http://0.0.0.0:7003`

**Terminal 4 (CRITICAL - This is the missing piece!):**
```bash
python phase1_data/forwarder.py
```
Wait for: `✓ Connected to telemetry stream`

#### Step 3: Verify Data Flow

Run the test script:
```bash
python test_pipeline.py
```

Expected output:
```
✓ Received: NorthEast - Loss: 2.34%
✓ Telemetry stream is working!

✓ Received UI payload with 4 regions
✓ UI WebSocket is working!

✓ Broker accepted test record
✓ Ingestion endpoint is working!

✓ ALL TESTS PASSED!
```

#### Step 4: Check Browser

1. Open: `http://localhost:7003`
2. Press `F12` to open Developer Console
3. Look for: `✓ Connected to UI broker`
4. Watch the region tiles - numbers should change every 0.5-1 second

### Common Issues

#### Issue 1: "Only 3 Python processes running"

**Problem:** Forwarder not started
**Solution:** 
```bash
python phase1_data/forwarder.py
```

#### Issue 2: "Forwarder shows connection errors"

**Problem:** Telemetry stream not running or wrong port
**Solution:**
1. Stop forwarder
2. Restart telemetry stream first
3. Wait 2 seconds
4. Start forwarder again

#### Issue 3: "Browser console shows WebSocket errors"

**Problem:** UI broker not running
**Solution:**
```bash
python phase4_interface/ui_broker.py
```

#### Issue 4: "Numbers update but very slowly"

**Problem:** EMA smoothing too aggressive
**Solution:** Edit `phase4_interface/ui_broker.py` line 142:
```python
alpha = 0.5  # Increase from 0.3 for faster response
```

#### Issue 5: "Port already in use"

**Problem:** Previous instance still running
**Solution:**
```bash
# Find the process
netstat -ano | findstr :7001

# Kill it (replace PID with actual number)
taskkill /PID <PID> /F
```

### Visual Verification

**What you should see in each terminal:**

**Terminal 1 (Telemetry):**
```
Telemetry stream running on ws://localhost:7001/telemetry
```
(Continuous output of JSON records)

**Terminal 2 (Cognitive API):**
```
INFO:     Uvicorn running on http://0.0.0.0:7002
INFO:     Application startup complete.
```

**Terminal 3 (UI Broker):**
```
INFO:     Uvicorn running on http://0.0.0.0:7003
INFO:     Application startup complete.
[INGEST] NorthEast: Loss=2.45% Latency=48.3ms (samples=50)
[INGEST] SouthEast: Loss=1.89% Latency=42.1ms (samples=50)
```
(Should see [INGEST] messages every few seconds)

**Terminal 4 (Forwarder):**
```
Starting telemetry forwarder...
Listening: ws://localhost:7001/telemetry
Forwarding to: http://localhost:7003/api/ingest/telemetry
✓ Connected to telemetry stream
```
(Should stay connected, no errors)

### Dashboard Verification

Open `http://localhost:7003` and watch for:

✅ **Region tiles show 4 regions:** NorthEast, SouthEast, MidWest, West
✅ **Numbers change every 0.5-1 seconds**
✅ **Packet Loss:** Fluctuates between 0.5-4.5%
✅ **Latency:** Varies between 30-65ms
✅ **Backhaul:** Drifts between 48-77%
✅ **Throughput:** Changes between 400-550 Mbps

### Still Not Working?

1. **Check browser cache:**
   - Press `Ctrl+Shift+R` to hard refresh
   - Or clear cache and reload

2. **Check firewall:**
   - Allow Python through Windows Firewall
   - Allow localhost connections

3. **Check Python version:**
   ```bash
   python --version
   ```
   Should be 3.8 or higher

4. **Reinstall dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

5. **Check logs:**
   - Look at Terminal 3 (UI Broker) for [INGEST] messages
   - If you don't see [INGEST] messages, the forwarder isn't sending data

### Debug Commands

```bash
# Test telemetry stream directly
python -c "import asyncio, websockets, json; asyncio.run((lambda: websockets.connect('ws://localhost:7001/telemetry')).__await__())"

# Test if broker accepts data
curl -X POST http://localhost:7003/api/ingest/telemetry ^
  -H "Content-Type: application/json" ^
  -d "{\"region\":\"NorthEast\",\"packet_loss_pct\":99.9,\"latency_ms\":999,\"jitter_ms\":5,\"cpu_load_pct\":50,\"mem_used_pct\":60,\"calls_dropped\":0,\"throughput_mbps\":500,\"backhaul_util_pct\":99,\"timestamp\":\"2025-11-01T00:00:00Z\",\"site_id\":\"TEST\",\"trace_id\":\"test\"}"

# Check if test data appears (should show high values)
curl -s http://localhost:7003/api/incident
```

### Architecture Diagram

```
┌─────────────────┐
│ Telemetry       │ ← YOU MUST START THIS (Terminal 1)
│ Port 7001       │
└────────┬────────┘
         │ WebSocket
         ▼
┌─────────────────┐
│ Forwarder       │ ← YOU MUST START THIS (Terminal 4) ⚠️
│ (no port)       │    THIS IS THE MISSING PIECE!
└────────┬────────┘
         │ HTTP POST to /api/ingest/telemetry
         ▼
┌─────────────────┐
│ UI Broker       │ ← YOU MUST START THIS (Terminal 3)
│ Port 7003       │
└────────┬────────┘
         │ WebSocket /ws/ui (broadcasts every 500ms)
         ▼
┌─────────────────┐
│ Dashboard       │ ← Open in browser: http://localhost:7003
│ (Browser)       │
└─────────────────┘
```

### Success Criteria

✅ 4 Python processes running
✅ 3 ports in use (7001, 7002, 7003)
✅ Forwarder shows "✓ Connected"
✅ UI Broker shows [INGEST] messages
✅ Browser console shows "✓ Connected to UI broker"
✅ Dashboard numbers change every 0.5-1 seconds

If ALL of these are true and dashboard still doesn't update:
1. Hard refresh browser (Ctrl+Shift+R)
2. Check browser console for JavaScript errors
3. Try a different browser
