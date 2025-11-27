import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Activity } from 'lucide-react';

interface BandWaveGraphProps {
  bandPowerHistory: Array<{
    timestamp: number;
    delta: number;
    theta: number;
    alpha: number;
    beta: number;
    gamma: number;
  }>;
}

const BAND_COLORS = {
  delta: '#6366f1', // indigo
  theta: '#8b5cf6', // violet
  alpha: '#22c55e', // green
  beta: '#f59e0b', // amber
  gamma: '#ef4444', // red
};

export const BandWaveGraph = ({ bandPowerHistory }: BandWaveGraphProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || bandPowerHistory.length < 2) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 20, right: 20, bottom: 30, left: 50 };
    const graphWidth = width - padding.left - padding.right;
    const graphHeight = height - padding.top - padding.bottom;

    // Clear canvas
    ctx.fillStyle = '#fafafa';
    ctx.fillRect(0, 0, width, height);

    // Find max value for scaling
    let maxValue = 0;
    for (const point of bandPowerHistory) {
      maxValue = Math.max(maxValue, point.delta, point.theta, point.alpha, point.beta, point.gamma);
    }
    maxValue = Math.max(maxValue, 1) * 1.1; // Add 10% padding

    // Draw grid
    ctx.strokeStyle = '#e4e4e7';
    ctx.lineWidth = 1;

    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (graphHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Y-axis labels
      const value = maxValue * (1 - i / 4);
      ctx.fillStyle = '#71717a';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(1), padding.left - 5, y + 3);
    }

    // Draw each band
    const bands = ['delta', 'theta', 'alpha', 'beta', 'gamma'] as const;

    for (const band of bands) {
      ctx.strokeStyle = BAND_COLORS[band];
      ctx.lineWidth = 2;
      ctx.beginPath();

      for (let i = 0; i < bandPowerHistory.length; i++) {
        const x = padding.left + (i / (bandPowerHistory.length - 1)) * graphWidth;
        const y = padding.top + graphHeight - (bandPowerHistory[i][band] / maxValue) * graphHeight;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }

    // Draw legend
    const legendY = height - 10;
    let legendX = padding.left;
    ctx.font = '11px sans-serif';

    for (const band of bands) {
      ctx.fillStyle = BAND_COLORS[band];
      ctx.fillRect(legendX, legendY - 8, 12, 3);
      ctx.fillStyle = '#3f3f46';
      ctx.textAlign = 'left';
      ctx.fillText(band.charAt(0).toUpperCase() + band.slice(1), legendX + 16, legendY);
      legendX += 70;
    }

  }, [bandPowerHistory]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="w-5 h-5 text-zinc-600" />
          Brain Waves Over Time
        </CardTitle>
      </CardHeader>
      <CardContent>
        <canvas
          ref={canvasRef}
          width={700}
          height={250}
          className="w-full"
          style={{ maxHeight: '250px' }}
        />
        {bandPowerHistory.length < 2 && (
          <div className="text-center text-zinc-500 text-sm py-8">
            Collecting data...
          </div>
        )}
      </CardContent>
    </Card>
  );
};
