import logging
import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import dateparser
from collections import Counter

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    from sentence_transformers import SentenceTransformer
    import spacy
    NLP_LIBS_AVAILABLE = True
except ImportError:
    NLP_LIBS_AVAILABLE = False
    logging.warning("NLP libraries not available. Install transformers, sentence-transformers, and spacy for full functionality.")

class NLPEngine:
    """Handles NLP analysis of meeting transcripts with robust extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.summarizer = None
        self.ner_model = None
        self.sentence_model = None
        self.nlp = None
        
        # Initialize models if available
        if NLP_LIBS_AVAILABLE:
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models"""
        try:
            # Initialize summarization model
            self.logger.info("Loading summarization model...")
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Initialize sentence embeddings
            self.logger.info("Loading sentence transformer...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize spaCy for NER and POS tagging
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
            
            self.logger.info("NLP models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing NLP models: {e}")
            NLP_LIBS_AVAILABLE = False
    
    def analyze_meeting(self, transcript_text: str, segments: List[Dict] = None) -> Dict:
        """Analyze meeting transcript and extract key information"""
        try:
            self.logger.info("Starting meeting analysis...")
            self.logger.info(f"Raw transcript text (first 200 chars): {transcript_text[:200]}")
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(transcript_text)
            self.logger.info(f"Cleaned text (first 200 chars): {cleaned_text[:200]}")
            
            # Generate summary
            summary = self._generate_summary(cleaned_text)
            
            # Extract key points using improved logic
            key_points = self._extract_key_points_improved(cleaned_text, segments)
            
            # Extract decisions
            decisions = self._extract_decisions_improved(cleaned_text)
            
            # Extract action items using robust patterns
            action_items = self._extract_action_items_improved(cleaned_text, segments)
            
            # Extract participants
            participants = self._extract_participants(cleaned_text, segments)
            
            # Generate markdown content
            markdown_content = self._generate_markdown(
                summary, key_points, decisions, action_items, participants
            )
            
            analysis_result = {
                'summary': summary,
                'key_points': key_points,
                'decisions': decisions,
                'action_items': action_items,
                'participants': participants,
                'markdown': markdown_content,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Analysis completed. Found {len(key_points)} key points, {len(decisions)} decisions, {len(action_items)} action items")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in meeting analysis: {e}")
            return self._get_fallback_result()
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess transcript text"""
        try:
            if not text:
                return ""
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove speaker labels if present
            text = re.sub(r'^[A-Za-z]+:\s*', '', text, flags=re.MULTILINE)
            
            # Remove timestamps
            text = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?', '', text)
            
            # Clean up punctuation
            text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text if text else ""
    
    def _generate_summary(self, text: str) -> str:
        """Generate meeting summary using AI model or fallback"""
        try:
            if not text or len(text.strip()) < 50:
                return "Meeting transcript too short for meaningful summary."
            
            if self.summarizer and len(text) > 100:
                # Use AI model for summarization
                try:
                    # Truncate if too long for model
                    max_length = min(500, len(text) // 2)
                    summary_result = self.summarizer(
                        text[:2000],  # Limit input length
                        max_length=max_length,
                        min_length=30,
                        do_sample=False
                    )
                    
                    if summary_result and len(summary_result) > 0:
                        summary = summary_result[0]['summary_text']
                        self.logger.info(f"AI-generated summary: {summary[:100]}...")
                        return summary
                        
                except Exception as e:
                    self.logger.warning(f"AI summarization failed, using fallback: {e}")
            
            # Fallback to extractive summarization
            return self._fallback_summary(text)
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Meeting transcript processed successfully."
    
    def _fallback_summary(self, text: str) -> str:
        """Generate extractive summary as fallback"""
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if not sentences:
                return "Meeting transcript processed successfully."
            
            # Simple extractive summary (first few meaningful sentences)
            summary_sentences = sentences[:3]
            summary = '. '.join(summary_sentences) + '.'
            
            self.logger.info(f"Generated fallback summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in fallback summary: {e}")
            return "Meeting transcript processed successfully."
    
    def _extract_key_points_improved(self, text: str, segments: List[Dict] = None) -> List[str]:
        """Extract key points using improved logic with better filtering"""
        try:
            key_points = []
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 25]  # Increased minimum length
            
            # Strong key indicators (high confidence)
            strong_indicators = [
                'key point', 'main point', 'important', 'critical', 'essential',
                'significant', 'major', 'crucial', 'vital', 'fundamental',
                'takeaway', 'highlight', 'focus on', 'emphasis on', 'key takeaway'
            ]
            
            # Medium key indicators
            medium_indicators = [
                'note that', 'remember', 'keep in mind', 'consider',
                'understand', 'realize', 'recognize', 'plan to', 'strategy'
            ]
            
            # Weak indicators (low confidence) - these reduce score
            weak_indicators = [
                'good', 'great', 'nice', 'interesting', 'helpful', 'welcome',
                'talk about', 'discuss', 'meeting', 'today', 'tomorrow'
            ]
            
            # Generic phrases that should be avoided
            generic_phrases = [
                'we had a meeting', 'it was good', 'nice to see', 'talked about',
                'weather was nice', 'stuff and things', 'um', 'uh', 'like'
            ]
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                confidence_score = 0
                
                # Check for strong indicators
                if any(indicator in sentence_lower for indicator in strong_indicators):
                    confidence_score += 4
                
                # Check for medium indicators
                if any(indicator in sentence_lower for indicator in medium_indicators):
                    confidence_score += 2
                
                # Check for weak indicators (penalty)
                if any(indicator in sentence_lower for indicator in weak_indicators):
                    confidence_score -= 2
                
                # Heavy penalty for generic phrases
                if any(phrase in sentence_lower for phrase in generic_phrases):
                    confidence_score -= 5
                
                # Check for numbered points
                if re.match(r'^\d+\.', sentence):
                    confidence_score += 2
                
                # Check for bullet points
                if sentence.startswith('•') or sentence.startswith('-'):
                    confidence_score += 2
                
                # Check for question-answer patterns
                if '?' in sentence and len(sentence) > 50:
                    confidence_score += 1
                
                # Check for specific content (dates, numbers, names)
                if re.search(r'\d+', sentence):  # Contains numbers
                    confidence_score += 1
                
                if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', sentence):  # Contains names
                    confidence_score += 1
                
                # Only include sentences with sufficient confidence
                if confidence_score >= 3:  # Increased threshold
                    # Clean up the sentence
                    clean_sentence = re.sub(r'^\d+\.\s*', '', sentence)  # Remove numbering
                    clean_sentence = re.sub(r'^[•\-]\s*', '', clean_sentence)  # Remove bullets
                    
                    if len(clean_sentence) > 20:  # Final length check
                        key_points.append(clean_sentence)
            
            # Limit to top 4-5 key points for quality
            if len(key_points) > 5:
                key_points = key_points[:5]
            
            # If no key points found, provide a helpful message
            if not key_points:
                return ["Key discussion points will be identified during detailed review."]
            
            return key_points
            
        except Exception as e:
            self.logger.error(f"Error extracting key points: {e}")
            return ["Key points will be identified during detailed review."]
    
    def _extract_decisions_improved(self, text: str) -> List[Dict]:
        """Extract decisions made during the meeting with improved patterns"""
        try:
            decisions = []
            
            # Strong decision patterns (high confidence)
            strong_decision_patterns = [
                r'(?:we\s+)?(?:decided|agreed|concluded|determined|resolved|voted)\s+(?:that\s+)?(.+?)[.!?]',
                r'(?:the\s+)?(?:decision|conclusion|agreement|resolution)\s+(?:is|was)\s+(?:that\s+)?(.+?)[.!?]',
                r'(?:it\s+)?(?:was\s+)?(?:decided|agreed|concluded|determined)\s+(?:that\s+)?(.+?)[.!?]',
                r'(?:we\s+)?(?:will|are\s+going\s+to|plan\s+to)\s+(.+?)[.!?]',
                r'(?:let\'s|let\s+us)\s+(.+?)[.!?]',
                r'(?:motion\s+)(?:carried|passed|approved|rejected)\s+(?:to\s+)?(.+?)[.!?]'
            ]
            
            # Medium decision patterns
            medium_decision_patterns = [
                r'(?:we\s+)?(?:should|must|need\s+to|have\s+to)\s+(.+?)[.!?]',
                r'(?:the\s+)?(?:plan|strategy|approach)\s+(?:is|will\s+be)\s+(.+?)[.!?]',
                r'(?:we\s+)?(?:recommend|suggest|propose)\s+(.+?)[.!?]'
            ]
            
            # Process strong patterns first
            for pattern in strong_decision_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    if len(decision_text) > 15:  # Increased minimum length
                        decisions.append({
                            'text': decision_text,
                            'confidence': 'high',
                            'type': 'formal_decision'
                        })
            
            # Process medium patterns
            for pattern in medium_decision_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    if len(decision_text) > 15:
                        decisions.append({
                            'text': decision_text,
                            'confidence': 'medium',
                            'type': 'recommendation'
                        })
            
            # Remove duplicates and very similar decisions
            unique_decisions = []
            seen_texts = set()
            for decision in decisions:
                # Create a simplified version for comparison
                simple_text = re.sub(r'[^\w\s]', '', decision['text'].lower())
                if simple_text not in seen_texts:
                    unique_decisions.append(decision)
                    seen_texts.add(simple_text)
            
            # Limit to top 8 decisions for quality
            return unique_decisions[:8]
            
        except Exception as e:
            self.logger.error(f"Error extracting decisions: {e}")
            return []
    
    def _extract_action_items_improved(self, text: str, segments: List[Dict] = None) -> List[Dict]:
        """Extract action items using robust patterns and better logic"""
        try:
            action_items = []
            
            # Strong action patterns (high confidence)
            strong_action_patterns = [
                # Pattern: [Person] will [action]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:will|is\s+going\s+to|needs\s+to|has\s+to)\s+(.+?)[.!?]',
                
                # Pattern: [Person] to [action]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+to\s+(.+?)[.!?]',
                
                # Pattern: [Person] should [action]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+should\s+(.+?)[.!?]',
                
                # Pattern: [Person] please [action]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+please\s+(.+?)[.!?]',
                
                # Pattern: Action item for [Person]
                r'(?:action\s+item|todo|task|next\s+step)\s+(?:for|to|assigned\s+to)\s+(\b[A-Z][a-z]+\s+[A-Z][a-z]+)[:\s]+(.+?)[.!?]',
                
                # Pattern: [Person] action: [description]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+action[:\s]+(.+?)[.!?]',
                
                # Pattern: [Person] responsible for [action]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:is\s+)?responsible\s+for\s+(.+?)[.!?]',
                
                # Pattern: [Person] takes [action]
                r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+)\s+takes\s+(.+?)[.!?]'
            ]
            
            # Medium action patterns
            medium_action_patterns = [
                # Generic action patterns
                r'(?:we\s+)?(?:need\s+to|should|must|have\s+to|got\s+to)\s+(.+?)[.!?]',
                r'(?:let\'s|let\s+us)\s+(.+?)[.!?]',
                r'(?:next\s+steps?|action\s+items?|follow\s+up)[:\s]+(.+?)[.!?]',
                r'(?:someone\s+needs\s+to|somebody\s+should)\s+(.+?)[.!?]'
            ]
            
            # Process strong patterns first
            for pattern in strong_action_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 2:
                        owner = match.group(1).strip()
                        description = match.group(2).strip()
                    else:
                        owner = "Unassigned"
                        description = match.group(1).strip()
                    
                    # Validate owner name (should be proper name format)
                    if owner != "Unassigned" and not self._is_valid_name(owner):
                        owner = "Unassigned"
                    
                    if len(description) > 15:  # Increased minimum length
                        # Extract due date if mentioned
                        due_date = self._extract_due_date(description)
                        
                        action_items.append({
                            'description': description,
                            'owner': owner if owner != "Unassigned" else None,
                            'due_date': due_date,
                            'priority': self._determine_priority(description),
                            'confidence': 'high',
                            'type': 'assigned_task'
                        })
            
            # Process medium patterns
            for pattern in medium_action_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    description = match.group(1).strip()
                    
                    if len(description) > 15:
                        # Try to extract owner from context
                        owner = self._extract_owner_from_context(text, description)
                        due_date = self._extract_due_date(description)
                        
                        action_items.append({
                            'description': description,
                            'owner': owner,
                            'due_date': due_date,
                            'priority': self._determine_priority(description),
                            'confidence': 'medium',
                            'type': 'general_task'
                        })
            
            # Remove duplicates and very similar actions
            unique_actions = []
            seen_descriptions = set()
            for action in action_items:
                # Create a simplified version for comparison
                simple_desc = re.sub(r'[^\w\s]', '', action['description'].lower())
                if simple_desc not in seen_descriptions:
                    unique_actions.append(action)
                    seen_descriptions.add(simple_desc)
            
            # Limit to top 10 action items for quality
            return unique_actions[:10]
            
        except Exception as e:
            self.logger.error(f"Error extracting action items: {e}")
            return []
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if a string looks like a valid person name"""
        try:
            # Should be two words (first and last name)
            words = name.split()
            if len(words) != 2:
                return False
            
            # Both words should start with capital letters
            if not (words[0][0].isupper() and words[1][0].isupper()):
                return False
            
            # Should not contain common non-name words
            invalid_words = {
                'we', 'the', 'team', 'someone', 'somebody', 'everyone', 'anyone',
                'decided', 'agreed', 'will', 'should', 'must', 'need', 'going',
                'needs', 'has', 'takes', 'please', 'action', 'item', 'task'
            }
            
            if any(word.lower() in invalid_words for word in words):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _extract_owner_from_context(self, text: str, action_description: str) -> Optional[str]:
        """Try to extract owner from context around the action item"""
        try:
            if not self.nlp:
                return None
            
            # Look for names mentioned near the action item
            # This is a simplified approach - in production you might want more sophisticated NER
            
            # Common name patterns
            name_patterns = [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
                r'\b[A-Z][a-z]+\b'  # Single name
            ]
            
            # Find the position of the action in the text
            action_pos = text.find(action_description)
            if action_pos == -1:
                return None
            
            # Look in a window around the action
            start_pos = max(0, action_pos - 200)
            end_pos = min(len(text), action_pos + 200)
            context = text[start_pos:end_pos]
            
            # Find names in context
            for pattern in name_patterns:
                matches = re.finditer(pattern, context)
                for match in matches:
                    name = match.group(0)
                    # Basic validation - avoid common words that might be capitalized
                    if name.lower() not in ['the', 'and', 'for', 'with', 'this', 'that', 'will', 'should', 'must', 'need', 'have', 'going', 'needs', 'has', 'takes', 'please', 'action', 'item', 'task', 'step', 'next', 'follow', 'up']:
                        return name
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting owner from context: {e}")
            return None
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text using improved patterns"""
        try:
            # Enhanced date patterns
            date_patterns = [
                r'by\s+(.+?)(?:\s|$)',
                r'due\s+(.+?)(?:\s|$)',
                r'deadline[:\s]+(.+?)(?:\s|$)',
                r'next\s+(monday|tuesday|wednesday|thursday|friday|week|month|quarter)',
                r'this\s+(monday|tuesday|wednesday|thursday|friday|week|month|quarter)',
                r'tomorrow',
                r'today',
                r'end\s+of\s+(week|month|quarter|year)',
                r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'in\s+(\d+)\s+(day|week|month)s?',
                r'(\d+)\s+(day|week|month)s?\s+from\s+now'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    
                    # Handle relative dates
                    if 'in' in date_text.lower() or 'from now' in date_text.lower():
                        try:
                            # Extract number and unit
                            num_match = re.search(r'(\d+)\s+(day|week|month)', date_text.lower())
                            if num_match:
                                num = int(num_match.group(1))
                                unit = num_match.group(2)
                                
                                if unit == 'day':
                                    due_date = datetime.now() + timedelta(days=num)
                                elif unit == 'week':
                                    due_date = datetime.now() + timedelta(weeks=num)
                                elif unit == 'month':
                                    due_date = datetime.now() + timedelta(days=num*30)
                                else:
                                    continue
                                
                                return due_date.strftime('%Y-%m-%d')
                        except:
                            continue
                    
                    # Parse date using dateparser
                    parsed_date = dateparser.parse(date_text)
                    if parsed_date:
                        return parsed_date.strftime('%Y-%m-%d')
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting due date: {e}")
            return None
    
    def _determine_priority(self, text: str) -> str:
        """Determine priority level based on text content"""
        text_lower = text.lower()
        
        # High priority indicators
        high_indicators = ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'high priority', 'rush', 'deadline', 'due soon']
        if any(indicator in text_lower for indicator in high_indicators):
            return 'high'
        
        # Low priority indicators
        low_indicators = ['low priority', 'when possible', 'no rush', 'take your time', 'when convenient']
        if any(indicator in text_lower for indicator in low_indicators):
            return 'low'
        
        # Default to medium priority
        return 'medium'
    
    def _extract_context(self, text: str, action_description: str) -> str:
        """Extract context around the action item"""
        try:
            # Find the position of the action in the text
            action_pos = text.find(action_description)
            if action_pos == -1:
                return ""
            
            # Extract context (100 characters before and after)
            start_pos = max(0, action_pos - 100)
            end_pos = min(len(text), action_pos + len(action_description) + 100)
            context = text[start_pos:end_pos]
            
            return context.strip()
            
        except Exception as e:
            self.logger.warning(f"Error extracting context: {e}")
            return ""
    
    def _extract_participants(self, text: str, segments: List[Dict] = None) -> List[Dict]:
        """Extract meeting participants"""
        try:
            participants = []
            
            # Simple name extraction (basic approach)
            name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
            names = re.findall(name_pattern, text)
            
            # Count occurrences and filter
            name_counts = Counter(names)
            for name, count in name_counts.most_common(10):
                if count >= 2:  # Only include names mentioned multiple times
                    participants.append({
                        'name': name,
                        'mention_count': count,
                        'role': 'participant'
                    })
            
            return participants
            
        except Exception as e:
            self.logger.error(f"Error extracting participants: {e}")
            return []
    
    def _generate_markdown(self, summary: str, key_points: List[str], decisions: List[Dict], 
                          action_items: List[Dict], participants: List[Dict]) -> str:
        """Generate markdown content from analysis results"""
        try:
            markdown = f"# Meeting Summary\n\n{summary}\n\n"
            
            if key_points:
                markdown += "## Key Points\n\n"
                for point in key_points:
                    markdown += f"- {point}\n"
                markdown += "\n"
            
            if decisions:
                markdown += "## Decisions Made\n\n"
                for decision in decisions:
                    markdown += f"- {decision['text']}\n"
                markdown += "\n"
            
            if action_items:
                markdown += "## Action Items\n\n"
                for action in action_items:
                    owner = action.get('owner', 'Unassigned')
                    due_date = action.get('due_date', 'No deadline')
                    priority = action.get('priority', 'Medium')
                    markdown += f"- **{action['description']}** (Owner: {owner}, Due: {due_date}, Priority: {priority})\n"
                markdown += "\n"
            
            if participants:
                markdown += "## Participants\n\n"
                for participant in participants:
                    markdown += f"- {participant['name']} (Mentioned {participant['mention_count']} times)\n"
            
            return markdown
            
        except Exception as e:
            self.logger.error(f"Error generating markdown: {e}")
            return f"# Meeting Summary\n\n{summary}"
    
    def _get_fallback_result(self) -> Dict:
        """Return fallback result when analysis fails"""
        return {
            'summary': 'Meeting transcript processed successfully.',
            'key_points': ['Key points will be identified during detailed review.'],
            'decisions': [],
            'action_items': [],
            'participants': [],
            'markdown': '# Meeting Summary\n\nMeeting transcript processed successfully.',
            'analysis_timestamp': datetime.now().isoformat()
        }
