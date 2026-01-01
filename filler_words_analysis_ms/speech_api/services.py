import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from django.conf import settings

from .db_connection import get_recording_by_id


class FillerWordsAnalysisService:

    def __init__(self):
        self.config = settings.FILLER_WORDS_CONFIG
        self.slovak_fillers = self.config['slovak_fillers']
        self.english_fillers = self.config['english_fillers']
        print(f"Loaded configuration: {self.config}")

    def transcribe_audio(self, audio_path: str) -> Optional[Dict[str, Any]]:
        try:
            import whisper

            model_name = self.config['whisper_model']
            print(f"Loading Whisper model: {model_name}")
            model = whisper.load_model(model_name)

            print(f"Transcribing audio file: {audio_path}")
            result = model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )

            return result

        except ImportError:
            print("ERROR: Whisper is not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None

    def detect_filler_words(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not transcript or 'segments' not in transcript:
            return []

        filler_occurrences = []
        all_fillers = self.slovak_fillers + self.english_fillers

        # Process each segment
        for segment in transcript['segments']:
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

        # Create bins for visualization (10 second intervals)
        time_labels, filler_counts = self.create_timeline_bins(
            filler_occurrences,
            duration,
            bin_size=10.0
        )

        if not time_labels:
            print("No data to visualize")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))

        # Top plot: Bar chart of filler words over time
        ax1.bar(time_labels, filler_counts, width=8, alpha=0.7, color='red', edgecolor='darkred')
        ax1.set_xlabel('Time (seconds)', fontsize=12)
        ax1.set_ylabel('Filler Words Count', fontsize=12)
        ax1.set_title(f'Filler Words Over Time - Recording {recording_id}',
                     fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')

        # Add threshold line
        if duration > 0:
            threshold_per_bin = (self.config['high_filler_threshold_per_minute'] / 60) * 10  # per 10 seconds
            ax1.axhline(
                threshold_per_bin,
                color='orange',
                linestyle='--',
                linewidth=2,
                label=f'High Usage Threshold ({threshold_per_bin:.1f} per 10s)'
            )
            ax1.legend(loc='upper right')

        # Bottom plot: Scatter plot of individual occurrences
        if filler_occurrences:
            slovak_times = [f['start_time'] for f in filler_occurrences if f['language'] == 'slovak']
            english_times = [f['start_time'] for f in filler_occurrences if f['language'] == 'english']

            if slovak_times:
                ax2.scatter(slovak_times, [1] * len(slovak_times),
                          color='blue', s=100, alpha=0.6, label='Slovak Fillers', marker='|')
            if english_times:
                ax2.scatter(english_times, [1.5] * len(english_times),
                          color='green', s=100, alpha=0.6, label='English Fillers', marker='|')

        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.set_ylabel('Filler Type', fontsize=12)
        ax2.set_title('Individual Filler Word Occurrences', fontsize=12, fontweight='bold')
        ax2.set_ylim(0.5, 2)
        ax2.set_yticks([1, 1.5])
        ax2.set_yticklabels(['Slovak', 'English'])
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.legend(loc='upper right')

        plt.tight_layout()

        output_path = output_dir / f'filler_words_timeline_{recording_id}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Filler words timeline visualization saved to: {output_path}")

    def analyze_filler_words(self, recording_id: int) -> Dict[str, Any]:
        print(f"Analyzing filler words for recording ID: {recording_id}")

        # Get recording information
        recording = get_recording_by_id(recording_id)
        if not recording:
            return {'success': False, 'error': f'Recording with ID {recording_id} not found'}

        # Construct path to processed audio
        video_filename = recording['filename']
        processed_filename = Path(video_filename).stem + '_processed.wav'
        processed_path = Path(settings.VIDEO_STORAGE_PATH) / processed_filename

        if not processed_path.exists():
            return {
                'success': False,
                'error': f'Processed audio file not found at: {processed_path}'
            }

        audio_path = str(processed_path)
        print(f"[DEBUG] Using processed audio from: {audio_path}")

        # Get duration from audio file
        try:
            import librosa
            audio, sr = librosa.load(audio_path, sr=None)
            duration = len(audio) / sr
            print(f"[DEBUG] Audio duration: {duration:.2f}s (sample rate: {sr} Hz)")
        except Exception as e:
            return {'success': False, 'error': f'Failed to load audio file: {e}'}

        # Check minimum duration
        min_duration = self.config['min_speech_duration']
        if duration < min_duration:
            return {
                'success': False,
                'error': f'Audio duration ({duration}s) is less than minimum required ({min_duration}s)'
            }

        # Transcribe audio
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return {'success': False, 'error': 'Transcription failed'}

        print(f"Transcription completed. Detected language: {transcript.get('language', 'unknown')}")

        # Detect filler words
        filler_occurrences = self.detect_filler_words(transcript)
        print(f"Detected {len(filler_occurrences)} filler word occurrences")

        # Calculate statistics
        statistics = self.calculate_statistics(filler_occurrences, duration)

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
            'filler_occurrences': filler_occurrences[:50],  # Limit to first 50 for response size
            'total_filler_occurrences': len(filler_occurrences),
            'message': 'Filler words analysis completed successfully.'
        }
