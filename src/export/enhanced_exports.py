import streamlit as st
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class EnhancedExportEngine:
    """Enhanced export engine with multiple formats and better error handling"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def export_json(self, meeting_id: int, transcript: Dict, notes: Dict) -> str:
        """Export meeting data as structured JSON"""
        try:
            # Get meeting details
            meeting_data = self.db_manager.get_meeting(meeting_id)
            if not meeting_data:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            meeting = meeting_data['meeting']
            action_items = meeting_data['action_items']
            
            # Create comprehensive export structure
            export_data = {
                "meeting_info": {
                    "id": meeting['id'],
                    "title": meeting['title'],
                    "date_created": str(meeting.get('date_created', '')),
                    "duration_seconds": meeting.get('duration_seconds', 0),
                    "status": meeting.get('status', 'Unknown')
                },
                "transcript": {
                    "full_text": transcript.get('text', ''),
                    "segments": transcript.get('segments', []),
                    "language": transcript.get('language', 'en'),
                    "confidence": transcript.get('confidence', 0.0)
                },
                "analysis": {
                    "summary": notes.get('summary', ''),
                    "key_points": notes.get('key_points', []),
                    "decisions": notes.get('decisions', []),
                    "action_items": [
                        {
                            "description": action.get('description', ''),
                            "owner": action.get('owner', ''),
                            "due_date": str(action.get('due_date', '')) if action.get('due_date') else None,
                            "priority": action.get('priority', 'Medium'),
                            "status": action.get('status', 'Open')
                        }
                        for action in action_items
                    ]
                },
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "export_version": "2.0",
                    "total_action_items": len(action_items),
                    "meeting_duration_minutes": round(meeting.get('duration_seconds', 0) / 60, 1)
                }
            }
            
            return json.dumps(export_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error exporting JSON: {e}")
            raise
    
    def export_csv(self, meeting_id: int, transcript: Dict, notes: Dict) -> str:
        """Export meeting data as CSV"""
        try:
            # Get meeting details
            meeting_data = self.db_manager.get_meeting(meeting_id)
            if not meeting_data:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            meeting = meeting_data['meeting']
            action_items = meeting_data['action_items']
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "Meeting ID", "Meeting Title", "Date Created", "Duration (min)", 
                "Status", "Summary", "Key Points", "Decisions"
            ])
            
            # Meeting row
            duration_min = round(meeting.get('duration_seconds', 0) / 60, 1)
            key_points = '; '.join(notes.get('key_points', []))
            decisions = '; '.join(notes.get('decisions', []))
            
            writer.writerow([
                meeting['id'],
                meeting['title'],
                meeting.get('date_created', ''),
                duration_min,
                meeting.get('status', 'Unknown'),
                notes.get('summary', ''),
                key_points,
                decisions
            ])
            
            # Action items section
            if action_items:
                writer.writerow([])  # Empty row
                writer.writerow([
                    "Action Item", "Owner", "Due Date", "Priority", "Status"
                ])
                
                for action in action_items:
                    writer.writerow([
                        action.get('description', ''),
                        action.get('owner', ''),
                        action.get('due_date', ''),
                        action.get('priority', 'Medium'),
                        action.get('status', 'Open')
                    ])
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            raise
    
    def export_html(self, meeting_id: int, transcript: Dict, notes: Dict) -> str:
        """Export meeting data as formatted HTML"""
        try:
            # Get meeting details
            meeting_data = self.db_manager.get_meeting(meeting_id)
            if not meeting_data:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            meeting = meeting_data['meeting']
            action_items = meeting_data['action_items']
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Meeting Notes - {meeting['title']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                    .section {{ margin-bottom: 30px; }}
                    .section h2 {{ color: #2c3e50; border-left: 4px solid #3498db; padding-left: 15px; }}
                    .action-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #e74c3c; }}
                    .metric {{ display: inline-block; margin: 20px; text-align: center; }}
                    .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                    .metric-label {{ color: #7f8c8d; font-size: 14px; }}
                    .transcript {{ background: #f8f9fa; padding: 20px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📋 Meeting Notes</h1>
                    <h2>{meeting['title']}</h2>
                    <div class="metric">
                        <div class="metric-value">{meeting.get('date_created', 'Unknown date')}</div>
                        <div class="metric-label">Meeting Date</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{round(meeting.get('duration_seconds', 0) / 60, 1)} min</div>
                        <div class="metric-label">Duration</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{len(action_items)}</div>
                        <div class="metric-label">Action Items</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📝 Summary</h2>
                    <p>{notes.get('summary', 'No summary available')}</p>
                </div>
                
                <div class="section">
                    <h2>🎯 Key Points</h2>
                    <ul>
                        {''.join([f'<li>{point}</li>' for point in notes.get('key_points', [])])}
                    </ul>
                </div>
                
                <div class="section">
                    <h2>✅ Decisions</h2>
                    <ul>
                        {''.join([f'<li>{decision}</li>' for decision in notes.get('decisions', [])])}
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🚀 Action Items</h2>
                    {''.join([f'''
                    <div class="action-item">
                        <strong>Action:</strong> {action.get('description', '')}<br>
                        <strong>Owner:</strong> {action.get('owner', 'Unassigned')}<br>
                        <strong>Due Date:</strong> {action.get('due_date', 'No deadline')}<br>
                        <strong>Priority:</strong> {action.get('priority', 'Medium')}<br>
                        <strong>Status:</strong> {action.get('status', 'Open')}
                    </div>
                    ''' for action in action_items])}
                </div>
                
                <div class="section">
                    <h2>📝 Full Transcript</h2>
                    <div class="transcript">{transcript.get('text', 'No transcript available')}</div>
                </div>
                
                <div class="section">
                    <h2>📊 Meeting Statistics</h2>
                    <p><strong>Export Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Total Duration:</strong> {round(meeting.get('duration_seconds', 0) / 60, 1)} minutes</p>
                    <p><strong>Action Items:</strong> {len(action_items)}</p>
                    <p><strong>Status:</strong> {meeting.get('status', 'Unknown')}</p>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"Error exporting HTML: {e}")
            raise
    
    def export_summary_report(self, meeting_id: int, transcript: Dict, notes: Dict) -> str:
        """Export a concise summary report"""
        try:
            # Get meeting details
            meeting_data = self.db_manager.get_meeting(meeting_id)
            if not meeting_data:
                raise ValueError(f"Meeting {meeting_id} not found")
            
            meeting = meeting_data['meeting']
            action_items = meeting_data['action_items']
            
            # Create summary report
            report = f"""
# Meeting Summary Report

## Meeting Details
- **Title**: {meeting['title']}
- **Date**: {meeting.get('date_created', 'Unknown')}
- **Duration**: {round(meeting.get('duration_seconds', 0) / 60, 1)} minutes
- **Status**: {meeting.get('status', 'Unknown')}

## Executive Summary
{notes.get('summary', 'No summary available')}

## Key Points
{chr(10).join([f'- {point}' for point in notes.get('key_points', [])])}

## Decisions Made
{chr(10).join([f'- {decision}' for decision in notes.get('decisions', [])])}

## Action Items ({len(action_items)} total)
{chr(10).join([f'- **{action.get('description', '')}** (Owner: {action.get('owner', 'Unassigned')}, Due: {action.get('due_date', 'No deadline')}, Priority: {action.get('priority', 'Medium')})' for action in action_items])}

## Next Steps
1. Review and assign action items
2. Schedule follow-up meetings if needed
3. Share summary with stakeholders

---
*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
            """
            
            return report.strip()
            
        except Exception as e:
            self.logger.error(f"Error exporting summary report: {e}")
            raise
    
    def get_available_formats(self) -> List[Dict[str, str]]:
        """Get list of available export formats"""
        return [
            {
                "format": "JSON",
                "extension": "json",
                "description": "Structured data export for integration",
                "mime_type": "application/json"
            },
            {
                "format": "CSV",
                "extension": "csv",
                "description": "Spreadsheet-friendly format",
                "mime_type": "text/csv"
            },
            {
                "format": "HTML",
                "extension": "html",
                "description": "Formatted web page",
                "mime_type": "text/html"
            },
            {
                "format": "Markdown",
                "extension": "md",
                "description": "Plain text with formatting",
                "mime_type": "text/markdown"
            },
            {
                "format": "Summary Report",
                "extension": "md",
                "description": "Concise executive summary",
                "mime_type": "text/markdown"
            }
        ]
    
    def export_all_formats(self, meeting_id: int, transcript: Dict, notes: Dict) -> Dict[str, str]:
        """Export meeting data in all available formats"""
        try:
            exports = {}
            
            # Export in each format
            exports['json'] = self.export_json(meeting_id, transcript, notes)
            exports['csv'] = self.export_csv(meeting_id, transcript, notes)
            exports['html'] = self.export_html(meeting_id, transcript, notes)
            exports['markdown'] = self.export_summary_report(meeting_id, transcript, notes)
            exports['summary'] = self.export_summary_report(meeting_id, transcript, notes)
            
            return exports
            
        except Exception as e:
            self.logger.error(f"Error exporting all formats: {e}")
            raise
