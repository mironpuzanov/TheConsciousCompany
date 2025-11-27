"""
Session Brain Data Analyzer
Provides detailed insights from recorded EEG sessions
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import sys


class SessionAnalyzer:
    """Analyze recorded EEG session data for brain insights"""

    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.metadata = self._load_json('metadata.json')
        self.summary = self._load_json('summary.json')
        self.processed = self._load_json('processed.json')
        self.events = self._load_json('events.json')

    def _load_json(self, filename: str):
        """Load JSON file from session directory"""
        path = self.session_path / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def get_basic_info(self) -> Dict:
        """Get basic session information"""
        return {
            'session_id': self.metadata['session_id'],
            'name': self.metadata.get('name', 'Unnamed Session'),
            'duration_minutes': self.metadata['duration_seconds'] / 60,
            'start_time': datetime.fromisoformat(self.metadata['start_time']),
            'total_samples': len(self.processed),
            'sample_rate': self.metadata['sample_rate'],
        }

    def analyze_brain_states(self) -> Dict:
        """Analyze brain state transitions and patterns"""
        states = [s['brain_state'] for s in self.processed]

        # Count transitions
        transitions = []
        for i in range(1, len(states)):
            if states[i] != states[i-1]:
                transitions.append({
                    'from': states[i-1],
                    'to': states[i],
                    'time': self.processed[i]['local_time']
                })

        # State durations
        state_durations = {}
        current_state = states[0]
        duration = 1

        for state in states[1:]:
            if state == current_state:
                duration += 1
            else:
                if current_state not in state_durations:
                    state_durations[current_state] = []
                state_durations[current_state].append(duration)
                current_state = state
                duration = 1

        return {
            'dominant_state': self.summary['dominant_state'],
            'distribution': self.summary['brain_state_distribution'],
            'transitions': len(transitions),
            'transition_events': transitions[:10],  # First 10 transitions
            'avg_duration_per_state': {
                state: np.mean(durations) for state, durations in state_durations.items()
            }
        }

    def analyze_band_powers(self) -> Dict:
        """Detailed analysis of brain wave bands"""
        bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
        band_data = {band: [s['band_powers'][band] for s in self.processed] for band in bands}

        analysis = {}
        for band, values in band_data.items():
            analysis[band] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values),
                'percentile_25': np.percentile(values, 25),
                'percentile_75': np.percentile(values, 75),
            }

        # Find dominant frequency patterns
        avg_powers = {band: np.mean(values) for band, values in band_data.items()}
        sorted_bands = sorted(avg_powers.items(), key=lambda x: x[1], reverse=True)

        return {
            'detailed_stats': analysis,
            'dominant_frequencies': sorted_bands,
            'balance': self._assess_band_balance(avg_powers)
        }

    def _assess_band_balance(self, powers: Dict) -> str:
        """Assess overall brain wave balance"""
        if powers['gamma'] > 50:
            return "High artifact/noise detected - check electrode contact"
        elif powers['delta'] > 40:
            return "Deep relaxation or drowsiness - high slow-wave activity"
        elif powers['theta'] > 20:
            return "Meditative state - elevated theta activity"
        elif powers['alpha'] > 30:
            return "Relaxed awareness - strong alpha rhythm"
        elif powers['beta'] > 30:
            return "Active thinking - elevated beta activity"
        else:
            return "Balanced state - no single frequency dominates"

    def analyze_cognitive_load(self) -> Dict:
        """Analyze cognitive load and mental effort"""
        beta_values = [s['band_powers']['beta'] for s in self.processed]
        forehead_emg = [s['forehead_emg'] for s in self.processed]

        # High beta + high forehead EMG = cognitive effort
        cognitive_load = []
        for i in range(len(self.processed)):
            load = (beta_values[i] / 100) * 0.5 + forehead_emg[i] * 0.5
            cognitive_load.append(load)

        return {
            'mean_cognitive_load': np.mean(cognitive_load),
            'peak_cognitive_load': np.max(cognitive_load),
            'low_load_percentage': sum(1 for l in cognitive_load if l < 0.3) / len(cognitive_load) * 100,
            'high_load_percentage': sum(1 for l in cognitive_load if l > 0.7) / len(cognitive_load) * 100,
        }

    def analyze_stress_indicators(self) -> Dict:
        """Analyze stress and tension indicators"""
        emg_intensity = [s['emg_intensity'] for s in self.processed]
        forehead_emg = [s['forehead_emg'] for s in self.processed]
        hr_values = [s['heart_rate'] for s in self.processed if s['heart_rate'] > 0]
        beta_values = [s['band_powers']['beta'] for s in self.processed]

        # Calculate stress index (0-1)
        stress_scores = []
        for i in range(len(self.processed)):
            stress = (
                emg_intensity[i] * 0.3 +  # Muscle tension
                forehead_emg[i] * 0.2 +    # Mental tension
                (beta_values[i] / 100) * 0.2  # Mental activity
            )
            stress_scores.append(min(stress, 1.0))

        return {
            'avg_muscle_tension': np.mean(emg_intensity),
            'avg_mental_tension': np.mean(forehead_emg),
            'avg_stress_score': np.mean(stress_scores),
            'stress_periods': sum(1 for s in stress_scores if s > 0.7),
            'relaxed_periods': sum(1 for s in stress_scores if s < 0.3),
            'heart_rate_avg': np.mean(hr_values) if hr_values else 0,
            'heart_rate_variability': 'Good' if np.std(hr_values) > 10 else 'Low' if hr_values else 'N/A'
        }

    def analyze_attention_focus(self) -> Dict:
        """Analyze attention and focus patterns"""
        beta_values = [s['band_powers']['beta'] for s in self.processed]
        alpha_values = [s['band_powers']['alpha'] for s in self.processed]
        blink_intensity = [s['blink_intensity'] for s in self.processed]

        # Focus = high beta, low alpha, low blink
        focus_scores = []
        for i in range(len(self.processed)):
            focus = (
                (beta_values[i] / 100) * 0.4 +
                (1 - alpha_values[i] / 100) * 0.3 +
                (1 - blink_intensity[i]) * 0.3
            )
            focus_scores.append(focus)

        return {
            'avg_focus_score': np.mean(focus_scores),
            'peak_focus': np.max(focus_scores),
            'focused_periods': sum(1 for f in focus_scores if f > 0.6),
            'unfocused_periods': sum(1 for f in focus_scores if f < 0.4),
            'blink_rate': np.mean(blink_intensity),
            'assessment': self._assess_focus(np.mean(focus_scores))
        }

    def _assess_focus(self, score: float) -> str:
        """Assess focus level from score"""
        if score > 0.7:
            return "High focus - sustained attention"
        elif score > 0.5:
            return "Moderate focus - intermittent attention"
        elif score > 0.3:
            return "Low focus - distracted state"
        else:
            return "Unfocused - relaxed or drowsy"

    def analyze_emotional_state(self) -> Dict:
        """Analyze emotional indicators from EEG"""
        alpha_values = [s['band_powers']['alpha'] for s in self.processed]
        theta_values = [s['band_powers']['theta'] for s in self.processed]
        movement = [s['movement_intensity'] for s in self.processed]
        hr_values = [s['heart_rate'] for s in self.processed if s['heart_rate'] > 0]

        # Emotional arousal = movement + HR variability
        arousal_score = np.mean(movement)

        # Valence = alpha asymmetry proxy (positive emotion)
        # (We don't have full hemisphere data, but high alpha = relaxed/positive)
        valence_score = np.mean(alpha_values) / 100

        return {
            'arousal_level': arousal_score,
            'valence_estimate': valence_score,
            'emotional_quadrant': self._get_emotional_quadrant(arousal_score, valence_score),
            'theta_meditation': np.mean(theta_values),
            'alpha_relaxation': np.mean(alpha_values),
        }

    def _get_emotional_quadrant(self, arousal: float, valence: float) -> str:
        """Map arousal/valence to emotional quadrant"""
        if arousal > 0.5 and valence > 0.5:
            return "Excited/Happy (high arousal, positive valence)"
        elif arousal > 0.5 and valence <= 0.5:
            return "Anxious/Stressed (high arousal, negative valence)"
        elif arousal <= 0.5 and valence > 0.5:
            return "Calm/Content (low arousal, positive valence)"
        else:
            return "Sad/Bored (low arousal, negative valence)"

    def analyze_talking_patterns(self) -> Dict:
        """Analyze talking and silence patterns"""
        talking_samples = sum(1 for s in self.processed if s['is_talking'])
        total_samples = len(self.processed)

        # Find talking episodes
        episodes = []
        in_episode = False
        episode_start = 0

        for i, sample in enumerate(self.processed):
            if sample['is_talking'] and not in_episode:
                in_episode = True
                episode_start = i
            elif not sample['is_talking'] and in_episode:
                in_episode = False
                episodes.append({
                    'start': episode_start,
                    'end': i,
                    'duration': i - episode_start
                })

        return {
            'talking_ratio': talking_samples / total_samples,
            'talking_duration_seconds': talking_samples,
            'silence_duration_seconds': total_samples - talking_samples,
            'talking_episodes': len(episodes),
            'avg_episode_duration': np.mean([e['duration'] for e in episodes]) if episodes else 0,
            'longest_episode': max([e['duration'] for e in episodes]) if episodes else 0,
        }

    def generate_full_report(self) -> str:
        """Generate comprehensive analysis report"""
        info = self.get_basic_info()
        brain_states = self.analyze_brain_states()
        bands = self.analyze_band_powers()
        cognitive = self.analyze_cognitive_load()
        stress = self.analyze_stress_indicators()
        attention = self.analyze_attention_focus()
        emotional = self.analyze_emotional_state()
        talking = self.analyze_talking_patterns()

        report = f"""
{'='*80}
CONSCIOUSNESS OS - SESSION BRAIN DATA ANALYSIS
{'='*80}

SESSION: {info['name']}
ID: {info['session_id']}
Date: {info['start_time'].strftime('%B %d, %Y at %I:%M %p')}
Duration: {info['duration_minutes']:.1f} minutes
Samples: {info['total_samples']} samples

{'='*80}
1. BRAIN STATE ANALYSIS
{'='*80}

Dominant State: {brain_states['dominant_state']}

State Distribution:
"""
        for state, count in brain_states['distribution'].items():
            percentage = count / info['total_samples'] * 100
            report += f"  • {state}: {count} samples ({percentage:.1f}%)\n"

        report += f"""
State Transitions: {brain_states['transitions']} transitions
Average Duration per State:
"""
        for state, duration in brain_states['avg_duration_per_state'].items():
            report += f"  • {state}: {duration:.1f} seconds\n"

        report += f"""
{'='*80}
2. BRAIN WAVE BAND ANALYSIS
{'='*80}

Frequency Balance: {bands['balance']}

Dominant Frequencies (highest to lowest):
"""
        for band, power in bands['dominant_frequencies']:
            report += f"  {band.upper():8s}: {power:5.1f}%\n"

        report += f"""
Detailed Band Statistics:

DELTA (1-4 Hz) - Deep Sleep / Unconscious:
  Mean: {bands['detailed_stats']['delta']['mean']:.1f}%
  Range: {bands['detailed_stats']['delta']['min']:.1f}% - {bands['detailed_stats']['delta']['max']:.1f}%

THETA (4-8 Hz) - Meditation / Creativity:
  Mean: {bands['detailed_stats']['theta']['mean']:.1f}%
  Range: {bands['detailed_stats']['theta']['min']:.1f}% - {bands['detailed_stats']['theta']['max']:.1f}%

ALPHA (8-13 Hz) - Relaxed Awareness:
  Mean: {bands['detailed_stats']['alpha']['mean']:.1f}%
  Range: {bands['detailed_stats']['alpha']['min']:.1f}% - {bands['detailed_stats']['alpha']['max']:.1f}%

BETA (13-30 Hz) - Active Thinking:
  Mean: {bands['detailed_stats']['beta']['mean']:.1f}%
  Range: {bands['detailed_stats']['beta']['min']:.1f}% - {bands['detailed_stats']['beta']['max']:.1f}%

GAMMA (30-100 Hz) - High-level Processing / Artifacts:
  Mean: {bands['detailed_stats']['gamma']['mean']:.1f}%
  Range: {bands['detailed_stats']['gamma']['min']:.1f}% - {bands['detailed_stats']['gamma']['max']:.1f}%

{'='*80}
3. COGNITIVE LOAD & MENTAL EFFORT
{'='*80}

Average Cognitive Load: {cognitive['mean_cognitive_load']:.2f} (0-1 scale)
Peak Cognitive Load: {cognitive['peak_cognitive_load']:.2f}

Cognitive Load Distribution:
  • Low Load (<30%): {cognitive['low_load_percentage']:.1f}% of session
  • High Load (>70%): {cognitive['high_load_percentage']:.1f}% of session

{'='*80}
4. STRESS & TENSION INDICATORS
{'='*80}

Average Stress Score: {stress['avg_stress_score']:.2f} (0-1 scale)
Muscle Tension (EMG): {stress['avg_muscle_tension']:.2f}
Mental Tension (Forehead): {stress['avg_mental_tension']:.2f}

Period Distribution:
  • Stressed Periods (>70%): {stress['stress_periods']} samples
  • Relaxed Periods (<30%): {stress['relaxed_periods']} samples

Heart Rate:
  • Average: {stress['heart_rate_avg']:.0f} bpm
  • Variability: {stress['heart_rate_variability']}

{'='*80}
5. ATTENTION & FOCUS
{'='*80}

{attention['assessment']}

Focus Score: {attention['avg_focus_score']:.2f} (0-1 scale)
Peak Focus: {attention['peak_focus']:.2f}
Blink Rate: {attention['blink_rate']:.3f}

Attention Periods:
  • Focused (>60%): {attention['focused_periods']} samples
  • Unfocused (<40%): {attention['unfocused_periods']} samples

{'='*80}
6. EMOTIONAL STATE INDICATORS
{'='*80}

Emotional State: {emotional['emotional_quadrant']}

Arousal Level: {emotional['arousal_level']:.2f}
Valence Estimate: {emotional['valence_estimate']:.2f}

Meditation Indicators:
  • Theta Activity: {emotional['theta_meditation']:.1f}%
  • Alpha Relaxation: {emotional['alpha_relaxation']:.1f}%

{'='*80}
7. TALKING PATTERNS
{'='*80}

Talking Ratio: {talking['talking_ratio']*100:.1f}%
Talking Duration: {talking['talking_duration_seconds']} seconds
Silence Duration: {talking['silence_duration_seconds']} seconds

Episodes: {talking['talking_episodes']} talking episodes
Average Episode: {talking['avg_episode_duration']:.1f} seconds
Longest Episode: {talking['longest_episode']} seconds

{'='*80}
8. KEY INSIGHTS & RECOMMENDATIONS
{'='*80}

"""

        # Generate insights based on data
        insights = []

        if bands['dominant_frequencies'][0][0] == 'gamma' and bands['dominant_frequencies'][0][1] > 50:
            insights.append("⚠️  High gamma detected - check TP9 electrode contact")
        elif bands['dominant_frequencies'][0][0] == 'delta':
            insights.append("💤 High delta activity - deeply relaxed or drowsy state")
        elif bands['dominant_frequencies'][0][0] == 'theta':
            insights.append("🧘 Elevated theta - meditative or creative state")
        elif bands['dominant_frequencies'][0][0] == 'alpha':
            insights.append("😌 Strong alpha rhythm - relaxed but alert")

        if stress['avg_stress_score'] > 0.7:
            insights.append("😰 High stress indicators - consider relaxation techniques")
        elif stress['avg_stress_score'] < 0.3:
            insights.append("😊 Low stress levels - relaxed state maintained")

        if attention['avg_focus_score'] > 0.6:
            insights.append("🎯 Good focus maintained throughout session")
        elif attention['avg_focus_score'] < 0.4:
            insights.append("🌊 Unfocused state - may indicate relaxation or distraction")

        if stress['heart_rate_avg'] < 50:
            insights.append("💓 Very low heart rate - deep relaxation or rest state")
        elif stress['heart_rate_avg'] > 80:
            insights.append("💓 Elevated heart rate - physical or mental activity")

        if talking['talking_ratio'] > 0.8:
            insights.append("🗣️  High talking ratio - conversation or presentation")

        for insight in insights:
            report += f"{insight}\n"

        report += f"""
{'='*80}
END OF REPORT
{'='*80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Tool: Consciousness OS Brain Data Analyzer
"""

        return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_session.py <session_id>")
        sys.exit(1)

    session_id = sys.argv[1]
    session_path = Path("sessions") / session_id

    if not session_path.exists():
        print(f"Session not found: {session_id}")
        sys.exit(1)

    analyzer = SessionAnalyzer(session_path)
    report = analyzer.generate_full_report()

    # Save report
    report_path = session_path / "brain_analysis_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)

    print(report)
    print(f"\nReport saved to: {report_path}")
