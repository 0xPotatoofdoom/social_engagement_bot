"""
Strategic Relationship Tracker - tracks interactions with strategic accounts and relationship progression.

This module provides:
1. Strategic account engagement logging
2. Response rate tracking  
3. Mutual interaction detection
4. Relationship quality scoring
5. Influence analysis
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .schemas import EngagementRecord


class StrategicRelationshipTracker:
    """Tracks relationships and interactions with strategic accounts"""
    
    def __init__(self, data_dir: str = "data/analytics"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.engagements_file = self.data_dir / "strategic_engagements.json"
        self.relationships_file = self.data_dir / "relationship_metrics.json"
        
        # Strategic accounts from CLAUDE.md
        self.strategic_accounts = {
            'tier_1': ['VitalikButerin', 'dabit3', 'PatrickAlphaC', 'saucepoint', 'TheCryptoLark'],
            'tier_2': ['VirtualBacon0x', 'Morecryptoonl', 'AzFlin']
        }
        
        # Initialize files if they don't exist
        if not self.engagements_file.exists():
            self._save_json(self.engagements_file, [])
        if not self.relationships_file.exists():
            self._save_json(self.relationships_file, {})
    
    def log_engagement(self, target_account: str, engagement_type: str, 
                      content_url: str, our_response: str, 
                      opportunity_score: float, voice_alignment: float) -> Dict[str, Any]:
        """Log engagement with a strategic account"""
        
        engagement_id = str(uuid.uuid4())[:8]
        
        engagement = EngagementRecord(
            engagement_id=engagement_id,
            timestamp=datetime.now(),
            target_account=target_account,
            engagement_type=engagement_type,
            content_url=content_url,
            our_content=our_response,
            opportunity_score=opportunity_score,
            voice_alignment=voice_alignment
        )
        
        # Save engagement
        self._save_engagement(engagement)
        
        # Update relationship metrics
        self._update_relationship_metrics(target_account, engagement)
        
        result = engagement.to_dict()
        result['relationship_tier'] = self._get_account_tier(target_account)
        result['content_category'] = self._categorize_content(content_url, our_response)
        
        return result
    
    def detect_mutual_interactions(self, days: int = 14) -> Dict[str, List[Dict[str, Any]]]:
        """Detect mutual interactions with strategic accounts"""
        # This is a placeholder - in real implementation, this would:
        # 1. Monitor mentions/replies from strategic accounts
        # 2. Track when they engage with our content first
        # 3. Identify organic conversation threads
        
        # Simulate some mutual interactions based on engagement patterns
        engagements = self._load_json(self.engagements_file)
        recent_engagements = [
            eng for eng in engagements 
            if self._is_recent(eng.get('timestamp'), days)
        ]
        
        # Simulate detection of mutual interactions
        mutual_interactions = {
            'initiated_by_them': [
                {
                    'strategic_account': 'saucepoint',
                    'engagement_type': 'like',
                    'content_url': 'https://twitter.com/our_account/status/123',
                    'relationship_progression_score': 0.1,
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'initiated_by_us': recent_engagements,
            'organic_conversations': []  # Will be populated when we detect back-and-forth
        }
        
        return mutual_interactions
    
    def analyze_strategic_account_influence(self) -> Dict[str, Dict[str, float]]:
        """Analyze influence metrics of strategic accounts"""
        influence_data = {}
        
        # Data based on known influence of strategic accounts
        account_influence = {
            'VitalikButerin': {
                'follower_count': 5800000,
                'engagement_rate': 3.2,
                'ai_blockchain_authority_score': 0.95,
                'potential_amplification': 0.85
            },
            'saucepoint': {
                'follower_count': 45000,
                'engagement_rate': 8.5,
                'ai_blockchain_authority_score': 0.90,
                'potential_amplification': 0.75
            },
            'dabit3': {
                'follower_count': 280000,
                'engagement_rate': 5.1,
                'ai_blockchain_authority_score': 0.88,
                'potential_amplification': 0.80
            },
            'PatrickAlphaC': {
                'follower_count': 120000,
                'engagement_rate': 6.8,
                'ai_blockchain_authority_score': 0.85,
                'potential_amplification': 0.70
            }
        }
        
        # Add tier 2 accounts with lower influence
        tier_2_accounts = ['VirtualBacon0x', 'Morecryptoonl', 'AzFlin']
        for account in tier_2_accounts:
            account_influence[account] = {
                'follower_count': 25000,
                'engagement_rate': 4.5,
                'ai_blockchain_authority_score': 0.70,
                'potential_amplification': 0.50
            }
        
        return account_influence
    
    def _save_engagement(self, engagement: EngagementRecord) -> None:
        """Save engagement record to file"""
        engagements = self._load_json(self.engagements_file)
        engagements.append(engagement.to_dict())
        
        # Keep only last 1000 engagements
        if len(engagements) > 1000:
            engagements = engagements[-1000:]
        
        self._save_json(self.engagements_file, engagements)
    
    def _update_relationship_metrics(self, account: str, engagement: EngagementRecord) -> None:
        """Update relationship metrics for an account"""
        relationships = self._load_json(self.relationships_file)
        
        if account not in relationships:
            relationships[account] = {
                'total_engagements': 0,
                'responses_received': 0,
                'last_interaction': None,
                'relationship_strength': 0.0,
                'first_engagement': None
            }
        
        # Update metrics
        relationships[account]['total_engagements'] += 1
        relationships[account]['last_interaction'] = engagement.timestamp.isoformat()
        
        if relationships[account]['first_engagement'] is None:
            relationships[account]['first_engagement'] = engagement.timestamp.isoformat()
        
        # Calculate relationship strength (simplified formula)
        total_engagements = relationships[account]['total_engagements']
        base_strength = min(0.1 * total_engagements, 0.5)  # Max 0.5 from volume
        quality_bonus = engagement.opportunity_score * 0.3  # Up to 0.3 from quality
        voice_bonus = engagement.voice_alignment * 0.2    # Up to 0.2 from voice alignment
        
        relationships[account]['relationship_strength'] = min(1.0, base_strength + quality_bonus + voice_bonus)
        
        self._save_json(self.relationships_file, relationships)
    
    def _get_account_tier(self, account: str) -> str:
        """Get tier for strategic account"""
        if account in self.strategic_accounts['tier_1']:
            return 'tier_1'
        elif account in self.strategic_accounts['tier_2']:
            return 'tier_2'
        else:
            return 'general'
    
    def _categorize_content(self, content_url: str, our_response: str) -> str:
        """Categorize content type based on URL and response"""
        # Simple keyword-based categorization
        response_lower = our_response.lower()
        
        if any(keyword in response_lower for keyword in ['v4', 'uniswap', 'hooks']):
            return 'uniswap_v4'
        elif any(keyword in response_lower for keyword in ['ai', 'blockchain', 'convergence']):
            return 'ai_blockchain'
        elif any(keyword in response_lower for keyword in ['technical', 'implementation', 'architecture']):
            return 'technical_discussion'
        else:
            return 'general'
    
    def _is_recent(self, timestamp_str: str, days: int) -> bool:
        """Check if timestamp is within recent days"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return (datetime.now() - timestamp).days <= days
        except:
            return False
    
    def _load_json(self, file_path: Path) -> Any:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_json(self, file_path: Path, data: Any) -> None:
        """Save data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)