import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class AnalyticsDashboard:
    """Comprehensive analytics dashboard for meeting insights"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_meeting_metrics(self) -> Dict:
        """Get comprehensive meeting metrics"""
        try:
            meetings = self.db_manager.get_recent_meetings(limit=100)
            
            if not meetings:
                return {
                    'total_meetings': 0,
                    'total_duration': 0,
                    'total_actions': 0,
                    'avg_duration': 0,
                    'avg_actions': 0,
                    'meeting_trends': [],
                    'action_completion': [],
                    'meeting_types': []
                }
            
            # Calculate basic metrics
            total_meetings = len(meetings)
            total_duration = sum(m.get('duration_seconds', 0) for m in meetings)
            total_actions = sum(m.get('action_count', 0) for m in meetings)
            avg_duration = total_duration / total_meetings if total_meetings > 0 else 0
            avg_actions = total_actions / total_meetings if total_meetings > 0 else 0
            
            # Meeting trends over time
            meeting_trends = self._calculate_meeting_trends(meetings)
            
            # Action completion analysis
            action_completion = self._analyze_action_completion(meetings)
            
            # Meeting type distribution
            meeting_types = self._analyze_meeting_types(meetings)
            
            return {
                'total_meetings': total_meetings,
                'total_duration': total_duration,
                'total_actions': total_actions,
                'avg_duration': avg_duration,
                'avg_actions': avg_actions,
                'meeting_trends': meeting_trends,
                'action_completion': action_completion,
                'meeting_types': meeting_types
            }
            
        except Exception as e:
            self.logger.error(f"Error getting meeting metrics: {e}")
            return {}
    
    def _calculate_meeting_trends(self, meetings: List[Dict]) -> List[Dict]:
        """Calculate meeting trends over time"""
        try:
            trends = []
            for meeting in meetings:
                date_created = meeting.get('date_created')
                if date_created:
                    if isinstance(date_created, str):
                        try:
                            date_obj = datetime.strptime(date_created, '%Y-%m-%d %H:%M:%S')
                        except:
                            date_obj = datetime.now()
                    else:
                        date_obj = date_created
                    
                    trends.append({
                        'date': date_obj.strftime('%Y-%m-%d'),
                        'duration': meeting.get('duration_seconds', 0) / 60,  # Convert to minutes
                        'actions': meeting.get('action_count', 0)
                    })
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating meeting trends: {e}")
            return []
    
    def _analyze_action_completion(self, meetings: List[Dict]) -> List[Dict]:
        """Analyze action item completion patterns"""
        try:
            action_data = []
            for meeting in meetings:
                action_count = meeting.get('action_count', 0)
                if action_count > 0:
                    action_data.append({
                        'meeting_id': meeting.get('id'),
                        'title': meeting.get('title', 'Unknown'),
                        'action_count': action_count,
                        'duration': meeting.get('duration_seconds', 0) / 60
                    })
            
            return action_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing action completion: {e}")
            return []
    
    def _analyze_meeting_types(self, meetings: List[Dict]) -> List[Dict]:
        """Analyze meeting type distribution"""
        try:
            type_counts = {}
            for meeting in meetings:
                title = meeting.get('title', '').lower()
                
                # Simple meeting type detection
                if any(word in title for word in ['standup', 'daily', 'scrum']):
                    meeting_type = 'Standup'
                elif any(word in title for word in ['planning', 'sprint', 'roadmap']):
                    meeting_type = 'Planning'
                elif any(word in title for word in ['review', 'retro', 'feedback']):
                    meeting_type = 'Review'
                elif any(word in title for word in ['client', 'customer', 'stakeholder']):
                    meeting_type = 'Client'
                else:
                    meeting_type = 'Other'
                
                type_counts[meeting_type] = type_counts.get(meeting_type, 0) + 1
            
            return [{'type': k, 'count': v} for k, v in type_counts.items()]
            
        except Exception as e:
            self.logger.error(f"Error analyzing meeting types: {e}")
            return []
    
    def render_dashboard(self):
        """Render the complete analytics dashboard"""
        try:
            st.header("📊 Meeting Analytics Dashboard")
            
            # Get metrics
            metrics = self.get_meeting_metrics()
            
            if not metrics:
                st.info("No meeting data available for analytics")
                return
            
            # Key Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Meetings",
                    metrics['total_meetings'],
                    help="Total number of meetings processed"
                )
            
            with col2:
                st.metric(
                    "Total Duration",
                    f"{metrics['total_duration'] // 60} min",
                    help="Combined duration of all meetings"
                )
            
            with col3:
                st.metric(
                    "Total Actions",
                    metrics['total_actions'],
                    help="Total action items across all meetings"
                )
            
            with col4:
                st.metric(
                    "Avg Actions/Meeting",
                    f"{metrics['avg_actions']:.1f}",
                    help="Average action items per meeting"
                )
            
            st.divider()
            
            # Charts Row
            col1, col2 = st.columns(2)
            
            with col1:
                self._render_meeting_trends_chart(metrics['meeting_trends'])
            
            with col2:
                self._render_meeting_types_chart(metrics['meeting_types'])
            
            # Action Analysis Row
            col1, col2 = st.columns(2)
            
            with col1:
                self._render_action_analysis_chart(metrics['action_completion'])
            
            with col2:
                self._render_productivity_insights(metrics)
            
        except Exception as e:
            st.error(f"Error rendering analytics dashboard: {str(e)}")
            self.logger.error(f"Error rendering analytics dashboard: {e}")
    
    def _render_meeting_trends_chart(self, trends: List[Dict]):
        """Render meeting trends over time chart"""
        try:
            if not trends:
                st.info("No trend data available")
                return
            
            st.subheader("📈 Meeting Trends")
            
            # Create DataFrame
            df = pd.DataFrame(trends)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Line chart for duration trends
            fig = px.line(
                df, 
                x='date', 
                y='duration',
                title="Meeting Duration Trends",
                labels={'duration': 'Duration (minutes)', 'date': 'Date'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering trends chart: {str(e)}")
    
    def _render_meeting_types_chart(self, types: List[Dict]):
        """Render meeting type distribution chart"""
        try:
            if not types:
                st.info("No meeting type data available")
                return
            
            st.subheader("🎯 Meeting Type Distribution")
            
            # Create pie chart
            fig = px.pie(
                types,
                values='count',
                names='type',
                title="Meeting Types"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering types chart: {str(e)}")
    
    def _render_action_analysis_chart(self, actions: List[Dict]):
        """Render action item analysis chart"""
        try:
            if not actions:
                st.info("No action item data available")
                return
            
            st.subheader("🎯 Action Item Analysis")
            
            # Create DataFrame
            df = pd.DataFrame(actions)
            
            # Scatter plot: duration vs actions
            fig = px.scatter(
                df,
                x='duration',
                y='action_count',
                hover_data=['title'],
                title="Meeting Duration vs Action Items",
                labels={'duration': 'Duration (minutes)', 'action_count': 'Action Items'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering action analysis chart: {str(e)}")
    
    def _render_productivity_insights(self, metrics: Dict):
        """Render productivity insights and recommendations"""
        try:
            st.subheader("💡 Productivity Insights")
            
            # Calculate insights
            avg_duration = metrics['avg_duration'] / 60  # Convert to minutes
            
            insights = []
            
            if avg_duration > 60:
                insights.append("⚠️ **Long Meetings**: Average meeting duration is high. Consider breaking into shorter sessions.")
            elif avg_duration < 15:
                insights.append("✅ **Efficient Meetings**: Good meeting duration management.")
            else:
                insights.append("📊 **Balanced Meetings**: Meeting duration appears well-managed.")
            
            if metrics['avg_actions'] > 5:
                insights.append("⚠️ **Action Overload**: High action items per meeting. Consider focusing on fewer, more important items.")
            elif metrics['avg_actions'] < 1:
                insights.append("⚠️ **Low Action Items**: Meetings may lack clear outcomes. Consider adding action item tracking.")
            else:
                insights.append("✅ **Good Action Balance**: Appropriate number of action items per meeting.")
            
            if metrics['total_meetings'] > 20:
                insights.append("📈 **High Meeting Volume**: Consider reviewing meeting frequency and necessity.")
            elif metrics['total_meetings'] < 5:
                insights.append("📉 **Low Meeting Volume**: May need more regular team communication.")
            
            # Display insights
            for insight in insights:
                st.write(insight)
            
            # Recommendations
            st.subheader("🚀 Recommendations")
            st.write("• **Meeting Efficiency**: Focus on clear agendas and time limits")
            st.write("• **Action Tracking**: Ensure action items have owners and deadlines")
            st.write("• **Regular Reviews**: Schedule periodic meeting effectiveness reviews")
            
        except Exception as e:
            st.error(f"Error rendering productivity insights: {str(e)}")
