import streamlit as st
import os
import tempfile
from datetime import datetime
import logging

# Import core components
from core.nlp_engine import NLPEngine
from core.audio_processor import AudioProcessor
from core.transcription import TranscriptionEngine
from core.database import DatabaseManager
from core.meeting_templates import TemplateManager

# Import enhanced features
from analytics.analytics_dashboard import AnalyticsDashboard
from analytics.meeting_scoring import MeetingEffectivenessScorer
from export.enhanced_exports import EnhancedExportEngine
from export.export_engine import ExportEngine

# Import utilities
from utils.helpers import setup_page, create_temp_dir

def main():
    """Main Streamlit application for Multimodal Meeting Assistant"""
    
    # Page setup
    setup_page()
    
    # Initialize components
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'audio_processor' not in st.session_state:
        st.session_state.audio_processor = AudioProcessor()
    
    if 'transcription_engine' not in st.session_state:
        st.session_state.transcription_engine = TranscriptionEngine()
    
    if 'nlp_engine' not in st.session_state:
        st.session_state.nlp_engine = NLPEngine()
    
    if 'export_engine' not in st.session_state:
        st.session_state.export_engine = ExportEngine()
    
    if 'template_manager' not in st.session_state:
        st.session_state.template_manager = TemplateManager()
    
    if 'analytics_dashboard' not in st.session_state:
        st.session_state.analytics_dashboard = AnalyticsDashboard(st.session_state.db_manager)
    
    if 'enhanced_export_engine' not in st.session_state:
        st.session_state.enhanced_export_engine = EnhancedExportEngine(st.session_state.db_manager)
    
    if 'meeting_scorer' not in st.session_state:
        st.session_state.meeting_scorer = MeetingEffectivenessScorer()
    
    # Main UI
    st.title("🎙️ Multimodal Meeting Assistant")
    st.markdown("**Zero-cost, privacy-focused meeting transcription and analysis**")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_size = st.selectbox(
            "Whisper Model Size",
            ["base", "small", "medium"],
            help="Base: Fast, Small: Balanced, Medium: Most Accurate"
        )
        
        # Language selection
        language = st.selectbox(
            "Audio Language",
            ["en", "es", "fr", "de", "it", "pt", "auto"],
            help="Select language or auto-detect"
        )
        
        # Processing options
        enable_diarization = st.checkbox(
            "Enable Speaker Diarization",
            value=False,
            help="Identify different speakers (slower but more detailed)"
        )
        
        st.divider()
        
        # Meeting info
        st.subheader("📝 Meeting Details")
        meeting_title = st.text_input("Meeting Title", placeholder="Weekly Team Standup")
        meeting_date = st.date_input("Meeting Date", value=datetime.now())
        
        # Meeting type selection
        available_templates = st.session_state.template_manager.get_available_templates()
        template_names = list(available_templates.keys())
        template_descriptions = [available_templates[name]['description'] for name in template_names]
        
        meeting_type = st.selectbox(
            "Meeting Type",
            options=template_names,
            format_func=lambda x: f"{available_templates[x]['name']} - {available_templates[x]['description']}",
            help="Select meeting type for better analysis"
        )
        
        # Auto-detect option
        if st.checkbox("Auto-detect meeting type", value=True, help="Automatically detect meeting type from content"):
            auto_detect = True
        else:
            auto_detect = False
        
        # Export options
        st.subheader("📤 Export Options")
        export_formats = st.multiselect(
            "Export Formats",
            ["Markdown", "PDF", "ICS Calendar"],
            default=["Markdown"]
        )
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["🎵 Upload & Process", "📊 Analytics Dashboard", "📋 Meeting History"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("🎵 Upload Audio File")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=['mp3', 'wav', 'm4a', 'flac', 'ogg'],
                help="Supported formats: MP3, WAV, M4A, FLAC, OGG"
            )
            
            if uploaded_file is not None:
                # Display file info
                file_details = st.session_state.audio_processor.get_file_info(uploaded_file)
                st.info(f"📁 **File**: {file_details['name']} | **Size**: {file_details['size']} | **Duration**: {file_details['duration']}")
                
                # Process button
                if st.button("🚀 Process Meeting Audio", type="primary", use_container_width=True):
                    if not meeting_title:
                        st.warning("⚠️ Please enter a meeting title for better organization")
                        meeting_title = uploaded_file.name
                    
                    with st.spinner("Processing your meeting audio..."):
                        process_audio_file(uploaded_file, model_size, language, enable_diarization, meeting_title, meeting_date, meeting_type, auto_detect)
    
        # Get recent meetings first (moved outside col2 to fix scope issue)
        recent_meetings = st.session_state.db_manager.get_recent_meetings(limit=5)
        
        with col2:
            st.header("📊 Quick Stats")
            
            # Search and filter meetings
            search_query = st.text_input("🔍 Search meetings", placeholder="Search by title or content...")
            if search_query:
                search_results = st.session_state.db_manager.search_meetings(search_query)
                if search_results:
                    st.subheader(f"🔍 Search Results ({len(search_results)} found)")
                    for meeting in search_results[:3]:  # Show top 3 results
                        st.write(f"📅 {meeting['title'][:30]}...")
                        duration_seconds = meeting.get('duration_seconds', 0)
                        if duration_seconds:
                            duration_min = round(duration_seconds / 60, 1)
                            st.write(f"⏱️ {duration_min} min")
                        st.write("---")
                else:
                    st.info("No meetings found matching your search")
            
            # Meeting statistics
            if recent_meetings:
                total_meetings = len(recent_meetings)
                total_duration = sum(m.get('duration_seconds', 0) for m in recent_meetings)
                total_actions = sum(m.get('action_count', 0) for m in recent_meetings)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Meetings", total_meetings)
                with col2:
                    st.metric("Total Duration", f"{total_duration // 60} min")
                with col3:
                    st.metric("Total Actions", total_actions)
                
                st.divider()
            
            # Display recent meetings
            if recent_meetings:
                st.subheader("Recent Meetings")
                for meeting in recent_meetings:
                    st.write(f"📅 {meeting['title'][:30]}...")
                    # Handle duration - convert seconds to minutes or show "Unknown"
                    duration_seconds = meeting.get('duration_seconds', 0)
                    if duration_seconds:
                        duration_min = round(duration_seconds / 60, 1)
                        st.write(f"⏱️ {duration_min} min")
                    else:
                        st.write("⏱️ Duration unknown")
                    
                    # Show meeting date and action count
                    meeting_date = meeting.get('date_created', 'Unknown date')
                    if isinstance(meeting_date, str):
                        st.write(f"📅 {meeting_date}")
                    else:
                        st.write(f"📅 {meeting_date.strftime('%Y-%m-%d') if hasattr(meeting_date, 'strftime') else str(meeting_date)}")
                    
                    action_count = meeting.get('action_count', 0)
                    st.write(f"🎯 {action_count} action items")
                    
                    # Add view details button
                    if st.button(f"👁️ View Details", key=f"view_{meeting['id']}"):
                        display_meeting_details(meeting['id'])
                    
                    st.write("---")
            else:
                st.info("No meetings processed yet")
    
    with tab2:
        # Analytics Dashboard
        st.session_state.analytics_dashboard.render_dashboard()
    
    with tab3:
        # Meeting History
        st.header("📋 Meeting History")
        
        # Get all meetings for history view
        all_meetings = st.session_state.db_manager.get_recent_meetings(limit=50)
        
        if all_meetings:
            # Search and filter
            history_search = st.text_input("🔍 Search meeting history", placeholder="Search by title or content...", key="history_search")
            
            if history_search:
                search_results = st.session_state.db_manager.search_meetings(history_search)
                meetings_to_show = search_results
                st.info(f"Found {len(search_results)} meetings matching '{history_search}'")
            else:
                meetings_to_show = all_meetings
            
            # Display meetings in a table format
            for meeting in meetings_to_show:
                with st.expander(f"📅 {meeting['title']} - {meeting.get('date_created', 'Unknown date')}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write("**Duration:**")
                        duration_seconds = meeting.get('duration_seconds', 0)
                        if duration_seconds:
                            duration_min = round(duration_seconds / 60, 1)
                            st.write(f"⏱️ {duration_min} min")
                        else:
                            st.write("⏱️ Unknown")
                    
                    with col2:
                        st.write("**Actions:**")
                        action_count = meeting.get('action_count', 0)
                        st.write(f"🎯 {action_count}")
                    
                    with col3:
                        st.write("**Status:**")
                        st.write(f"✅ {meeting.get('status', 'Unknown')}")
                    
                    with col4:
                        if st.button("👁️ View Details", key=f"history_view_{meeting['id']}"):
                            display_meeting_details(meeting['id'])
        else:
            st.info("No meeting history available")
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        🔒 <strong>Privacy First:</strong> All processing happens locally on your device<br>
        💰 <strong>Zero Cost:</strong> No cloud services, no API keys, no hidden fees<br>
        🚀 <strong>Powered by:</strong> OpenAI Whisper + Hugging Face + Streamlit
        </div>
        """,
        unsafe_allow_html=True
    )

def process_audio_file(uploaded_file, model_size, language, enable_diarization, meeting_title, meeting_date, meeting_type, auto_detect):
    """Process the uploaded audio file through the complete pipeline"""
    
    try:
        # Create progress container
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            st.subheader("🔄 Processing Pipeline")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Step 1: Audio Processing
        status_text.text("Step 1/5: Processing audio file...")
        progress_bar.progress(20)
        
        temp_audio_path = st.session_state.audio_processor.save_uploaded_file(uploaded_file)
        
        # Step 2: Transcription
        status_text.text("Step 2/5: Transcribing audio...")
        progress_bar.progress(40)
        
        transcription_result = st.session_state.transcription_engine.transcribe(
            temp_audio_path, 
            model_size, 
            language,
            enable_diarization
        )
        
        # Step 3: NLP Analysis
        status_text.text("Step 3/5: Analyzing content...")
        progress_bar.progress(60)
        
        # Determine meeting type
        if auto_detect:
            detected_type = st.session_state.template_manager.auto_detect_template(transcription_result['text'])
            st.info(f"🤖 Auto-detected meeting type: {detected_type}")
            meeting_type = detected_type
        
        # Analyze with template
        template_analysis = st.session_state.template_manager.analyze_with_template(
            meeting_type, 
            transcription_result['text'], 
            transcription_result['segments']
        )
        
        # Combine with standard NLP analysis
        analysis_result = st.session_state.nlp_engine.analyze_meeting(
            transcription_result['text'],
            transcription_result['segments']
        )
        
        # Merge template analysis with standard analysis
        analysis_result.update(template_analysis)
        
        # Step 4: Save to Database
        status_text.text("Step 4/5: Saving results...")
        progress_bar.progress(80)
        
        meeting_id = st.session_state.db_manager.save_meeting(
            title=meeting_title or uploaded_file.name,
            date=meeting_date,
            audio_path=temp_audio_path,
            duration=transcription_result['duration'],
            transcription=transcription_result,
            analysis=analysis_result
        )
        
        # Step 5: Complete
        status_text.text("Step 5/5: Processing complete!")
        progress_bar.progress(100)
        
        # Success message
        st.success(f"✅ Meeting processed successfully! Meeting ID: {meeting_id}")
        
        # Display results
        display_meeting_results(meeting_id, transcription_result, analysis_result)
        
        # Debug: Show raw transcript for troubleshooting
        with st.expander("🔍 Debug: Raw Transcript"):
            st.write("**Raw transcription text:**")
            st.text_area("Raw Text", transcription_result['text'], height=200, key="debug_raw_text")
            st.write("**Transcription segments:**")
            st.json(transcription_result.get('segments', []))
        
        # Cleanup
        st.session_state.audio_processor.cleanup_temp_files()
        
    except Exception as e:
        st.error(f"❌ Error processing audio: {str(e)}")
        st.exception(e)

def display_meeting_details(meeting_id):
    """Display detailed view of a specific meeting"""
    try:
        meeting_data = st.session_state.db_manager.get_meeting(meeting_id)
        if not meeting_data:
            st.error("Meeting not found")
            return
        
        meeting = meeting_data['meeting']
        transcript = meeting_data['transcript']
        notes = meeting_data['notes']
        action_items = meeting_data['action_items']
        
        st.header(f"📋 {meeting['title']}")
        
        # Meeting metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Duration", f"{meeting.get('duration_seconds', 0) // 60} min")
        with col2:
            st.metric("Status", meeting.get('status', 'Unknown'))
        with col3:
            st.metric("Action Items", len(action_items))
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Summary", "🎯 Action Items", "📊 Transcript", "📤 Export", "📊 Scoring"])
        
        with tab1:
            if notes.get('summary'):
                st.subheader("Meeting Summary")
                st.write(notes['summary'])
            
            if notes.get('key_points'):
                st.subheader("Key Points")
                for point in notes.get('key_points', []):
                    st.write(f"• {point}")
        
        with tab2:
            st.subheader("Action Items")
            if action_items:
                for i, action in enumerate(action_items):
                    with st.expander(f"Action {i+1}: {action['description'][:50]}..."):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.text_input(f"Owner {i+1}", value=action.get('owner', ''), key=f"owner_detail_{i}")
                        with col2:
                            st.date_input(f"Due Date {i+1}", value=action.get('due_date'), key=f"due_date_detail_{i}")
                        with col3:
                            st.selectbox(f"Priority {i+1}", ['Low', 'Medium', 'High'], key=f"priority_detail_{i}")
            else:
                st.info("No action items for this meeting")
        
        with tab3:
            st.subheader("Full Transcript")
            if transcript.get('text'):
                st.text_area("Transcript", transcript['text'], height=300, key=f"transcript_{meeting_id}")
            else:
                st.info("No transcript available")
        
        with tab4:
            st.subheader("Export Options")
            
            # Enhanced export formats
            available_formats = st.session_state.enhanced_export_engine.get_available_formats()
            
            # Display format descriptions
            st.info("💡 **Export Formats Available:**")
            for fmt in available_formats:
                st.write(f"• **{fmt['format']}**: {fmt['description']}")
            
            st.divider()
            
            # Export buttons in a grid
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Export Markdown", key=f"md_{meeting_id}"):
                    markdown_content = st.session_state.enhanced_export_engine.export_summary_report(
                        meeting_id, transcript, notes
                    )
                    st.download_button(
                        "Download Markdown",
                        markdown_content,
                        file_name=f"meeting_notes_{meeting_id}.md",
                        mime="text/markdown"
                    )
            
            with col2:
                if st.button("📊 Export HTML", key=f"html_{meeting_id}"):
                    html_content = st.session_state.enhanced_export_engine.export_html(
                        meeting_id, transcript, notes
                    )
                    st.download_button(
                        "Download HTML",
                        html_content,
                        file_name=f"meeting_notes_{meeting_id}.html",
                        mime="text/html"
                    )
            
            with col3:
                if st.button("📅 Export Calendar", key=f"ics_{meeting_id}"):
                    ics_content = st.session_state.export_engine.export_calendar(
                        meeting_id, notes
                    )
                    st.download_button(
                        "Download Calendar",
                        ics_content,
                        file_name=f"meeting_actions_{meeting_id}.ics",
                        mime="text/calendar"
                    )
            
            # Additional export formats
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Export JSON", key=f"json_{meeting_id}"):
                    json_content = st.session_state.enhanced_export_engine.export_json(
                        meeting_id, transcript, notes
                    )
                    st.download_button(
                        "Download JSON",
                        json_content,
                        file_name=f"meeting_data_{meeting_id}.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("📋 Export CSV", key=f"csv_{meeting_id}"):
                    csv_content = st.session_state.enhanced_export_engine.export_csv(
                        meeting_id, transcript, notes
                    )
                    st.download_button(
                        "Download CSV",
                        csv_content,
                        file_name=f"meeting_data_{meeting_id}.csv",
                        mime="text/csv"
                    )
            
            # Bulk export option
            st.divider()
            if st.button("🚀 Export All Formats", key=f"bulk_{meeting_id}", type="primary"):
                with st.spinner("Generating all export formats..."):
                    try:
                        all_exports = st.session_state.enhanced_export_engine.export_all_formats(
                            meeting_id, transcript, notes
                        )
                        
                        st.success("✅ All export formats generated successfully!")
                        
                        # Create download buttons for all formats
                        for format_name, content in all_exports.items():
                            file_ext = "md" if format_name in ["markdown", "summary"] else format_name
                            st.download_button(
                                f"📥 Download {format_name.upper()}",
                                content,
                                file_name=f"meeting_{meeting_id}_{format_name}.{file_ext}",
                                mime="text/plain"
                            )
                        
                    except Exception as e:
                        st.error(f"❌ Error generating bulk exports: {str(e)}")
    
        with tab5:
            # Meeting Effectiveness Scoring
            st.session_state.meeting_scorer.render_scoring_dashboard(
                meeting_id, meeting, transcript, notes, action_items
            )
    
    except Exception as e:
        st.error(f"Error displaying meeting details: {str(e)}")
        st.exception(e)

def display_meeting_results(meeting_id, transcription_result, analysis_result):
    """Display the processed meeting results"""
    
    st.header("📋 Meeting Results")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "🎯 Action Items", "📊 Transcript", "📤 Export"])
    
    with tab1:
        st.subheader("Meeting Summary")
        st.write(analysis_result['summary'])
        
        if analysis_result['key_points']:
            st.subheader("Key Points")
            for point in analysis_result['key_points']:
                st.write(f"• {point}")
    
    with tab2:
        st.subheader("Action Items")
        if analysis_result['action_items']:
            for i, action in enumerate(analysis_result['action_items']):
                with st.expander(f"Action {i+1}: {action['description'][:50]}..."):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.text_input(f"Owner {i+1}", value=action.get('owner', ''), key=f"owner_{i}")
                    with col2:
                        st.date_input(f"Due Date {i+1}", value=action.get('due_date'), key=f"due_date_{i}")
                    with col3:
                        st.selectbox(f"Priority {i+1}", ['Low', 'Medium', 'High'], key=f"priority_{i}")
        else:
            st.info("No action items detected")
    
    with tab3:
        st.subheader("Full Transcript")
        st.text_area("Transcript", transcription_result['text'], height=300)
        
        if transcription_result.get('segments'):
            st.subheader("Timeline")
            for segment in transcription_result['segments'][:10]:  # Show first 10 segments
                st.write(f"**{segment['start']:.1f}s - {segment['end']:.1f}s**: {segment['text']}")
    
    with tab4:
        st.subheader("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export Markdown"):
                markdown_content = st.session_state.export_engine.export_markdown(
                    meeting_id, transcription_result, analysis_result
                )
                st.download_button(
                    "Download Markdown",
                    markdown_content,
                    file_name=f"meeting_notes_{meeting_id}.md",
                    mime="text/markdown"
                )
        
        with col2:
            if st.button("📊 Export PDF"):
                pdf_bytes = st.session_state.export_engine.export_pdf(
                    meeting_id, transcription_result, analysis_result
                )
                st.download_button(
                    "Download PDF",
                    pdf_bytes,
                    file_name=f"meeting_notes_{meeting_id}.pdf",
                    mime="application/pdf"
                )
        
        with col3:
            if st.button("📅 Export Calendar"):
                ics_content = st.session_state.export_engine.export_calendar(
                    meeting_id, analysis_result
                )
                st.download_button(
                    "Download Calendar",
                    ics_content,
                    file_name=f"meeting_actions_{meeting_id}.ics",
                    mime="text/calendar"
                )

if __name__ == "__main__":
    main()
