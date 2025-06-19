"""
Manual Review System for Content Approval
Allows human review before posting while preparing for eventual auto-posting
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class ContentStatus(Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    POSTED = "posted"
    EXPIRED = "expired"

class ContentType(Enum):
    REPLY = "reply"
    QUOTE_TWEET = "quote_tweet"
    ORIGINAL_POST = "original_post"
    THREAD = "thread"

@dataclass
class ReviewableContent:
    """Content item awaiting manual review"""
    id: str
    content_type: ContentType
    text: str
    context: Optional[str]  # Original tweet being replied to
    context_url: Optional[str]
    
    # Metadata
    opportunity_score: float
    voice_alignment_score: float
    engagement_prediction: float
    
    # Review data
    status: ContentStatus
    created_at: float
    expires_at: float
    reviewed_at: Optional[float] = None
    reviewer_notes: Optional[str] = None
    
    # Analytics
    follower_growth_potential: float = 0.0
    community_engagement_score: float = 0.0
    brand_safety_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['content_type'] = self.content_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewableContent':
        data['content_type'] = ContentType(data['content_type'])
        data['status'] = ContentStatus(data['status'])
        return cls(**data)

class ManualReviewSystem:
    """
    Manual content review system with analytics and auto-posting preparation
    """
    
    def __init__(self, review_dir: str = "data/review"):
        self.review_dir = Path(review_dir)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        
        self.pending_file = self.review_dir / "pending_review.json"
        self.approved_file = self.review_dir / "approved_content.json"
        self.analytics_file = self.review_dir / "review_analytics.json"
        
        self.pending_content: List[ReviewableContent] = []
        self.approved_content: List[ReviewableContent] = []
        
        # Auto-posting preparation settings
        self.auto_approve_threshold = 0.9  # Voice alignment score for auto-approval
        self.brand_safety_threshold = 0.8  # Minimum brand safety score
        self.max_pending_items = 50  # Prevent queue overflow
        self.content_expiry_hours = 6  # Content expires after 6 hours
        
        self._load_existing_content()
        
        logger.info("Manual review system initialized")
    
    def _load_existing_content(self):
        """Load existing pending and approved content"""
        try:
            if self.pending_file.exists():
                with open(self.pending_file, 'r') as f:
                    pending_data = json.load(f)
                    self.pending_content = [
                        ReviewableContent.from_dict(item) 
                        for item in pending_data
                    ]
            
            if self.approved_file.exists():
                with open(self.approved_file, 'r') as f:
                    approved_data = json.load(f)
                    self.approved_content = [
                        ReviewableContent.from_dict(item) 
                        for item in approved_data
                    ]
            
            # Clean up expired content
            self._cleanup_expired_content()
            
            logger.info(f"Loaded {len(self.pending_content)} pending and {len(self.approved_content)} approved items")
            
        except Exception as e:
            logger.error(f"Error loading content: {e}")
    
    def _save_content(self):
        """Save content to disk"""
        try:
            # Save pending content
            pending_data = [item.to_dict() for item in self.pending_content]
            with open(self.pending_file, 'w') as f:
                json.dump(pending_data, f, indent=2)
            
            # Save approved content (keep recent items only)
            recent_approved = [
                item for item in self.approved_content 
                if item.created_at > time.time() - (7 * 24 * 3600)  # Last 7 days
            ]
            approved_data = [item.to_dict() for item in recent_approved]
            with open(self.approved_file, 'w') as f:
                json.dump(approved_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving content: {e}")
    
    def submit_for_review(self, content_text: str, content_type: ContentType,
                         context: Optional[str] = None, context_url: Optional[str] = None,
                         opportunity_score: float = 0.0, voice_alignment_score: float = 0.0,
                         engagement_prediction: float = 0.0) -> str:
        """
        Submit content for manual review
        Returns: content_id for tracking
        """
        
        # Generate unique ID
        content_id = f"{content_type.value}_{int(time.time())}_{len(self.pending_content)}"
        
        # Calculate analytics scores
        follower_growth_potential = self._calculate_follower_growth_potential(
            content_text, content_type, voice_alignment_score
        )
        community_engagement_score = self._calculate_community_engagement_score(
            content_text, context
        )
        brand_safety_score = self._calculate_brand_safety_score(content_text)
        
        # Create reviewable content
        reviewable = ReviewableContent(
            id=content_id,
            content_type=content_type,
            text=content_text,
            context=context,
            context_url=context_url,
            opportunity_score=opportunity_score,
            voice_alignment_score=voice_alignment_score,
            engagement_prediction=engagement_prediction,
            status=ContentStatus.PENDING_REVIEW,
            created_at=time.time(),
            expires_at=time.time() + (self.content_expiry_hours * 3600),
            follower_growth_potential=follower_growth_potential,
            community_engagement_score=community_engagement_score,
            brand_safety_score=brand_safety_score
        )
        
        # Check for auto-approval (future feature)
        if self._should_auto_approve(reviewable):
            reviewable.status = ContentStatus.APPROVED
            reviewable.reviewed_at = time.time()
            reviewable.reviewer_notes = "Auto-approved based on quality scores"
            self.approved_content.append(reviewable)
            logger.info(f"Content auto-approved: {content_id}")
        else:
            # Add to manual review queue
            self.pending_content.append(reviewable)
            
            # Prevent queue overflow
            if len(self.pending_content) > self.max_pending_items:
                oldest = min(self.pending_content, key=lambda x: x.created_at)
                self.pending_content.remove(oldest)
                logger.warning(f"Removed oldest pending item due to queue overflow: {oldest.id}")
        
        self._save_content()
        
        logger.info(f"Content submitted for review: {content_id} (type: {content_type.value})")
        return content_id
    
    def get_pending_reviews(self, limit: int = 10) -> List[ReviewableContent]:
        """Get pending content for review"""
        self._cleanup_expired_content()
        
        # Sort by priority: follower growth potential + opportunity score
        pending = sorted(
            self.pending_content,
            key=lambda x: x.follower_growth_potential + x.opportunity_score,
            reverse=True
        )
        
        return pending[:limit]
    
    def approve_content(self, content_id: str, reviewer_notes: Optional[str] = None) -> bool:
        """Approve content for posting"""
        for item in self.pending_content:
            if item.id == content_id:
                item.status = ContentStatus.APPROVED
                item.reviewed_at = time.time()
                item.reviewer_notes = reviewer_notes
                
                self.pending_content.remove(item)
                self.approved_content.append(item)
                self._save_content()
                
                logger.info(f"Content approved: {content_id}")
                return True
        
        logger.warning(f"Content not found for approval: {content_id}")
        return False
    
    def reject_content(self, content_id: str, reviewer_notes: Optional[str] = None) -> bool:
        """Reject content"""
        for item in self.pending_content:
            if item.id == content_id:
                item.status = ContentStatus.REJECTED
                item.reviewed_at = time.time()
                item.reviewer_notes = reviewer_notes
                
                self.pending_content.remove(item)
                self._save_content()
                
                logger.info(f"Content rejected: {content_id}")
                return True
        
        logger.warning(f"Content not found for rejection: {content_id}")
        return False
    
    def get_approved_content(self, content_type: Optional[ContentType] = None) -> List[ReviewableContent]:
        """Get approved content ready for posting"""
        approved = [
            item for item in self.approved_content 
            if item.status == ContentStatus.APPROVED
        ]
        
        if content_type:
            approved = [item for item in approved if item.content_type == content_type]
        
        # Sort by opportunity score and recency
        return sorted(approved, key=lambda x: (x.opportunity_score, -x.created_at), reverse=True)
    
    def mark_as_posted(self, content_id: str) -> bool:
        """Mark content as posted"""
        for item in self.approved_content:
            if item.id == content_id:
                item.status = ContentStatus.POSTED
                self._save_content()
                logger.info(f"Content marked as posted: {content_id}")
                return True
        
        return False
    
    def _should_auto_approve(self, content: ReviewableContent) -> bool:
        """Check if content should be auto-approved (future feature)"""
        # For now, always require manual review
        # Future: auto-approve high-quality content
        return False
        
        # Future auto-approval logic:
        # return (
        #     content.voice_alignment_score >= self.auto_approve_threshold and
        #     content.brand_safety_score >= self.brand_safety_threshold and
        #     content.follower_growth_potential >= 0.7
        # )
    
    def _calculate_follower_growth_potential(self, content: str, content_type: ContentType, 
                                           voice_alignment: float) -> float:
        """Calculate follower growth potential of content"""
        score = voice_alignment * 0.4  # Base score from voice alignment
        
        # Boost for engagement elements
        if any(hook in content.lower() for hook in ['?', 'thoughts?', 'anyone else', 'what do you']):
            score += 0.3  # Questions drive engagement
        
        if any(hook in content.lower() for hook in ['hot take', 'unpopular opinion', 'fight me']):
            score += 0.2  # Controversial content drives engagement
        
        if any(emotion in content for emotion in ['😏', '🏍️', '💰']):
            score += 0.1  # Emojis help relatability
        
        # Content type modifiers
        if content_type == ContentType.REPLY:
            score += 0.2  # Replies are discovery-focused
        elif content_type == ContentType.ORIGINAL_POST:
            score += 0.1  # Original posts have broader reach
        
        return min(1.0, score)
    
    def _calculate_community_engagement_score(self, content: str, context: Optional[str]) -> float:
        """Calculate community engagement potential"""
        score = 0.5  # Base score
        
        # Boost for community terms
        community_terms = ['solana', 'base', 'meme', 'degen', 'ape', 'community', 'vibes']
        matches = sum(1 for term in community_terms if term in content.lower())
        score += min(0.3, matches * 0.1)
        
        # Boost for conversational elements
        if context:
            score += 0.2  # Replying to someone
        
        return min(1.0, score)
    
    def _calculate_brand_safety_score(self, content: str) -> float:
        """Calculate brand safety score"""
        # Simple brand safety check
        unsafe_terms = ['scam', 'rug', 'hate', 'illegal']
        
        if any(term in content.lower() for term in unsafe_terms):
            return 0.3
        
        # Check for excessive profanity or aggressive language
        aggressive_terms = ['fuck', 'shit', 'damn', 'idiot', 'stupid']
        aggressive_count = sum(1 for term in aggressive_terms if term in content.lower())
        
        if aggressive_count > 2:
            return 0.6
        elif aggressive_count > 0:
            return 0.8
        
        return 1.0
    
    def _cleanup_expired_content(self):
        """Remove expired content"""
        now = time.time()
        
        # Mark expired pending content
        expired_pending = [
            item for item in self.pending_content 
            if item.expires_at < now
        ]
        
        for item in expired_pending:
            item.status = ContentStatus.EXPIRED
            self.pending_content.remove(item)
        
        if expired_pending:
            logger.info(f"Cleaned up {len(expired_pending)} expired pending items")
    
    def get_review_analytics(self) -> Dict[str, Any]:
        """Get review system analytics"""
        now = time.time()
        last_24h = now - (24 * 3600)
        
        recent_approved = [
            item for item in self.approved_content 
            if item.reviewed_at and item.reviewed_at > last_24h
        ]
        
        recent_rejected = [
            item for item in self.approved_content 
            if item.status == ContentStatus.REJECTED and 
            item.reviewed_at and item.reviewed_at > last_24h
        ]
        
        analytics = {
            'pending_count': len(self.pending_content),
            'approved_today': len(recent_approved),
            'rejected_today': len(recent_rejected),
            'approval_rate': len(recent_approved) / max(1, len(recent_approved) + len(recent_rejected)),
            'avg_voice_alignment': sum(item.voice_alignment_score for item in recent_approved) / max(1, len(recent_approved)),
            'avg_follower_growth_potential': sum(item.follower_growth_potential for item in recent_approved) / max(1, len(recent_approved)),
            'content_type_distribution': self._get_content_type_distribution(),
            'queue_health': 'good' if len(self.pending_content) < self.max_pending_items * 0.8 else 'full'
        }
        
        return analytics
    
    def _get_content_type_distribution(self) -> Dict[str, int]:
        """Get distribution of content types in pending queue"""
        distribution = {ct.value: 0 for ct in ContentType}
        
        for item in self.pending_content:
            distribution[item.content_type.value] += 1
        
        return distribution
    
    def generate_review_email(self) -> str:
        """Generate email content for manual review"""
        pending = self.get_pending_reviews(5)
        
        if not pending:
            return "No content pending review."
        
        email_content = "📋 **Content Pending Review**\\n\\n"
        
        for item in pending:
            email_content += f"**ID:** {item.id}\\n"
            email_content += f"**Type:** {item.content_type.value}\\n"
            email_content += f"**Content:** {item.text}\\n"
            
            if item.context:
                email_content += f"**Context:** {item.context[:100]}...\\n"
            
            email_content += f"**Scores:** Voice={item.voice_alignment_score:.2f}, Growth={item.follower_growth_potential:.2f}\\n"
            email_content += f"**Created:** {datetime.fromtimestamp(item.created_at).strftime('%H:%M')}\\n"
            email_content += "---\\n\\n"
        
        return email_content