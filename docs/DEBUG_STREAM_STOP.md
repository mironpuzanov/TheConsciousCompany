# Debug Stream Stop Issue

## When Data Stops Recording

### Step 1: Check Live Logs
```bash
tail -f backend/backend.log
```

Watch for:
- `ERROR` messages
- `Stream task completed`
- `Stream appears stopped`
- `Fatal error`
- `chunks processed`

### Step 2: Check if Stream Task is Running
```bash
ps aux | grep "python.*main.py"
```

### Step 3: Check muselsl
```bash
ps aux | grep muselsl
```

If muselsl stopped, restart:
```bash
cd backend
source venv/bin/activate
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
muselsl stream --ppg --acc --gyro
```

### Step 4: Check LSL Streams
```bash
cd backend
source venv/bin/activate
python -c "from pylsl import resolve_streams; streams = resolve_streams(timeout=2.0); print(f'Found {len(streams)} LSL streams')"
```

Should show 4 streams (EEG, PPG, ACC, GYRO).

### Step 5: Check WebSocket Connection
In browser DevTools:
1. Open Network tab
2. Filter by "WS" (WebSocket)
3. Check if connection is "Open" or "Closed"
4. Check for errors in Console

### Common Causes

1. **Callback Exception**
   - Check logs for "Error in callback"
   - Stream continues but data processing fails

2. **MNE Processing Error**
   - Check logs for "Error in MNE processing"
   - Should fallback to basic processing

3. **Broadcast Error**
   - Check logs for "Error broadcasting data"
   - Stream continues but frontend doesn't receive data

4. **Stream Task Exited**
   - Check logs for "Stream task completed"
   - Task might have exited unexpectedly

5. **muselsl Stopped**
   - Check if muselsl process is running
   - Restart if needed

### What to Report

If stream still stops, provide:
1. Last 20 lines of `backend/backend.log`
2. Output of `ps aux | grep -E "python|muselsl"`
3. Browser console errors (if any)
4. When exactly it stops (immediately? after X seconds?)

