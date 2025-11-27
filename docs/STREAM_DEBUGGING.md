# Stream Debugging Guide

## If Data Stops Recording

### Check Backend Logs
```bash
tail -f backend/backend.log
```

Look for:
- `ERROR` messages
- `Stream task completed`
- `Stream appears stopped`
- `Fatal error in stream_data`

### Check if Stream is Running
```bash
ps aux | grep "python.*main.py"
```

### Check LSL Streams
```bash
cd backend
source venv/bin/activate
python -c "from pylsl import resolve_streams; streams = resolve_streams(timeout=2.0); print(f'Found {len(streams)} streams')"
```

### Common Issues

1. **muselsl stopped**
   - Check: `ps aux | grep muselsl`
   - Fix: Restart `muselsl stream --ppg --acc --gyro`

2. **Stream task crashed**
   - Check logs for exception
   - Stream should auto-recover, but may need reconnect

3. **No data from LSL**
   - Check if muselsl is actually streaming
   - Check LSL streams are available

4. **Processing errors**
   - Check logs for MNE/processing errors
   - Stream continues even with errors, but may affect data quality

### Manual Restart
If stream stops:
1. Click "Disconnect" in browser
2. Wait 2 seconds
3. Click "Connect" again

### Debug Mode
To see more logs, change logging level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

