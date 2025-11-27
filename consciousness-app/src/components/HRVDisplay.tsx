import { Heart } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface HRVDisplayProps {
  heartRate: number;
  hrvRmssd?: number;
  hrvSdnn?: number;
  hrvInterpretation?: any;
}

export const HRVDisplay = ({ heartRate }: HRVDisplayProps) => {
  const isValid = heartRate > 0 && heartRate < 200;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Heart className="w-6 h-6 text-red-500" />
          Heart Rate
        </CardTitle>
        <CardDescription>
          Estimated from PPG sensor
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Heart Rate */}
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-sm text-zinc-600 mb-1">Heart Rate</div>
            <div className="text-4xl font-bold text-red-600">
              {isValid ? Math.round(heartRate) : '--'}
              {isValid && <span className="text-2xl text-red-400 ml-2">bpm</span>}
            </div>
          </div>

          {/* Note about accuracy */}
          {isValid && (
            <div className="text-center text-xs text-zinc-500 py-1">
              Approximate value (low PPG sample rate)
            </div>
          )}

          {!isValid && (
            <div className="text-center text-xs text-zinc-500 py-2">
              Waiting for PPG data...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

