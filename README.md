# Consciousness OS

A real-time EEG meditation platform with AI-powered insights, built with Muse headband integration.

## Overview

Consciousness OS combines real-time EEG analysis with AI to provide deep insights into meditation and consciousness states. The system features:

- **Real-time EEG Streaming**: Direct integration with Muse EEG headband via Lab Streaming Layer (LSL)
- **Advanced Signal Processing**: ICA artifact removal, band power analysis, and mental state interpretation
- **AI Copilot**: Context-aware conversation analysis and meditation guidance
- **Live Visualization**: Real-time EEG waveforms, brain state monitoring, and HRV tracking
- **Session Recording**: Comprehensive session storage with analysis reports

## Architecture

### Backend (Python)
- FastAPI WebSocket server for real-time streaming
- muselsl for Muse headband BLE connectivity
- MNE-Python for EEG signal processing
- ML models for artifact detection and state classification

### Frontend (React + TypeScript)
- Real-time EEG visualization with Recharts
- WebSocket client for live data streaming
- Tailwind CSS + shadcn/ui components
- Meditation guidance interface

### AI Copilot
- Multi-model conversation analysis
- Emotional state detection
- Context-aware response generation
- OpenAI integration for advanced reasoning

## Project Structure

```
Consciousness OS/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Main server entry point
│   ├── muse_stream.py   # EEG streaming logic
│   ├── ml_analyzer.py   # ML-based analysis
│   ├── gpt5_copilot.py  # AI Copilot integration
│   └── sessions/        # Recorded meditation sessions
├── consciousness-app/    # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── hooks/       # WebSocket and Muse hooks
│   │   └── types/       # TypeScript definitions
├── conversation_analyzer/# AI conversation analysis system
├── docs/                # Documentation (organized by component)
│   ├── backend/         # Backend implementation docs
│   ├── frontend/        # Frontend and integration docs
│   ├── copilot/         # AI Copilot docs
│   ├── architecture/    # System architecture
│   └── planning/        # Development planning
└── venv/                # Python virtual environment (not in git)
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Muse EEG headband (Muse 2, Muse S, or compatible)
- macOS (for Bluetooth support) or Linux

### Backend Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Start the backend:
```bash
python main.py
```

### Frontend Setup

1. Install dependencies:
```bash
cd consciousness-app
npm install
```

2. Start development server:
```bash
npm run dev
```

### Muse Streaming

In a separate terminal, start the Muse LSL stream:
```bash
source venv/bin/activate
muselsl stream --backend bleak
```

## Usage

1. Turn on your Muse headband
2. Start muselsl stream (see above)
3. Start the backend server (`python backend/main.py`)
4. Start the frontend (`npm run dev` in consciousness-app/)
5. Open http://localhost:5173 in your browser
6. Click "Connect" to start streaming EEG data

## Features

### EEG Analysis
- **5-channel streaming**: TP9, AF7, AF8, TP10, AUX
- **Band power extraction**: Delta, Theta, Alpha, Beta, Gamma
- **Artifact detection**: Eye blinks, jaw clenches, motion artifacts
- **ICA processing**: Automated artifact removal
- **Mental state classification**: Focus, relaxation, drowsiness detection

### AI Copilot
- Real-time conversation analysis
- Emotional state tracking
- Context-aware meditation guidance
- Session insights and recommendations

### Visualization
- Live EEG waveforms
- Band power charts
- Brain state indicators
- HRV metrics
- Artifact status

## Documentation

See [docs/README.md](docs/README.md) for complete documentation.

Key docs:
- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Backend Architecture](docs/backend/ARCHITECTURE_PYTHON_BACKEND.md)
- [EEG Analysis](docs/backend/EEG_ANALYSIS_CAPABILITIES.md)
- [AI Copilot](docs/copilot/AI_COPILOT_IMPLEMENTATION_PLAN.md)

## Development Status

Currently in active development. Core features implemented:
- ✅ EEG streaming from Muse
- ✅ Real-time signal processing
- ✅ ICA artifact removal
- ✅ Band power analysis
- ✅ WebSocket streaming to frontend
- ✅ Live visualization
- ✅ Session recording
- ✅ AI Copilot integration
- 🚧 Advanced state classification
- 🚧 Meditation guidance system

## License

Proprietary - All rights reserved

## Contact

Miron Puzanov - mironpuzanov@github

---

Built with ❤️ for consciousness exploration
