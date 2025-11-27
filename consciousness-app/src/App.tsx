import { useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { MuseConnection } from './components/MuseConnection';
import { LiveEEGDisplay } from './components/LiveEEGDisplay';
import { EEGWaveform } from './components/EEGWaveform';
import { BandPowerDisplay } from './components/BandPowerDisplay';
import { HRVDisplay } from './components/HRVDisplay';
import { ArtifactStatus } from './components/ArtifactStatus';
import { ICAStatus } from './components/ICAStatus';
import { PostureDisplay } from './components/PostureDisplay';
import { SessionRecording } from './components/SessionRecording';
import { BandWaveGraph } from './components/BandWaveGraph';
import { Button } from './components/ui/button';
import { ConnectionStatus } from './types/muse';
import { AICopilot } from './components/AICopilot';

function App() {
  const { status, deviceInfo, eegData, eegHistory, bandPowers, bandPowerHistory, brainState, heartRate, hrvRmssd, hrvSdnn, icaStatus, artifactInfo, hrvInterpretation, postureInterpretation, bandChangeInterpretation, comprehensiveState, error, connect, disconnect } = useWebSocket();
  const [showDebug, setShowDebug] = useState(false);
  const [view, setView] = useState<'eeg' | 'copilot'>('eeg');

  return (
    <div className="min-h-screen bg-zinc-50 p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-4xl font-bold text-zinc-900">Consciousness OS</h1>
            <p className="text-zinc-600 mt-2">
              {view === 'eeg'
                ? 'EEG Brain Monitoring & Analysis'
                : 'AI Mental Health Co-Pilot'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex rounded-full bg-zinc-200 p-1">
              <Button
                variant={view === 'eeg' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setView('eeg')}
              >
                EEG Dashboard
              </Button>
              <Button
                variant={view === 'copilot' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setView('copilot')}
              >
                AI Co-Pilot
              </Button>
            </div>
            {view === 'eeg' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDebug(!showDebug)}
              >
                {showDebug ? 'Hide Debug' : 'Show Debug'}
              </Button>
            )}
          </div>
        </header>

        {view === 'eeg' ? (
          <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-6">
                <MuseConnection
                  status={status}
                  deviceInfo={deviceInfo}
                  error={error}
                  onConnect={connect}
                  onDisconnect={disconnect}
                />
                <HRVDisplay
                  heartRate={heartRate}
                  hrvRmssd={hrvRmssd}
                  hrvSdnn={hrvSdnn}
                  hrvInterpretation={hrvInterpretation}
                />
                <SessionRecording isConnected={status === ConnectionStatus.CONNECTED} />
              </div>
              <div className="lg:col-span-2">
                <BandPowerDisplay bandPowers={bandPowers} brainState={brainState} bandChangeInterpretation={bandChangeInterpretation} comprehensiveState={comprehensiveState} />
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-3 items-start">
              <div className="lg:col-span-2">
                <BandWaveGraph bandPowerHistory={bandPowerHistory} />
              </div>

              <div className="space-y-6">
                <PostureDisplay postureInterpretation={postureInterpretation} />
                <ICAStatus icaStatus={icaStatus} />
                <ArtifactStatus artifactInfo={artifactInfo} />
              </div>
            </div>

            {showDebug && (
              <>
                <LiveEEGDisplay eegData={eegData} />
                <EEGWaveform eegHistory={eegHistory} />
              </>
            )}
          </div>
        ) : (
          <AICopilot isEEGConnected={status === ConnectionStatus.CONNECTED} />
        )}

        <footer className="mt-12 text-center text-sm text-zinc-500">
          <p>Phase 1: Research & Validation - Connect mind, conversation, and insight.</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
