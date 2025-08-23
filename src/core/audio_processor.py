import os
import tempfile
from pathlib import Path
import logging
from typing import Dict, Optional, Tuple
import streamlit as st

try:
    import librosa
    import soundfile as sf
    from pydub import AudioSegment
    import numpy as np
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    logging.warning("Audio processing libraries not available. Install librosa, soundfile, and pydub for full functionality.")

class AudioProcessor:
    """Handles audio file processing, validation, and preprocessing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = None
        self.supported_formats = {
            'mp3': 'audio/mp3',
            'wav': 'audio/wav',
            'wav_alt': 'audio/x-wav',  # Alternative MIME type for WAV files
            'm4a': 'audio/mp4',
            'flac': 'audio/flac',
            'ogg': 'audio/ogg'
        }
        self.max_file_size_mb = 100  # 100MB limit
    
    def get_file_info(self, uploaded_file) -> Dict:
        """Extract basic information about the uploaded file"""
        try:
            file_info = {
                'name': uploaded_file.name,
                'size': self._format_file_size(uploaded_file.size),
                'type': uploaded_file.type,
                'duration': 'Unknown'
            }
            
            # Try to get duration if audio libraries are available
            if AUDIO_LIBS_AVAILABLE:
                try:
                    # Save temporarily to get duration
                    temp_path = self._save_temp_file(uploaded_file)
                    duration = self._get_audio_duration(temp_path)
                    file_info['duration'] = duration
                    
                    # Clean up temp file
                    os.unlink(temp_path)
                except Exception as e:
                    self.logger.warning(f"Could not determine audio duration: {e}")
            
            return file_info
            
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return {
                'name': uploaded_file.name if uploaded_file else 'Unknown',
                'size': 'Unknown',
                'type': 'Unknown',
                'duration': 'Unknown'
            }
    
    def save_uploaded_file(self, uploaded_file) -> str:
        """Save uploaded file to temporary location and return path"""
        try:
            # Validate file
            is_valid, error_msg = self._validate_file(uploaded_file)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Create temp directory if needed
            if not self.temp_dir:
                self.temp_dir = Path(tempfile.mkdtemp(prefix="meeting_assistant_"))
            
            # Generate unique filename
            file_extension = Path(uploaded_file.name).suffix
            temp_filename = f"audio_{int(time.time())}{file_extension}"
            temp_path = self.temp_dir / temp_filename
            
            # Save file
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            self.logger.info(f"File saved to temporary location: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"Error saving uploaded file: {e}")
            raise
    
    def preprocess_audio(self, audio_path: str, target_format: str = 'wav') -> str:
        """Preprocess audio file for optimal transcription"""
        try:
            if not AUDIO_LIBS_AVAILABLE:
                self.logger.warning("Audio preprocessing libraries not available")
                return audio_path
            
            self.logger.info(f"Preprocessing audio: {audio_path}")
            
            # Apply audio quality enhancements
            enhanced_path = self._enhance_audio_quality(audio_path)
            
            # Convert to target format if needed
            if target_format != 'wav':
                enhanced_path = self._convert_audio_format(enhanced_path, target_format)
            
            return enhanced_path
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=None)
            
            # Normalize audio
            audio_normalized = librosa.util.normalize(audio)
            
            # Convert to mono if stereo
            if len(audio_normalized.shape) > 1:
                audio_normalized = librosa.to_mono(audio_normalized)
            
            # Resample to 16kHz if needed (Whisper works best with 16kHz)
            if sr != 16000:
                audio_normalized = librosa.resample(audio_normalized, orig_sr=sr, target_sr=16000)
                sr = 16000
            
            # Generate output path
            output_path = str(Path(audio_path).with_suffix(f'.{target_format}'))
            
            # Save processed audio
            sf.write(output_path, audio_normalized, sr)
            
            self.logger.info(f"Audio preprocessed and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error preprocessing audio: {e}")
            return audio_path  # Return original path if preprocessing fails
    
    def get_audio_duration(self, audio_path: str) -> str:
        """Get audio duration in human-readable format"""
        try:
            if not AUDIO_LIBS_AVAILABLE:
                return "Unknown"
            
            duration_seconds = librosa.get_duration(path=audio_path)
            return self._format_duration(duration_seconds)
            
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            return "Unknown"
    
    def extract_audio_segments(self, audio_path: str, segment_length: int = 30) -> list:
        """Extract audio segments for processing long files"""
        try:
            if not AUDIO_LIBS_AVAILABLE:
                return []
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=None)
            
            # Calculate segment boundaries
            segment_samples = segment_length * sr
            segments = []
            
            for i in range(0, len(audio), segment_samples):
                segment = audio[i:i + segment_samples]
                segment_path = f"{audio_path}_segment_{i//segment_samples}.wav"
                
                # Save segment
                sf.write(segment_path, segment, sr)
                segments.append({
                    'path': segment_path,
                    'start_time': i / sr,
                    'end_time': min((i + segment_samples) / sr, len(audio) / sr)
                })
            
            self.logger.info(f"Extracted {len(segments)} audio segments")
            return segments
            
        except Exception as e:
            self.logger.error(f"Error extracting audio segments: {e}")
            return []
    
    def cleanup_temp_files(self):
        """Clean up temporary files and directories"""
        try:
            if self.temp_dir and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.warning(f"Could not cleanup temp files: {e}")
    
    def _validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """Validate uploaded file"""
        # Check file type - handle multiple MIME types for same format
        file_type = uploaded_file.type
        supported_types = list(self.supported_formats.values())
        
        # Also check file extension as fallback
        file_extension = Path(uploaded_file.name).suffix.lower()
        supported_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        
        if file_type not in supported_types and file_extension not in supported_extensions:
            return False, f"Unsupported file type: {file_type} (extension: {file_extension})"
        
        # Check file size
        if uploaded_file.size > self.max_file_size_mb * 1024 * 1024:
            return False, f"File too large: {self._format_file_size(uploaded_file.size)} (max: {self.max_file_size_mb}MB)"
        
        return True, "File valid"
    
    def _save_temp_file(self, uploaded_file) -> str:
        """Save file to temporary location and return path"""
        temp_fd, temp_path = tempfile.mkstemp(suffix=Path(uploaded_file.name).suffix)
        with os.fdopen(temp_fd, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return temp_path
    
    def _get_audio_duration(self, audio_path: str) -> str:
        """Get audio duration from file"""
        try:
            duration_seconds = librosa.get_duration(path=audio_path)
            return self._format_duration(duration_seconds)
        except:
            return "Unknown"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def get_supported_formats_info(self) -> Dict:
        """Get information about supported audio formats"""
        return {
            'mp3': {
                'name': 'MP3 Audio',
                'extension': '.mp3',
                'description': 'Compressed audio format, widely supported',
                'max_size_mb': 100
            },
            'wav': {
                'name': 'WAV Audio', 
                'extension': '.wav',
                'description': 'Uncompressed audio format, high quality',
                'max_size_mb': 100
            },
            'm4a': {
                'name': 'M4A Audio',
                'extension': '.m4a', 
                'description': 'Apple audio format, good compression',
                'max_size_mb': 100
            },
            'flac': {
                'name': 'FLAC Audio',
                'extension': '.flac',
                'description': 'Lossless compression, high quality',
                'max_size_mb': 100
            },
            'ogg': {
                'name': 'OGG Audio',
                'extension': '.ogg',
                'description': 'Open source audio format',
                'max_size_mb': 100
            }
        }
    
    def convert_audio_format(self, input_path: str, output_format: str) -> str:
        """Convert audio to different format"""
        try:
            if not AUDIO_LIBS_AVAILABLE:
                raise ImportError("Audio conversion libraries not available")
            
            # Load audio with pydub
            audio = AudioSegment.from_file(input_path)
            
            # Generate output path
            output_path = str(Path(input_path).with_suffix(f'.{output_format}'))
            
            # Export in new format
            if output_format == 'wav':
                audio.export(output_path, format='wav')
            elif output_format == 'mp3':
                audio.export(output_path, format='mp3', bitrate='128k')
            elif output_format == 'flac':
                audio.export(output_path, format='flac')
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            self.logger.info(f"Audio converted to {output_format}: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error converting audio format: {e}")
            raise
    
    def _enhance_audio_quality(self, audio_path: str) -> str:
        """Enhance audio quality using FFmpeg filters"""
        try:
            if not self._check_ffmpeg_available():
                self.logger.warning("FFmpeg not available, skipping audio enhancement")
                return audio_path
            
            # Create enhanced output path
            input_path = Path(audio_path)
            enhanced_path = input_path.parent / f"enhanced_{input_path.name}"
            
            # FFmpeg command for audio enhancement
            ffmpeg_cmd = [
                'ffmpeg', '-i', str(input_path),
                '-af', 'highpass=f=200,lowpass=f=3000,volume=1.5,anlmdn=s=7:p=0.002:r=0.01',
                '-ar', '16000',  # Sample rate optimal for Whisper
                '-ac', '1',      # Mono audio
                '-y',            # Overwrite output
                str(enhanced_path)
            ]
            
            import subprocess
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Audio enhanced successfully: {enhanced_path}")
                return str(enhanced_path)
            else:
                self.logger.warning(f"Audio enhancement failed: {result.stderr}")
                return audio_path
                
        except Exception as e:
            self.logger.error(f"Error enhancing audio quality: {e}")
            return audio_path
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available on the system"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def validate_audio_quality(self, audio_path: str) -> Dict:
        """Validate audio quality and detect potential issues"""
        try:
            if not AUDIO_LIBS_AVAILABLE:
                return {'status': 'unknown', 'message': 'Audio libraries not available'}
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=None)
            
            # Check duration
            duration = len(audio) / sr
            if duration < 1:
                return {'status': 'error', 'message': 'Audio too short (less than 1 second)'}
            
            # Check sample rate
            if sr < 8000:
                return {'status': 'warning', 'message': f'Low sample rate: {sr}Hz (recommended: 16kHz+)'}
            
            # Check for silence
            silence_threshold = 0.01
            silence_ratio = np.sum(np.abs(audio) < silence_threshold) / len(audio)
            if silence_ratio > 0.8:
                return {'status': 'warning', 'message': 'High silence ratio detected'}
            
            # Check for clipping
            if np.max(np.abs(audio)) > 0.95:
                return {'status': 'warning', 'message': 'Audio clipping detected'}
            
            # Check for noise
            noise_level = np.std(audio)
            if noise_level < 0.001:
                return {'status': 'warning', 'message': 'Very low audio levels detected'}
            
            return {
                'status': 'good',
                'message': 'Audio quality appears good',
                'duration': duration,
                'sample_rate': sr,
                'silence_ratio': silence_ratio,
                'noise_level': noise_level
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error analyzing audio: {str(e)}'}

# Import time at the top level
import time
