import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import re

# WeasyPrint import disabled due to system library issues on macOS
WEASYPRINT_AVAILABLE = False
HTML = CSS = FontConfiguration = None
logging.warning("WeasyPrint disabled. PDF export will not be available.")

try:
    from ics import Calendar, Event, Attendee
    ICS_AVAILABLE = True
except ImportError:
    ICS_AVAILABLE = False
    logging.warning("ICS library not available. Calendar export will be disabled.")

class ExportEngine:
    """Handles export of meeting data to various formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates_dir = Path(__file__).parent / "templates"
        
        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize default templates
        self._create_default_templates()
    
    def export_markdown(self, meeting_id: int, transcription_result: Dict, 
                       analysis_result: Dict) -> str:
        """Export meeting data to Markdown format"""
        try:
            markdown_content = self._generate_markdown_content(
                meeting_id, transcription_result, analysis_result
            )
            
            self.logger.info(f"Markdown export generated for meeting {meeting_id}")
            return markdown_content
            
        except Exception as e:
            self.logger.error(f"Error generating markdown export: {e}")
            raise
    
    def export_pdf(self, meeting_id: int, transcription_result: Dict, 
                  analysis_result: Dict) -> bytes:
        """Export meeting data to PDF format"""
        try:
            if not WEASYPRINT_AVAILABLE:
                raise ImportError("WeasyPrint not available. Install weasyprint for PDF export.")
            
            # Generate HTML content
            html_content = self._generate_html_content(
                meeting_id, transcription_result, analysis_result
            )
            
            # Convert HTML to PDF
            pdf_bytes = self._html_to_pdf(html_content)
            
            self.logger.info(f"PDF export generated for meeting {meeting_id}")
            return pdf_bytes
            
        except Exception as e:
            self.logger.error(f"Error generating PDF export: {e}")
            raise
    
    def export_calendar(self, meeting_id: int, analysis_result: Dict) -> str:
        """Export action items to ICS calendar format"""
        try:
            if not ICS_AVAILABLE:
                raise ImportError("ICS library not available. Install ics for calendar export.")
            
            # Generate ICS calendar
            ics_content = self._generate_ics_calendar(meeting_id, analysis_result)
            
            self.logger.info(f"Calendar export generated for meeting {meeting_id}")
            return ics_content
            
        except Exception as e:
            self.logger.error(f"Error generating calendar export: {e}")
            raise
    
    def _generate_markdown_content(self, meeting_id: int, transcription_result: Dict, 
                                 analysis_result: Dict) -> str:
        """Generate comprehensive markdown content"""
        try:
            markdown = f"# Meeting Notes - ID: {meeting_id}\n\n"
            
            # Meeting metadata
            markdown += "## Meeting Information\n"
            markdown += f"- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            markdown += f"- **Duration**: {transcription_result.get('duration', 'Unknown')}\n"
            markdown += f"- **Model Used**: {transcription_result.get('model', 'Unknown')}\n"
            markdown += f"- **Language**: {transcription_result.get('language', 'Unknown')}\n"
            markdown += f"- **Confidence**: {transcription_result.get('confidence', 0):.2f}\n\n"
            
            # Summary
            if analysis_result.get('summary'):
                markdown += "## Executive Summary\n"
                markdown += f"{analysis_result['summary']}\n\n"
            
            # Key Points
            if analysis_result.get('key_points'):
                markdown += "## Key Points\n"
                for i, point in enumerate(analysis_result['key_points'], 1):
                    markdown += f"{i}. {point}\n"
                markdown += "\n"
            
            # Decisions
            if analysis_result.get('decisions'):
                markdown += "## Decisions Made\n"
                for i, decision in enumerate(analysis_result['decisions'], 1):
                    confidence = decision.get('confidence', 'medium')
                    markdown += f"{i}. {decision['text']} *(Confidence: {confidence})*\n"
                markdown += "\n"
            
            # Action Items
            if analysis_result.get('action_items'):
                markdown += "## Action Items\n"
                for i, action in enumerate(analysis_result['action_items'], 1):
                    markdown += f"### {i}. {action['description']}\n"
                    
                    if action.get('owner'):
                        markdown += f"- **Owner**: {action['owner']}\n"
                    
                    if action.get('due_date'):
                        markdown += f"- **Due Date**: {action['due_date']}\n"
                    
                    markdown += f"- **Priority**: {action['priority'].title()}\n"
                    
                    if action.get('context'):
                        markdown += f"- **Context**: {action['context']}\n"
                    
                    markdown += "\n"
            
            # Participants
            if analysis_result.get('participants'):
                markdown += "## Participants\n"
                for participant in analysis_result['participants']:
                    markdown += f"- **{participant['name']}** ({participant['mention_count']} mentions)\n"
                markdown += "\n"
            
            # Full Transcript
            if transcription_result.get('text'):
                markdown += "## Full Transcript\n"
                markdown += "```\n"
                markdown += transcription_result['text']
                markdown += "\n```\n\n"
            
            # Timeline (if segments available)
            if transcription_result.get('segments'):
                markdown += "## Timeline\n"
                for segment in transcription_result['segments'][:20]:  # Show first 20 segments
                    timestamp = self._format_timestamp(segment.get('start', 0))
                    speaker = segment.get('speaker', 'Unknown')
                    text = segment.get('text', '')
                    
                    markdown += f"**{timestamp}** [{speaker}]: {text}\n\n"
            
            # Footer
            markdown += "---\n"
            markdown += f"*Generated by Multimodal Meeting Assistant on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
            
            return markdown
            
        except Exception as e:
            self.logger.error(f"Error generating markdown content: {e}")
            raise
    
    def _generate_html_content(self, meeting_id: int, transcription_result: Dict, 
                             analysis_result: Dict) -> str:
        """Generate HTML content for PDF conversion"""
        try:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Meeting Notes - {meeting_id}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 40px;
                        color: #333;
                    }}
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #34495e;
                        border-bottom: 2px solid #bdc3c7;
                        padding-bottom: 5px;
                        margin-top: 30px;
                    }}
                    h3 {{
                        color: #7f8c8d;
                        margin-top: 25px;
                    }}
                    .metadata {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .action-item {{
                        background-color: #e8f4fd;
                        padding: 15px;
                        margin: 10px 0;
                        border-left: 4px solid #3498db;
                        border-radius: 3px;
                    }}
                    .decision {{
                        background-color: #e8f8f5;
                        padding: 10px;
                        margin: 8px 0;
                        border-left: 4px solid #27ae60;
                        border-radius: 3px;
                    }}
                    .key-point {{
                        background-color: #fef9e7;
                        padding: 10px;
                        margin: 8px 0;
                        border-left: 4px solid #f39c12;
                        border-radius: 3px;
                    }}
                    .participant {{
                        display: inline-block;
                        background-color: #ecf0f1;
                        padding: 5px 10px;
                        margin: 3px;
                        border-radius: 15px;
                        font-size: 0.9em;
                    }}
                    .transcript {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9em;
                        white-space: pre-wrap;
                        max-height: 400px;
                        overflow-y: auto;
                    }}
                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #bdc3c7;
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 0.9em;
                    }}
                </style>
            </head>
            <body>
                <h1>Meeting Notes - ID: {meeting_id}</h1>
                
                <div class="metadata">
                    <h2>Meeting Information</h2>
                    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Duration:</strong> {transcription_result.get('duration', 'Unknown')}</p>
                    <p><strong>Model Used:</strong> {transcription_result.get('model', 'Unknown')}</p>
                    <p><strong>Language:</strong> {transcription_result.get('language', 'Unknown')}</p>
                    <p><strong>Confidence:</strong> {transcription_result.get('confidence', 0):.2f}</p>
                </div>
            """
            
            # Summary
            if analysis_result.get('summary'):
                html += f"""
                <h2>Executive Summary</h2>
                <p>{analysis_result['summary']}</p>
                """
            
            # Key Points
            if analysis_result.get('key_points'):
                html += "<h2>Key Points</h2>"
                for i, point in enumerate(analysis_result['key_points'], 1):
                    html += f'<div class="key-point">{i}. {point}</div>'
            
            # Decisions
            if analysis_result.get('decisions'):
                html += "<h2>Decisions Made</h2>"
                for i, decision in enumerate(analysis_result['decisions'], 1):
                    confidence = decision.get('confidence', 'medium')
                    html += f'<div class="decision">{i}. {decision["text"]} <em>(Confidence: {confidence})</em></div>'
            
            # Action Items
            if analysis_result.get('action_items'):
                html += "<h2>Action Items</h2>"
                for i, action in enumerate(analysis_result['action_items'], 1):
                    html += f'<div class="action-item">'
                    html += f'<h3>{i}. {action["description"]}</h3>'
                    
                    if action.get('owner'):
                        html += f'<p><strong>Owner:</strong> {action["owner"]}</p>'
                    
                    if action.get('due_date'):
                        html += f'<p><strong>Due Date:</strong> {action["due_date"]}</p>'
                    
                    html += f'<p><strong>Priority:</strong> {action["priority"].title()}</p>'
                    
                    if action.get('context'):
                        html += f'<p><strong>Context:</strong> {action["context"]}</p>'
                    
                    html += '</div>'
            
            # Participants
            if analysis_result.get('participants'):
                html += "<h2>Participants</h2>"
                for participant in analysis_result['participants']:
                    html += f'<span class="participant">{participant["name"]} ({participant["mention_count"]} mentions)</span>'
                html += "<br><br>"
            
            # Footer
            html += f"""
                <div class="footer">
                    Generated by Multimodal Meeting Assistant on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"Error generating HTML content: {e}")
            raise
    
    def _html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML content to PDF using WeasyPrint"""
        try:
            # Configure fonts
            font_config = FontConfiguration()
            
            # Create HTML object
            html = HTML(string=html_content)
            
            # Convert to PDF
            pdf_bytes = html.write_pdf(
                stylesheets=[],
                font_config=font_config
            )
            
            return pdf_bytes
            
        except Exception as e:
            self.logger.error(f"Error converting HTML to PDF: {e}")
            raise
    
    def _generate_ics_calendar(self, meeting_id: int, analysis_result: Dict) -> str:
        """Generate ICS calendar with action items"""
        try:
            # Create calendar
            cal = Calendar()
            cal.creator = "Multimodal Meeting Assistant"
            cal.name = f"Meeting {meeting_id} - Action Items"
            cal.description = f"Action items from meeting {meeting_id}"
            
            # Add action items as calendar events
            action_items = analysis_result.get('action_items', [])
            
            for i, action in enumerate(action_items):
                event = Event()
                event.name = f"Action Item: {action['description'][:50]}..."
                event.description = action['description']
                
                # Set due date
                if action.get('due_date'):
                    due_date = datetime.strptime(action['due_date'], '%Y-%m-%d')
                    event.begin = due_date.replace(hour=9, minute=0)  # 9 AM
                    event.end = due_date.replace(hour=10, minute=0)   # 10 AM
                else:
                    # Default to tomorrow if no due date
                    tomorrow = datetime.now() + timedelta(days=1)
                    event.begin = tomorrow.replace(hour=9, minute=0)
                    event.end = tomorrow.replace(hour=10, minute=0)
                
                # Add owner as attendee if available
                if action.get('owner'):
                    attendee = Attendee(
                        email=f"{action['owner'].lower().replace(' ', '.')}@company.com",
                        common_name=action['owner']
                    )
                    event.attendees.add(attendee)
                
                # Set priority and status
                priority = action.get('priority', 'medium')
                event.categories = [f"Priority: {priority.title()}"]
                
                # Add to calendar
                cal.events.add(event)
            
            # Export to string
            ics_content = str(cal)
            
            return ics_content
            
        except Exception as e:
            self.logger.error(f"Error generating ICS calendar: {e}")
            raise
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp in MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _create_default_templates(self):
        """Create default export templates"""
        try:
            # Markdown template
            markdown_template = self.templates_dir / "markdown_template.md"
            if not markdown_template.exists():
                with open(markdown_template, 'w') as f:
                    f.write(self._get_default_markdown_template())
            
            # HTML template
            html_template = self.templates_dir / "html_template.html"
            if not html_template.exists():
                with open(html_template, 'w') as f:
                    f.write(self._get_default_html_template())
            
            # CSS template
            css_template = self.templates_dir / "style_template.css"
            if not css_template.exists():
                with open(css_template, 'w') as f:
                    f.write(self._get_default_css_template())
                    
        except Exception as e:
            self.logger.warning(f"Could not create default templates: {e}")
    
    def _get_default_markdown_template(self) -> str:
        """Get default markdown template"""
        return """# Meeting Notes Template

## Meeting Information
- **Date**: {{date}}
- **Duration**: {{duration}}
- **Participants**: {{participants}}

## Agenda
{{agenda}}

## Discussion Points
{{discussion_points}}

## Decisions Made
{{decisions}}

## Action Items
{{action_items}}

## Next Steps
{{next_steps}}

---
*Generated by Multimodal Meeting Assistant*
"""
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <link rel="stylesheet" href="style_template.css">
</head>
<body>
    <h1>{{title}}</h1>
    {{content}}
</body>
</html>
"""
    
    def _get_default_css_template(self) -> str:
        """Get default CSS template"""
        return """body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 40px;
    color: #333;
}

h1, h2, h3 {
    color: #2c3e50;
}

.metadata {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    margin: 20px 0;
}

.action-item {
    background-color: #e8f4fd;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #3498db;
    border-radius: 3px;
}
"""
    
    def get_export_formats(self) -> List[str]:
        """Get list of available export formats"""
        formats = ["Markdown"]
        
        if WEASYPRINT_AVAILABLE:
            formats.append("PDF")
        
        if ICS_AVAILABLE:
            formats.append("ICS Calendar")
        
        return formats
    
    def validate_export_data(self, transcription_result: Dict, analysis_result: Dict) -> Tuple[bool, str]:
        """Validate data before export"""
        try:
            # Check required fields
            if not transcription_result.get('text'):
                return False, "No transcript text available"
            
            if not analysis_result.get('summary'):
                return False, "No meeting summary available"
            
            return True, "Data valid for export"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Clear any temporary files
            pass
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
