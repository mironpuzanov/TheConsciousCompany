import { useMemo, useState } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';

type TurnInsight = {
  speaker: string;
  text: string;
  timestamp: number;
  emotions: Record<string, number>;
  psych_labels: string[];
};

type RuleHit = {
  id?: string;
  description?: string;
  action?: string;
  telemetry_key?: string;
};

type AnalysisResponse = {
  session_id: string;
  analysis: {
    turns: TurnInsight[];
    state_trace: Array<Record<string, number>>;
    rules_fired: RuleHit[];
    llm_summary?: {
      narrative?: string;
      takeaways?: string[];
      scores?: Record<string, number>;
    };
    additional_insights?: {
      ner_entities?: string[];
      stress_summary?: {
        average: number;
        peak: number;
        detections: number;
        total_turns_analyzed?: number;
        significant_stress_average?: number;
      };
      emotion_summary?: Record<string, number>;
      total_turns?: number;
      psychological_patterns?: Record<string, number>;
    };
  };
};

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function ConversationInsights() {
  const [title, setTitle] = useState('');
  const [transcript, setTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transcript.trim()) {
      setError('Transcript cannot be empty.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/conversation/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          transcript,
        }),
      });
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      const data = (await response.json()) as AnalysisResponse;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const primaryEmotion = useMemo(() => {
    if (!result?.analysis.turns.length) return null;
    const aggregated: Record<string, number> = {};
    let total = 0;
    result.analysis.turns.forEach((turn) => {
      Object.entries(turn.emotions || {}).forEach(([label, score]) => {
        aggregated[label] = (aggregated[label] || 0) + score;
        total += score;
      });
    });
    // Normalize to percentages
    return Object.entries(aggregated)
      .map(([label, score]) => [label, total > 0 ? (score / total) * 100 : 0])
      .sort((a, b) => (b[1] as number) - (a[1] as number))
      .slice(0, 5);
  }, [result]);

  const psychologicalLabels = useMemo(() => {
    if (!result?.analysis.turns.length) return null;
    const aggregated: Record<string, number> = {};
    result.analysis.turns.forEach((turn) => {
      turn.psych_labels?.forEach((label) => {
        aggregated[label] = (aggregated[label] || 0) + 1;
      });
    });
    return Object.entries(aggregated)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  }, [result]);

  const averageStress = useMemo(() => {
    if (!result?.analysis.state_trace.length) return null;
    const stressValues = result.analysis.state_trace
      .map((state) => state.values?.stress || 0)
      .filter((v) => v > 0);
    if (stressValues.length === 0) return null;
    const avg = stressValues.reduce((a, b) => a + b, 0) / stressValues.length;
    return avg;
  }, [result]);

  return (
    <div className="space-y-8">
      <Card className="p-6">
        <h2 className="text-2xl font-semibold mb-4">Upload Transcript</h2>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Title / Meeting Name</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Product sync with team..."
              className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">Transcript (text or JSON turns)</label>
            <textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              rows={6}
              className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-400 focus:outline-none"
              placeholder="Speaker: text..."
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze Conversation'}
          </Button>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </form>
      </Card>

      {result && (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold">Narrative Summary</h3>
                <p className="text-sm text-zinc-500">Session ID: {result.session_id}</p>
              </div>
              <div className="text-sm text-zinc-500">
                Scores:{' '}
                {Object.entries(result.analysis.llm_summary?.scores || {}).map(([key, value]) => (
                  <span key={key} className="mr-3 capitalize">
                    {key}: {value ?? 0}
                  </span>
                ))}
              </div>
            </div>
            <p className="mt-4 text-zinc-800 leading-relaxed">{result.analysis.llm_summary?.narrative || 'No summary returned.'}</p>
          </Card>

          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Top Emotions</h3>
              {primaryEmotion?.length ? (
                <div className="space-y-2">
                  {primaryEmotion.map(([label, score]) => (
                    <div key={label} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-zinc-700">{label}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-zinc-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{ width: `${Math.min(score as number, 100)}%` }}
                          />
                        </div>
                        <span className="text-zinc-600 font-mono text-xs">{(score as number).toFixed(1)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500">No emotion data.</p>
              )}
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Psychological Patterns</h3>
              {psychologicalLabels?.length ? (
                <div className="space-y-2">
                  {psychologicalLabels.map(([label, count]) => (
                    <div key={label} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-zinc-700">{label.replace('-', ' ')}</span>
                      <span className="text-zinc-600 font-mono text-xs">
                        {count} {count === 1 ? 'turn' : 'turns'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500">No patterns detected.</p>
              )}
              {averageStress !== null && (
                <div className="mt-4 pt-4 border-t border-zinc-200">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-700">Average Stress</span>
                    <span className="text-zinc-600 font-mono text-xs">{(averageStress * 100).toFixed(1)}%</span>
                  </div>
                </div>
              )}
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Insights & Rules</h3>
                <button
                  onClick={() => setShowRules(!showRules)}
                  className="text-xs text-zinc-500 hover:text-zinc-700"
                >
                  {showRules ? 'Hide' : 'Show'} ({result.analysis.rules_fired.length})
                </button>
              </div>
              {showRules && (
                <div className="text-xs text-zinc-500 space-y-2 max-h-64 overflow-y-auto">
                  {result.analysis.rules_fired.length ? (
                    <ul className="space-y-2">
                      {result.analysis.rules_fired.map((rule, idx) => (
                        <li key={idx} className="p-2 bg-zinc-50 rounded text-zinc-600">
                          <span className="font-medium">{rule.description || rule.telemetry_key}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No specific patterns triggered.</p>
                  )}
                  <p className="text-xs text-zinc-400 mt-4 italic">
                    These are technical rule detections stored for analysis. Not meant for direct interpretation.
                  </p>
                </div>
              )}
            </Card>
          </div>

          {result.analysis.additional_insights && (
            <div className="grid gap-6 lg:grid-cols-2">
              {result.analysis.additional_insights.ner_entities && result.analysis.additional_insights.ner_entities.length > 0 && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Key Entities & Topics</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.analysis.additional_insights.ner_entities.map((entity, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium"
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </Card>
              )}

              {result.analysis.additional_insights.stress_summary && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Stress Analysis</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-zinc-700">Average Stress Level</span>
                        <p className="text-xs text-zinc-500">From stress detection model</p>
                      </div>
                      <span className="font-mono text-zinc-600">
                        {(result.analysis.additional_insights.stress_summary.average * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-zinc-700">Peak Stress Moment</span>
                        <p className="text-xs text-zinc-500">Highest detected stress</p>
                      </div>
                      <span className="font-mono text-zinc-600">
                        {(result.analysis.additional_insights.stress_summary.peak * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-zinc-700">Turns with Significant Stress</span>
                        <p className="text-xs text-zinc-500">Stress level &gt; 50% (out of {result.analysis.additional_insights.total_turns || result.analysis.additional_insights.stress_summary.total_turns_analyzed || 'N/A'} total)</p>
                      </div>
                      <span className="font-mono text-zinc-600">
                        {result.analysis.additional_insights.stress_summary.detections}
                      </span>
                    </div>
                    {result.analysis.additional_insights.stress_summary.significant_stress_average > 0 && (
                      <div className="flex justify-between items-center mt-2 pt-2 border-t border-zinc-200">
                        <div>
                          <span className="text-zinc-700 text-xs">Avg. Significant Stress</span>
                        </div>
                        <span className="font-mono text-zinc-600 text-xs">
                          {(result.analysis.additional_insights.stress_summary.significant_stress_average * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-zinc-400 mt-4 italic">
                    Note: "Psychological Patterns" shows stress from zero-shot model (different metric). This shows stress from dedicated stress detection model.
                  </p>
                </Card>
              )}
            </div>
          )}

          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Turn Timeline</h3>
              <button
                onClick={() => setShowTimeline(!showTimeline)}
                className="text-xs text-zinc-500 hover:text-zinc-700"
              >
                {showTimeline ? 'Hide' : 'Show'} ({result.analysis.turns.length} turns)
              </button>
            </div>
            {showTimeline && (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {result.analysis.turns.map((turn, idx) => (
                  <div key={idx} className="border-b border-zinc-100 pb-3 last:border-none last:pb-0">
                    <div className="flex items-center justify-between text-xs text-zinc-500">
                      <span className="font-medium text-zinc-700">{turn.speaker || 'Unknown'}</span>
                      <span>{turn.timestamp?.toFixed(1)}s</span>
                    </div>
                    <p className="text-sm text-zinc-800 mt-1">{turn.text}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-600">
                      {Object.entries(turn.emotions || {})
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 2)
                        .filter(([_, score]) => score > 0.3)  // Only show significant emotions
                        .map(([label, score]) => (
                          <span key={label} className="rounded-full bg-zinc-200 px-2 py-0.5">
                            {label}: {score.toFixed(2)}
                          </span>
                        ))}
                      {turn.psych_labels?.length
                        ? turn.psych_labels.map((label) => (
                            <span key={label} className="rounded-full bg-slate-100 px-2 py-0.5">
                              {label}
                            </span>
                          ))
                        : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {!showTimeline && (
              <p className="text-sm text-zinc-500 italic">Click "Show" to view detailed turn-by-turn analysis</p>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

