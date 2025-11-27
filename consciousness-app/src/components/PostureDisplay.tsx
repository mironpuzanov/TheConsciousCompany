import { Move } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface PostureDisplayProps {
  postureInterpretation?: any;
}

export const PostureDisplay = ({ postureInterpretation }: PostureDisplayProps) => {
  const statusColors: Record<string, string> = {
    'Good': 'text-green-600 bg-green-50 border-green-200',
    'Slight tilt': 'text-amber-600 bg-amber-50 border-amber-200',
    'Forward tilt': 'text-orange-600 bg-orange-50 border-orange-200',
    'Backward tilt': 'text-orange-600 bg-orange-50 border-orange-200',
    'Side tilt': 'text-orange-600 bg-orange-50 border-orange-200',
    'Moving': 'text-blue-600 bg-blue-50 border-blue-200',
    'Still': 'text-green-600 bg-green-50 border-green-200',
    'Unstable': 'text-red-600 bg-red-50 border-red-200',
  };

  const hasData = postureInterpretation && postureInterpretation.status;
  const status = hasData ? postureInterpretation.status : 'Waiting...';
  const isAnalyzing = status === 'Analyzing...' || status === 'No posture data';
  
  const colorClass = hasData && !isAnalyzing
    ? (statusColors[status] || 'text-zinc-600 bg-zinc-50 border-zinc-200')
    : 'text-zinc-500 bg-zinc-50 border-zinc-200';

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Move className="w-5 h-5 text-zinc-600" />
          Posture
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`p-4 rounded-lg border ${colorClass} h-[60px] flex items-center justify-center`}>
          <div className="text-base font-semibold">
            {status}
          </div>
        </div>
        {hasData && postureInterpretation.meaning && !isAnalyzing && (
          <div className="text-xs text-zinc-500 mt-2 text-center">
            {postureInterpretation.meaning}
          </div>
        )}
      </CardContent>
    </Card>
  );
};


