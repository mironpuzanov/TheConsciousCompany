# Server Status - Consciousness OS

## Current Status: ✅ All Services Running

### Services
1. **muselsl** - ✅ Running (PID: check with `ps aux | grep muselsl`)
   - Streaming: EEG (256 Hz), PPG (64 Hz), ACC (52 Hz), GYRO (52 Hz)
   - Command: `muselsl stream --ppg --acc --gyro`

2. **Python Backend** - ✅ Running (Port 8000)
   - FastAPI server with WebSocket support
   - Endpoint: http://localhost:8000
   - Health check: http://localhost:8000/

3. **React Frontend** - ✅ Running (Port 5173)
   - Vite dev server
   - URL: http://localhost:5173

## Quick Start

1. **Start muselsl** (if not running):
   ```bash
   cd backend
   source venv/bin/activate
   export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
   muselsl stream --ppg --acc --gyro
   ```

2. **Start backend** (if not running):
   ```bash
   cd backend
   source venv/bin/activate
   export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
   python main.py
   ```

3. **Start frontend** (if not running):
   ```bash
   cd consciousness-app
   npm run dev
   ```

4. **Open browser**: http://localhost:5173

## Troubleshooting

### Backend not connecting to Muse
- Check muselsl is running: `ps aux | grep muselsl`
- Check LSL streams: `python -c "from pylsl import resolve_streams; print(len(resolve_streams()))"`
- Restart muselsl if needed

### Frontend not loading
- Check port 5173: `lsof -i :5173`
- Check frontend logs: `tail -f consciousness-app/frontend.log`

### WebSocket connection failed
- Check backend is running: `curl http://localhost:8000/`
- Check backend logs: `tail -f backend/backend.log`
- Check browser console for WebSocket errors

## Log Files
- Backend: `backend/backend.log`
- muselsl: `backend/muselsl.log`
- Frontend: `consciousness-app/frontend.log`

