import streamlit as st
import os
import tempfile
from pathlib import Path
import logging

def setup_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Multimodal Meeting Assistant",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .info-box {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .success-box {
            background-color: #d4edda;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #28a745;
        }
        .warning-box {
            background-color: #fff3cd;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #ffc107;
        }
        .error-box {
            background-color: #f8d7da;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #dc3545;
        }
        </style>
    """, unsafe_allow_html=True)

def create_temp_dir():
    """Create a temporary directory for processing files"""
    temp_dir = Path(tempfile.mkdtemp(prefix="meeting_assistant_"))
    return temp_dir

def get_file_size_mb(file_size_bytes):
    """Convert file size from bytes to MB"""
    return round(file_size_bytes / (1024 * 1024), 2)

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('meeting_assistant.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_audio_file(file):
    """Validate uploaded audio file"""
    allowed_types = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac', 'audio/ogg']
    max_size_mb = 100  # 100MB limit
    
    if file.type not in allowed_types:
        return False, f"Unsupported file type: {file.type}"
    
    if file.size > max_size_mb * 1024 * 1024:
        return False, f"File too large: {get_file_size_mb(file.size)}MB (max: {max_size_mb}MB)"
    
    return True, "File valid"

def create_progress_tracker():
    """Create a progress tracking object"""
    return {
        'current_step': 0,
        'total_steps': 5,
        'step_names': [
            'Processing audio file',
            'Transcribing audio',
            'Analyzing content',
            'Saving results',
            'Generating exports'
        ]
    }

def update_progress(tracker, step_name=None):
    """Update progress tracker"""
    if step_name:
        tracker['current_step'] = tracker['step_names'].index(step_name)
    else:
        tracker['current_step'] += 1
    
    progress = (tracker['current_step'] + 1) / tracker['total_steps']
    return progress, tracker['step_names'][tracker['current_step']]

def cleanup_temp_files(temp_dir):
    """Clean up temporary files"""
    try:
        if temp_dir and temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
    except Exception as e:
        logging.warning(f"Could not cleanup temp files: {e}")

def get_supported_formats():
    """Get list of supported audio formats"""
    return {
        'mp3': 'MP3 Audio (.mp3)',
        'wav': 'WAV Audio (.wav)',
        'm4a': 'M4A Audio (.m4a)',
        'flac': 'FLAC Audio (.flac)',
        'ogg': 'OGG Audio (.ogg)'
    }

def format_timestamp(seconds):
    """Format timestamp in MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"
