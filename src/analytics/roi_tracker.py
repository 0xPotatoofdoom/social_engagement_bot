"""
ROI Tracker - tracks return on investment for the X engagement bot system.

This module provides:
1. Comprehensive ROI calculation
2. Value generation tracking
3. Investment optimization recommendations
4. Cost-benefit analysis
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .follower_growth_tracker import FollowerGrowthTracker


class ROITracker:
    """Tracks ROI and value generation for the X engagement bot investment"""
    
    def __init__(self, data_dir: str = "data/analytics"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.roi_file = self.data_dir / "roi_tracking.json"
        self.follower_tracker = FollowerGrowthTracker(data_dir)
        
        # Investment costs
        self.monthly_costs = {
            'x_api_pro': 200,  # X API Pro tier
            'claude_api': 20,  # Estimated Claude API usage
            'server_hosting': 0,  # Currently using local Docker
            'development_time': 0  # One-time setup cost
        }
        
        # Value multipliers (conservative estimates)
        self.value_multipliers = {
            'follower_value_per_verified': 2.5,  # Value per verified follower
            'strategic_relationship_value': 100,  # Value per active strategic relationship
            'authority_recognition_value': 500,  # Value of established authority
            'time_saved_per_hour': 50,  # Value of automation vs manual work
            'viral_content_multiplier': 10  # Multiplier for viral content value
        }
        
        if not self.roi_file.exists():
            self._initialize_roi_tracking()
    
    def calculate_comprehensive_roi(self, months: int = 3) -> Dict[str, Any]:
        """Calculate comprehensive ROI for the investment period"""
        
        # Calculate total investment
        monthly_cost = sum(self.monthly_costs.values())
        total_investment = monthly_cost * months
        
        # Get baseline and current metrics
        baseline_data = self.follower_tracker._load_baseline_metrics()
        baseline_followers = baseline_data.get('verified_followers', 397)
        
        # Estimate current followers (baseline + growth)
        estimated_daily_growth = 1.5
        days_elapsed = 30  # Assume 1 month since deployment
        current_estimated_followers = baseline_followers + int(estimated_daily_growth * days_elapsed)
        
        # Calculate value generated
        value_generated = self._calculate_value_generated(baseline_followers, current_estimated_followers, months)
        
        # Calculate ROI metrics
        net_value = value_generated['total_value'] - total_investment
        roi_percentage = (net_value / total_investment) * 100 if total_investment > 0 else 0
        payback_period_months = total_investment / (value_generated['monthly_value'] if value_generated['monthly_value'] > 0 else 1)
        
        # Project annual ROI
        annual_investment = monthly_cost * 12
        annual_value = value_generated['monthly_value'] * 12
        projected_annual_roi = ((annual_value - annual_investment) / annual_investment) * 100 if annual_investment > 0 else 0
        
        # Optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(value_generated, total_investment)
        
        # Resource allocation recommendations
        resource_recommendations = self._generate_resource_allocation_recommendations(value_generated)
        
        return {
            'analysis_period_months': months,
            'total_investment': total_investment,
            'monthly_investment': monthly_cost,
            'investment_breakdown': self.monthly_costs,
            'value_generated': value_generated,
            'roi_metrics': {
                'net_value': round(net_value, 2),
                'roi_percentage': round(roi_percentage, 1),
                'payback_period_months': round(payback_period_months, 1),
                'projected_annual_roi': round(projected_annual_roi, 1)
            },
            'optimization_opportunities': optimization_opportunities,
            'resource_allocation_recommendations': resource_recommendations,
            'investment_grade': self._calculate_investment_grade(roi_percentage),
            'calculated_at': datetime.now().isoformat()
        }
    
    def _calculate_value_generated(self, baseline_followers: int, current_followers: int, months: int) -> Dict[str, float]:
        """Calculate total value generated from the investment"""
        
        # Follower value
        follower_growth = current_followers - baseline_followers
        follower_value = follower_growth * self.value_multipliers['follower_value_per_verified']
        
        # Strategic relationship value
        estimated_strategic_relationships = 3  # Conservative estimate
        relationship_value = estimated_strategic_relationships * self.value_multipliers['strategic_relationship_value']
        
        # Authority value (progressive - increases over time)
        authority_progress = min(1.0, months / 6)  # 6 months to established authority
        authority_value = authority_progress * self.value_multipliers['authority_recognition_value']
        
        # Time saved value
        hours_saved_per_month = 80  # 20 hours/week of manual monitoring
        time_saved_value = hours_saved_per_month * months * self.value_multipliers['time_saved_per_hour']
        
        # Engagement value (from improved content quality)
        baseline_engagement_rate = 4.9  # From analytics
        estimated_current_engagement = 6.2  # Improved through optimization
        engagement_improvement = estimated_current_engagement - baseline_engagement_rate
        engagement_value = engagement_improvement * 100  # Value per % improvement
        
        # Opportunity value (high-quality opportunities identified)
        opportunities_per_month = 30  # Estimated opportunities identified
        opportunity_value_each = 25  # Estimated value per opportunity
        opportunity_value = opportunities_per_month * months * opportunity_value_each
        
        # Network effects value (compounding relationships)
        network_effects_multiplier = 1 + (months * 0.1)  # 10% increase per month
        network_effects_value = relationship_value * (network_effects_multiplier - 1)
        
        total_value = (
            follower_value +
            relationship_value +
            authority_value +
            time_saved_value +
            engagement_value +
            opportunity_value +
            network_effects_value
        )
        
        monthly_value = total_value / months if months > 0 else 0
        
        return {
            'follower_value': round(follower_value, 2),
            'relationship_value': round(relationship_value, 2),
            'authority_value': round(authority_value, 2),
            'time_saved_value': round(time_saved_value, 2),
            'engagement_value': round(engagement_value, 2),
            'opportunity_value': round(opportunity_value, 2),
            'network_effects_value': round(network_effects_value, 2),
            'total_value': round(total_value, 2),
            'monthly_value': round(monthly_value, 2)
        }
    
    def _identify_optimization_opportunities(self, value_generated: Dict[str, float], total_investment: float) -> List[Dict[str, Any]]:
        """Identify opportunities to optimize ROI"""
        opportunities = []
        
        # Analyze value components for optimization potential
        value_components = [
            ('follower_value', 'Follower Growth'),
            ('relationship_value', 'Strategic Relationships'),
            ('authority_value', 'Authority Building'),
            ('opportunity_value', 'Opportunity Quality')
        ]
        
        for component_key, component_name in value_components:
            component_value = value_generated.get(component_key, 0)
            component_percentage = (component_value / value_generated['total_value']) * 100 if value_generated['total_value'] > 0 else 0
            
            if component_percentage < 15:  # Low contribution
                opportunities.append({
                    'area': component_name,
                    'current_value': component_value,
                    'optimization_potential': 'high',
                    'recommended_actions': self._get_optimization_actions(component_key),
                    'estimated_value_increase': component_value * 0.5  # 50% improvement potential
                })
            elif component_percentage > 40:  # High contribution - protect and enhance
                opportunities.append({
                    'area': component_name,
                    'current_value': component_value,
                    'optimization_potential': 'medium',
                    'recommended_actions': [f'Maintain and slightly enhance {component_name.lower()}'],
                    'estimated_value_increase': component_value * 0.2  # 20% improvement potential
                })
        
        # Overall optimization recommendations
        if value_generated['total_value'] / total_investment < 3:  # Less than 3x return
            opportunities.append({
                'area': 'Overall System Efficiency',
                'current_value': value_generated['total_value'],
                'optimization_potential': 'high',
                'recommended_actions': [
                    'Increase strategic account engagement frequency',
                    'Improve opportunity detection relevance',
                    'Enhance voice consistency across content types'
                ],
                'estimated_value_increase': total_investment  # 1x investment increase
            })
        
        return opportunities
    
    def _get_optimization_actions(self, component_key: str) -> List[str]:
        """Get specific optimization actions for a value component"""
        action_map = {
            'follower_value': [
                'Increase posting frequency during peak engagement hours',
                'Improve content virality through controversial takes',
                'Enhance strategic account relationship building'
            ],
            'relationship_value': [
                'Increase response quality and technical depth',
                'Initiate more conversations with tier 1 accounts',
                'Focus on mutual engagement opportunities'
            ],
            'authority_value': [
                'Create more original technical content',
                'Engage in high-visibility discussions',
                'Build thought leadership in v4/Unichain space'
            ],
            'opportunity_value': [
                'Refine opportunity detection algorithms',
                'Focus on higher-score opportunities only',
                'Improve voice alignment in responses'
            ]
        }
        
        return action_map.get(component_key, ['Analyze and optimize this component'])
    
    def _generate_resource_allocation_recommendations(self, value_generated: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate recommendations for resource allocation"""
        
        total_value = value_generated['total_value']
        recommendations = []
        
        # X API Investment
        api_efficiency = value_generated['opportunity_value'] / (self.monthly_costs['x_api_pro'] * 3)
        if api_efficiency > 3:  # Good return
            recommendations.append({
                'resource': 'X API Pro Subscription',
                'current_allocation': self.monthly_costs['x_api_pro'],
                'recommendation': 'maintain',
                'reasoning': f'Good ROI: ${api_efficiency:.1f} value per dollar spent',
                'suggested_changes': None
            })
        else:
            recommendations.append({
                'resource': 'X API Pro Subscription',
                'current_allocation': self.monthly_costs['x_api_pro'],
                'recommendation': 'optimize',
                'reasoning': f'Below target ROI: ${api_efficiency:.1f} value per dollar spent',
                'suggested_changes': 'Improve opportunity detection efficiency'
            })
        
        # Claude API Usage
        claude_efficiency = (value_generated['authority_value'] + value_generated['engagement_value']) / (self.monthly_costs['claude_api'] * 3)
        if claude_efficiency > 5:
            recommendations.append({
                'resource': 'Claude API Usage',
                'current_allocation': self.monthly_costs['claude_api'],
                'recommendation': 'increase',
                'reasoning': f'High ROI: ${claude_efficiency:.1f} value per dollar spent',
                'suggested_changes': 'Consider increasing usage for more sophisticated analysis'
            })
        
        # Time Investment
        recommendations.append({
            'resource': 'Development and Monitoring Time',
            'current_allocation': 'automated',
            'recommendation': 'maintain',
            'reasoning': f'Automation delivering ${value_generated["time_saved_value"]:.0f} in time savings',
            'suggested_changes': 'Continue automation focus, minimal manual intervention'
        })
        
        return recommendations
    
    def _calculate_investment_grade(self, roi_percentage: float) -> str:
        """Calculate investment grade based on ROI"""
        if roi_percentage >= 500:  # 5x return
            return 'A+ (Excellent)'
        elif roi_percentage >= 300:  # 3x return
            return 'A (Very Good)'
        elif roi_percentage >= 200:  # 2x return
            return 'B+ (Good)'
        elif roi_percentage >= 100:  # 1x return (break even)
            return 'B (Acceptable)'
        elif roi_percentage >= 0:  # Positive return
            return 'C (Below Target)'
        else:  # Negative return
            return 'D (Needs Improvement)'
    
    def _initialize_roi_tracking(self) -> None:
        """Initialize ROI tracking file"""
        initial_data = {
            'tracking_started': datetime.now().isoformat(),
            'baseline_metrics': self.follower_tracker._load_baseline_metrics(),
            'investment_assumptions': {
                'monthly_costs': self.monthly_costs,
                'value_multipliers': self.value_multipliers
            },
            'roi_history': []
        }
        
        with open(self.roi_file, 'w') as f:
            json.dump(initial_data, f, indent=2, default=str)