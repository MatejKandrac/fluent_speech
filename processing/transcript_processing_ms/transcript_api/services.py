import os
from pathlib import Path
from typing import Dict, Any, Optional

from django.conf import settings

from .db_connection import get_recording_by_id, save_transcript_words, mark_transcript_processing_finished


class TranscriptProcessingService:

    def __init__(self):
        self.config = settings.WHISPER_CONFIG
        print(f"Loaded Whisper configuration: {self.config}")

    def transcribe_audio(self, audio_path: str) -> Optional[Dict[str, Any]]:
        try:
            import whisper

            model_name = self.config['whisper_model']
            print(f"Loading Whisper model: {model_name}")
            model = whisper.load_model(model_name)

            # Parse suppress_tokens - empty string means suppress nothing (preserve filler words)
            suppress_tokens_str = self.config.get('suppress_tokens', '')
            if suppress_tokens_str == '':
                # Empty list disables all token suppression, preserving filler words
                suppress_tokens = []
                print("[DEBUG] Token suppression disabled - filler words will be preserved")
            else:
                # Parse comma-separated list of token IDs if provided
                suppress_tokens = [int(t.strip()) for t in suppress_tokens_str.split(',') if t.strip()]
                print(f"[DEBUG] Suppressing tokens: {suppress_tokens}")

            print(f"Transcribing audio file: {audio_path}")
            result = model.transcribe(
                audio_path,
                word_timestamps=self.config['word_timestamps'],
                verbose=False,
                temperature=self.config['temperature'],
                condition_on_previous_text=False,
                no_speech_threshold=self.config['no_speech_threshold'],
                logprob_threshold=self.config['logprob_threshold'],
                compression_ratio_threshold=self.config['compression_ratio_threshold'],
                suppress_tokens=suppress_tokens  # Empty list preserves all tokens including fillers
            )

            return result

        except ImportError:
            print("ERROR: Whisper is not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None

    def process_transcript(self, recording_id: int) -> Dict[str, Any]:
        print(f"Processing transcript for recording ID: {recording_id}")

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
        min_duration = self.config['min_audio_duration']
        if duration < min_duration:
            return {
                'success': False,
                'error': f'Audio duration ({duration:.2f}s) is less than minimum required ({min_duration}s)'
            }

        # Transcribe audio
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return {'success': False, 'error': 'Transcription failed'}

        print(f"Transcription completed. Detected language: {transcript.get('language', 'unknown')}")

        # Save transcript words to database
        segments = transcript.get('segments', [])
        if segments:
            save_success = save_transcript_words(recording_id, segments)
            if not save_success:
                print(f"Warning: Failed to save transcript words to database for recording {recording_id}")

        # Optionally save transcript to file
        if self.config['save_transcript_to_file'] and settings.DEBUG:
            output_dir = Path(settings.BASE_DIR) / 'debug_output' / str(recording_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            transcript_file = output_dir / 'transcript.txt'

            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript["text"])

            print(f"Transcript saved to: {transcript_file}")

        mark_transcript_processing_finished(recording_id)
        print(f"Marked transcript_processing_finished=True for recording ID: {recording_id}")

        return {
            'success': True,
            'recording_id': recording_id,
            'duration': round(duration, 2),
            'detected_language': transcript.get('language', 'unknown'),
            'text': transcript.get('text', ''),
            'segments': transcript.get('segments', []),
            'message': 'Transcript processing completed successfully.'
        }
