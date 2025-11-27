"""
Mental State Interpreter
Combines EEG, HRV, and posture data to provide meaningful mental state feedback
"""

from typing import Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MentalStateInterpreter:
    """
    Interprets raw metrics into meaningful mental states
    Provides explanations and recommendations
    """

    # Frequency band meanings
    BAND_MEANINGS = {
        'delta': {
            'range': '0.5-4 Hz',
            'meaning': 'Deep sleep, unconsciousness, or severe artifact',
            'normal_awake': '5-15%',
            'high_awake': 'Usually indicates artifact, poor signal, or extreme fatigue'
        },
        'theta': {
            'range': '4-8 Hz',
            'meaning': 'Drowsiness, meditation, creativity, memory formation',
            'normal_awake': '10-20%',
            'high_awake': 'Creative flow, meditative state, or drowsiness'
        },
        'alpha': {
            'range': '8-13 Hz',
            'meaning': 'Relaxed awareness, eyes closed, calm focus',
            'normal_awake': '15-30%',
            'high_awake': 'Relaxed, calm, or meditative state'
        },
        'beta': {
            'range': '13-30 Hz',
            'meaning': 'Active thinking, focus, problem-solving, alertness',
            'normal_awake': '20-35%',
            'high_awake': 'Focused, alert, actively thinking'
        },
        'gamma': {
            'range': '30-50 Hz',
            'meaning': 'Peak focus, binding of information, high-level cognition',
            'normal_awake': '5-15%',
            'high_awake': 'Deep thinking, intense focus, cognitive binding'
        }
    }

    @staticmethod
    def interpret_band_changes(current: Dict[str, float], previous: Optional[Dict[str, float]] = None) -> str:
        """
        Interpret changes in frequency bands
        
        Args:
            current: Current band powers
            previous: Previous band powers (optional)
        
        Returns:
            Human-readable interpretation
        """
        if previous is None:
            return "Establishing baseline..."
        
        changes = {}
        for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            diff = current.get(band, 0) - previous.get(band, 0)
            if abs(diff) > 3:  # Significant change (>3%)
                changes[band] = diff
        
        if not changes:
            return "Brain activity is stable"
        
        interpretations = []
        
        # Gamma changes
        if 'gamma' in changes:
            if changes['gamma'] > 5:
                interpretations.append("🧠 Entering deep thinking mode (gamma increased)")
            elif changes['gamma'] < -5:
                interpretations.append("🧠 Leaving intense focus (gamma decreased)")
        
        # Beta changes
        if 'beta' in changes:
            if changes['beta'] > 5:
                interpretations.append("💭 More active thinking (beta increased)")
            elif changes['beta'] < -5:
                interpretations.append("💭 Less active thinking (beta decreased)")
        
        # Alpha changes
        if 'alpha' in changes:
            if changes['alpha'] > 5:
                interpretations.append("😌 More relaxed (alpha increased)")
            elif changes['alpha'] < -5:
                interpretations.append("😌 Less relaxed (alpha decreased)")
        
        # Delta changes (usually artifact)
        if 'delta' in changes and abs(changes['delta']) > 5:
            if changes['delta'] > 5:
                interpretations.append("⚠️ Delta rising - possible artifact or fatigue")
            else:
                interpretations.append("✅ Delta decreasing - signal improving")
        
        return " | ".join(interpretations) if interpretations else "Minor fluctuations"

    @staticmethod
    def interpret_hrv(hrv_rmssd: float, hrv_sdnn: float, heart_rate: float) -> Dict[str, str]:
        """
        Interpret HRV metrics in plain language
        
        Args:
            hrv_rmssd: RMSSD in milliseconds (short-term HRV)
            hrv_sdnn: SDNN in milliseconds (overall HRV)
            heart_rate: Heart rate in BPM
        
        Returns:
            Dictionary with interpretations
        """
        if hrv_rmssd == 0 or hrv_sdnn == 0:
            return {
                'status': 'No HRV data',
                'meaning': 'Waiting for heart rate data...',
                'rmssd_meaning': 'N/A',
                'sdnn_meaning': 'N/A',
                'heart_rate_meaning': 'N/A'
            }
        
        # RMSSD interpretation (short-term variability)
        # Typical range: 20-100ms for healthy adults
        # Higher = more relaxed, lower = more stressed
        if hrv_rmssd > 50:
            rmssd_status = "Excellent"
            rmssd_meaning = "Very relaxed, low stress"
        elif hrv_rmssd > 30:
            rmssd_status = "Good"
            rmssd_meaning = "Relaxed, low stress"
        elif hrv_rmssd > 20:
            rmssd_status = "Moderate"
            rmssd_meaning = "Moderate stress"
        else:
            rmssd_status = "Low"
            rmssd_meaning = "High stress or fatigue"
        
        # SDNN interpretation (overall variability)
        # Typical range: 30-100ms for healthy adults
        if hrv_sdnn > 60:
            sdnn_status = "Excellent"
            sdnn_meaning = "Very healthy variability"
        elif hrv_sdnn > 40:
            sdnn_status = "Good"
            sdnn_meaning = "Healthy variability"
        elif hrv_sdnn > 25:
            sdnn_status = "Moderate"
            sdnn_meaning = "Moderate variability"
        else:
            sdnn_status = "Low"
            sdnn_meaning = "Reduced variability (stress/fatigue)"
        
        # Heart rate interpretation
        if heart_rate > 100:
            hr_status = "Elevated"
            hr_meaning = "High heart rate (stress, activity, or excitement)"
        elif heart_rate > 80:
            hr_status = "Slightly elevated"
            hr_meaning = "Moderate heart rate"
        elif heart_rate > 60:
            hr_status = "Normal"
            hr_meaning = "Resting heart rate"
        else:
            hr_status = "Low"
            hr_meaning = "Low heart rate (very relaxed or fit)"
        
        # Overall status
        if rmssd_status in ["Excellent", "Good"] and hr_status == "Normal":
            overall_status = "Calm & Relaxed"
        elif rmssd_status in ["Low", "Moderate"] or hr_status == "Elevated":
            overall_status = "Stressed or Active"
        else:
            overall_status = "Moderate"
        
        return {
            'status': overall_status,
            'meaning': f"HRV indicates {overall_status.lower()} state",
            'rmssd_meaning': f"RMSSD: {hrv_rmssd:.0f}ms ({rmssd_status}) - {rmssd_meaning}",
            'sdnn_meaning': f"SDNN: {hrv_sdnn:.0f}ms ({sdnn_status}) - {sdnn_meaning}",
            'heart_rate_meaning': f"Heart Rate: {heart_rate:.0f} BPM ({hr_status}) - {hr_meaning}",
            'rmssd_value': float(hrv_rmssd),
            'sdnn_value': float(hrv_sdnn),
            'heart_rate_value': float(heart_rate)
        }

    @staticmethod
    def interpret_posture(gyro_data: Optional[np.ndarray], acc_data: Optional[np.ndarray], 
                         posture_history: Optional[list] = None) -> Dict[str, str]:
        """
        Interpret posture from gyroscope and accelerometer data with smoothing
        
        Args:
            gyro_data: Gyroscope data [x, y, z] in deg/s
            acc_data: Accelerometer data [x, y, z] in g
            posture_history: List of recent posture readings for smoothing
        
        Returns:
            Dictionary with posture interpretation
        """
        if gyro_data is None and acc_data is None:
            return {
                'status': 'No posture data',
                'meaning': 'Waiting for sensor data...',
                'recommendation': ''
            }
        
        # Check for movement first using gyroscope (more sensitive)
        if gyro_data is not None and len(gyro_data) >= 3:
            gyro_magnitude = np.sqrt(gyro_data[0]**2 + gyro_data[1]**2 + gyro_data[2]**2)
            # If moving significantly (>30 deg/s), report movement
            if gyro_magnitude > 30:
                return {
                    'status': 'Moving',
                    'meaning': 'Head is moving - posture cannot be determined',
                    'recommendation': 'Stay still for accurate posture reading',
                    'pitch': 0,
                    'roll': 0
                }
        
        # Use smoothed values from history if available (need more samples for stability)
        if posture_history and len(posture_history) > 15:  # Need 15+ samples (15 seconds)
            # Average recent pitch and roll values
            pitches = [p.get('pitch', 0) for p in posture_history if p.get('pitch') is not None]
            rolls = [p.get('roll', 0) for p in posture_history if p.get('roll') is not None]
            
            if pitches and rolls:
                avg_pitch = np.mean(pitches)
                avg_roll = np.mean(rolls)
                
                # Calculate variance - if high, user is moving
                pitch_std = np.std(pitches)
                roll_std = np.std(rolls)
                
                # If high variance, user is moving around
                if pitch_std > 10 or roll_std > 10:
                    return {
                        'status': 'Unstable',
                        'meaning': 'Posture is changing frequently',
                        'recommendation': 'Try to maintain a steady position',
                        'pitch': float(avg_pitch),
                        'roll': float(avg_roll)
                    }
                
                # Use averaged values for interpretation (stricter thresholds)
                if abs(avg_pitch) < 10 and abs(avg_roll) < 10:
                    return {
                        'status': 'Good',
                        'meaning': 'Head is upright and balanced',
                        'recommendation': 'Maintain this posture',
                        'pitch': float(avg_pitch),
                        'roll': float(avg_roll)
                    }
                elif abs(avg_pitch) > 20:  # Lower threshold for detection
                    if avg_pitch > 0:
                        return {
                            'status': 'Forward tilt',
                            'meaning': 'Head tilted forward (looking down)',
                            'recommendation': 'Raise your head to reduce neck strain',
                            'pitch': float(avg_pitch),
                            'roll': float(avg_roll)
                        }
                    else:
                        return {
                            'status': 'Backward tilt',
                            'meaning': 'Head tilted backward',
                            'recommendation': 'Adjust to neutral position',
                            'pitch': float(avg_pitch),
                            'roll': float(avg_roll)
                        }
                elif abs(avg_roll) > 15:  # Lower threshold
                    return {
                        'status': 'Side tilt',
                        'meaning': 'Head tilted to one side',
                        'recommendation': 'Straighten your head',
                        'pitch': float(avg_pitch),
                        'roll': float(avg_roll)
                    }
                else:
                    return {
                        'status': 'Slight tilt',
                        'meaning': f'Head slightly tilted (pitch: {avg_pitch:.0f}°, roll: {avg_roll:.0f}°)',
                        'recommendation': 'Minor adjustment recommended',
                        'pitch': float(avg_pitch),
                        'roll': float(avg_roll)
                    }
        
        # Use accelerometer for static posture (gravity vector)
        if acc_data is not None and len(acc_data) >= 3:
            # Calculate head tilt from accelerometer
            # When upright, z should be close to 1g (pointing down)
            # x and y should be close to 0
            x, y, z = acc_data[0], acc_data[1], acc_data[2]
            magnitude = np.sqrt(x**2 + y**2 + z**2)
            
            if magnitude < 0.5:
                return {
                    'status': 'Unstable',
                    'meaning': 'Sensor data unreliable',
                    'recommendation': 'Check device connection'
                }
            
            # Normalize
            x_norm = x / magnitude
            y_norm = y / magnitude
            z_norm = z / magnitude
            
            # Calculate tilt angles
            pitch = np.arcsin(-x_norm) * 180 / np.pi  # Forward/backward tilt
            roll = np.arcsin(y_norm) * 180 / np.pi   # Left/right tilt
            
            # Interpret posture
            if abs(pitch) < 15 and abs(roll) < 15:
                status = "Good"
                meaning = "Head is upright and balanced"
                recommendation = "Maintain this posture"
            elif abs(pitch) > 30:
                if pitch > 0:
                    status = "Forward tilt"
                    meaning = "Head tilted forward (looking down)"
                    recommendation = "Raise your head to reduce neck strain"
                else:
                    status = "Backward tilt"
                    meaning = "Head tilted backward"
                    recommendation = "Adjust to neutral position"
            elif abs(roll) > 20:
                status = "Side tilt"
                meaning = "Head tilted to one side"
                recommendation = "Straighten your head"
            else:
                status = "Slight tilt"
                meaning = f"Head slightly tilted (pitch: {pitch:.0f}°, roll: {roll:.0f}°)"
                recommendation = "Minor adjustment recommended"
            
            return {
                'status': status,
                'meaning': meaning,
                'recommendation': recommendation,
                'pitch': float(pitch),
                'roll': float(roll)
            }
        
        # Use gyroscope for movement detection
        if gyro_data is not None and len(gyro_data) >= 3:
            magnitude = np.sqrt(gyro_data[0]**2 + gyro_data[1]**2 + gyro_data[2]**2)
            
            if magnitude > 50:  # deg/s
                return {
                    'status': 'Moving',
                    'meaning': 'Head is moving',
                    'recommendation': 'Try to stay still for better EEG signal'
                }
            else:
                return {
                    'status': 'Still',
                    'meaning': 'Head is relatively still',
                    'recommendation': 'Good for signal quality'
                }
        
        return {
            'status': 'Unknown',
            'meaning': 'Insufficient data',
            'recommendation': ''
        }

    @staticmethod
    def get_comprehensive_state(
        brain_state: str,
        band_powers: Dict[str, float],
        hrv_data: Dict,
        posture_data: Dict,
        signal_quality: float
    ) -> Dict[str, str]:
        """
        Get comprehensive mental state interpretation combining all metrics
        
        Returns:
            Dictionary with overall mental state and recommendations
        """
        # Base interpretation
        state_meanings = {
            'focused': '🧠 Focused - Actively thinking and engaged',
            'peak_focus': '⚡ Peak Focus - Deep thinking, high cognitive load',
            'relaxed': '😌 Relaxed - Calm and at ease',
            'creative': '✨ Creative - In a flow state, creative thinking',
            'drowsy': '😴 Drowsy - Tired or falling asleep',
            'mixed': '🔄 Mixed - Transitioning or unclear state',
            'artifact_detected': '⚠️ Artifact - Signal contaminated, results unreliable',
            'low_confidence': '❓ Low Confidence - Poor signal quality',
            'unknown': '❓ Unknown - Insufficient data'
        }
        
        base_meaning = state_meanings.get(brain_state, f"State: {brain_state}")
        
        # Combine with HRV
        hrv_status = hrv_data.get('status', 'Unknown')
        hrv_meaning = hrv_data.get('meaning', '')
        
        # Combine with posture
        posture_status = posture_data.get('status', 'Unknown')
        posture_meaning = posture_data.get('meaning', '')
        
        # Overall assessment
        if signal_quality < 50:
            overall = "⚠️ Poor Signal Quality"
            recommendation = "Check electrode contact and minimize movement"
        elif brain_state in ['artifact_detected', 'low_confidence']:
            overall = "⚠️ Unreliable Data"
            recommendation = "Wait for signal to stabilize"
        elif brain_state == 'peak_focus' and hrv_status == 'Calm & Relaxed':
            overall = "🎯 Optimal Focus"
            recommendation = "Great state for deep work - maintain this"
        elif brain_state == 'focused' and hrv_status == 'Calm & Relaxed':
            overall = "✅ Focused & Calm"
            recommendation = "Good state for productive work"
        elif brain_state == 'relaxed' and hrv_status == 'Calm & Relaxed':
            overall = "😌 Relaxed & Calm"
            recommendation = "Good state for rest or light tasks"
        elif hrv_status == 'Stressed or Active':
            overall = "⚡ Active State"
            recommendation = "High arousal - good for alert tasks, but consider breaks if sustained"
        else:
            overall = f"🔄 {brain_state.title()}"
            recommendation = "Monitor changes over time"
        
        return {
            'overall_state': overall,
            'brain_state_meaning': base_meaning,
            'hrv_interpretation': hrv_meaning,
            'posture_interpretation': posture_meaning,
            'recommendation': recommendation,
            'signal_quality': f"{signal_quality:.0f}%"
        }

