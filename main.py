#!/usr/bin/env python3
"""
Multimodal Meeting Assistant - Main Entry Point
A comprehensive AI-powered meeting transcription and analysis tool
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
from app import main

if __name__ == "__main__":
    main()
