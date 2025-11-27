import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Brain } from 'lucide-react';
import type { BandPowers } from '../types/muse';
import { BANDS } from '../utils/signalProcessing';

interface BandPowerDisplayProps {
  bandPowers: BandPowers | null;
  brainState?: string;
  bandChangeInterpretation?: string;
  comprehensiveState?: any;
}

export const BandPowerDisplay = ({ bandPowers, brainState, bandChangeInterpretation, comprehensiveState }: BandPowerDisplayProps) => {

  // Transform for chart - use useMemo to prevent recalculation
  const chartData = useMemo(() => {
    if (!bandPowers) return [];
    return [
      { name: 'Delta', power: bandPowers.delta, color: BANDS.delta.color },
      { name: 'Theta', power: bandPowers.theta, color: BANDS.theta.color },
      { name: 'Alpha', power: bandPowers.alpha, color: BANDS.alpha.color },
      { name: 'Beta', power: bandPowers.beta, color: BANDS.beta.color },
      { name: 'Gamma', power: bandPowers.gamma, color: BANDS.gamma.color },
    ];
  }, [bandPowers]);

  // Map backend brain state to display - use useMemo
  const brainStateDisplay = useMemo(() => {
    if (!brainState) {
      return { state: 'Waiting for data...', color: 'text-zinc-500' };
    }

    const stateMap: Record<string, { state: string; color: string }> = {
      'relaxed': { state: '😌 Relaxed', color: 'text-green-600' },
      'focused': { state: '🧠 Focused', color: 'text-blue-600' },
      'creative': { state: '🎨 Creative', color: 'text-purple-600' },
      'drowsy': { state: '😴 Drowsy', color: 'text-zinc-600' },
      'peak_focus': { state: '⚡ Peak Focus', color: 'text-indigo-600' },
      'mixed': { state: '🔄 Mixed', color: 'text-amber-600' },
      'unknown': { state: '⏳ Analyzing...', color: 'text-zinc-500' },
    };

    return stateMap[brainState] || { state: brainState, color: 'text-zinc-600' };
  }, [brainState]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-6 h-6" />
          Frequency Band Analysis
        </CardTitle>
        <CardDescription>
          Distribution of brainwave frequencies
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Brain State Indicator - Fixed height */}
          <div className="text-center p-4 bg-zinc-50 rounded-lg min-h-[100px] flex flex-col justify-center">
            <div className="text-sm text-zinc-600 mb-1">Current State</div>
            <div className={`text-2xl font-bold ${brainStateDisplay.color}`}>
              {brainStateDisplay.state}
            </div>
            {bandChangeInterpretation && bandChangeInterpretation !== "Brain activity is stable" && (
              <div className="text-xs text-blue-600 mt-2 pt-2 border-t border-zinc-200">
                {bandChangeInterpretation}
              </div>
            )}
          </div>

          {/* Band Power Chart */}
          {chartData.length === 0 ? (
            <div className="text-center text-zinc-500 py-8">
              Connect to Muse and wait for backend processing
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis
                  label={{ value: 'Power (%)', angle: -90, position: 'insideLeft' }}
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e4e4e7',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Bar dataKey="power" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}

          {/* Band Info */}
          <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600">
            <div><span className="font-medium">Delta (0.5-4 Hz):</span> Deep sleep</div>
            <div><span className="font-medium">Theta (4-8 Hz):</span> Meditation</div>
            <div><span className="font-medium">Alpha (8-13 Hz):</span> Relaxed</div>
            <div><span className="font-medium">Beta (13-30 Hz):</span> Focused</div>
            <div className="col-span-2"><span className="font-medium">Gamma (30-50 Hz):</span> Peak concentration</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
