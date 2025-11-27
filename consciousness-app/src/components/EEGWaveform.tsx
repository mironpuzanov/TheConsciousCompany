import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { TrendingUp } from 'lucide-react';
import type { EEGReading } from '../types/muse';

interface EEGWaveformProps {
  eegHistory: EEGReading[];
}

const CHANNEL_LABELS = ['TP9', 'AF7', 'AF8', 'TP10'];
const CHANNEL_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']; // blue, green, amber, red

export const EEGWaveform = ({ eegHistory }: EEGWaveformProps) => {
  // Smooth the data using moving average for better visualization
  const smoothData = useMemo(() => {
    if (!eegHistory || eegHistory.length === 0) return [];
    
    const windowSize = 3; // Smooth over 3 samples
    const smoothed: typeof eegHistory = [];
    
    for (let i = 0; i < eegHistory.length; i++) {
      const start = Math.max(0, i - Math.floor(windowSize / 2));
      const end = Math.min(eegHistory.length, i + Math.ceil(windowSize / 2));
      const window = eegHistory.slice(start, end);
      
      const avgData = eegHistory[0].data.map((_, chIdx) => {
        const sum = window.reduce((acc, reading) => acc + reading.data[chIdx], 0);
        return sum / window.length;
      });
      
      smoothed.push({
        timestamp: eegHistory[i].timestamp,
        data: avgData
      });
    }
    
    return smoothed;
  }, [eegHistory]);

  // Transform data for Recharts - use useMemo to prevent recalculation on every render
  // Limit to last 64 samples (0.25 seconds at 20 Hz update rate) to prevent browser crash
  const chartData = useMemo(() => {
    const limitedHistory = smoothData.slice(-64); // Only show last 64 points
    return limitedHistory.map((reading, index) => ({
      index,
      TP9: reading.data[0] || 0,
      AF7: reading.data[1] || 0,
      AF8: reading.data[2] || 0,
      TP10: reading.data[3] || 0,
    }));
  }, [smoothData]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-6 h-6" />
          EEG Waveforms
        </CardTitle>
        <CardDescription>
          Real-time brainwave signals from 4 electrodes
        </CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="text-center text-zinc-500 py-8">
            Connect to Muse to see waveforms
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
              <XAxis
                dataKey="index"
                hide
              />
              <YAxis
                label={{ value: 'μV', angle: -90, position: 'insideLeft' }}
                domain={['auto', 'auto']}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e4e4e7',
                  borderRadius: '6px',
                }}
                labelFormatter={() => 'EEG Signal'}
              />
              <Legend />
              {CHANNEL_LABELS.map((channel, index) => (
                <Line
                  key={channel}
                  type="monotone"
                  dataKey={channel}
                  stroke={CHANNEL_COLORS[index]}
                  dot={false}
                  strokeWidth={1.5}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};
