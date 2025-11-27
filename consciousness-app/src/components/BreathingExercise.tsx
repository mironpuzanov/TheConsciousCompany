import { useState, useEffect } from 'react';
import { Button } from './ui/button';

interface BreathingExerciseProps {
  isOpen: boolean;
  onClose: () => void;
}

export function BreathingExercise({ isOpen, onClose }: BreathingExerciseProps) {
  const [phase, setPhase] = useState<'inhale' | 'hold' | 'exhale'>('inhale');
  const [count, setCount] = useState(4);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    if (!isOpen || !isActive) return;

    const interval = setInterval(() => {
      setCount((prev) => {
        if (prev === 1) {
          // Move to next phase
          setPhase((currentPhase) => {
            if (currentPhase === 'inhale') return 'hold';
            if (currentPhase === 'hold') return 'exhale';
            return 'inhale';
          });
          return 4;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen, isActive]);

  const start = () => {
    setIsActive(true);
    setPhase('inhale');
    setCount(4);
  };

  const stop = () => {
    setIsActive(false);
    setPhase('inhale');
    setCount(4);
  };

  if (!isOpen) return null;

  const getPhaseInstruction = () => {
    switch (phase) {
      case 'inhale':
        return 'Breathe In';
      case 'hold':
        return 'Hold';
      case 'exhale':
        return 'Breathe Out';
    }
  };

  const getPhaseColor = () => {
    switch (phase) {
      case 'inhale':
        return 'from-blue-400 to-blue-600';
      case 'hold':
        return 'from-purple-400 to-purple-600';
      case 'exhale':
        return 'from-green-400 to-green-600';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold text-zinc-900">Breathing Exercise</h2>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Breathing Circle */}
        <div className="flex flex-col items-center justify-center mb-8">
          <div
            className={`relative w-48 h-48 rounded-full bg-gradient-to-br ${getPhaseColor()}
            flex items-center justify-center transition-all duration-1000 ${
              isActive
                ? phase === 'inhale'
                  ? 'scale-110'
                  : phase === 'exhale'
                  ? 'scale-90'
                  : 'scale-100'
                : 'scale-100'
            }`}
          >
            <div className="text-center">
              <p className="text-white text-2xl font-bold mb-2">{getPhaseInstruction()}</p>
              {isActive && (
                <p className="text-white text-5xl font-bold">{count}</p>
              )}
            </div>
          </div>

          {isActive && (
            <p className="text-zinc-600 mt-4 text-sm">
              4-4-4 breathing pattern: Reduces stress and anxiety
            </p>
          )}
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          {!isActive ? (
            <Button
              onClick={start}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white"
            >
              Start Exercise
            </Button>
          ) : (
            <Button
              onClick={stop}
              className="flex-1 bg-red-500 hover:bg-red-600 text-white"
            >
              Stop
            </Button>
          )}
          <Button
            onClick={onClose}
            variant="outline"
            className="flex-1"
          >
            Close
          </Button>
        </div>

        {/* Instructions */}
        <div className="mt-6 p-4 bg-zinc-50 rounded-lg">
          <p className="text-sm text-zinc-600">
            <strong>How it works:</strong> Follow the circle as it expands and contracts. Inhale
            for 4 seconds, hold for 4 seconds, then exhale for 4 seconds. This 4-4-4 breathing
            pattern activates your parasympathetic nervous system, reducing stress.
          </p>
        </div>
      </div>
    </div>
  );
}
