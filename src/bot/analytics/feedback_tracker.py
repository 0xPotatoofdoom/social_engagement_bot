"""
Feedback Tracking System for Voice Evolution
Tracks opportunity quality ratings and reply version selections to improve voice over time
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
from bot.utils.logging_config import get_component_logger

logger = get_component_logger("feedback_tracker")

@dataclass
class OpportunityFeedback:
    """Feedback data for a single opportunity"""
    opportunity_id: str
    timestamp: str
    
    # Opportunity quality feedback
    quality_rating: Optional[int] = None  # 1-5 scale
    quality_reason: Optional[str] = None
    
    # Reply selection feedback
    selected_reply_version: Optional[str] = None  # 'primary', 'alt1', 'alt2', 'custom'
    custom_reply_used: Optional[str] = None
    
    # Performance tracking
    actual_engagement: Optional[Dict] = None  # Actual engagement metrics if available
    voice_effectiveness: Optional[float] = None  # How well voice aligned with desired outcome
    
    # Learning insights
    what_worked: Optional[str] = None
    what_could_improve: Optional[str] = None
    voice_adjustments_needed: Optional[List[str]] = None
    
    # User improvement suggestions
    user_improvement_suggestions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OpportunityFeedback':
        return cls(**data)

@dataclass
class VoiceLearningInsights:
    """Aggregated insights for voice evolution"""
    timestamp: str
    period_analyzed: str  # 'week', 'month', etc.
    
    # Opportunity quality trends
    avg_quality_rating: float
    quality_trend: str  # 'improving', 'declining', 'stable'
    
    # Reply effectiveness patterns
    most_effective_reply_style: str
    least_effective_reply_style: str
    primary_vs_alt_success_rate: Dict[str, float]
    
    # Voice characteristic performance
    voice_characteristics_performance: Dict[str, float]
    recommended_adjustments: List[str]
    
    # Specific improvements
    content_patterns_to_increase: List[str]
    content_patterns_to_decrease: List[str]

class FeedbackTracker:
    """
    Tracks feedback on opportunities and reply selections to improve voice over time
    """
    
    def __init__(self):
        self.data_dir = Path("data/feedback")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.data_dir / "opportunity_feedback.json"
        self.insights_file = self.data_dir / "voice_insights.json"
        self.pending_feedback_file = self.data_dir / "pending_feedback.json"
        
        self.feedback_data: List[OpportunityFeedback] = []
        self.pending_feedback: Dict[str, Dict] = {}
        
        self._load_feedback_data()
        self._load_pending_feedback()
        
        logger.info(
            "feedback_tracker_initialized",
            existing_feedback_count=len(self.feedback_data),
            pending_feedback_count=len(self.pending_feedback)
        )
    
    def _load_feedback_data(self):
        """Load existing feedback data"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    feedback_data = json.load(f)
                    self.feedback_data = [
                        OpportunityFeedback.from_dict(item) 
                        for item in feedback_data
                    ]
                logger.info(f"Loaded {len(self.feedback_data)} feedback records")
            else:
                logger.info("No existing feedback data found")
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            self.feedback_data = []
    
    def _load_pending_feedback(self):
        """Load pending feedback requests"""
        try:
            if self.pending_feedback_file.exists():
                with open(self.pending_feedback_file, 'r') as f:
                    self.pending_feedback = json.load(f)
                logger.info(f"Loaded {len(self.pending_feedback)} pending feedback requests")
            else:
                logger.info("No pending feedback found")
        except Exception as e:
            logger.error(f"Error loading pending feedback: {e}")
            self.pending_feedback = {}
    
    def _save_feedback_data(self):
        """Save feedback data to disk"""
        try:
            feedback_dicts = [item.to_dict() for item in self.feedback_data]
            with open(self.feedback_file, 'w') as f:
                json.dump(feedback_dicts, f, indent=2)
            logger.info(f"Saved {len(self.feedback_data)} feedback records")
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")
    
    def _save_pending_feedback(self):
        """Save pending feedback to disk"""
        try:
            with open(self.pending_feedback_file, 'w') as f:
                json.dump(self.pending_feedback, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pending feedback: {e}")
    
    def create_opportunity_tracking(self, opportunity_data: Dict) -> str:
        """
        Create tracking for a new opportunity sent in email alerts
        Returns unique opportunity ID for feedback tracking
        """
        opportunity_id = str(uuid.uuid4())[:8]
        
        tracking_data = {
            'opportunity_id': opportunity_id,
            'timestamp': datetime.now().isoformat(),
            'account_username': opportunity_data.get('account_username'),
            'opportunity_type': opportunity_data.get('opportunity_type'),
            'overall_score': opportunity_data.get('overall_score'),
            'generated_reply': opportunity_data.get('generated_reply'),
            'alternative_responses': opportunity_data.get('alternative_responses', []),
            'voice_alignment_score': opportunity_data.get('voice_alignment_score'),
            'content_url': opportunity_data.get('content_url')
        }
        
        self.pending_feedback[opportunity_id] = tracking_data
        self._save_pending_feedback()
        
        logger.info(
            "opportunity_tracking_created",
            opportunity_id=opportunity_id,
            account=opportunity_data.get('account_username'),
            score=opportunity_data.get('overall_score')
        )
        
        return opportunity_id
    
    def record_quality_feedback(self, opportunity_id: str, quality_rating: int, reason: str = None):
        """Record quality rating for an opportunity (1-5 scale)"""
        if opportunity_id not in self.pending_feedback:
            logger.warning(f"Opportunity ID {opportunity_id} not found in pending feedback")
            return False
        
        # Find existing feedback or create new
        feedback = self._get_or_create_feedback(opportunity_id)
        feedback.quality_rating = quality_rating
        feedback.quality_reason = reason
        
        self._save_feedback_data()
        
        logger.info(
            "quality_feedback_recorded",
            opportunity_id=opportunity_id,
            rating=quality_rating,
            reason=reason
        )
        
        return True
    
    def record_reply_selection(self, opportunity_id: str, selected_version: str, custom_reply: str = None):
        """Record which reply version was selected/used"""
        if opportunity_id not in self.pending_feedback:
            logger.warning(f"Opportunity ID {opportunity_id} not found in pending feedback")
            return False
        
        feedback = self._get_or_create_feedback(opportunity_id)
        feedback.selected_reply_version = selected_version
        if custom_reply:
            feedback.custom_reply_used = custom_reply
        
        self._save_feedback_data()
        
        logger.info(
            "reply_selection_recorded",
            opportunity_id=opportunity_id,
            version=selected_version,
            custom_used=bool(custom_reply)
        )
        
        return True
    
    def record_improvement_suggestion(self, opportunity_id: str, suggestion: str, context: str = None):
        """Record user improvement suggestion for an opportunity"""
        if opportunity_id not in self.pending_feedback:
            logger.warning(f"Opportunity ID {opportunity_id} not found in pending feedback")
            return False
        
        feedback = self._get_or_create_feedback(opportunity_id)
        
        # Initialize the list if it doesn't exist
        if feedback.user_improvement_suggestions is None:
            feedback.user_improvement_suggestions = []
        
        # Add the new suggestion with timestamp
        timestamped_suggestion = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {suggestion}"
        if context:
            timestamped_suggestion += f" (Context: {context})"
        
        feedback.user_improvement_suggestions.append(timestamped_suggestion)
        
        self._save_feedback_data()
        
        logger.info(
            "improvement_suggestion_recorded",
            opportunity_id=opportunity_id,
            suggestion_length=len(suggestion),
            total_suggestions=len(feedback.user_improvement_suggestions)
        )
        
        return True
    
    def _get_or_create_feedback(self, opportunity_id: str) -> OpportunityFeedback:
        """Get existing feedback record or create new one"""
        # Check if feedback already exists
        for feedback in self.feedback_data:
            if feedback.opportunity_id == opportunity_id:
                return feedback
        
        # Create new feedback record
        pending_data = self.pending_feedback.get(opportunity_id, {})
        feedback = OpportunityFeedback(
            opportunity_id=opportunity_id,
            timestamp=pending_data.get('timestamp', datetime.now().isoformat())
        )
        
        self.feedback_data.append(feedback)
        return feedback
    
    def generate_feedback_urls(self, opportunity_id: str, base_url: str = None) -> Dict[str, str]:
        """Generate feedback URLs for email alerts"""
        # Use environment variable if base_url not provided
        if base_url is None:
            base_url = os.getenv('FEEDBACK_BASE_URL', 'http://localhost:8080')
        
        feedback_urls = {
            # Quality rating URLs
            'excellent': f"{base_url}/feedback/{opportunity_id}/quality/5",
            'good': f"{base_url}/feedback/{opportunity_id}/quality/4", 
            'okay': f"{base_url}/feedback/{opportunity_id}/quality/3",
            'poor': f"{base_url}/feedback/{opportunity_id}/quality/2",
            'bad': f"{base_url}/feedback/{opportunity_id}/quality/1",
            
            # Reply selection URLs
            'used_primary': f"{base_url}/feedback/{opportunity_id}/reply/primary",
            'used_alt1': f"{base_url}/feedback/{opportunity_id}/reply/alt1",
            'used_alt2': f"{base_url}/feedback/{opportunity_id}/reply/alt2",
            'used_custom': f"{base_url}/feedback/{opportunity_id}/reply/custom",
            'not_used': f"{base_url}/feedback/{opportunity_id}/reply/none"
        }
        
        return feedback_urls
    
    def analyze_voice_performance(self, days_back: int = 30) -> VoiceLearningInsights:
        """Analyze feedback data to generate voice improvement insights"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Filter recent feedback
        recent_feedback = [
            f for f in self.feedback_data 
            if f.quality_rating is not None and 
            datetime.fromisoformat(f.timestamp) > cutoff_date
        ]
        
        if not recent_feedback:
            logger.warning("No recent feedback data available for analysis")
            return self._create_empty_insights()
        
        # Calculate quality trends
        quality_ratings = [f.quality_rating for f in recent_feedback if f.quality_rating]
        avg_quality = sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0
        
        # Analyze reply effectiveness
        reply_selections = {}
        for feedback in recent_feedback:
            if feedback.selected_reply_version:
                version = feedback.selected_reply_version
                reply_selections[version] = reply_selections.get(version, 0) + 1
        
        # Calculate success rates
        total_selections = sum(reply_selections.values())
        success_rates = {
            version: count / total_selections 
            for version, count in reply_selections.items()
        } if total_selections > 0 else {}
        
        # Generate recommendations
        recommendations = self._generate_voice_recommendations(recent_feedback, avg_quality)
        
        insights = VoiceLearningInsights(
            timestamp=datetime.now().isoformat(),
            period_analyzed=f"last_{days_back}_days",
            avg_quality_rating=avg_quality,
            quality_trend=self._determine_quality_trend(recent_feedback),
            most_effective_reply_style=max(reply_selections.keys(), key=reply_selections.get) if reply_selections else "primary",
            least_effective_reply_style=min(reply_selections.keys(), key=reply_selections.get) if reply_selections else "unknown",
            primary_vs_alt_success_rate=success_rates,
            voice_characteristics_performance={},  # To be calculated based on more data
            recommended_adjustments=recommendations,
            content_patterns_to_increase=[],
            content_patterns_to_decrease=[]
        )
        
        logger.info(
            "voice_performance_analyzed",
            avg_quality=avg_quality,
            feedback_count=len(recent_feedback),
            recommendations_count=len(recommendations)
        )
        
        return insights
    
    def _create_empty_insights(self) -> VoiceLearningInsights:
        """Create empty insights when no data available"""
        return VoiceLearningInsights(
            timestamp=datetime.now().isoformat(),
            period_analyzed="insufficient_data",
            avg_quality_rating=0.0,
            quality_trend="unknown",
            most_effective_reply_style="primary",
            least_effective_reply_style="unknown", 
            primary_vs_alt_success_rate={},
            voice_characteristics_performance={},
            recommended_adjustments=["Collect more feedback data"],
            content_patterns_to_increase=[],
            content_patterns_to_decrease=[]
        )
    
    def _determine_quality_trend(self, feedback_data: List[OpportunityFeedback]) -> str:
        """Determine if quality is improving, declining, or stable"""
        if len(feedback_data) < 5:
            return "insufficient_data"
        
        # Sort by timestamp and compare first half vs second half
        sorted_feedback = sorted(feedback_data, key=lambda x: x.timestamp)
        mid_point = len(sorted_feedback) // 2
        
        first_half_avg = sum(f.quality_rating for f in sorted_feedback[:mid_point]) / mid_point
        second_half_avg = sum(f.quality_rating for f in sorted_feedback[mid_point:]) / (len(sorted_feedback) - mid_point)
        
        if second_half_avg > first_half_avg + 0.3:
            return "improving"
        elif second_half_avg < first_half_avg - 0.3:
            return "declining"
        else:
            return "stable"
    
    def _generate_voice_recommendations(self, feedback_data: List[OpportunityFeedback], avg_quality: float) -> List[str]:
        """Generate specific voice adjustment recommendations"""
        recommendations = []
        
        if avg_quality < 3.0:
            recommendations.extend([
                "Increase technical depth in responses",
                "Use more crypto-native language",
                "Reduce corporate speak, add more degen edge"
            ])
        elif avg_quality < 4.0:
            recommendations.extend([
                "Fine-tune authority vs approachability balance",
                "Experiment with more direct communication style"
            ])
        else:
            recommendations.append("Voice performing well, maintain current approach")
        
        # Analyze specific patterns from quality reasons
        poor_quality_reasons = [
            f.quality_reason for f in feedback_data 
            if f.quality_rating and f.quality_rating <= 2 and f.quality_reason
        ]
        
        if poor_quality_reasons:
            recommendations.append("Review specific feedback reasons for targeted improvements")
        
        return recommendations
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of all feedback data"""
        if not self.feedback_data:
            return {"total_feedback": 0, "message": "No feedback data available"}
        
        quality_ratings = [f.quality_rating for f in self.feedback_data if f.quality_rating]
        reply_selections = {}
        
        for feedback in self.feedback_data:
            if feedback.selected_reply_version:
                version = feedback.selected_reply_version
                reply_selections[version] = reply_selections.get(version, 0) + 1
        
        return {
            "total_feedback": len(self.feedback_data),
            "quality_ratings": {
                "count": len(quality_ratings),
                "average": sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0,
                "distribution": {i: quality_ratings.count(i) for i in range(1, 6)}
            },
            "reply_selections": reply_selections,
            "pending_feedback": len(self.pending_feedback)
        }

# Global feedback tracker instance
_feedback_tracker: Optional[FeedbackTracker] = None

def get_feedback_tracker() -> FeedbackTracker:
    """Get or create global feedback tracker instance"""
    global _feedback_tracker
    if _feedback_tracker is None:
        _feedback_tracker = FeedbackTracker()
    return _feedback_tracker