import { AlertCircle, CheckCircle, Eye, Activity, Move, Zap, Radio } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface ArtifactStatusProps {
  artifactInfo: {
    has_artifact: boolean;
    artifact_type: string;
    artifact_details?: {
      eye_blink?: boolean;
      muscle?: boolean;
      motion?: boolean;
      em_interference?: boolean;
      poor_contact?: boolean;
      statistical?: boolean;
      bad_channels?: number[];
      channel_names?: string[];
    };
  } | null;
}

const ARTIFACT_ICONS: Record<string, any> = {
  eye_blink: Eye,
  muscle: Activity,
  motion: Move,
  em_interference: Zap,
  poor_contact: Radio,
  statistical: AlertCircle,
  clean: CheckCircle,
};

const ARTIFACT_LABELS: Record<string, string> = {
  eye_blink: 'Eye Blink',
  muscle: 'Muscle Artifact',
  motion: 'Head Movement',
  em_interference: 'EM Interference',
  poor_contact: 'Poor Contact',
  statistical: 'Statistical Anomaly',
  clean: 'Clean Signal',
};

const ARTIFACT_COLORS: Record<string, string> = {
  eye_blink: 'text-blue-600',
  muscle: 'text-orange-600',
  motion: 'text-purple-600',
  em_interference: 'text-yellow-600',
  poor_contact: 'text-red-600',
  statistical: 'text-amber-600',
  clean: 'text-green-600',
};

export const ArtifactStatus = ({ artifactInfo }: ArtifactStatusProps) => {
  if (!artifactInfo) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-6 h-6" />
            Artifact Detection
          </CardTitle>
          <CardDescription>
            Signal quality and artifact status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center text-zinc-500 py-4">
            Waiting for data...
          </div>
        </CardContent>
      </Card>
    );
  }

  const { has_artifact, artifact_type, artifact_details } = artifactInfo;
  const Icon = ARTIFACT_ICONS[artifact_type] || AlertCircle;
  const label = ARTIFACT_LABELS[artifact_type] || artifact_type;
  const color = ARTIFACT_COLORS[artifact_type] || 'text-zinc-600';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-6 h-6" />
          Artifact Detection
        </CardTitle>
        <CardDescription>
          Signal quality and artifact status
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Main Status */}
          <div className={`text-center p-4 rounded-lg ${has_artifact ? 'bg-amber-50' : 'bg-green-50'}`}>
            <div className="flex items-center justify-center gap-2 mb-2">
              <Icon className={`w-6 h-6 ${color}`} />
              <div className={`text-xl font-bold ${color}`}>
                {label}
              </div>
            </div>
            <div className="text-sm text-zinc-600">
              {has_artifact ? 'Artifacts detected - classification may be inaccurate' : 'Clean signal - ready for analysis'}
            </div>
          </div>

          {/* Bad Channels */}
          {artifact_details?.bad_channels && artifact_details.bad_channels.length > 0 && (
            <div className="p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="text-xs font-semibold text-red-900 mb-1">⚠️ Bad Channels Detected:</div>
              <div className="text-sm text-red-700">
                {artifact_details.bad_channels.map((chIdx, i) => {
                  const channelName = artifact_details?.channel_names?.[chIdx] || `Channel ${chIdx}`;
                  return (
                    <span key={chIdx}>
                      {channelName}
                      {i < artifact_details.bad_channels!.length - 1 ? ', ' : ''}
                    </span>
                  );
                })}
              </div>
              <div className="text-xs text-red-600 mt-1">
                Check electrode contact - these channels have extreme values
              </div>
            </div>
          )}

          {/* Artifact Details */}
          {artifact_details && (
            <div className="space-y-2">
              <div className="text-xs font-medium text-zinc-700 mb-2">Detection Details:</div>
              {Object.entries(artifact_details).map(([key, value]) => {
                // Skip non-boolean fields
                if (typeof value !== 'boolean' || key === 'poor_contact' && artifact_details.bad_channels && artifact_details.bad_channels.length > 0) {
                  return null; // Skip poor_contact if we're showing bad_channels
                }
                const DetailIcon = ARTIFACT_ICONS[key] || AlertCircle;
                const detailLabel = ARTIFACT_LABELS[key] || key;
                const detailColor = value ? ARTIFACT_COLORS[key] || 'text-red-600' : 'text-zinc-400';
                
                return (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <DetailIcon className={`w-4 h-4 ${detailColor}`} />
                      <span className="text-zinc-700">{detailLabel}</span>
                    </div>
                    <span className={value ? 'text-red-600 font-medium' : 'text-zinc-400'}>
                      {value ? 'Detected' : 'Clear'}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

