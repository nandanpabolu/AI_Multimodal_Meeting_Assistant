import streamlit as st
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import re

class MeetingEffectivenessScorer:
    """Score meeting effectiveness based on various metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Scoring weights
        self.weights = {
            'duration_efficiency': 0.25,
            'action_item_quality': 0.30,
            'content_structure': 0.20,
            'follow_up_planning': 0.15,
            'participant_engagement': 0.10
        }
    
    def calculate_meeting_score(self, meeting_data: Dict, transcript: Dict, notes: Dict, action_items: List[Dict]) -> Dict:
        """Calculate comprehensive meeting effectiveness score"""
        try:
            scores = {}
            
            # Duration efficiency score
            scores['duration_efficiency'] = self._score_duration_efficiency(
                meeting_data.get('duration_seconds', 0),
                len(action_items)
            )
            
            # Action item quality score
            scores['action_item_quality'] = self._score_action_item_quality(action_items)
            
            # Content structure score
            scores['content_structure'] = self._score_content_structure(notes, transcript)
            
            # Follow-up planning score
            scores['follow_up_planning'] = self._score_follow_up_planning(action_items, notes)
            
            # Participant engagement score
            scores['participant_engagement'] = self._score_participant_engagement(transcript)
            
            # Calculate weighted total score
            total_score = sum(
                scores[metric] * self.weights[metric] 
                for metric in scores.keys()
            )
            
            # Determine grade and category
            grade, category = self._get_grade_and_category(total_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(scores, total_score)
            
            return {
                'total_score': round(total_score, 2),
                'grade': grade,
                'category': category,
                'individual_scores': scores,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating meeting score: {e}")
            return {
                'total_score': 0,
                'grade': 'F',
                'category': 'Unable to Score',
                'individual_scores': {},
                'recommendations': ['Error occurred during scoring'],
                'timestamp': datetime.now().isoformat()
            }
    
    def _score_duration_efficiency(self, duration_seconds: int, action_count: int) -> float:
        """Score based on meeting duration vs action items ratio"""
        try:
            if duration_seconds == 0 or action_count == 0:
                return 5.0  # Neutral score
            
            duration_minutes = duration_seconds / 60
            actions_per_minute = action_count / duration_minutes
            
            # Optimal: 0.1-0.3 actions per minute
            if 0.1 <= actions_per_minute <= 0.3:
                return 10.0  # Excellent
            elif 0.05 <= actions_per_minute <= 0.5:
                return 8.0   # Good
            elif actions_per_minute < 0.05:
                return 6.0   # Fair (too few actions)
            else:
                return 4.0   # Poor (too many actions)
                
        except Exception as e:
            self.logger.error(f"Error scoring duration efficiency: {e}")
            return 5.0
    
    def _score_action_item_quality(self, action_items: List[Dict]) -> float:
        """Score based on action item completeness and quality"""
        try:
            if not action_items:
                return 3.0  # Poor - no action items
            
            total_score = 0
            max_possible = len(action_items) * 10
            
            for action in action_items:
                action_score = 0
                
                # Description quality (0-3 points)
                description = action.get('description', '')
                if description and len(description.strip()) > 10:
                    action_score += 3
                elif description and len(description.strip()) > 5:
                    action_score += 2
                else:
                    action_score += 1
                
                # Owner assignment (0-2 points)
                if action.get('owner'):
                    action_score += 2
                
                # Due date (0-2 points)
                if action.get('due_date'):
                    action_score += 2
                
                # Priority (0-1 point)
                if action.get('priority'):
                    action_score += 1
                
                # Status (0-1 point)
                if action.get('status'):
                    action_score += 1
                
                total_score += action_score
            
            # Convert to 10-point scale
            final_score = (total_score / max_possible) * 10
            return round(final_score, 2)
            
        except Exception as e:
            self.logger.error(f"Error scoring action item quality: {e}")
            return 5.0
    
    def _score_content_structure(self, notes: Dict, transcript: Dict) -> float:
        """Score based on meeting content structure and organization"""
        try:
            score = 5.0  # Start with neutral score
            
            # Summary quality
            if notes.get('summary') and len(notes['summary']) > 50:
                score += 1.5
            elif notes.get('summary') and len(notes['summary']) > 20:
                score += 1.0
            
            # Key points
            key_points = notes.get('key_points', [])
            if len(key_points) >= 3:
                score += 1.5
            elif len(key_points) >= 1:
                score += 1.0
            #test
            # Decisions
            decisions = notes.get('decisions', [])
            if len(decisions) >= 1:
                score += 1.0
            
            # Transcript length (indicates substantial content)
            transcript_text = transcript.get('text', '')
            if len(transcript_text) > 500:
                score += 1.0
            
            return min(10.0, score)
            
        except Exception as e:
            self.logger.error(f"Error scoring content structure: {e}")
            return 5.0
    
    def _score_follow_up_planning(self, action_items: List[Dict], notes: Dict) -> float:
        """Score based on follow-up planning and next steps"""
        try:
            score = 5.0  # Start with neutral score
            
            # Action items with due dates
            actions_with_dates = sum(1 for action in action_items if action.get('due_date'))
            if actions_with_dates > 0:
                score += 2.0
            
            # Action items with owners
            actions_with_owners = sum(1 for action in action_items if action.get('owner'))
            if actions_with_owners > 0:
                score += 2.0
            
            # Next steps mentioned in notes
            summary = notes.get('summary', '').lower()
            if any(word in summary for word in ['next', 'follow', 'schedule', 'plan']):
                score += 1.0
            
            return min(10.0, score)
            
        except Exception as e:
            self.logger.error(f"Error scoring follow-up planning: {e}")
            return 5.0
    
    def _score_participant_engagement(self, transcript: Dict) -> float:
        """Score based on participant engagement indicators"""
        try:
            score = 5.0  # Start with neutral score
            
            transcript_text = transcript.get('text', '').lower()
            
            # Engagement indicators
            engagement_words = [
                'question', 'discuss', 'agree', 'disagree', 'suggest', 'propose',
                'think', 'believe', 'consider', 'review', 'feedback', 'input'
            ]
            
            engagement_count = sum(1 for word in engagement_words if word in transcript_text)
            
            if engagement_count >= 5:
                score += 3.0
            elif engagement_count >= 3:
                score += 2.0
            elif engagement_count >= 1:
                score += 1.0
            
            # Questions asked
            question_count = transcript_text.count('?')
            if question_count >= 3:
                score += 2.0
            elif question_count >= 1:
                score += 1.0
            
            return min(10.0, score)
            
        except Exception as e:
            self.logger.error(f"Error scoring participant engagement: {e}")
            return 5.0
    
    def _get_grade_and_category(self, total_score: float) -> Tuple[str, str]:
        """Convert score to letter grade and category"""
        if total_score >= 9.0:
            return 'A', 'Excellent'
        elif total_score >= 8.0:
            return 'B', 'Good'
        elif total_score >= 7.0:
            return 'C', 'Satisfactory'
        elif total_score >= 6.0:
            return 'D', 'Needs Improvement'
        else:
            return 'F', 'Poor'
    
    def _generate_recommendations(self, scores: Dict, total_score: float) -> List[str]:
        """Generate specific recommendations based on scores"""
        recommendations = []
        
        # Duration efficiency recommendations
        if scores.get('duration_efficiency', 5) < 7:
            recommendations.append("⏰ **Optimize meeting duration** - Consider shorter, more focused meetings")
        
        # Action item quality recommendations
        if scores.get('action_item_quality', 5) < 7:
            recommendations.append("🎯 **Improve action items** - Ensure each action has an owner, due date, and clear description")
        
        # Content structure recommendations
        if scores.get('content_structure', 5) < 7:
            recommendations.append("📝 **Enhance meeting structure** - Create clear agendas and document key decisions")
        
        # Follow-up planning recommendations
        if scores.get('follow_up_planning', 5) < 7:
            recommendations.append("📅 **Plan follow-ups** - Schedule follow-up meetings and set clear deadlines")
        
        # Participant engagement recommendations
        if scores.get('participant_engagement', 5) < 7:
            recommendations.append("👥 **Increase engagement** - Encourage questions and active participation")
        
        # Overall recommendations based on total score
        if total_score < 6:
            recommendations.append("🚨 **Immediate attention needed** - This meeting needs significant improvement")
        elif total_score < 7.5:
            recommendations.append("⚠️ **Room for improvement** - Focus on the areas with lowest scores")
        elif total_score >= 8.5:
            recommendations.append("✅ **Great meeting!** - Consider sharing best practices with the team")
        
        return recommendations
    
    def render_scoring_dashboard(self, meeting_id: int, meeting_data: Dict, transcript: Dict, notes: Dict, action_items: List[Dict]):
        """Render the scoring dashboard in Streamlit"""
        try:
            st.header("📊 Meeting Effectiveness Score")
            
            # Calculate score
            score_result = self.calculate_meeting_score(meeting_data, transcript, notes, action_items)
            
            # Display overall score
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Overall Score",
                    f"{score_result['total_score']}/10",
                    f"Grade: {score_result['grade']}"
                )
            
            with col2:
                st.metric(
                    "Category",
                    score_result['category'],
                    help="Meeting effectiveness classification"
                )
            
            with col3:
                st.metric(
                    "Action Items",
                    len(action_items),
                    help="Total action items identified"
                )
            
            st.divider()
            
            # Individual metric scores
            st.subheader("📈 Detailed Scoring")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Duration efficiency
                duration_score = score_result['individual_scores'].get('duration_efficiency', 0)
                st.metric(
                    "⏰ Duration Efficiency",
                    f"{duration_score}/10",
                    help="Based on action items per minute ratio"
                )
                
                # Action item quality
                action_score = score_result['individual_scores'].get('action_item_quality', 0)
                st.metric(
                    "🎯 Action Item Quality",
                    f"{action_score}/10",
                    help="Based on completeness and clarity"
                )
                
                # Content structure
                content_score = score_result['individual_scores'].get('content_structure', 0)
                st.metric(
                    "📝 Content Structure",
                    f"{content_score}/10",
                    help="Based on meeting organization and documentation"
                )
            
            with col2:
                # Follow-up planning
                followup_score = score_result['individual_scores'].get('follow_up_planning', 0)
                st.metric(
                    "📅 Follow-up Planning",
                    f"{followup_score}/10",
                    help="Based on next steps and deadlines"
                )
                
                # Participant engagement
                engagement_score = score_result['individual_scores'].get('participant_engagement', 0)
                st.metric(
                    "👥 Participant Engagement",
                    f"{engagement_score}/10",
                    help="Based on interaction indicators"
                )
            
            st.divider()
            
            # Recommendations
            st.subheader("💡 Recommendations")
            for recommendation in score_result['recommendations']:
                st.write(recommendation)
            
            # Score breakdown chart
            st.subheader("📊 Score Breakdown")
            
            # Create a simple bar chart using Streamlit
            metrics = list(score_result['individual_scores'].keys())
            values = list(score_result['individual_scores'].values())
            
            # Display as a simple chart
            for i, (metric, value) in enumerate(zip(metrics, values)):
                metric_name = metric.replace('_', ' ').title()
                st.write(f"**{metric_name}**: {value}/10")
                st.progress(value / 10)
            
            st.divider()
            
            # Export score data
            if st.button("📊 Export Score Report", key=f"export_score_{meeting_id}"):
                score_json = {
                    "meeting_id": meeting_id,
                    "meeting_title": meeting_data.get('title', 'Unknown'),
                    "scoring_results": score_result
                }
                
                st.download_button(
                    "Download Score Report (JSON)",
                    str(score_json),
                    file_name=f"meeting_score_{meeting_id}.json",
                    mime="application/json"
                )
                
        except Exception as e:
            st.error(f"Error rendering scoring dashboard: {str(e)}")
            self.logger.error(f"Error rendering scoring dashboard: {e}")
