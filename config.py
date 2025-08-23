"""
Configuration file for Multimodal Meeting Assistant
Customize these settings based on your needs
"""

import os
from pathlib import Path

# Application Configuration
APP_NAME = "Multimodal Meeting Assistant"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Zero-cost, privacy-focused meeting transcription and analysis"

# File Paths
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
EXPORT_DIR = BASE_DIR / "exports"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
TEMP_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Audio Processing Configuration
AUDIO_CONFIG = {
    "max_file_size_mb": 100,
    "supported_formats": [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
    "sample_rate": 16000,  # Whisper works best with 16kHz
    "chunk_duration": 30,  # seconds per chunk for long files
    "temp_file_cleanup": True
}

# Whisper Configuration
WHISPER_CONFIG = {
    "default_model": "base",  # base, small, medium
    "available_models": ["base", "small", "medium"],
    "model_info": {
        "base": {
            "size": "74MB",
            "speed": "fast",
            "accuracy": "good",
            "memory_mb": 1
        },
        "small": {
            "size": "244MB", 
            "speed": "medium",
            "accuracy": "better",
            "memory_mb": 2
        },
        "medium": {
            "size": "769MB",
            "speed": "slow",
            "accuracy": "best",
            "memory_mb": 5
        }
    },
    "language_detection": True,
    "confidence_threshold": 0.5
}

# NLP Configuration
NLP_CONFIG = {
    "summarization": {
        "model": "facebook/bart-large-cnn",
        "max_length": 150,
        "min_length": 50,
        "chunk_size": 1000
    },
    "action_extraction": {
        "min_description_length": 10,
        "max_action_items": 15,
        "priority_keywords": {
            "high": ["urgent", "asap", "immediately", "critical", "emergency"],
            "low": ["low priority", "when possible", "no rush"]
        }
    },
    "decision_extraction": {
        "max_decisions": 10,
        "confidence_keywords": ["decided", "agreed", "concluded", "determined"]
    },
    "participant_extraction": {
        "min_mention_count": 2,
        "max_participants": 10
    }
}

# Database Configuration
DATABASE_CONFIG = {
    "path": BASE_DIR / "meetings.db",
    "backup_enabled": True,
    "backup_interval_days": 7,
    "max_backups": 10,
    "auto_cleanup_days": 90  # Clean up old meetings after 90 days
}

# Export Configuration
EXPORT_CONFIG = {
    "markdown": {
        "enabled": True,
        "include_transcript": True,
        "include_timeline": True,
        "max_timeline_segments": 20
    },
    "pdf": {
        "enabled": True,
        "page_size": "A4",
        "margins": "1in",
        "include_header": True,
        "include_footer": True
    },
    "calendar": {
        "enabled": True,
        "default_duration_hours": 1,
        "default_start_hour": 9,  # 9 AM
        "include_priority": True
    }
}

# UI Configuration
UI_CONFIG = {
    "theme": "light",
    "sidebar_state": "expanded",
    "page_layout": "wide",
    "max_upload_size_mb": 100,
    "progress_bar_style": "default",
    "show_debug_info": False
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "enable_caching": True,
    "cache_models": True,
    "max_concurrent_transcriptions": 1,
    "memory_limit_mb": 4096,  # 4GB
    "cleanup_interval_minutes": 30
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "meeting_assistant.log",
    "max_file_size_mb": 10,
    "backup_count": 5
}

# Security Configuration
SECURITY_CONFIG = {
    "allowed_file_types": AUDIO_CONFIG["supported_formats"],
    "max_file_size_bytes": AUDIO_CONFIG["max_file_size_mb"] * 1024 * 1024,
    "sanitize_outputs": True,
    "log_sensitive_operations": False
}

# Feature Flags
FEATURES = {
    "speaker_diarization": True,
    "real_time_processing": False,
    "batch_processing": False,
    "cloud_backup": False,
    "api_endpoints": False,
    "mobile_support": False
}

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "development":
    LOGGING_CONFIG["level"] = "DEBUG"
    UI_CONFIG["show_debug_info"] = True
    FEATURES["real_time_processing"] = True

if os.getenv("ENVIRONMENT") == "production":
    LOGGING_CONFIG["level"] = "WARNING"
    PERFORMANCE_CONFIG["enable_caching"] = True
    SECURITY_CONFIG["log_sensitive_operations"] = True

# Validation functions
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check required directories
    for dir_path in [TEMP_DIR, EXPORT_DIR, MODELS_DIR, LOGS_DIR]:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")
    
    # Validate audio config
    if AUDIO_CONFIG["max_file_size_mb"] <= 0:
        errors.append("Max file size must be positive")
    
    # Validate Whisper config
    if WHISPER_CONFIG["default_model"] not in WHISPER_CONFIG["available_models"]:
        errors.append("Default Whisper model must be in available models list")
    
    # Validate database config
    if DATABASE_CONFIG["auto_cleanup_days"] <= 0:
        errors.append("Auto cleanup days must be positive")
    
    return errors

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "base_directory": str(BASE_DIR),
        "max_file_size_mb": AUDIO_CONFIG["max_file_size_mb"],
        "default_whisper_model": WHISPER_CONFIG["default_model"],
        "supported_formats": AUDIO_CONFIG["supported_formats"],
        "features_enabled": {k: v for k, v in FEATURES.items() if v},
        "export_formats": [k for k, v in EXPORT_CONFIG.items() if v.get("enabled", False)]
    }

# Initialize configuration
if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration validation passed!")
        print("\nConfiguration summary:")
        summary = get_config_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
