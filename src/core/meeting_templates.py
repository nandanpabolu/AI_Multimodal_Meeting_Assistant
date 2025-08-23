import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

class MeetingTemplate:
    """Base class for meeting templates"""
    
    def __init__(self):
        self.name = "Generic Meeting"
        self.description = "Standard meeting template"
        self.key_indicators = []
        self.required_sections = []
        self.action_item_patterns = []
        self.decision_patterns = []
    
    def analyze_meeting(self, transcript: str, segments: List[Dict]) -> Dict:
        """Analyze meeting based on template"""
        return {
            'meeting_type': self.name,
            'key_points': self._extract_key_points(transcript),
            'action_items': self._extract_action_items(transcript),
            'decisions': self._extract_decisions(transcript),
            'participants': self._extract_participants(transcript, segments),
            'next_steps': self._extract_next_steps(transcript)
        }
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract key points based on template"""
        return []
    
    def _extract_action_items(self, transcript: str) -> List[Dict]:
        """Extract action items based on template"""
        return []
    
    def _extract_decisions(self, transcript: str) -> List[str]:
        """Extract decisions based on template"""
        return []
    
    def _extract_participants(self, transcript: str, segments: List[Dict]) -> List[Dict]:
        """Extract participant information"""
        return []
    
    def _extract_next_steps(self, transcript: str) -> List[str]:
        """Extract next steps based on template"""
        return []

class StandupTemplate(MeetingTemplate):
    """Template for daily standup meetings"""
    
    def __init__(self):
        super().__init__()
        self.name = "Daily Standup"
        self.description = "Daily team status update meeting"
        self.key_indicators = [
            'yesterday', 'today', 'blockers', 'impediments', 'sprint', 'story points'
        ]
        self.required_sections = ['yesterday_work', 'today_plan', 'blockers']
        self.action_item_patterns = [
            r'(?:need to|will|going to|plan to)\s+([^.!?]+)',
            r'(?:blocked by|waiting for|need help with)\s+([^.!?]+)'
        ]
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract standup-specific key points"""
        key_points = []
        
        # Look for yesterday/today patterns
        yesterday_pattern = r'(?:yesterday|yesterday i|yesterday we)\s+([^.!?]+)'
        today_pattern = r'(?:today|today i|today we)\s+([^.!?]+)'
        
        for match in re.finditer(yesterday_pattern, transcript, re.IGNORECASE):
            key_points.append(f"Yesterday: {match.group(1).strip()}")
        
        for match in re.finditer(today_pattern, transcript, re.IGNORECASE):
            key_points.append(f"Today: {match.group(1).strip()}")
        
        # Look for blockers
        blocker_pattern = r'(?:blocked|blocker|impediment|stuck|need help)\s+([^.!?]+)'
        for match in re.finditer(blocker_pattern, transcript, re.IGNORECASE):
            key_points.append(f"Blocker: {match.group(1).strip()}")
        
        return key_points[:5]  # Limit to top 5
    
    def _extract_action_items(self, transcript: str) -> List[Dict]:
        """Extract standup-specific action items"""
        action_items = []
        
        # Look for commitment patterns
        commitment_patterns = [
            r'(?:i will|we will|going to|plan to)\s+([^.!?]+)',
            r'(?:need to|have to|must)\s+([^.!?]+)',
            r'(?:tomorrow|next|following)\s+([^.!?]+)'
        ]
        
        for pattern in commitment_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                action_items.append({
                    'description': match.group(1).strip(),
                    'owner': 'Team Member',  # Will be refined later
                    'due_date': self._extract_due_date(match.group(1)),
                    'priority': 'Medium',
                    'context': 'Standup commitment'
                })
        
        return action_items[:10]  # Limit to top 10
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        # Look for date patterns
        date_patterns = [
            r'tomorrow',
            r'next\s+(?:monday|tuesday|wednesday|thursday|friday|week)',
            r'this\s+(?:week|sprint)',
            r'by\s+(?:end\s+of\s+)?(?:day|week|sprint)'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return text  # Return the text for now, will parse later
        
        return None

class PlanningTemplate(MeetingTemplate):
    """Template for project planning meetings"""
    
    def __init__(self):
        super().__init__()
        self.name = "Project Planning"
        self.description = "Project planning and estimation meeting"
        self.key_indicators = [
            'estimate', 'story points', 'sprint', 'milestone', 'deadline', 'scope', 'requirements'
        ]
        self.required_sections = ['objectives', 'timeline', 'resources', 'risks']
        self.action_item_patterns = [
            r'(?:assign|delegate|responsible for)\s+([^.!?]+)',
            r'(?:need to|must|should)\s+([^.!?]+)',
            r'(?:by|before|until)\s+([^.!?]+)'
        ]
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract planning-specific key points"""
        key_points = []
        
        # Look for planning patterns
        planning_patterns = [
            r'(?:objective|goal|target)\s+([^.!?]+)',
            r'(?:milestone|deadline|due date)\s+([^.!?]+)',
            r'(?:estimate|story points|effort)\s+([^.!?]+)',
            r'(?:risk|issue|concern)\s+([^.!?]+)'
        ]
        
        for pattern in planning_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                key_points.append(f"{pattern.split('_')[0].title()}: {match.group(1).strip()}")
        
        return key_points[:8]  # Limit to top 8
    
    def _extract_action_items(self, transcript: str) -> List[Dict]:
        """Extract planning-specific action items"""
        action_items = []
        
        # Look for assignment patterns
        assignment_patterns = [
            r'(?:assign|delegate|responsible for)\s+([^.!?]+)',
            r'(?:need to|must|should)\s+([^.!?]+)',
            r'(?:by|before|until)\s+([^.!?]+)'
        ]
        
        for pattern in assignment_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                action_items.append({
                    'description': match.group(1).strip(),
                    'owner': self._extract_owner(match.group(1)),
                    'due_date': self._extract_due_date(match.group(1)),
                    'priority': self._determine_priority(match.group(1)),
                    'context': 'Planning meeting'
                })
        
        return action_items[:15]  # Limit to top 15
    
    def _extract_owner(self, text: str) -> str:
        """Extract owner from text"""
        # Look for names or roles
        name_patterns = [
            r'(?:assign|delegate|responsible for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:will|should|must)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return 'Unassigned'
    
    def _determine_priority(self, text: str) -> str:
        """Determine priority based on text content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['urgent', 'critical', 'blocker', 'immediate']):
            return 'High'
        elif any(word in text_lower for word in ['important', 'key', 'essential']):
            return 'Medium'
        else:
            return 'Low'

class ReviewTemplate(MeetingTemplate):
    """Template for code/design review meetings"""
    
    def __init__(self):
        super().__init__()
        self.name = "Code/Design Review"
        self.description = "Technical review and feedback meeting"
        self.key_indicators = [
            'review', 'feedback', 'comment', 'issue', 'bug', 'improvement', 'suggestion'
        ]
        self.required_sections = ['review_items', 'feedback', 'decisions', 'follow_up']
        self.action_item_patterns = [
            r'(?:fix|update|change|modify)\s+([^.!?]+)',
            r'(?:need to|should|must)\s+([^.!?]+)',
            r'(?:address|resolve|handle)\s+([^.!?]+)'
        ]
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract review-specific key points"""
        key_points = []
        
        # Look for review patterns
        review_patterns = [
            r'(?:issue|problem|bug)\s+([^.!?]+)',
            r'(?:improvement|enhancement|optimization)\s+([^.!?]+)',
            r'(?:feedback|comment|suggestion)\s+([^.!?]+)',
            r'(?:approve|reject|conditional)\s+([^.!?]+)'
        ]
        
        for pattern in review_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                key_points.append(f"{pattern.split('_')[0].title()}: {match.group(1).strip()}")
        
        return key_points[:6]  # Limit to top 6
    
    def _extract_action_items(self, transcript: str) -> List[Dict]:
        """Extract review-specific action items"""
        action_items = []
        
        # Look for fix patterns
        fix_patterns = [
            r'(?:fix|update|change|modify)\s+([^.!?]+)',
            r'(?:need to|should|must)\s+([^.!?]+)',
            r'(?:address|resolve|handle)\s+([^.!?]+)'
        ]
        
        for pattern in fix_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                action_items.append({
                    'description': match.group(1).strip(),
                    'owner': self._extract_owner(match.group(1)),
                    'due_date': self._extract_due_date(match.group(1)),
                    'priority': self._determine_priority(match.group(1)),
                    'context': 'Review feedback'
                })
        
        return action_items[:12]  # Limit to top 12

class TemplateManager:
    """Manages meeting templates and applies them to meetings"""
    
    def __init__(self):
        self.templates = {
            'standup': StandupTemplate(),
            'planning': PlanningTemplate(),
            'review': ReviewTemplate(),
            'generic': MeetingTemplate()
        }
        self.logger = logging.getLogger(__name__)
    
    def get_available_templates(self) -> Dict[str, Dict]:
        """Get list of available templates"""
        return {
            name: {
                'name': template.name,
                'description': template.description,
                'key_indicators': template.key_indicators
            }
            for name, template in self.templates.items()
        }
    
    def analyze_with_template(self, template_name: str, transcript: str, segments: List[Dict]) -> Dict:
        """Analyze meeting using specific template"""
        if template_name not in self.templates:
            self.logger.warning(f"Template '{template_name}' not found, using generic")
            template_name = 'generic'
        
        template = self.templates[template_name]
        self.logger.info(f"Analyzing meeting with template: {template.name}")
        
        return template.analyze_meeting(transcript, segments)
    
    def auto_detect_template(self, transcript: str) -> str:
        """Automatically detect the best template based on content"""
        transcript_lower = transcript.lower()
        
        # Score each template based on keyword matches
        scores = {}
        for name, template in self.templates.items():
            score = 0
            for indicator in template.key_indicators:
                if indicator.lower() in transcript_lower:
                    score += 1
            scores[name] = score
        
        # Find template with highest score
        best_template = max(scores, key=scores.get)
        self.logger.info(f"Auto-detected template: {best_template} (score: {scores[best_template]})")
        
        return best_template
