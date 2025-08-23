import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any

class DatabaseManager:
    """Manages SQLite database operations for the Meeting Assistant"""
    
    def __init__(self, db_path: str = "meetings.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create meetings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meetings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                        meeting_date DATE,
                        audio_file_path TEXT NOT NULL,
                        duration_seconds INTEGER,
                        language TEXT DEFAULT 'en',
                        model_used TEXT DEFAULT 'whisper-base',
                        status TEXT DEFAULT 'completed',
                        file_size_mb REAL,
                        participants_count INTEGER DEFAULT 0
                    )
                """)
                
                # Create transcripts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transcripts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        segments_json TEXT,
                        confidence_score REAL,
                        language_detected TEXT,
                        word_count INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings (id)
                    )
                """)
                
                # Create notes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id INTEGER NOT NULL,
                        summary TEXT,
                        key_points TEXT,
                        decisions_json TEXT,
                        actions_json TEXT,
                        participants_json TEXT,
                        markdown_content TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings (id)
                    )
                """)
                
                # Create action_items table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS action_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id INTEGER NOT NULL,
                        note_id INTEGER,
                        description TEXT NOT NULL,
                        owner TEXT,
                        due_date DATE,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'pending',
                        context TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings (id),
                        FOREIGN KEY (note_id) REFERENCES notes (id)
                    )
                """)
                
                # Create speakers table for diarization
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS speakers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id INTEGER NOT NULL,
                        speaker_id TEXT NOT NULL,
                        speaker_label TEXT,
                        total_time_seconds REAL,
                        segment_count INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings (id)
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def save_meeting(self, title: str, date: datetime, audio_path: str, 
                    duration: int, transcription: Dict, analysis: Dict) -> int:
        """Save a complete meeting with transcription and analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert meeting record
                cursor.execute("""
                    INSERT INTO meetings (
                        title, meeting_date, audio_file_path, duration_seconds,
                        language, model_used, status, file_size_mb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title, date, audio_path, duration,
                    transcription.get('language', 'en'),
                    transcription.get('model', 'whisper-base'),
                    'completed',
                    transcription.get('file_size_mb', 0)
                ))
                
                meeting_id = cursor.lastrowid
                
                # Insert transcript
                cursor.execute("""
                    INSERT INTO transcripts (
                        meeting_id, text, segments_json, confidence_score,
                        language_detected, word_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    meeting_id,
                    transcription['text'],
                    json.dumps(transcription.get('segments', [])),
                    transcription.get('confidence', 0.0),
                    transcription.get('language', 'en'),
                    len(transcription['text'].split())
                ))
                
                # Insert notes
                cursor.execute("""
                    INSERT INTO notes (
                        meeting_id, summary, key_points, decisions_json,
                        actions_json, participants_json, markdown_content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    meeting_id,
                    analysis.get('summary', ''),
                    json.dumps(analysis.get('key_points', [])),
                    json.dumps(analysis.get('decisions', [])),
                    json.dumps(analysis.get('action_items', [])),
                    json.dumps(analysis.get('participants', [])),
                    analysis.get('markdown', '')
                ))
                
                # Insert action items
                for action in analysis.get('action_items', []):
                    cursor.execute("""
                        INSERT INTO action_items (
                            meeting_id, description, owner, due_date,
                            priority, context
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        meeting_id,
                        action.get('description', ''),
                        action.get('owner', ''),
                        action.get('due_date'),
                        action.get('priority', 'medium'),
                        action.get('context', '')
                    ))
                
                # Insert speakers if diarization was used
                if transcription.get('speakers'):
                    for speaker_id, speaker_data in transcription['speakers'].items():
                        cursor.execute("""
                            INSERT INTO speakers (
                                meeting_id, speaker_id, speaker_label,
                                total_time_seconds, segment_count
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            meeting_id,
                            speaker_id,
                            speaker_data.get('label', f'Speaker {speaker_id}'),
                            speaker_data.get('total_time', 0),
                            speaker_data.get('segment_count', 0)
                        ))
                
                conn.commit()
                self.logger.info(f"Meeting saved successfully with ID: {meeting_id}")
                return meeting_id
                
        except Exception as e:
            self.logger.error(f"Error saving meeting: {e}")
            raise
    
    def get_meeting(self, meeting_id: int) -> Optional[Dict]:
        """Get a complete meeting by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get meeting details
                cursor.execute("""
                    SELECT * FROM meetings WHERE id = ?
                """, (meeting_id,))
                meeting = cursor.fetchone()
                
                if not meeting:
                    return None
                
                # Get transcript
                cursor.execute("""
                    SELECT * FROM transcripts WHERE meeting_id = ?
                """, (meeting_id,))
                transcript = cursor.fetchone()
                
                # Get notes
                cursor.execute("""
                    SELECT * FROM notes WHERE meeting_id = ?
                """, (meeting_id,))
                notes = cursor.fetchone()
                
                # Get action items
                cursor.execute("""
                    SELECT * FROM action_items WHERE meeting_id = ?
                """, (meeting_id,))
                action_items = cursor.fetchall()
                
                # Get speakers
                cursor.execute("""
                    SELECT * FROM speakers WHERE meeting_id = ?
                """, (meeting_id,))
                speakers = cursor.fetchall()
                
                # Compile complete meeting data
                meeting_data = {
                    'meeting': dict(meeting),
                    'transcript': dict(transcript) if transcript else {},
                    'notes': dict(notes) if notes else {},
                    'action_items': [dict(item) for item in action_items],
                    'speakers': [dict(speaker) for speaker in speakers]
                }
                
                return meeting_data
                
        except Exception as e:
            self.logger.error(f"Error getting meeting {meeting_id}: {e}")
            return None
    
    def get_recent_meetings(self, limit: int = 10) -> List[Dict]:
        """Get recent meetings for dashboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT m.id, m.title, m.date_created, m.duration_seconds,
                           m.status, COUNT(ai.id) as action_count
                    FROM meetings m
                    LEFT JOIN action_items ai ON m.id = ai.meeting_id
                    GROUP BY m.id
                    ORDER BY m.date_created DESC
                    LIMIT ?
                """, (limit,))
                
                meetings = cursor.fetchall()
                return [dict(meeting) for meeting in meetings]
                
        except Exception as e:
            self.logger.error(f"Error getting recent meetings: {e}")
            return []
    
    def search_meetings(self, query: str) -> List[Dict]:
        """Search meetings by title or content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                search_term = f"%{query}%"
                cursor.execute("""
                    SELECT DISTINCT m.id, m.title, m.date_created, m.duration_seconds
                    FROM meetings m
                    LEFT JOIN transcripts t ON m.id = t.meeting_id
                    LEFT JOIN notes n ON m.id = n.meeting_id
                    WHERE m.title LIKE ? OR t.text LIKE ? OR n.summary LIKE ?
                    ORDER BY m.date_created DESC
                """, (search_term, search_term, search_term))
                
                meetings = cursor.fetchall()
                return [dict(meeting) for meeting in meetings]
                
        except Exception as e:
            self.logger.error(f"Error searching meetings: {e}")
            return []
    
    def update_meeting(self, meeting_id: int, updates: Dict) -> bool:
        """Update meeting information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [meeting_id]
                
                cursor.execute(f"""
                    UPDATE meetings SET {set_clause} WHERE id = ?
                """, values)
                
                conn.commit()
                self.logger.info(f"Meeting {meeting_id} updated successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating meeting {meeting_id}: {e}")
            return False
    
    def delete_meeting(self, meeting_id: int) -> bool:
        """Delete a meeting and all related data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete related records first (foreign key constraints)
                cursor.execute("DELETE FROM action_items WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM speakers WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM notes WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM transcripts WHERE meeting_id = ?", (meeting_id,))
                cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
                
                conn.commit()
                self.logger.info(f"Meeting {meeting_id} deleted successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting meeting {meeting_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total meetings
                cursor.execute("SELECT COUNT(*) FROM meetings")
                stats['total_meetings'] = cursor.fetchone()[0]
                
                # Total duration
                cursor.execute("SELECT SUM(duration_seconds) FROM meetings")
                total_duration = cursor.fetchone()[0] or 0
                stats['total_duration_hours'] = round(total_duration / 3600, 2)
                
                # Total action items
                cursor.execute("SELECT COUNT(*) FROM action_items")
                stats['total_action_items'] = cursor.fetchone()[0]
                
                # Pending action items
                cursor.execute("SELECT COUNT(*) FROM action_items WHERE status = 'pending'")
                stats['pending_action_items'] = cursor.fetchone()[0]
                
                # Recent activity
                cursor.execute("""
                    SELECT COUNT(*) FROM meetings 
                    WHERE date_created >= datetime('now', '-7 days')
                """)
                stats['meetings_last_7_days'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    def export_database(self, export_path: str) -> bool:
        """Export database to SQL file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                with open(export_path, 'w') as f:
                    for line in conn.iterdump():
                        f.write(f'{line}\n')
            
            self.logger.info(f"Database exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting database: {e}")
            return False
