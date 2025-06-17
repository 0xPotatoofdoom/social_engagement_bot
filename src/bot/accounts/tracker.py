"""
Strategic Account Monitoring System
Tracks AI x blockchain thought leaders, relationship progression, and engagement opportunities
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
from bot.utils.logging_config import get_strategic_accounts_logger

logger = get_strategic_accounts_logger()

@dataclass
class AccountProfile:
    """Strategic account profile with monitoring and relationship data"""
    username: str
    display_name: str
    tier: int  # 1, 2, or 3
    category: str  # 'ai_blockchain', 'uniswap', 'trading', 'developers', 'defi', 'creators'
    follower_count: int
    following_count: int
    account_age: str
    verification_status: bool
    
    # Classification scores (0-1)
    influence_score: float
    relevance_score: float
    engagement_potential: float
    
    # Content analysis
    posting_frequency: float  # posts per day
    content_themes: List[str]
    technical_depth: float  # 0-1 scale
    ai_blockchain_focus: float  # 0-1 scale
    
    # Relationship tracking
    relationship_score: float  # 0-1 scale
    relationship_stage: int  # 0-5 (unknown to strategic partnership)
    interaction_history: List[Dict]
    last_interaction: Optional[str]
    reciprocal_engagement: List[Dict]
    
    # Monitoring configuration
    alert_triggers: List[str]
    monitoring_priority: int  # monitoring frequency multiplier
    last_updated: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AccountProfile':
        return cls(**data)

@dataclass
class EngagementOpportunity:
    """High-value engagement opportunity from strategic account"""
    account_username: str
    account_tier: int
    content_id: str
    content_text: str
    content_url: str
    timestamp: str
    
    # Opportunity scoring
    relevance_score: float
    technical_depth: float
    engagement_potential: float
    strategic_value: float
    overall_score: float
    
    # Context analysis
    ai_blockchain_relevance: float
    content_themes: List[str]
    opportunity_type: str  # 'technical_question', 'collaboration', 'trend_discussion', etc.
    suggested_response_type: str
    time_sensitivity: str  # 'immediate', 'within_hour', 'within_day'
    
    def to_dict(self) -> Dict:
        return asdict(self)

class StrategicAccountTracker:
    """
    Comprehensive strategic account monitoring and relationship tracking system
    """
    
    def __init__(self, x_client=None, claude_client=None):
        self.x_client = x_client
        self.claude_client = claude_client
        self.data_dir = Path("data/strategic_accounts")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.accounts_file = self.data_dir / "accounts.json"
        self.opportunities_file = self.data_dir / "opportunities.json"
        self.relationships_file = self.data_dir / "relationships.json"
        
        self.accounts: Dict[str, AccountProfile] = {}
        self.opportunities: List[EngagementOpportunity] = []
        
        # Account classification criteria
        self.tier_1_criteria = {
            'min_followers': 10000,
            'min_ai_blockchain_focus': 0.6,
            'min_technical_depth': 0.7,
            'categories': ['ai_blockchain', 'uniswap', 'trading']
        }
        
        self.tier_2_criteria = {
            'min_followers': 1000,
            'min_ai_blockchain_focus': 0.4,
            'min_technical_depth': 0.5,
            'categories': ['developers', 'defi', 'ai_blockchain']
        }
        
        # Load existing data
        self._load_accounts()
        
    def _load_accounts(self):
        """Load strategic accounts from persistent storage"""
        try:
            if self.accounts_file.exists():
                with open(self.accounts_file, 'r') as f:
                    accounts_data = json.load(f)
                    self.accounts = {
                        username: AccountProfile.from_dict(data)
                        for username, data in accounts_data.items()
                    }
                logger.info(f"Loaded {len(self.accounts)} strategic accounts")
            else:
                logger.info("No existing accounts file, starting fresh")
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
            self.accounts = {}
    
    def _save_accounts(self):
        """Save strategic accounts to persistent storage"""
        try:
            accounts_data = {
                username: account.to_dict()
                for username, account in self.accounts.items()
            }
            with open(self.accounts_file, 'w') as f:
                json.dump(accounts_data, f, indent=2)
            logger.info(f"Saved {len(self.accounts)} strategic accounts")
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
    
    async def add_strategic_account(
        self,
        username: str,
        tier: int,
        category: str,
        manual_classification: Optional[Dict] = None
    ) -> AccountProfile:
        """
        Add account to strategic monitoring with classification
        """
        try:
            logger.info(f"Adding strategic account: @{username} (Tier {tier}, {category})")
            
            # Get account info from X API (if available)
            account_data = await self._fetch_account_data(username)
            
            # Create profile with manual classification or defaults
            if manual_classification:
                profile_data = manual_classification
            else:
                profile_data = {
                    'influence_score': 0.8 if tier == 1 else 0.6 if tier == 2 else 0.4,
                    'relevance_score': 0.9 if category == 'ai_blockchain' else 0.7,
                    'engagement_potential': 0.7,
                    'technical_depth': 0.8 if tier == 1 else 0.6,
                    'ai_blockchain_focus': 0.9 if category == 'ai_blockchain' else 0.5
                }
            
            account = AccountProfile(
                username=username,
                display_name=account_data.get('display_name', username),
                tier=tier,
                category=category,
                follower_count=account_data.get('follower_count', 0),
                following_count=account_data.get('following_count', 0),
                account_age=account_data.get('account_age', 'unknown'),
                verification_status=account_data.get('verified', False),
                
                influence_score=profile_data['influence_score'],
                relevance_score=profile_data['relevance_score'],
                engagement_potential=profile_data['engagement_potential'],
                
                posting_frequency=1.0,  # Default posts per day
                content_themes=[category],
                technical_depth=profile_data['technical_depth'],
                ai_blockchain_focus=profile_data['ai_blockchain_focus'],
                
                relationship_score=0.0,  # No relationship yet
                relationship_stage=0,    # Unknown
                interaction_history=[],
                last_interaction=None,
                reciprocal_engagement=[],
                
                alert_triggers=self._get_default_alert_triggers(tier, category),
                monitoring_priority=tier,  # Tier 1 = highest priority
                last_updated=datetime.now().isoformat()
            )
            
            self.accounts[username] = account
            self._save_accounts()
            
            logger.info(f"Successfully added @{username} to strategic monitoring")
            return account
            
        except Exception as e:
            logger.error(f"Error adding strategic account @{username}: {e}")
            raise
    
    async def _fetch_account_data(self, username: str) -> Dict:
        """Fetch account data from X API"""
        if not self.x_client:
            return {'display_name': username, 'follower_count': 0}
        
        try:
            # Use X API to get account information
            user = self.x_client.client.get_user(username=username)
            if user.data:
                return {
                    'display_name': user.data.name,
                    'follower_count': user.data.public_metrics['followers_count'],
                    'following_count': user.data.public_metrics['following_count'],
                    'verified': user.data.verified if hasattr(user.data, 'verified') else False,
                    'account_age': user.data.created_at.isoformat() if hasattr(user.data, 'created_at') else 'unknown'
                }
        except Exception as e:
            logger.warning(f"Could not fetch data for @{username}: {e}")
        
        return {'display_name': username, 'follower_count': 0}
    
    def _get_default_alert_triggers(self, tier: int, category: str) -> List[str]:
        """Get default alert triggers based on tier and category"""
        triggers = []
        
        if tier == 1:
            triggers.extend([
                'posts_ai_blockchain_content',
                'asks_technical_question',
                'mentions_collaboration',
                'trending_topic_participation'
            ])
        
        if category == 'ai_blockchain':
            triggers.extend([
                'convergence_discussion',
                'technical_analysis',
                'prediction_content'
            ])
        elif category == 'uniswap':
            triggers.extend([
                'v4_discussion',
                'protocol_development',
                'technical_insights'
            ])
        elif category == 'trading':
            triggers.extend([
                'hft_discussion',
                'performance_insights',
                'algorithm_discussion'
            ])
        
        return list(set(triggers))  # Remove duplicates
    
    async def analyze_account_content(
        self,
        username: str,
        content: Dict
    ) -> Optional[EngagementOpportunity]:
        """
        Analyze content from strategic account for engagement opportunities
        """
        if username not in self.accounts:
            return None
        
        account = self.accounts[username]
        
        try:
            # Use Claude API for content analysis
            if self.claude_client:
                analysis = await self._analyze_content_with_ai(content, account)
            else:
                analysis = self._analyze_content_basic(content, account)
            
            # Check if this is a high-value opportunity
            if analysis['overall_score'] >= 0.6:  # Minimum threshold for opportunities
                opportunity = EngagementOpportunity(
                    account_username=username,
                    account_tier=account.tier,
                    content_id=content.get('id', 'unknown'),
                    content_text=content.get('text', ''),
                    content_url=f"https://twitter.com/{username}/status/{content.get('id', '')}",
                    timestamp=datetime.now().isoformat(),
                    
                    relevance_score=analysis['relevance_score'],
                    technical_depth=analysis['technical_depth'],
                    engagement_potential=analysis['engagement_potential'],
                    strategic_value=analysis['strategic_value'],
                    overall_score=analysis['overall_score'],
                    
                    ai_blockchain_relevance=analysis['ai_blockchain_relevance'],
                    content_themes=analysis['content_themes'],
                    opportunity_type=analysis['opportunity_type'],
                    suggested_response_type=analysis['suggested_response_type'],
                    time_sensitivity=analysis['time_sensitivity']
                )
                
                self.opportunities.append(opportunity)
                self._save_opportunities()
                
                logger.info(f"High-value opportunity identified from @{username}: {analysis['opportunity_type']}")
                return opportunity
        
        except Exception as e:
            logger.error(f"Error analyzing content from @{username}: {e}")
        
        return None
    
    async def _analyze_content_with_ai(self, content: Dict, account: AccountProfile) -> Dict:
        """Use Claude API to analyze content for engagement opportunities"""
        content_text = content.get('text', '')
        
        analysis_prompt = f"""
        Analyze this content from @{account.username} (Tier {account.tier} {account.category} account) for AI x blockchain engagement opportunities:
        
        Content: "{content_text}"
        
        Account Context:
        - Technical Depth: {account.technical_depth}
        - AI x Blockchain Focus: {account.ai_blockchain_focus}
        - Relationship Stage: {account.relationship_stage}
        
        Provide analysis in JSON format:
        {{
            "relevance_score": 0.0-1.0,
            "technical_depth": 0.0-1.0,
            "engagement_potential": 0.0-1.0,
            "strategic_value": 0.0-1.0,
            "ai_blockchain_relevance": 0.0-1.0,
            "content_themes": ["theme1", "theme2"],
            "opportunity_type": "technical_question|collaboration|trend_discussion|educational|innovation",
            "suggested_response_type": "technical_insight|question|collaboration_suggestion|educational_support",
            "time_sensitivity": "immediate|within_hour|within_day|digest"
        }}
        """
        
        try:
            response = await self.claude_client.analyze_content(analysis_prompt)
            analysis = json.loads(response)
            
            # Calculate overall score
            analysis['overall_score'] = (
                analysis['relevance_score'] * 0.3 +
                analysis['technical_depth'] * 0.25 +
                analysis['engagement_potential'] * 0.25 +
                analysis['strategic_value'] * 0.2
            )
            
            return analysis
        except Exception as e:
            logger.warning(f"AI analysis failed, falling back to basic analysis: {e}")
            return self._analyze_content_basic(content, account)
    
    def _analyze_content_basic(self, content: Dict, account: AccountProfile) -> Dict:
        """Basic content analysis without AI"""
        content_text = content.get('text', '').lower()
        
        # AI x blockchain keyword detection
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'algorithm']
        blockchain_keywords = ['blockchain', 'crypto', 'defi', 'uniswap', 'ethereum', 'smart contract']
        convergence_keywords = ['autonomous', 'intelligent', 'predictive', 'automated']
        
        ai_mentions = sum(1 for keyword in ai_keywords if keyword in content_text)
        blockchain_mentions = sum(1 for keyword in blockchain_keywords if keyword in content_text)
        convergence_mentions = sum(1 for keyword in convergence_keywords if keyword in content_text)
        
        # Basic scoring
        ai_blockchain_relevance = min(1.0, (ai_mentions + blockchain_mentions + convergence_mentions) / 5)
        technical_depth = 0.8 if any(word in content_text for word in ['implementation', 'architecture', 'performance', 'optimization']) else 0.4
        
        # Question detection
        has_question = '?' in content_text
        engagement_potential = 0.8 if has_question else 0.5
        
        # Strategic value based on account tier
        strategic_value = 0.9 if account.tier == 1 else 0.7 if account.tier == 2 else 0.5
        
        relevance_score = ai_blockchain_relevance * account.ai_blockchain_focus
        
        overall_score = (
            relevance_score * 0.3 +
            technical_depth * 0.25 +
            engagement_potential * 0.25 +
            strategic_value * 0.2
        )
        
        # Determine opportunity type
        if has_question and technical_depth > 0.6:
            opportunity_type = "technical_question"
            suggested_response_type = "technical_insight"
        elif 'collaborate' in content_text or 'partnership' in content_text:
            opportunity_type = "collaboration"
            suggested_response_type = "collaboration_suggestion"
        elif ai_blockchain_relevance > 0.7:
            opportunity_type = "trend_discussion"
            suggested_response_type = "technical_insight"
        else:
            opportunity_type = "educational"
            suggested_response_type = "educational_support"
        
        time_sensitivity = "immediate" if overall_score > 0.8 else "within_hour" if overall_score > 0.6 else "within_day"
        
        return {
            'relevance_score': relevance_score,
            'technical_depth': technical_depth,
            'engagement_potential': engagement_potential,
            'strategic_value': strategic_value,
            'overall_score': overall_score,
            'ai_blockchain_relevance': ai_blockchain_relevance,
            'content_themes': ['ai_blockchain'] if ai_blockchain_relevance > 0.5 else ['general'],
            'opportunity_type': opportunity_type,
            'suggested_response_type': suggested_response_type,
            'time_sensitivity': time_sensitivity
        }
    
    def _save_opportunities(self):
        """Save engagement opportunities to persistent storage"""
        try:
            opportunities_data = [opp.to_dict() for opp in self.opportunities[-100:]]  # Keep last 100
            with open(self.opportunities_file, 'w') as f:
                json.dump(opportunities_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving opportunities: {e}")
    
    async def track_relationship_progression(
        self,
        username: str,
        interaction_type: str,
        outcome: str = "positive"
    ):
        """Update relationship scoring based on interactions"""
        if username not in self.accounts:
            return
        
        account = self.accounts[username]
        
        # Record interaction
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'type': interaction_type,
            'outcome': outcome
        }
        account.interaction_history.append(interaction)
        
        # Update relationship score based on interaction
        score_increment = {
            'reply': 0.05,
            'quote_tweet': 0.08,
            'mention': 0.03,
            'collaboration_response': 0.15,
            'reciprocal_engagement': 0.10
        }.get(interaction_type, 0.02)
        
        if outcome == "positive":
            account.relationship_score = min(1.0, account.relationship_score + score_increment)
        elif outcome == "negative":
            account.relationship_score = max(0.0, account.relationship_score - score_increment * 0.5)
        
        # Update relationship stage based on score
        if account.relationship_score >= 0.9:
            account.relationship_stage = 5  # Strategic partnership
        elif account.relationship_score >= 0.7:
            account.relationship_stage = 4  # Collaboration
        elif account.relationship_score >= 0.5:
            account.relationship_stage = 3  # Engagement
        elif account.relationship_score >= 0.3:
            account.relationship_stage = 2  # Recognition
        elif account.relationship_score >= 0.1:
            account.relationship_stage = 1  # Awareness
        else:
            account.relationship_stage = 0  # Unknown
        
        account.last_interaction = datetime.now().isoformat()
        account.last_updated = datetime.now().isoformat()
        
        self._save_accounts()
        logger.info(f"Updated relationship with @{username}: score={account.relationship_score:.2f}, stage={account.relationship_stage}")
    
    async def get_high_priority_opportunities(self, limit: int = 10) -> List[EngagementOpportunity]:
        """Get highest priority engagement opportunities"""
        # Sort by overall score and time sensitivity
        sorted_opportunities = sorted(
            self.opportunities,
            key=lambda x: (x.overall_score, x.account_tier),
            reverse=True
        )
        
        # Filter recent opportunities (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_opportunities = [
            opp for opp in sorted_opportunities
            if datetime.fromisoformat(opp.timestamp) > cutoff_time
        ]
        
        return recent_opportunities[:limit]
    
    def get_strategic_accounts_summary(self) -> Dict:
        """Get summary of strategic accounts and relationships"""
        if not self.accounts:
            return {
                'total_accounts': 0,
                'by_tier': {},
                'by_category': {},
                'relationship_stages': {},
                'top_opportunities': 0
            }
        
        summary = {
            'total_accounts': len(self.accounts),
            'by_tier': {},
            'by_category': {},
            'relationship_stages': {},
            'average_relationship_score': 0,
            'recent_opportunities': len([
                opp for opp in self.opportunities 
                if datetime.fromisoformat(opp.timestamp) > datetime.now() - timedelta(hours=24)
            ])
        }
        
        # Count by tier
        for account in self.accounts.values():
            tier = f"Tier {account.tier}"
            summary['by_tier'][tier] = summary['by_tier'].get(tier, 0) + 1
            
            # Count by category
            summary['by_category'][account.category] = summary['by_category'].get(account.category, 0) + 1
            
            # Count by relationship stage
            stage = f"Stage {account.relationship_stage}"
            summary['relationship_stages'][stage] = summary['relationship_stages'].get(stage, 0) + 1
        
        # Calculate average relationship score
        if self.accounts:
            summary['average_relationship_score'] = sum(
                account.relationship_score for account in self.accounts.values()
            ) / len(self.accounts)
        
        return summary

    async def initialize_tier_1_accounts(self):
        """Initialize with high-priority Tier 1 strategic accounts"""
        tier_1_accounts = [
            # AI x Blockchain Thought Leaders
            ("VitalikButerin", 1, "ai_blockchain", {
                'influence_score': 1.0, 'relevance_score': 0.9, 'engagement_potential': 0.8,
                'technical_depth': 0.9, 'ai_blockchain_focus': 0.7
            }),
            ("karpathy", 1, "ai_blockchain", {
                'influence_score': 0.9, 'relevance_score': 0.8, 'engagement_potential': 0.7,
                'technical_depth': 0.95, 'ai_blockchain_focus': 0.6
            }),
            
            # Uniswap Ecosystem
            ("hayden_adams", 1, "uniswap", {
                'influence_score': 0.9, 'relevance_score': 1.0, 'engagement_potential': 0.8,
                'technical_depth': 0.8, 'ai_blockchain_focus': 0.5
            }),
            ("Uniswap", 1, "uniswap", {
                'influence_score': 1.0, 'relevance_score': 1.0, 'engagement_potential': 0.7,
                'technical_depth': 0.8, 'ai_blockchain_focus': 0.4
            }),
            
            # AI Trading & Research
            ("nanexcool", 1, "trading", {
                'influence_score': 0.8, 'relevance_score': 0.8, 'engagement_potential': 0.7,
                'technical_depth': 0.8, 'ai_blockchain_focus': 0.6
            }),
        ]
        
        logger.info("Initializing Tier 1 strategic accounts...")
        for username, tier, category, classification in tier_1_accounts:
            try:
                await self.add_strategic_account(username, tier, category, classification)
            except Exception as e:
                logger.error(f"Failed to add @{username}: {e}")
        
        logger.info(f"Tier 1 initialization complete. {len(self.accounts)} accounts added.")
        return self.get_strategic_accounts_summary()