import { Activity } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import type { EEGReading } from '../types/muse';

interface LiveEEGDisplayProps {
  eegData: EEGReading | null;
}

const CHANNEL_LABELS = [
  'TP9 (Left Ear)',
  'AF7 (Left Forehead)',
  'AF8 (Right Forehead)',
  'TP10 (Right Ear)',
];

export const LiveEEGDisplay = ({ eegData }: LiveEEGDisplayProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-6 h-6" />
          Live EEG Data
        </CardTitle>
        <CardDescription>
          Real-time brainwave readings from 4 channels
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!eegData ? (
          <div className="text-center text-zinc-500 py-8">
            Connect to Muse to see live EEG data
          </div>
        ) : (
          <div className="space-y-3">
            {eegData.data.map((value, index) => (
              <div key={index} className="space-y-1">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium text-zinc-700">{CHANNEL_LABELS[index]}</span>
                  <span className="text-zinc-600 font-mono">{value.toFixed(2)} μV</span>
                </div>
                <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-100"
                    style={{
                      width: `${Math.min(Math.abs(value) / 10, 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}

            <div className="text-xs text-zinc-500 pt-2">
              Last updated: {new Date(eegData.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
