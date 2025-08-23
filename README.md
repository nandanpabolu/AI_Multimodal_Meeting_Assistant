# 🎙️ Multimodal Meeting Assistant

A comprehensive, AI-powered meeting transcription and analysis tool that transforms audio meetings into actionable insights, action items, and professional reports.

## ✨ **Features**

### 🎯 **Core Functionality**
- **Audio Transcription**: OpenAI Whisper-powered transcription
- **NLP Analysis**: Intelligent summarization and key point extraction
- **Action Item Tracking**: Automatic extraction with owners and due dates
- **Meeting Templates**: Specialized templates for different meeting types
- **Database Storage**: Local SQLite database for privacy

### 📊 **Advanced Analytics**
- **Analytics Dashboard**: Comprehensive meeting metrics and insights
- **Interactive Charts**: Visual data representation with Plotly
- **Productivity Insights**: AI-powered recommendations
- **Meeting Effectiveness Scoring**: 5-dimensional scoring system

### 📤 **Export Capabilities**
- **Multiple Formats**: Markdown, HTML, JSON, CSV, ICS calendar
- **Professional Reports**: Beautiful HTML templates
- **Bulk Export**: Export all formats simultaneously
- **Custom Templates**: Flexible export customization

### 🎨 **User Experience**
- **Modern UI**: Clean, professional Streamlit interface
- **Tabbed Navigation**: Organized feature access
- **Search & Filter**: Find meetings quickly
- **Responsive Design**: Works on all devices

## 🚀 **Quick Start**

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/multimodal-meeting-assistant.git
cd multimodal-meeting-assistant
```

### **2. Create Virtual Environment**
```bash
python -m venv meeting_assistant_env
source meeting_assistant_env/bin/activate  # On Windows: meeting_assistant_env\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Run the Application**
```bash
streamlit run main.py
```

The app will open at `http://localhost:8501`

## 📁 **Project Structure**

```
multimodal-meeting-assistant/
├── src/                           # Source code
│   ├── core/                     # Core functionality
│   │   ├── app.py               # Main Streamlit application
│   │   ├── nlp_engine.py        # NLP analysis engine
│   │   ├── audio_processor.py   # Audio processing utilities
│   │   ├── transcription.py     # Transcription engine
│   │   ├── database.py          # Database management
│   │   └── meeting_templates.py # Meeting template system
│   ├── analytics/                # Analytics features
│   │   ├── analytics_dashboard.py # Analytics dashboard
│   │   └── meeting_scoring.py   # Meeting effectiveness scoring
│   ├── export/                   # Export functionality
│   │   ├── enhanced_exports.py  # Enhanced export engine
│   │   └── export_engine.py     # Core export engine
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   └── helpers.py           # Helper functions
│   └── templates/                # HTML/CSS templates
│       ├── html_template.html
│       ├── style_template.css
│       └── markdown_template.md
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── config.py                     # Configuration settings
├── LICENSE                       # License information
└── README.md                     # This file
```

## 🔧 **Configuration**

### **Environment Variables**
Create a `.env` file in the root directory:

```env
# Optional: Customize Whisper model size
WHISPER_MODEL_SIZE=base  # Options: tiny, base, small, medium, large

# Optional: Customize Streamlit settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### **Audio File Support**
- **Formats**: MP3, WAV, M4A, FLAC, OGG
- **Size Limit**: Up to 100MB per file
- **Quality**: Automatic audio enhancement

## 📊 **Usage Guide**

### **1. Upload Audio**
- Drag and drop or browse for audio files
- Supported formats: MP3, WAV, M4A, FLAC, OGG
- Enter meeting title and select meeting type

### **2. Process Meeting**
- Choose Whisper model size (base/small/medium)
- Enable speaker diarization (optional)
- Click "Process Meeting Audio"

### **3. Review Results**
- **Summary Tab**: AI-generated meeting summary
- **Action Items**: Extracted tasks with owners and due dates
- **Key Points**: Important discussion highlights
- **Analytics**: Meeting insights and metrics
- **Scoring**: Meeting effectiveness evaluation

### **4. Export & Share**
- Multiple export formats available
- Professional HTML reports
- Calendar integration (ICS)
- Bulk export functionality

## 🎯 **Meeting Templates**

### **Available Templates**
- **Standup**: Daily team updates
- **Planning**: Project planning and strategy
- **Review**: Performance and project reviews
- **Generic**: General meeting format

### **Custom Templates**
Create custom templates by modifying `src/core/meeting_templates.py`

## 📈 **Analytics Dashboard**

### **Metrics Available**
- Total meetings and duration
- Action item completion rates
- Meeting type distribution
- Productivity trends
- Participant engagement

### **Visualizations**
- Interactive charts with Plotly
- Trend analysis
- Performance comparisons
- Custom date ranges

## 🚀 **Deployment**

### **Local Development**
```bash
streamlit run main.py
```

### **Streamlit Cloud**
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Deploy automatically

### **Docker Deployment**
```bash
docker build -t meeting-assistant .
docker run -p 8501:8501 meeting-assistant
```

## 🔒 **Privacy & Security**

- **Local Processing**: All audio processing happens locally
- **No Cloud Storage**: Audio files are not uploaded to external services
- **Database Privacy**: SQLite database stored locally
- **No API Keys**: Zero external dependencies

## 🛠️ **Development**

### **Install Development Dependencies**
```bash
pip install -r requirements-dev.txt
```

### **Run Tests**
```bash
python -m pytest tests/
```

### **Code Quality**
```bash
black src/
flake8 src/
mypy src/
```

## 📋 **Requirements**

### **System Requirements**
- Python 3.8+
- 4GB RAM minimum
- 2GB free disk space
- FFmpeg (for audio processing)

### **Python Dependencies**
- Streamlit 1.28+
- OpenAI Whisper
- Transformers (Hugging Face)
- spaCy
- SQLite3
- Plotly
- Pandas

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- OpenAI for Whisper transcription
- Hugging Face for NLP models
- Streamlit for the web framework
- Community contributors

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/yourusername/multimodal-meeting-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/multimodal-meeting-assistant/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/multimodal-meeting-assistant/wiki)

---

**Built with ❤️ for productive meetings everywhere!**
# AI_Multimodal_Meeting_Assistant
