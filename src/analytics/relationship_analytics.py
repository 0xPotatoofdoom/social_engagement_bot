"""
Relationship Analytics - advanced analytics for strategic account relationships and progression.

This module provides:
1. Response rate calculations
2. Relationship quality scoring
3. Milestone tracking
4. Opportunity quality analysis
5. Relationship progression predictions
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from .strategic_relationship_tracker import StrategicRelationshipTracker


class RelationshipAnalytics:
    """Advanced analytics for strategic relationship progression and optimization"""
    
    def __init__(self, data_dir: str = "data/analytics"):
        self.data_dir = Path(data_dir)
        self.relationship_tracker = StrategicRelationshipTracker(data_dir)
        
    def calculate_response_rates(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Calculate response rates from strategic accounts"""
        relationships = self._load_json(self.relationship_tracker.relationships_file)
        engagements = self._load_json(self.relationship_tracker.engagements_file)
        
        # Get recent engagements
        recent_engagements = [
            eng for eng in engagements 
            if self._is_recent(eng.get('timestamp'), days)
        ]
        
        response_rates = {}
        
        # Calculate for each strategic account
        for tier, accounts in self.relationship_tracker.strategic_accounts.items():
            for account in accounts:
                account_engagements = [
                    eng for eng in recent_engagements 
                    if eng.get('target_account') == account
                ]
                
                total_engagements = len(account_engagements)
                
                # Simulate response data (in real implementation, track actual responses)
                responses_received = max(0, int(total_engagements * 0.15))  # 15% response rate estimate
                
                if total_engagements > 0:
                    response_rate = responses_received / total_engagements
                    avg_response_time = 24  # hours
                    quality_score = 0.7  # Quality of responses
                else:
                    response_rate = 0.0
                    avg_response_time = 0
                    quality_score = 0.0
                
                response_rates[account] = {
                    'total_engagements': total_engagements,
                    'responses_received': responses_received,
                    'response_rate_percentage': round(response_rate * 100, 1),
                    'avg_response_time_hours': avg_response_time,
                    'quality_of_responses': quality_score,
                    'tier': tier
                }
        
        return response_rates
    
    def calculate_relationship_scores(self) -> Dict[str, Dict[str, Any]]:
        """Calculate relationship quality scores with each strategic account"""
        relationships = self._load_json(self.relationship_tracker.relationships_file)
        response_rates = self.calculate_response_rates()
        
        relationship_scores = {}
        
        for tier, accounts in self.relationship_tracker.strategic_accounts.items():
            for account in accounts:
                # Get current relationship data
                relationship_data = relationships.get(account, {})
                response_data = response_rates.get(account, {})
                
                # Calculate relationship score components
                interaction_frequency = min(1.0, relationship_data.get('total_engagements', 0) / 10)
                response_quality = response_data.get('quality_of_responses', 0) * response_data.get('response_rate_percentage', 0) / 100
                mutual_engagement_ratio = 0.2  # Placeholder - will be calculated from actual mutual interactions
                
                # Overall relationship score (0-1 scale)
                current_score = (
                    interaction_frequency * 0.4 +
                    response_quality * 0.4 +
                    mutual_engagement_ratio * 0.2
                )
                
                # Determine progression trend
                progression_trend = 'stable'  # Placeholder - would analyze historical data
                if current_score > 0.3:
                    progression_trend = 'improving'
                elif current_score < 0.1:
                    progression_trend = 'needs_attention'
                
                # Estimate time to next milestone
                next_milestone_map = {
                    'first_response': 30,
                    'mutual_engagement': 60,
                    'strong_relationship': 120,
                    'collaboration': 180
                }
                
                current_milestone = 'first_response'
                if response_data.get('responses_received', 0) > 0:
                    current_milestone = 'mutual_engagement'
                if current_score > 0.5:
                    current_milestone = 'strong_relationship'
                if current_score > 0.8:
                    current_milestone = 'collaboration'
                
                next_milestones = list(next_milestone_map.keys())
                try:
                    current_index = next_milestones.index(current_milestone)
                    if current_index < len(next_milestones) - 1:
                        next_milestone = next_milestones[current_index + 1]
                        time_to_milestone = next_milestone_map[next_milestone]
                    else:
                        next_milestone = 'maintained_collaboration'
                        time_to_milestone = 0
                except ValueError:
                    next_milestone = 'first_response'
                    time_to_milestone = 30
                
                relationship_scores[account] = {
                    'current_score': round(current_score, 2),
                    'progression_trend': progression_trend,
                    'interaction_frequency': round(interaction_frequency, 2),
                    'response_quality': round(response_quality, 2),
                    'mutual_engagement_ratio': round(mutual_engagement_ratio, 2),
                    'time_to_relationship_milestone': time_to_milestone,
                    'next_milestone': next_milestone,
                    'tier': tier
                }
        
        return relationship_scores
    
    def track_relationship_milestones(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Track relationship milestones for each strategic account"""
        relationships = self._load_json(self.relationship_tracker.relationships_file)
        response_rates = self.calculate_response_rates()
        
        milestones = {}
        
        milestone_types = [
            'first_response',
            'first_like', 
            'first_repost',
            'conversation',
            'collaboration',
            'recommendation'
        ]
        
        for tier, accounts in self.relationship_tracker.strategic_accounts.items():
            for account in accounts:
                account_milestones = {}
                relationship_data = relationships.get(account, {})
                response_data = response_rates.get(account, {})
                
                for milestone in milestone_types:
                    achieved = False
                    date = None
                    
                    # Determine if milestone is achieved
                    if milestone == 'first_response':
                        achieved = response_data.get('responses_received', 0) > 0
                        if achieved:
                            date = relationship_data.get('first_engagement')
                    
                    elif milestone == 'first_like':
                        # Placeholder - would track actual likes
                        achieved = relationship_data.get('total_engagements', 0) > 2
                        if achieved:
                            date = relationship_data.get('first_engagement')
                    
                    elif milestone == 'conversation':
                        # Placeholder - would track multi-turn conversations
                        achieved = response_data.get('responses_received', 0) > 1
                    
                    # Add other milestone logic here
                    
                    account_milestones[milestone] = {
                        'achieved': achieved,
                        'date': date,
                        'description': self._get_milestone_description(milestone)
                    }
                
                milestones[account] = account_milestones
        
        return milestones
    
    def analyze_opportunity_quality_by_account(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Analyze quality of opportunities by strategic account"""
        engagements = self._load_json(self.relationship_tracker.engagements_file)
        
        # Get recent engagements
        recent_engagements = [
            eng for eng in engagements 
            if self._is_recent(eng.get('timestamp'), days)
        ]
        
        opportunity_quality = {}
        
        for tier, accounts in self.relationship_tracker.strategic_accounts.items():
            for account in accounts:
                account_engagements = [
                    eng for eng in recent_engagements 
                    if eng.get('target_account') == account
                ]
                
                if account_engagements:
                    avg_opportunity_score = sum(
                        eng.get('opportunity_score', 0) for eng in account_engagements
                    ) / len(account_engagements)
                    
                    avg_voice_alignment = sum(
                        eng.get('voice_alignment', 0) for eng in account_engagements
                    ) / len(account_engagements)
                    
                    # Simulate engagement success rate
                    engagement_success_rate = min(1.0, avg_opportunity_score * 0.8)
                    
                    # Placeholder for conversion to followers
                    conversion_to_followers = max(0, len(account_engagements) * 0.1)
                    
                else:
                    avg_opportunity_score = 0
                    avg_voice_alignment = 0
                    engagement_success_rate = 0
                    conversion_to_followers = 0
                
                opportunity_quality[account] = {
                    'avg_opportunity_score': round(avg_opportunity_score, 2),
                    'engagement_success_rate': round(engagement_success_rate, 2),
                    'voice_alignment_avg': round(avg_voice_alignment, 2),
                    'total_opportunities': len(account_engagements),
                    'conversion_to_followers': conversion_to_followers,
                    'tier': tier
                }
        
        return opportunity_quality
    
    def predict_relationship_progression(self, target_accounts: List[str], 
                                       time_horizon_days: int = 90) -> Dict[str, Dict[str, Any]]:
        """Predict relationship development trajectory"""
        relationship_scores = self.calculate_relationship_scores()
        
        predictions = {}
        
        for account in target_accounts:
            current_data = relationship_scores.get(account, {})
            current_score = current_data.get('current_score', 0)
            
            # Simple progression model
            growth_rate = 0.01  # 1% improvement per week
            weeks = time_horizon_days / 7
            
            estimated_score = min(1.0, current_score + (growth_rate * weeks))
            
            # Calculate probabilities based on estimated score
            probability_mutual_follow = min(1.0, estimated_score * 1.2)
            probability_collaboration = min(1.0, max(0, (estimated_score - 0.5) * 2))
            
            # Engagement frequency recommendation
            if current_score < 0.2:
                recommended_frequency = '2-3 times per week'
            elif current_score < 0.5:
                recommended_frequency = 'weekly'
            else:
                recommended_frequency = 'bi-weekly'
            
            predictions[account] = {
                'probability_of_mutual_follow': round(probability_mutual_follow, 2),
                'probability_of_collaboration': round(probability_collaboration, 2),
                'estimated_relationship_strength': round(estimated_score, 2),
                'recommended_engagement_frequency': recommended_frequency,
                'optimal_content_types': ['technical_discussion', 'uniswap_v4', 'ai_blockchain']
            }
        
        return predictions
    
    def analyze_strategic_network_effects(self) -> Dict[str, Any]:
        """Analyze network effects between strategic accounts"""
        # Placeholder for network analysis
        # In real implementation, this would analyze interconnections
        
        return {
            'account_interconnections': {
                'VitalikButerin_saucepoint': 0.8,  # High connection
                'dabit3_PatrickAlphaC': 0.6,      # Moderate connection
            },
            'influence_pathways': [
                'VitalikButerin -> saucepoint -> broader_community',
                'dabit3 -> PatrickAlphaC -> developer_community'
            ],
            'optimal_engagement_sequence': [
                'saucepoint',  # Start with most accessible
                'PatrickAlphaC',
                'dabit3',
                'VitalikButerin'  # Build up to highest influence
            ],
            'network_amplification_potential': 0.75
        }
    
    def analyze_competitor_relationships(self, competitors: List[str], 
                                       strategic_accounts: List[str]) -> Dict[str, Any]:
        """Analyze competitor relationships with strategic accounts"""
        # Placeholder for competitor analysis
        # In real implementation, this would monitor competitor engagement
        
        return {
            'competitor_engagement_frequency': {
                'competitor_1': 0.3,  # Low engagement
                'competitor_2': 0.6   # Moderate engagement
            },
            'competitor_response_rates': {
                'competitor_1': 0.1,
                'competitor_2': 0.2
            },
            'our_position_vs_competitors': 'emerging_player',
            'opportunities_to_differentiate': [
                'Technical depth in AI x blockchain convergence',
                'Consistent high-quality engagement',
                'Focus on Uniswap v4 innovation'
            ]
        }
    
    def _get_milestone_description(self, milestone: str) -> str:
        """Get description for relationship milestone"""
        descriptions = {
            'first_response': 'Strategic account responds to our engagement',
            'first_like': 'Strategic account likes our content',
            'first_repost': 'Strategic account shares our content',
            'conversation': 'Multi-turn conversation established',
            'collaboration': 'Joint discussion or content collaboration',
            'recommendation': 'Strategic account recommends us to others'
        }
        return descriptions.get(milestone, 'Unknown milestone')
    
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