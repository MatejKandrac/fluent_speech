import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import requests
import soundfile as sf

from django.conf import settings

from .db_connection import get_recording_by_id, get_transcript_words


class FillerWordsAnalysisService:

    def __init__(self):
        self.config = settings.FILLER_WORDS_CONFIG
        self.slovak_fillers = self.config['slovak_fillers']
        self.english_fillers = self.config['english_fillers']
        print(f"Loaded configuration: {self.config}")

    def detect_filler_words(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not transcript or 'segments' not in transcript:
            return []

        filler_occurrences = []
        all_fillers = self.slovak_fillers + self.english_fillers

        # Process each segment
        for segment in transcript['segments']:
            # If we have word-level data, use it for precise timestamps
            if 'words' in segment and segment['words']:
                for word_data in segment['words']:
                    word_text = word_data['word'].lower().strip().rstrip('.,')

                    # Check if this word is a filler word
                    for filler in all_fillers:
                        # Use word boundaries to avoid partial matches
                        pattern = r'\b' + re.escape(filler) + r'\b'
                        if re.search(pattern, word_text):
                            is_slovak = filler in self.slovak_fillers

                            filler_occurrences.append({
                                'word': filler,
                                'language': 'slovak' if is_slovak else 'english',
                                'start_time': word_data.get('start_time', word_data.get('start', 0)),
                                'end_time': word_data.get('end_time', word_data.get('end', 0)),
                                'segment_text': segment.get('text', ''),
                                'probability': word_data.get('probability', 1.0)
                            })
            else:
                # Fallback: use segment-level detection (less precise)
                text = segment['text'].lower().strip()
                start_time = segment['start']
                end_time = segment['end']

                # Check for filler words
                for filler in all_fillers:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(filler) + r'\b'
                    matches = list(re.finditer(pattern, text))

                    for match in matches:
                        is_slovak = filler in self.slovak_fillers

                        filler_occurrences.append({
                            'word': filler,
                            'language': 'slovak' if is_slovak else 'english',
                            'start_time': start_time,
                            'end_time': end_time,
                            'segment_text': text
                        })

        # Sort by time
        filler_occurrences.sort(key=lambda x: x['start_time'])

        return filler_occurrences

    def calculate_statistics(
        self,
        filler_occurrences: List[Dict[str, Any]],
        duration: float
    ) -> Dict[str, Any]:

        if not filler_occurrences:
            return {
                'total_filler_words': 0,
                'fillers_per_minute': 0,
                'most_common_filler': None,
                'slovak_fillers_count': 0,
                'english_fillers_count': 0,
                'duration': duration,
                'is_high_usage': False
            }

        total_fillers = len(filler_occurrences)
        fillers_per_minute = (total_fillers / duration) * 60 if duration > 0 else 0

        # Count by language
        slovak_count = sum(1 for f in filler_occurrences if f['language'] == 'slovak')
        english_count = sum(1 for f in filler_occurrences if f['language'] == 'english')

        # Find most common filler word
        word_counts = {}
        for occurrence in filler_occurrences:
            word = occurrence['word']
            word_counts[word] = word_counts.get(word, 0) + 1

        most_common_filler = max(word_counts.items(), key=lambda x: x[1]) if word_counts else (None, 0)

        # Check if usage is high
        high_threshold = self.config['high_filler_threshold_per_minute']
        is_high_usage = fillers_per_minute > high_threshold

        return {
            'total_filler_words': total_fillers,
            'fillers_per_minute': round(fillers_per_minute, 2),
            'most_common_filler': {
                'word': most_common_filler[0],
                'count': most_common_filler[1]
            } if most_common_filler[0] else None,
            'slovak_fillers_count': slovak_count,
            'english_fillers_count': english_count,
            'filler_word_distribution': word_counts,
            'duration': round(duration, 2),
            'is_high_usage': is_high_usage,
            'high_usage_threshold': high_threshold
        }

    def create_timeline_bins(
        self,
        filler_occurrences: List[Dict[str, Any]],
        duration: float,
        bin_size: float = 10.0
    ) -> Tuple[List[float], List[int]]:

        if duration <= 0:
            return [], []

        num_bins = int(np.ceil(duration / bin_size))
        bins = np.zeros(num_bins)

        for occurrence in filler_occurrences:
            start_time = occurrence['start_time']
            bin_idx = int(start_time / bin_size)
            if bin_idx < num_bins:
                bins[bin_idx] += 1

        time_labels = [i * bin_size for i in range(num_bins)]

        return time_labels, bins.tolist()

    def visualize_filler_words_timeline(
        self,
        filler_occurrences: List[Dict[str, Any]],
        duration: float,
        recording_id: int,
        output_dir: Optional[str] = None
    ):

        if output_dir is None:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        if not filler_occurrences:
            print("No data to visualize")
            return

        fig, ax = plt.subplots(figsize=(16, 5))

        # Build step function from actual event timestamps
        times = [0.0] + [f['start_time'] for f in filler_occurrences] + [duration]
        counts = [0] + list(range(1, len(filler_occurrences) + 1)) + [len(filler_occurrences)]

        ax.step(times, counts, where='post', color='red', linewidth=2)
        ax.fill_between(times, counts, step='post', alpha=0.15, color='red')
        ax.scatter([f['start_time'] for f in filler_occurrences],
                   range(1, len(filler_occurrences) + 1),
                   color='red', s=40, zorder=5)
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Total Filler Words', fontsize=12)
        ax.set_title(f'Filler Words Usage Over Time - Recording {recording_id}',
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = output_dir / f'filler_words_timeline_{recording_id}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Filler words timeline visualization saved to: {output_path}")

    def get_transcript_from_db(self, recording_id: int) -> Optional[Dict[str, Any]]:
        try:
            # Get words from database
            words = get_transcript_words(recording_id)

            if not words:
                print(f"No transcript words found in database for recording {recording_id}")
                return None

            # Calculate duration from last word's end time
            duration = max(word['end_time'] for word in words) if words else 0

            # Reconstruct segments from words
            # Group words into segments (approximate - every 5 seconds or until significant pause)
            segments = []
            current_segment = {
                'start': 0,
                'end': 0,
                'text': '',
                'words': []
            }

            segment_duration = 5.0  # Group words into ~5 second segments

            for word_data in words:
                # Start new segment if we've exceeded segment duration
                if word_data['start_time'] - current_segment['start'] > segment_duration and current_segment['words']:
                    # Trim leading space from text
                    current_segment['text'] = current_segment['text'].strip()
                    segments.append(current_segment)
                    current_segment = {
                        'start': word_data['start_time'],
                        'end': word_data['end_time'],
                        'text': '',
                        'words': []
                    }

                # Add to current segment
                if not current_segment['words']:
                    current_segment['start'] = word_data['start_time']

                current_segment['end'] = word_data['end_time']
                current_segment['text'] += ' ' + word_data['word']
                current_segment['words'].append(word_data)

            # Add final segment
            if current_segment['words']:
                current_segment['text'] = current_segment['text'].strip()
                segments.append(current_segment)

            # Build full text
            full_text = ' '.join(word['word'] for word in words)

            print(f"Loaded {len(words)} words from database, reconstructed {len(segments)} segments")

            return {
                'text': full_text,
                'language': 'unknown',  # Language not stored in word table
                'segments': segments,
                'duration': duration
            }

        except Exception as e:
            print(f"Error getting transcript from database: {e}")
            return None

    def fetch_pitch_timeseries(self, recording_id: int) -> Optional[List[Dict[str, Any]]]:
        try:
            url = f"{settings.PITCH_ANALYSIS_SERVICE_URL}/api/v1/pitch/{recording_id}/timeseries/"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                return data['timeseries'], data['duration_per_frame']
            print(f"Pitch timeseries request failed: {data.get('error')}")
            return None, None
        except Exception as e:
            print(f"Error fetching pitch timeseries: {e}")
            return None, None

    def detect_uhh_sounds(
        self,
        words: List[Dict[str, Any]],
        pitch_timeseries: List[Dict[str, Any]],
        duration_per_frame: float,
    ) -> List[Dict[str, Any]]:
        std_threshold = self.config['uhh_pitch_std_threshold']
        min_gap_duration = self.config['uhh_min_gap_duration_ms'] / 1000.0
        min_voiced_duration = self.config['uhh_min_voiced_duration_ms'] / 1000.0

        # Find inter-word gaps only (pre-speech silence before first word is excluded)
        gaps = []
        if words:
            for i in range(len(words) - 1):
                gap_start = words[i]['end_time']
                gap_end = words[i + 1]['start_time']
                if gap_end - gap_start >= min_gap_duration:
                    gaps.append((gap_start, gap_end))

        uhh_occurrences = []

        for gap_start, gap_end in gaps:
            # Collect pitch values for frames within this gap
            voiced_values = [
                frame['pitch']
                for frame in pitch_timeseries
                if gap_start <= frame['time'] < gap_end and frame['pitch'] is not None
            ]

            if not voiced_values:
                continue

            voiced_duration = len(voiced_values) * duration_per_frame
            if voiced_duration < min_voiced_duration:
                continue

            pitch_std = float(np.std(voiced_values))
            if pitch_std < std_threshold:
                uhh_occurrences.append({
                    'word': 'uhh',
                    'language': 'non-verbal',
                    'start_time': round(gap_start, 2),
                    'end_time': round(gap_end, 2),
                    'pitch_mean': round(float(np.mean(voiced_values)), 2),
                    'pitch_std': round(pitch_std, 2),
                    'voiced_duration': round(voiced_duration, 2),
                })

        return uhh_occurrences

    def save_pitch_debug_plot(
        self,
        pitch_timeseries: List[Dict[str, Any]],
        words: List[Dict[str, Any]],
        uhh_occurrences: List[Dict[str, Any]],
        recording_id: int,
    ):
        try:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            times = [f['time'] for f in pitch_timeseries]
            pitches = [f['pitch'] if f['pitch'] is not None else np.nan for f in pitch_timeseries]

            fig, ax = plt.subplots(figsize=(18, 5))

            # Shade word spans (light blue) so gaps are visually obvious
            for word in words:
                ax.axvspan(word['start_time'], word['end_time'], color='steelblue', alpha=0.15)

            # Shade detected uhh segments (orange) and annotate with std
            for uhh in uhh_occurrences:
                ax.axvspan(uhh['start_time'], uhh['end_time'], color='orange', alpha=0.4, label='uhh')
                ax.text(
                    (uhh['start_time'] + uhh['end_time']) / 2,
                    ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 300,
                    f"std={uhh['pitch_std']:.1f}",
                    ha='center', va='bottom', fontsize=7, color='darkorange'
                )

            # Plot pitch on top
            ax.plot(times, pitches, linewidth=1, color='green', label='Pitch (Hz)')

            # Annotate uhh std values (re-do after plot so ylim is known)
            ymax = ax.get_ylim()[1]
            for uhh in uhh_occurrences:
                ax.text(
                    (uhh['start_time'] + uhh['end_time']) / 2,
                    ymax * 0.95,
                    f"std={uhh['pitch_std']:.1f}",
                    ha='center', va='top', fontsize=7,
                    color='darkorange',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.6)
                )

            ax.set_xlabel('Time (s)', fontsize=11)
            ax.set_ylabel('Pitch (Hz)', fontsize=11)
            ax.set_title(
                f'Pitch + Uhh Detection — Recording {recording_id}  '
                f'(blue=word, orange=uhh, threshold std<{self.config["uhh_pitch_std_threshold"]})',
                fontsize=12
            )
            ax.set_ylim([50, 350])
            ax.grid(True, alpha=0.3)

            # Deduplicate legend
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), loc='upper right')

            plt.tight_layout()
            output_path = output_dir / 'pitch_uhh.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Pitch uhh debug plot saved to: {output_path}")

        except Exception as e:
            print(f"Error saving pitch debug plot: {e}")

    def save_uhh_audio_clips(
        self,
        uhh_occurrences: List[Dict[str, Any]],
        recording_filename: str,
        recording_id: int,
    ):
        try:
            processed_wav = Path(settings.VIDEO_STORAGE_PATH) / (Path(recording_filename).stem + '_processed.wav')
            if not processed_wav.exists():
                print(f"Processed WAV not found at {processed_wav}, skipping uhh clip export")
                return

            audio, sr = sf.read(str(processed_wav))

            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            for i, uhh in enumerate(uhh_occurrences):
                start_sample = int(uhh['start_time'] * sr)
                end_sample = int(uhh['end_time'] * sr)
                clip = audio[start_sample:end_sample]

                clip_path = output_dir / f'uhh_{i + 1}_{uhh["start_time"]:.2f}s.wav'
                sf.write(str(clip_path), clip, sr)
                print(f"Saved uhh clip {i + 1}: {clip_path}")

        except Exception as e:
            print(f"Error saving uhh audio clips: {e}")

    def analyze_filler_words(self, recording_id: int) -> Dict[str, Any]:
        print(f"Analyzing filler words for recording ID: {recording_id}")

        # Get recording information
        recording = get_recording_by_id(recording_id)
        if not recording:
            return {'success': False, 'error': f'Recording with ID {recording_id} not found'}

        # Get transcript from database
        transcript = self.get_transcript_from_db(recording_id)
        if not transcript:
            return {
                'success': False,
                'error': 'Failed to get transcript from database. Please run transcript processing first.'
            }

        duration = transcript.get('duration', 0)
        print(f"Received transcript with duration: {duration:.2f}s")

        # Check minimum duration
        min_duration = self.config['min_speech_duration']
        if duration < min_duration:
            return {
                'success': False,
                'error': f'Audio duration ({duration}s) is less than minimum required ({min_duration}s)'
            }

        # Detect filler words from transcript
        filler_occurrences = self.detect_filler_words(transcript)
        print(f"Detected {len(filler_occurrences)} filler word occurrences")

        # Detect uhh sounds via pitch cross-referencing
        words = [w for seg in transcript.get('segments', []) for w in seg.get('words', [])]
        pitch_timeseries, duration_per_frame = self.fetch_pitch_timeseries(recording_id)
        uhh_occurrences = []
        if pitch_timeseries is not None:
            uhh_occurrences = self.detect_uhh_sounds(words, pitch_timeseries, duration_per_frame)
            print(f"Detected {len(uhh_occurrences)} uhh sounds")
        else:
            print("Pitch timeseries unavailable, skipping uhh detection")

        all_occurrences = sorted(filler_occurrences + uhh_occurrences, key=lambda x: x['start_time'])

        # Calculate statistics
        statistics = self.calculate_statistics(all_occurrences, duration)

        # Save pitch debug plot + uhh audio clips (always, for tuning uhh detection thresholds)
        if pitch_timeseries is not None:
            self.save_pitch_debug_plot(pitch_timeseries, words, uhh_occurrences, recording_id)
            if uhh_occurrences:
                self.save_uhh_audio_clips(uhh_occurrences, recording['filename'], recording_id)

        # Create visualization if in debug mode
        if settings.DEBUG:
            self.visualize_filler_words_timeline(
                filler_occurrences,
                duration,
                recording_id
            )

        return {
            'success': True,
            'recording_id': recording_id,
            'duration': round(duration, 2),
            'detected_language': transcript.get('language', 'unknown'),
            'statistics': statistics,
            'filler_occurrences': all_occurrences[:50],  # Limit to first 50 for response size
            'total_filler_occurrences': len(all_occurrences),
            'uhh_occurrences_count': len(uhh_occurrences),
            'message': 'Filler words analysis completed successfully.'
        }
