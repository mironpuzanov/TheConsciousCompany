import { Bluetooth, BluetoothOff, Activity } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ConnectionStatus } from '../types/muse';
import type { MuseDeviceInfo } from '../types/muse';

interface MuseConnectionProps {
  status: ConnectionStatus;
  deviceInfo: MuseDeviceInfo | null;
  error: string | null;
  onConnect: () => void;
  onDisconnect: () => void;
}

export const MuseConnection = ({
  status,
  deviceInfo,
  error,
  onConnect,
  onDisconnect,
}: MuseConnectionProps) => {
  const isConnected = status === ConnectionStatus.CONNECTED;
  const isConnecting = status === ConnectionStatus.CONNECTING;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isConnected ? <Bluetooth className="w-6 h-6 text-blue-500" /> : <BluetoothOff className="w-6 h-6" />}
          Muse Connection
        </CardTitle>
        <CardDescription>
          {isConnected ? 'Connected to your Muse headband' : 'Connect to your Muse 2 headband via Bluetooth'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Button
            onClick={isConnected ? onDisconnect : onConnect}
            disabled={isConnecting}
            variant={isConnected ? 'outline' : 'default'}
          >
            {isConnecting ? 'Connecting...' : isConnected ? 'Disconnect' : 'Connect to Muse'}
          </Button>

          {status === ConnectionStatus.CONNECTED && (
            <div className="flex items-center gap-2 text-green-600">
              <Activity className="w-4 h-4 animate-pulse" />
              <span className="text-sm font-medium">Live</span>
            </div>
          )}
        </div>

        {deviceInfo && (
          <div className="text-sm text-zinc-600">
            <p>Device: {deviceInfo.name}</p>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
            <p className="font-medium">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {!isConnected && !error && (
          <div className="text-xs text-zinc-500 bg-zinc-50 p-3 rounded-md">
            <p className="font-medium mb-1">Note:</p>
            <p>Make sure:</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Python backend is running (python backend/main.py)</li>
              <li>Muse headband is turned on</li>
              <li>Run: <code className="bg-zinc-200 px-1 rounded">muselsl stream --ppg --acc --gyro</code></li>
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
