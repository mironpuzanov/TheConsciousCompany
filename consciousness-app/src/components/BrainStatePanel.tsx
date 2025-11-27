import type { BrainState, TextFeatures } from '../types/copilot';

interface BrainStatePanelProps {
  brainState: BrainState | null;
  textFeatures: TextFeatures | null;
  incongruence: boolean;
  shouldIntervene: boolean;
}

export function BrainStatePanel({
  brainState,
  textFeatures,
  incongruence,
  shouldIntervene,
}: BrainStatePanelProps) {
  const getStressColor = (value: number) => {
    if (value < 0.3) return 'text-green-600';
    if (value < 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStressLabel = (value: number) => {
    if (value < 0.3) return 'Low';
    if (value < 0.7) return 'Moderate';
    return 'High';
  };

  const getEmotionEmoji = (emotion: string | undefined, score?: number) => {
    if (!emotion) return '😐';

    const emojiMap: Record<string, string> = {
      joy: '😊',
      sadness: '😢',
      anger: '😠',
      fear: '😨',
      anxiety: '😰',
      surprise: '😲',
      disgust: '🤢',
      love: '❤️',
      optimism: '😄',
      pessimism: '😞',
      neutral: '😐',
      positive: '😊',
      negative: '😟',
    };

    // For neutral, vary emoji by confidence score
    if (emotion.toLowerCase() === 'neutral' && score !== undefined) {
      if (score < 0.4) return '🤔'; // Low confidence neutral
      if (score < 0.6) return '😐'; // Medium confidence neutral
      return '😶'; // High confidence neutral
    }

    return emojiMap[emotion.toLowerCase()] || '😐';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-6 h-full overflow-y-auto">
      <h2 className="text-xl font-semibold text-zinc-900">Real-Time State</h2>

      {/* Incongruence Alert */}
      {incongruence && (
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-2">⚠️</span>
            <div>
              <p className="font-semibold text-yellow-900">Incongruence Detected</p>
              <p className="text-sm text-yellow-700">
                Your words don't match your brain activity
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Intervention Alert */}
      {shouldIntervene && (
        <div className="bg-red-50 border-2 border-red-400 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-2">🚨</span>
            <div>
              <p className="font-semibold text-red-900">High Stress Detected</p>
              <p className="text-sm text-red-700">Consider taking a break or breathing exercise</p>
            </div>
          </div>
        </div>
      )}

      {/* Brain State */}
      <div className="space-y-4">
        <h3 className="font-semibold text-zinc-700">Brain Activity</h3>

        {brainState ? (
          <>
            {/* Stress Level */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-zinc-700">Stress</span>
                <span className={`text-sm font-semibold ${getStressColor(brainState.stress)}`}>
                  {getStressLabel(brainState.stress)} ({Math.round(brainState.stress * 100)}%)
                </span>
              </div>
              <div className="w-full bg-zinc-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    brainState.stress < 0.3
                      ? 'bg-green-500'
                      : brainState.stress < 0.7
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${brainState.stress * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Cognitive Load */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-zinc-700">Cognitive Load</span>
                <span className="text-sm font-semibold text-zinc-900">
                  {Math.round(brainState.cognitive_load * 100)}%
                </span>
              </div>
              <div className="w-full bg-zinc-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${brainState.cognitive_load * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Heart Rate */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-zinc-700">Heart Rate</span>
              <span className="text-lg font-semibold text-red-500">
                ❤️ {brainState.hr} bpm
              </span>
            </div>

            {/* Emotion Arousal */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-zinc-700">Emotional Arousal</span>
                <span className="text-sm font-semibold text-zinc-900">
                  {Math.round(brainState.emotion_arousal * 100)}%
                </span>
              </div>
              <div className="w-full bg-zinc-200 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full"
                  style={{ width: `${brainState.emotion_arousal * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Band Powers */}
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="text-center">
                <p className="text-xs text-zinc-500">Alpha</p>
                <p className="text-sm font-semibold">{Math.round(brainState.alpha)}%</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-zinc-500">Beta</p>
                <p className="text-sm font-semibold">{Math.round(brainState.beta)}%</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-zinc-500">Gamma</p>
                <p className="text-sm font-semibold">{Math.round(brainState.gamma)}%</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-zinc-500">Theta</p>
                <p className="text-sm font-semibold">{Math.round(brainState.theta)}%</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-zinc-500">Delta</p>
                <p className="text-sm font-semibold">{Math.round(brainState.delta)}%</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-zinc-500">EMG</p>
                <p className="text-sm font-semibold">
                  {Math.round(brainState.emg_intensity * 100)}%
                </p>
              </div>
            </div>
          </>
        ) : (
          <p className="text-sm text-zinc-400">No brain data available</p>
        )}
      </div>

      {/* Text Analysis */}
      <div className="space-y-3 pt-4 border-t border-zinc-200">
        <h3 className="font-semibold text-zinc-700">Speech Analysis</h3>

        {textFeatures ? (
          <>
            {/* Sentiment */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-zinc-700">Sentiment</span>
              <span className="text-sm font-semibold">
                {getEmotionEmoji(textFeatures.sentiment.label, textFeatures.sentiment.score)} {textFeatures.sentiment.label}{' '}
                ({Math.round(textFeatures.sentiment.score * 100)}%)
              </span>
            </div>

            {/* Emotion */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-zinc-700">Emotion</span>
              <span className="text-sm font-semibold">
                {getEmotionEmoji(textFeatures.emotion.label, textFeatures.emotion.score)} {textFeatures.emotion.label}{' '}
                ({Math.round(textFeatures.emotion.score * 100)}%)
              </span>
            </div>

            {/* Topics */}
            {textFeatures.topics.length > 0 && (
              <div>
                <span className="text-sm font-medium text-zinc-700">Topics</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {textFeatures.topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-zinc-100 text-zinc-700 text-xs rounded-full"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Psychological Patterns */}
            {textFeatures.psychological_labels && Object.keys(textFeatures.psychological_labels).length > 0 && (
              <div>
                <span className="text-sm font-medium text-zinc-700">Psychological Patterns</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {Object.entries(textFeatures.psychological_labels)
                    .filter(([_, score]) => score > 0.5)
                    .sort(([_, a], [__, b]) => b - a)
                    .slice(0, 3)
                    .map(([label, score], idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
                        title={`${Math.round(score * 100)}%`}
                      >
                        {label} ({Math.round(score * 100)}%)
                      </span>
                    ))}
                </div>
              </div>
            )}

            {/* Stress Indicators */}
            {textFeatures.stress_indicators && Object.keys(textFeatures.stress_indicators).length > 0 && (
              <div>
                <span className="text-sm font-medium text-zinc-700">Stress Indicators</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {Object.entries(textFeatures.stress_indicators)
                    .filter(([_, score]) => score > 0.5)
                    .sort(([_, a], [__, b]) => b - a)
                    .slice(0, 2)
                    .map(([label, score], idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full"
                        title={`${Math.round(score * 100)}%`}
                      >
                        {label.split(':')[1] || label} ({Math.round(score * 100)}%)
                      </span>
                    ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-zinc-400">No speech data available</p>
        )}
      </div>
    </div>
  );
}
