import { Brain, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface ICAStatusProps {
  icaStatus: { fitted: boolean; progress: number } | null;
}

export const ICAStatus = ({ icaStatus }: ICAStatusProps) => {
  if (!icaStatus) {
    return null;
  }

  const { fitted, progress } = icaStatus;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-6 h-6" />
          ICA Calibration
        </CardTitle>
        <CardDescription>
          Independent Component Analysis for artifact removal
        </CardDescription>
      </CardHeader>
      <CardContent>
        {fitted ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-green-600">
              <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
              <span className="font-medium">ICA Active</span>
            </div>
            <p className="text-sm text-zinc-600">
              Artifacts are being automatically removed from your signal
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span className="text-sm font-medium">Calibrating ICA...</span>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-zinc-600">
                <span>Collecting data for artifact removal</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
            <p className="text-xs text-zinc-500">
              Please remain still for <span className="font-bold text-blue-600">{Math.max(0, 30 - Math.floor(progress * 0.3))}</span> more seconds...
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

