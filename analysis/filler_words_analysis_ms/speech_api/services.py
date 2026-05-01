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
                min_prob = self.config['min_word_probability']
                for word_data in segment['words']:
                    probability = word_data.get('probability', 1.0)
                    if probability < min_prob:
                        continue

                    word_text = word_data['word'].lower().strip().rstrip('.,')

                    for filler in all_fillers:
                        pattern = r'\b' + re.escape(filler) + r'\b'
                        if re.search(pattern, word_text):
                            is_slovak = filler in self.slovak_fillers
                            filler_occurrences.append({
                                'word': filler,
                                'language': 'slovak' if is_slovak else 'english',
                                'start_time': word_data.get('start_time', word_data.get('start', 0)),
                                'end_time': word_data.get('end_time', word_data.get('end', 0)),
                                'segment_text': segment.get('text', ''),
                                'probability': probability
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

    @staticmethod
    def _compute_flux_timeseries(
        audio: np.ndarray, sr: int, n_frames: int, hop_length: int = 800, n_fft: int = 1600
    ) -> np.ndarray:
        mono = audio.mean(axis=1) if audio.ndim > 1 else audio
        window = np.hanning(n_fft)
        flux = np.full(n_frames, np.nan)
        prev_spec = None
        for i in range(n_frames):
            start = i * hop_length
            end = start + n_fft
            if end > len(mono):
                break
            spec = np.abs(np.fft.rfft(mono[start:end] * window))
            if prev_spec is not None:
                flux[i] = float(np.sqrt(np.sum((spec - prev_spec) ** 2)))
            prev_spec = spec
        return flux

    @staticmethod
    def _segment_mean_flux(
        audio: np.ndarray, sr: int, start_time: float, end_time: float,
        hop_length: int = 800, n_fft: int = 1600
    ) -> float:
        mono = audio.mean(axis=1) if audio.ndim > 1 else audio
        start_s = int(start_time * sr)
        end_s = int(end_time * sr)
        chunk = mono[start_s:end_s]
        window = np.hanning(n_fft)
        prev_spec = None
        flux_vals = []
        for i in range(0, len(chunk) - n_fft + 1, hop_length):
            spec = np.abs(np.fft.rfft(chunk[i:i + n_fft] * window))
            if prev_spec is not None:
                flux_vals.append(float(np.sqrt(np.sum((spec - prev_spec) ** 2))))
            prev_spec = spec
        return float(np.mean(flux_vals)) if flux_vals else float('nan')

    def _log_sliding_window_candidates(
        self,
        words: List[Dict[str, Any]],
        pitch_timeseries: List[Dict[str, Any]],
        duration_per_frame: float,
        audio: Optional[np.ndarray] = None,
        sr: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        std_threshold = self.config['uhh_pitch_std_threshold']
        flux_max = self.config['uhh_flux_max']
        min_duration = self.config['uhh_min_voiced_duration_ms'] / 1000.0
        max_duration = self.config['uhh_max_run_duration_ms'] / 1000.0
        window_frames = max(2, round(self.config['uhh_window_ms'] / 1000.0 / duration_per_frame))
        min_voiced_fraction = self.config['uhh_min_voiced_fraction']

        pitches = np.array([
            f['pitch'] if f['pitch'] is not None else np.nan
            for f in pitch_timeseries
        ])
        n = len(pitches)

        print(f"  [sliding window] {window_frames} frames ({self.config['uhh_window_ms']:.0f}ms), "
              f"std<{std_threshold}, voiced>={min_voiced_fraction*100:.0f}%")

        stable = np.zeros(n, dtype=bool)
        for i in range(n - window_frames + 1):
            window = pitches[i:i + window_frames]
            voiced = window[~np.isnan(window)]
            if len(voiced) >= window_frames * min_voiced_fraction and np.std(voiced) < std_threshold:
                stable[i] = True

        segments = []
        i = 0
        while i < n:
            if stable[i]:
                seg_start = i
                seg_end = i + window_frames
                i += 1
                while i < n and stable[i]:
                    seg_end = i + window_frames
                    i += 1
                segments.append((seg_start, min(seg_end - 1, n - 1)))
            else:
                i += 1

        all_candidates = []
        accepted = []
        for start_idx, end_idx in segments:
            seg_start_time = pitch_timeseries[start_idx]['time']
            seg_end_time = pitch_timeseries[end_idx]['time'] + duration_per_frame
            duration = seg_end_time - seg_start_time

            if duration < min_duration or duration > max_duration:
                continue

            voiced_values = pitches[start_idx:end_idx + 1]
            voiced_values = voiced_values[~np.isnan(voiced_values)]
            if len(voiced_values) == 0:
                continue

            pitch_std = float(np.std(voiced_values))
            pitch_mean = float(np.mean(voiced_values))

            flux = float('nan')
            if audio is not None and sr is not None:
                flux = self._segment_mean_flux(audio, sr, seg_start_time, seg_end_time)

            passes = (
                pitch_std < std_threshold and
                (flux_max <= 0 or np.isnan(flux) or flux < flux_max)
            )

            overlapping_words = [
                w['word'] for w in words
                if w['start_time'] < seg_end_time and w['end_time'] > seg_start_time
            ]
            overlap_str = ' '.join(overlapping_words) if overlapping_words else '(no whisper words)'
            flux_str = f' flux={flux:.0f}' if not np.isnan(flux) else ''
            marker = 'ACCEPT' if passes else 'skip  '
            print(f"  [{marker}] t={seg_start_time:.2f}s dur={duration*1000:.0f}ms "
                  f"std={pitch_std:.1f} mean={pitch_mean:.0f}Hz{flux_str} | [{overlap_str}]")

            all_candidates.append({
                'start_time': seg_start_time,
                'end_time': seg_end_time,
                'duration': duration,
                'pitch_std': pitch_std,
                'pitch_mean': pitch_mean,
                'flux': flux,
            })
            if passes:
                accepted.append({
                    'word': 'uhh',
                    'language': 'non-verbal',
                    'start_time': round(seg_start_time, 2),
                    'end_time': round(seg_end_time, 2),
                    'pitch_mean': round(pitch_mean, 2),
                    'pitch_std': round(pitch_std, 2),
                    'voiced_duration': round(duration, 2),
                })

        return all_candidates, accepted

    def save_pitch_debug_plot(
        self,
        pitch_timeseries: List[Dict[str, Any]],
        words: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        recording_id: int,
        audio: Optional[np.ndarray] = None,
        sr: Optional[int] = None,
    ):
        try:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            times = [f['time'] for f in pitch_timeseries]
            pitches = [f['pitch'] if f['pitch'] is not None else np.nan for f in pitch_timeseries]

            has_flux = audio is not None and sr is not None
            flux_vals = None
            if has_flux:
                flux_vals = self._compute_flux_timeseries(audio, sr, len(pitch_timeseries))

            fig, axes = plt.subplots(
                2 if has_flux else 1, 1,
                figsize=(18, 9 if has_flux else 5),
                sharex=True,
                gridspec_kw={'height_ratios': [2, 1]} if has_flux else {}
            )
            ax_pitch = axes[0] if has_flux else axes
            ax_flux = axes[1] if has_flux else None

            for word in words:
                ax_pitch.axvspan(word['start_time'], word['end_time'], color='steelblue', alpha=0.15)
            for c in candidates:
                ax_pitch.axvspan(c['start_time'], c['end_time'], color='orange', alpha=0.35,
                                 label='candidate')
            ax_pitch.plot(times, pitches, linewidth=1, color='green', label='Pitch (Hz)')
            ax_pitch.set_ylabel('Pitch (Hz)', fontsize=11)
            ax_pitch.set_title(
                f'Pitch + Candidates — Recording {recording_id}  '
                f'(blue=word, orange=candidate, std<{self.config["uhh_pitch_std_threshold"]})',
                fontsize=12
            )
            ax_pitch.set_ylim([50, 350])
            ax_pitch.grid(True, alpha=0.3)
            handles, labels = ax_pitch.get_legend_handles_labels()
            ax_pitch.legend(dict(zip(labels, handles)).values(),
                            dict(zip(labels, handles)).keys(), loc='upper right')

            if has_flux and ax_flux is not None:
                flux_times = times[:len(flux_vals)]
                ax_flux.plot(flux_times, flux_vals, linewidth=0.8, color='purple', label='Spectral flux')
                for c in candidates:
                    ax_flux.axvspan(c['start_time'], c['end_time'], color='orange', alpha=0.25)
                ax_flux.set_xlabel('Time (s)', fontsize=11)
                ax_flux.set_ylabel('Spectral flux', fontsize=11)
                ax_flux.grid(True, alpha=0.3)
                ax_flux.legend(loc='upper right')
            else:
                ax_pitch.set_xlabel('Time (s)', fontsize=11)

            plt.tight_layout()
            output_path = output_dir / 'pitch_uhh.png'
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Pitch debug plot saved to: {output_path}")

        except Exception as e:
            print(f"Error saving pitch debug plot: {e}")

    def save_uhh_audio_clips(
        self,
        uhh_occurrences: List[Dict[str, Any]],
        recording_id: int,
        audio: np.ndarray,
        sr: int,
    ):
        try:
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

    def find_filler_peak_zones(
        self,
        all_occurrences: List[Dict[str, Any]],
        duration: float,
        recording_id: int,
    ) -> Dict[str, Any]:
        """Detect one or more time segments with elevated filler word density.

        Uses a bottom-up segmentation approach (one of the four approaches
        described in the thesis, section 2.4.1): starts with each fixed-size
        bin as its own segment, then iteratively merges adjacent segments whose
        mean filler rates are most similar. Merging stops when the cheapest
        remaining merge would join two segments that differ by more than
        merge_threshold (= k × overall std of rates). This naturally isolates
        high-density regions without needing a global penalty parameter.

        Post-filter: segments whose mean rate exceeds the overall rate by
        peak_zone_threshold_multiplier are returned as filler zones.
        """
        if not all_occurrences or duration <= 0:
            return {'zones': [], 'distribution': 'even'}

        total = len(all_occurrences)
        overall_rate_per_min = (total / duration) * 60.0
        threshold_multiplier = self.config.get('peak_zone_threshold_multiplier', 2.0)
        merge_k = self.config.get('bottom_up_merge_k', 1.0)

        bin_size = self.config.get('segmentation_bin_size', 10.0)
        n_bins = max(1, int(np.ceil(duration / bin_size)))
        counts = np.zeros(n_bins)

        for occ in all_occurrences:
            idx = min(int(occ['start_time'] / bin_size), n_bins - 1)
            counts[idx] += 1

        rates = counts * (60.0 / bin_size)  # fillers/minute per bin

        print(
            f"Filler bottom-up segmentation: {n_bins} bins × {bin_size}s, "
            f"rates/min={[round(v, 1) for v in rates]}, "
            f"overall={overall_rate_per_min:.1f}/min"
        )

        if n_bins < 2:
            return {'zones': [], 'distribution': 'even'}

        overall_std = float(np.std(rates))
        merge_threshold = merge_k * overall_std

        # Bottom-up segmentation: each entry is [bin_start, bin_end, weighted_mean]
        # bin_start/end are bin indices (inclusive)
        segs = [[i, i, float(rates[i])] for i in range(n_bins)]

        while len(segs) > 1:
            costs = [abs(segs[i][2] - segs[i + 1][2]) for i in range(len(segs) - 1)]
            min_cost = min(costs)
            if min_cost > merge_threshold:
                break
            i = costs.index(min_cost)
            lo, hi = segs[i][0], segs[i + 1][1]
            width_a = segs[i][1] - segs[i][0] + 1
            width_b = segs[i + 1][1] - segs[i + 1][0] + 1
            merged_mean = (segs[i][2] * width_a + segs[i + 1][2] * width_b) / (width_a + width_b)
            segs[i] = [lo, hi, merged_mean]
            del segs[i + 1]

        print(f"Bottom-up produced {len(segs)} segment(s): "
              f"{[(round(s[0]*bin_size,1), round(s[1]*bin_size+bin_size,1), round(s[2],1)) for s in segs]}")

        cutoff = overall_rate_per_min * threshold_multiplier
        zones = []
        for seg in segs:
            if seg[2] >= cutoff:
                start_s = round(seg[0] * bin_size, 2)
                end_s   = round(min((seg[1] + 1) * bin_size, duration), 2)
                zones.append({
                    'start': start_s,
                    'end': end_s,
                    'rate_per_min': round(seg[2], 2),
                    'overall_rate_per_min': round(overall_rate_per_min, 2),
                    'peak_ratio': round(seg[2] / overall_rate_per_min, 2) if overall_rate_per_min > 0 else None,
                })

        distribution = 'concentrated' if zones else 'even'
        print(f"Filler zones: {len(zones)} ({distribution}), cutoff={cutoff:.1f}/min")

        self._save_zone_plot(rates, segs, zones, cutoff, overall_rate_per_min,
                             bin_size, duration, recording_id)

        return {
            'distribution': distribution,
            'zones': zones,
            'overall_rate_per_min': round(overall_rate_per_min, 2),
            'threshold_multiplier': threshold_multiplier,
        }

    def _save_zone_plot(
        self,
        rates: np.ndarray,
        segs: List[List],
        zones: List[Dict],
        cutoff: float,
        overall_rate: float,
        bin_size: float,
        duration: float,
        recording_id: int,
    ):
        try:
            out_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
            out_dir.mkdir(parents=True, exist_ok=True)

            n = len(rates)
            bin_starts = [i * bin_size for i in range(n)]
            bin_widths = [min(bin_size, duration - s) for s in bin_starts]

            zone_set = set()
            for z in zones:
                for seg in segs:
                    if round(seg[0] * bin_size, 2) == z['start']:
                        for b in range(seg[0], seg[1] + 1):
                            zone_set.add(b)

            colors = ['#e74c3c' if i in zone_set else '#95a5a6' for i in range(n)]

            fig, ax = plt.subplots(figsize=(14, 5))
            bars = ax.bar(bin_starts, rates, width=bin_widths, align='edge',
                          color=colors, edgecolor='white', linewidth=0.8)

            ax.axhline(overall_rate, color='steelblue', linewidth=1.8,
                       linestyle='--', label=f'Overall avg ({overall_rate:.1f}/min)')
            ax.axhline(cutoff, color='#e74c3c', linewidth=1.5,
                       linestyle=':', label=f'Zone threshold ({cutoff:.1f}/min = {self.config["peak_zone_threshold_multiplier"]:.1f}× avg)')

            for seg in segs[:-1]:
                boundary = (seg[1] + 1) * bin_size
                ax.axvline(boundary, color='black', linewidth=1.0, linestyle='-', alpha=0.4)

            for seg in segs:
                mid = (seg[0] + seg[1] + 1) / 2 * bin_size
                ax.text(mid, max(rates) * 0.95, f'{seg[2]:.0f}',
                        ha='center', va='top', fontsize=8, color='#2c3e50',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

            ax.set_xlabel('Time (s)', fontsize=11)
            ax.set_ylabel('Filler words / minute', fontsize=11)
            ax.set_title(
                f'Filler Word Density — Recording {recording_id}  '
                f'(bin={bin_size:.0f}s, merge_k={self.config["bottom_up_merge_k"]}, '
                f'threshold={self.config["peak_zone_threshold_multiplier"]}×)',
                fontsize=12
            )
            ax.set_xlim(0, duration)
            ax.set_ylim(0, max(max(rates) * 1.15, cutoff * 1.15, 10))
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, axis='y', alpha=0.3)

            plt.tight_layout()
            path = out_dir / 'filler_zones.png'
            plt.savefig(str(path), dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Filler zone plot saved to: {path}")
        except Exception as e:
            print(f"Error saving filler zone plot: {e}")

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

        # Log stable-pitch candidates via sliding window (diagnostic only, not added to score)
        words = [w for seg in transcript.get('segments', []) for w in seg.get('words', [])]
        pitch_timeseries, duration_per_frame = self.fetch_pitch_timeseries(recording_id)
        audio_data, audio_sr = None, None
        candidates = []
        if pitch_timeseries is not None:
            try:
                processed_wav = Path(settings.VIDEO_STORAGE_PATH) / (Path(recording['filename']).stem + '.wav')
                if processed_wav.exists():
                    audio_data, audio_sr = sf.read(str(processed_wav))
            except Exception as e:
                print(f"Could not load audio for spectral flux: {e}")
            candidates, uhh_occurrences = self._log_sliding_window_candidates(
                words, pitch_timeseries, duration_per_frame, audio_data, audio_sr
            )
            print(f"Sliding window: {len(candidates)} candidates, {len(uhh_occurrences)} accepted")
        else:
            print("Pitch timeseries unavailable, skipping sliding window candidates")

        all_occurrences = sorted(filler_occurrences + uhh_occurrences, key=lambda x: x['start_time'])

        statistics = self.calculate_statistics(all_occurrences, duration)

        if pitch_timeseries is not None:
            self.save_pitch_debug_plot(pitch_timeseries, words, candidates, recording_id,
                                       audio_data, audio_sr)

        if uhh_occurrences and audio_data is not None and audio_sr is not None:
            self.save_uhh_audio_clips(uhh_occurrences, recording_id, audio_data, audio_sr)

        if settings.DEBUG:
            self.visualize_filler_words_timeline(filler_occurrences, duration, recording_id)

        peak_zones = self.find_filler_peak_zones(all_occurrences, duration, recording_id)

        return {
            'success': True,
            'recording_id': recording_id,
            'duration': round(duration, 2),
            'detected_language': transcript.get('language', 'unknown'),
            'statistics': statistics,
            'filler_occurrences': all_occurrences[:50],
            'total_filler_occurrences': len(all_occurrences),
            'uhh_occurrences': uhh_occurrences,
            'uhh_occurrences_count': len(uhh_occurrences),
            'peak_zones': peak_zones,
            'message': 'Filler words analysis completed successfully.'
        }
