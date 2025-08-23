import os
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Install openai-whisper for transcription functionality.")

try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.utils.hook import ProgressHook
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False
    logging.warning("Pyannote.audio not available. Speaker diarization will be disabled.")

class TranscriptionEngine:
    """Handles audio transcription using OpenAI Whisper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.current_model = None
        self.current_model_size = None
        
        # Model configurations
        self.model_configs = {
            'base': {
                'size': 'base',
                'params': '74M',
                'speed': 'fast',
                'accuracy': 'good',
                'memory_mb': 1
            },
            'small': {
                'size': 'small',
                'params': '244M', 
                'speed': 'medium',
                'accuracy': 'better',
                'memory_mb': 2
            },
            'medium': {
                'size': 'medium',
                'params': '769M',
                'speed': 'slow',
                'accuracy': 'best',
                'memory_mb': 5
            }
        }
    
    def transcribe(self, audio_path: str, model_size: str = 'base', 
                  language: str = 'auto', enable_diarization: bool = False) -> Dict:
        """Transcribe audio file using Whisper"""
        try:
            if not WHISPER_AVAILABLE:
                raise ImportError("Whisper is not available. Please install openai-whisper.")
            
            # Load model
            model = self._load_model(model_size)
            
            # Get audio duration
            duration = self._get_audio_duration(audio_path)
            
            # Transcribe with Whisper
            self.logger.info(f"Starting transcription with {model_size} model...")
            start_time = time.time()
            
            # Whisper transcription
            result = model.transcribe(
                audio_path,
                language=language if language != 'auto' else None,
                task="transcribe",
                verbose=False
            )
            
            transcription_time = time.time() - start_time
            
            # Process results
            self.logger.info(f"Whisper transcription completed. Raw text length: {len(result['text'])}")
            self.logger.info(f"Raw transcription preview: {result['text'][:200]}...")
            
            transcription_result = {
                'text': result['text'].strip(),
                'segments': self._process_segments(result['segments']),
                'language': result.get('language', language),
                'model': model_size,
                'duration': duration,
                'transcription_time': transcription_time,
                'confidence': self._calculate_confidence(result['segments']),
                'file_size_mb': self._get_file_size_mb(audio_path)
            }
            
            self.logger.info(f"Processed transcription text length: {len(transcription_result['text'])}")
            self.logger.info(f"Processed text preview: {transcription_result['text'][:200]}...")
            
            # Add speaker diarization if enabled
            if enable_diarization and DIARIZATION_AVAILABLE:
                self.logger.info("Adding speaker diarization...")
                speakers = self._add_speaker_diarization(audio_path, transcription_result['segments'])
                transcription_result['speakers'] = speakers
                transcription_result['segments'] = self._merge_speakers_with_segments(
                    transcription_result['segments'], speakers
                )
            
            self.logger.info(f"Transcription completed in {transcription_time:.2f}s")
            return transcription_result
            
        except Exception as e:
            self.logger.error(f"Error in transcription: {e}")
            raise
    
    def _load_model(self, model_size: str):
        """Load Whisper model with caching"""
        try:
            if model_size not in self.model_configs:
                raise ValueError(f"Invalid model size: {model_size}")
            
            # Check if model is already loaded
            if (self.current_model and self.current_model_size == model_size):
                return self.current_model
            
            # Load new model
            self.logger.info(f"Loading Whisper {model_size} model...")
            model = whisper.load_model(model_size)
            
            # Cache the model
            self.models[model_size] = model
            self.current_model = model
            self.current_model_size = model_size
            
            self.logger.info(f"Whisper {model_size} model loaded successfully")
            return model
            
        except Exception as e:
            self.logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def _process_segments(self, segments: List[Dict]) -> List[Dict]:
        """Process and clean Whisper segments"""
        processed_segments = []
        
        for segment in segments:
            processed_segment = {
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': segment.get('avg_logprob', 0.0),
                'no_speech_prob': segment.get('no_speech_prob', 0.0)
            }
            processed_segments.append(processed_segment)
        
        return processed_segments
    
    def _add_speaker_diarization(self, audio_path: str, segments: List[Dict]) -> Dict:
        """Add speaker diarization using pyannote.audio"""
        try:
            if not DIARIZATION_AVAILABLE:
                return {}
            
            # Initialize diarization pipeline
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization@2.1",
                use_auth_token=None  # Use local model
            )
            
            # Run diarization
            diarization = pipeline(audio_path)
            
            # Process diarization results
            speakers = {}
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if speaker not in speakers:
                    speakers[speaker] = {
                        'label': f"Speaker {speaker}",
                        'segments': [],
                        'total_time': 0,
                        'segment_count': 0
                    }
                
                speakers[speaker]['segments'].append({
                    'start': turn.start,
                    'end': turn.end
                })
                speakers[speaker]['total_time'] += turn.end - turn.start
                speakers[speaker]['segment_count'] += 1
            
            return speakers
            
        except Exception as e:
            self.logger.warning(f"Speaker diarization failed: {e}")
            return {}
    
    def _merge_speakers_with_segments(self, segments: List[Dict], speakers: Dict) -> List[Dict]:
        """Merge speaker information with transcription segments"""
        if not speakers:
            return segments
        
        # Create speaker timeline
        speaker_timeline = []
        for speaker_id, speaker_data in speakers.items():
            for segment in speaker_data['segments']:
                speaker_timeline.append({
                    'speaker': speaker_id,
                    'start': segment['start'],
                    'end': segment['end']
                })
        
        # Sort by start time
        speaker_timeline.sort(key=lambda x: x['start'])
        
        # Assign speakers to segments
        for segment in segments:
            segment['speaker'] = self._find_speaker_for_segment(
                segment, speaker_timeline
            )
        
        return segments
    
    def _find_speaker_for_segment(self, segment: Dict, speaker_timeline: List[Dict]) -> str:
        """Find which speaker is talking during a segment"""
        segment_mid = (segment['start'] + segment['end']) / 2
        
        for speaker_info in speaker_timeline:
            if speaker_info['start'] <= segment_mid <= speaker_info['end']:
                return speaker_info['speaker']
        
        return "Unknown"
    
    def _calculate_confidence(self, segments: List[Dict]) -> float:
        """Calculate overall confidence score from segments"""
        if not segments:
            return 0.0
        
        total_confidence = sum(segment.get('avg_logprob', 0.0) for segment in segments)
        return total_confidence / len(segments)
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            import librosa
            return librosa.get_duration(path=audio_path)
        except ImportError:
            # Fallback: estimate from file size (rough approximation)
            file_size = os.path.getsize(audio_path)
            # Assume 128kbps bitrate for estimation
            estimated_duration = (file_size * 8) / (128 * 1000)
            return estimated_duration
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB"""
        try:
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0
    
    def get_model_info(self, model_size: str = None) -> Dict:
        """Get information about available models"""
        if model_size:
            return self.model_configs.get(model_size, {})
        
        return self.model_configs
    
    def get_transcription_stats(self, transcription_result: Dict) -> Dict:
        """Get statistics about the transcription"""
        try:
            text = transcription_result['text']
            segments = transcription_result.get('segments', [])
            
            stats = {
                'word_count': len(text.split()),
                'character_count': len(text),
                'segment_count': len(segments),
                'duration_seconds': transcription_result.get('duration', 0),
                'transcription_time': transcription_result.get('transcription_time', 0),
                'words_per_minute': 0,
                'confidence_score': transcription_result.get('confidence', 0)
            }
            
            # Calculate words per minute
            if stats['duration_seconds'] > 0:
                stats['words_per_minute'] = (stats['word_count'] / stats['duration_seconds']) * 60
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating transcription stats: {e}")
            return {}
    
    def validate_audio_file(self, audio_path: str) -> Tuple[bool, str]:
        """Validate audio file for transcription"""
        try:
            if not os.path.exists(audio_path):
                return False, "Audio file does not exist"
            
            # Check file size
            file_size_mb = self._get_file_size_mb(audio_path)
            if file_size_mb > 100:  # 100MB limit
                return False, f"File too large: {file_size_mb}MB (max: 100MB)"
            
            # Check file extension
            supported_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
            file_ext = Path(audio_path).suffix.lower()
            if file_ext not in supported_extensions:
                return False, f"Unsupported file format: {file_ext}"
            
            return True, "File valid for transcription"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def cleanup(self):
        """Clean up loaded models to free memory"""
        try:
            self.models.clear()
            self.current_model = None
            self.current_model_size = None
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("Transcription engine cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'ja', 'ko', 'zh',
            'ar', 'tr', 'sv', 'da', 'no', 'fi', 'hu', 'cs', 'ro', 'bg', 'hr', 'sk',
            'sl', 'et', 'lv', 'lt', 'mt', 'auto'
        ]
    
    def estimate_transcription_time(self, audio_duration: float, model_size: str = 'base') -> float:
        """Estimate transcription time based on audio duration and model size"""
        # Rough estimates based on model complexity
        speed_factors = {
            'base': 1.0,      # 1x real-time
            'small': 2.0,     # 2x real-time  
            'medium': 4.0      # 4x real-time
        }
        
        factor = speed_factors.get(model_size, 1.0)
        estimated_time = audio_duration / factor
        
        return estimated_time
