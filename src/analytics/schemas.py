"""
Data schemas for analytics systems - standardized data structures for
follower growth, strategic relationships, and voice evolution tracking.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class FollowerSnapshot:
    """Standardized follower snapshot data structure"""
    timestamp: datetime
    verified_followers: int
    total_followers: int
    following_count: int
    posts_count: int
    source: str
    quality_indicators: Dict[str, float]
    
    def is_valid(self) -> bool:
        """Validate snapshot data"""
        return (
            self.verified_followers <= self.total_followers and
            self.verified_followers > 0 and
            self.total_followers > 0 and
            self.source in ['x_api', 'manual', 'estimated']
        )
    
    def growth_rate_since_yesterday(self) -> Optional[float]:
        """Calculate growth rate since yesterday - placeholder for now"""
        # This will be implemented when we have historical data
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass 
class GrowthMetrics:
    """Standardized growth metrics data structure"""
    period: str
    start_followers: int
    end_followers: int
    net_growth: int
    daily_average: float
    growth_rate_percentage: float
    acceleration: float  # Positive = accelerating growth
    
    def is_valid(self) -> bool:
        """Validate growth metrics"""
        return (
            self.end_followers >= self.start_followers and
            self.net_growth == (self.end_followers - self.start_followers) and
            self.daily_average >= 0
        )
    
    def extrapolate_to_date(self, target_date: str) -> int:
        """Extrapolate growth to target date - placeholder"""
        # This will be implemented with proper date calculations
        return self.end_followers + int(self.daily_average * 90)  # Rough 3-month estimate


@dataclass
class EngagementRecord:
    """Standardized engagement record structure"""
    engagement_id: str
    timestamp: datetime
    target_account: str
    engagement_type: str
    content_url: str
    our_content: str
    opportunity_score: float
    voice_alignment: float
    response_received: Optional[bool] = None
    response_quality: Optional[float] = None
    relationship_impact: Optional[float] = None
    
    def is_valid(self) -> bool:
        """Validate engagement record"""
        return (
            0 <= self.opportunity_score <= 1 and
            0 <= self.voice_alignment <= 1 and
            self.engagement_type in ['reply', 'like', 'repost', 'mention'] and
            len(self.engagement_id) > 0
        )
    
    def get_relationship_tier(self) -> str:
        """Get relationship tier for this account - placeholder"""
        # This will be implemented with strategic accounts data
        strategic_tier_1 = ['saucepoint', 'VitalikButerin', 'dabit3', 'PatrickAlphaC']
        if self.target_account in strategic_tier_1:
            return 'tier_1'
        return 'general'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class RelationshipMetrics:
    """Standardized relationship metrics structure"""
    account: str
    relationship_strength: float  # 0-1 scale
    total_engagements: int
    responses_received: int
    response_rate: float
    avg_response_time_hours: float
    mutual_engagement_score: float
    influence_potential: float
    last_interaction: datetime
    
    def is_valid(self) -> bool:
        """Validate relationship metrics"""
        return (
            0 <= self.relationship_strength <= 1 and
            0 <= self.response_rate <= 1 and
            self.responses_received <= self.total_engagements and
            0 <= self.mutual_engagement_score <= 1 and
            0 <= self.influence_potential <= 1
        )
    
    def get_relationship_grade(self) -> str:
        """Get letter grade for relationship strength"""
        if self.relationship_strength >= 0.8:
            return 'A'
        elif self.relationship_strength >= 0.6:
            return 'B'
        elif self.relationship_strength >= 0.4:
            return 'C'
        elif self.relationship_strength >= 0.2:
            return 'D'
        else:
            return 'F'
    
    def get_next_milestone(self) -> str:
        """Get next relationship milestone to achieve"""
        if self.responses_received == 0:
            return 'first_response'
        elif self.mutual_engagement_score < 0.2:
            return 'mutual_engagement'
        elif self.relationship_strength < 0.5:
            return 'strong_relationship'
        else:
            return 'collaboration'


@dataclass
class VoiceProfile:
    """Standardized voice profile data structure"""
    timestamp: datetime
    technical_authority: float
    innovation_focus: float
    forward_thinking: float
    enthusiasm_level: float
    degen_language_ratio: float
    controversy_comfort: float
    humor_inclusion: float
    voice_alignment_score: float
    
    def is_valid(self) -> bool:
        """Validate voice profile"""
        voice_characteristics = [
            self.technical_authority,
            self.innovation_focus,
            self.forward_thinking,
            self.enthusiasm_level,
            self.degen_language_ratio,
            self.controversy_comfort,
            self.humor_inclusion,
            self.voice_alignment_score
        ]
        return all(0 <= char <= 1 for char in voice_characteristics)
    
    def distance_from_target(self) -> float:
        """Calculate distance from target voice profile"""
        target = {
            'technical_authority': 0.75,
            'innovation_focus': 0.80,
            'forward_thinking': 0.85
        }
        
        distance = 0
        for characteristic, target_value in target.items():
            current_value = getattr(self, characteristic)
            distance += abs(current_value - target_value) ** 2
        
        return distance ** 0.5
    
    def get_voice_grade(self) -> str:
        """Get letter grade for voice development"""
        distance = self.distance_from_target()
        if distance <= 0.1:
            return 'A'
        elif distance <= 0.2:
            return 'B'
        elif distance <= 0.3:
            return 'C'
        elif distance <= 0.4:
            return 'D'
        else:
            return 'F'


@dataclass
class VoiceFeedbackRecord:
    """Standardized voice feedback data structure"""
    opportunity_id: str
    quality_rating: int  # 1-5 stars
    reply_used: str  # primary, alt1, alt2, custom, none
    voice_characteristics: Dict[str, float]
    engagement_result: Dict[str, int]
    timestamp: datetime
    
    def is_valid(self) -> bool:
        """Validate voice feedback record"""
        return (
            1 <= self.quality_rating <= 5 and
            self.reply_used in ['primary', 'alt1', 'alt2', 'custom', 'none'] and
            len(self.opportunity_id) > 0 and
            all(0 <= value <= 1 for value in self.voice_characteristics.values())
        )
    
    def calculate_voice_impact(self) -> float:
        """Calculate the impact of voice characteristics on performance"""
        # Simple weighted average of engagement results
        total_engagement = sum(self.engagement_result.values())
        if total_engagement == 0:
            return 0.0
        
        # Weight by quality rating
        return (total_engagement * self.quality_rating) / 25  # Max possible: 5 rating * 5 engagements
    
    def get_optimization_insights(self) -> Dict[str, str]:
        """Get insights for voice optimization"""
        insights = {}
        
        if self.quality_rating >= 4:
            insights['voice_success'] = 'Voice characteristics working well'
        elif self.quality_rating <= 2:
            insights['voice_improvement'] = 'Voice needs adjustment'
        
        if sum(self.engagement_result.values()) > 3:
            insights['engagement_success'] = 'High engagement achieved'
        
        return insights


# Placeholder classes for advanced analytics (to be implemented)
class UnifiedAnalyticsDatabase:
    """Placeholder for unified analytics database"""
    
    def has_table(self, table_name: str) -> bool:
        """Check if table exists - placeholder"""
        return False
    
    def query(self, sql: str) -> Optional[Any]:
        """Execute query - placeholder"""
        return None


class RealTimeAnalyticsProcessor:
    """Placeholder for real-time analytics processing"""
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process analytics event - placeholder"""
        return {
            'updated_relationship_score': None,
            'follower_growth_impact_prediction': None,
            'voice_optimization_recommendations': None,
            'alerts_triggered': None
        }