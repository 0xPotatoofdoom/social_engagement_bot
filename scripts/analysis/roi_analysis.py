"""
ROI Analysis for AI x Blockchain Monitoring System
Calculate return on investment and justify API tier upgrade costs
"""

import json
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd

# Add src to path
sys.path.append("../../src")

@dataclass
class ROIMetrics:
    """ROI calculation metrics"""
    
    # Cost Analysis
    current_monthly_cost: float = 0.0          # Free tier
    proposed_monthly_cost: float = 200.0       # Pro tier
    
    # Opportunity Metrics (from monitoring data)
    opportunities_per_day: float = 0.0
    high_priority_opportunities_per_day: float = 0.0
    conversion_rate: float = 0.0               # % of opportunities acted upon
    
    # Engagement Metrics
    avg_engagement_per_opportunity: float = 0.0 # likes, replies, retweets
    follower_growth_rate: float = 0.0          # followers gained per month
    strategic_connections_made: int = 0         # Tier 1 account relationships
    
    # Business Value Metrics
    value_per_strategic_connection: float = 500.0    # Estimated value
    value_per_high_priority_opportunity: float = 50.0 # Estimated value
    time_saved_per_day: float = 2.0            # Hours saved vs manual monitoring
    hourly_rate: float = 100.0                 # Your time value
    
    def calculate_monthly_value(self) -> Dict[str, float]:
        """Calculate monthly value generated"""
        days_per_month = 30
        
        # Direct value from opportunities
        opportunity_value = (
            self.opportunities_per_day * 
            days_per_month * 
            self.conversion_rate * 
            self.value_per_high_priority_opportunity
        )
        
        # Value from strategic connections
        connection_value = (
            self.strategic_connections_made * 
            self.value_per_strategic_connection
        )
        
        # Time savings value
        time_value = (
            self.time_saved_per_day * 
            days_per_month * 
            self.hourly_rate
        )
        
        # Indirect value from follower growth and engagement
        # (harder to quantify, conservative estimate)
        engagement_value = (
            self.follower_growth_rate * 
            self.avg_engagement_per_opportunity * 
            0.1  # Conservative multiplier
        )
        
        total_value = opportunity_value + connection_value + time_value + engagement_value
        
        return {
            'opportunity_value': opportunity_value,
            'connection_value': connection_value,
            'time_savings_value': time_value,
            'engagement_value': engagement_value,
            'total_monthly_value': total_value,
            'roi_current_tier': ((total_value - self.current_monthly_cost) / max(1, self.current_monthly_cost)) * 100,
            'roi_pro_tier': ((total_value - self.proposed_monthly_cost) / self.proposed_monthly_cost) * 100,
            'break_even_value': self.proposed_monthly_cost,
            'monthly_profit': total_value - self.proposed_monthly_cost
        }

class ROIAnalyzer:
    """Analyze ROI from monitoring metrics"""
    
    def __init__(self):
        self.metrics_file = Path('data/metrics/performance_metrics.json')
        self.roi_file = Path('data/metrics/roi_analysis.json')
        self.roi_file.parent.mkdir(exist_ok=True)
    
    def load_monitoring_data(self) -> List[Dict]:
        """Load historical monitoring data"""
        if not self.metrics_file.exists():
            return []
        
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metrics: {e}")
            return []
    
    def calculate_roi_from_data(self, data: List[Dict]) -> ROIMetrics:
        """Calculate ROI metrics from monitoring data"""
        if not data:
            # Return baseline estimates for new deployment
            return ROIMetrics(
                opportunities_per_day=3.0,
                high_priority_opportunities_per_day=1.0,
                conversion_rate=0.3,
                avg_engagement_per_opportunity=5.0,
                follower_growth_rate=20.0,
                strategic_connections_made=2
            )
        
        # Calculate from actual data
        recent_data = data[-168:]  # Last week of hourly data
        
        if not recent_data:
            return ROIMetrics()
        
        # Calculate averages
        total_opportunities = sum(item.get('opportunities_found', 0) for item in recent_data)
        total_high_priority = sum(item.get('high_priority_opportunities', 0) for item in recent_data)
        total_emails = sum(item.get('email_alerts_sent', 0) for item in recent_data)
        
        hours_of_data = len(recent_data)
        opportunities_per_hour = total_opportunities / max(1, hours_of_data)
        high_priority_per_hour = total_high_priority / max(1, hours_of_data)
        
        # Estimate conversion rate based on email alerts sent
        conversion_rate = total_emails / max(1, total_high_priority) if total_high_priority > 0 else 0.3
        
        return ROIMetrics(
            opportunities_per_day=opportunities_per_hour * 24,
            high_priority_opportunities_per_day=high_priority_per_hour * 24,
            conversion_rate=min(1.0, conversion_rate),
            avg_engagement_per_opportunity=5.0,  # Conservative estimate
            follower_growth_rate=opportunities_per_hour * 24 * 2,  # Estimate based on activity
            strategic_connections_made=max(1, int(total_high_priority / 10))  # 1 connection per 10 opportunities
        )
    
    def generate_roi_report(self) -> Dict:
        """Generate comprehensive ROI report"""
        data = self.load_monitoring_data()
        roi_metrics = self.calculate_roi_from_data(data)
        value_analysis = roi_metrics.calculate_monthly_value()
        
        # Rate limiting analysis
        if data:
            rate_limit_hits = sum(item.get('rate_limit_hits', 0) for item in data[-24:])  # Last 24 hours
            api_calls = sum(item.get('api_calls_made', 0) for item in data[-24:])
            rate_limit_percentage = (rate_limit_hits / max(1, api_calls)) * 100
        else:
            rate_limit_percentage = 0
        
        # API tier comparison
        free_tier_limits = {
            'search_tweets': 300,    # per 15 min
            'user_timeline': 1500,   # per 15 min
            'monthly_tweets': 1500   # total per month
        }
        
        pro_tier_limits = {
            'search_tweets': 300,    # per 15 min (same)
            'user_timeline': 1500,   # per 15 min (same) 
            'monthly_tweets': 50000  # significant increase
        }
        
        report = {
            'analysis_date': datetime.now().isoformat(),
            'monitoring_data_points': len(data),
            'roi_metrics': {
                'opportunities_per_day': roi_metrics.opportunities_per_day,
                'high_priority_per_day': roi_metrics.high_priority_opportunities_per_day,
                'conversion_rate': roi_metrics.conversion_rate,
                'strategic_connections': roi_metrics.strategic_connections_made
            },
            'value_analysis': value_analysis,
            'rate_limiting': {
                'current_hit_rate': rate_limit_percentage,
                'estimated_missed_opportunities': rate_limit_percentage * 0.1,  # Conservative
                'free_tier_sufficient': rate_limit_percentage < 10
            },
            'tier_comparison': {
                'free_tier': {
                    'monthly_cost': 0,
                    'limitations': free_tier_limits,
                    'estimated_monthly_value': value_analysis['total_monthly_value']
                },
                'pro_tier': {
                    'monthly_cost': 200,
                    'capabilities': pro_tier_limits,
                    'estimated_monthly_value': value_analysis['total_monthly_value'] * 1.2  # 20% improvement
                }
            },
            'recommendations': self.generate_recommendations(value_analysis, rate_limit_percentage)
        }
        
        # Save analysis
        with open(self.roi_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def generate_recommendations(self, value_analysis: Dict, rate_limit_percentage: float) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        monthly_profit = value_analysis['monthly_profit']
        roi_pro_tier = value_analysis['roi_pro_tier']
        
        if monthly_profit > 0:
            recommendations.append(f"✅ UPGRADE RECOMMENDED: Pro tier generates ${monthly_profit:.0f}/month profit")
        else:
            recommendations.append(f"⏳ WAIT: Need ${abs(monthly_profit):.0f} more monthly value to justify upgrade")
        
        if roi_pro_tier > 100:
            recommendations.append(f"💰 HIGH ROI: {roi_pro_tier:.0f}% return on investment")
        elif roi_pro_tier > 50:
            recommendations.append(f"📈 GOOD ROI: {roi_pro_tier:.0f}% return on investment")
        else:
            recommendations.append(f"📊 LOW ROI: {roi_pro_tier:.0f}% return - focus on improving conversion")
        
        if rate_limit_percentage > 15:
            recommendations.append("🚨 HIGH RATE LIMITING: Upgrade would unlock more opportunities")
        elif rate_limit_percentage > 5:
            recommendations.append("⚠️ MODERATE RATE LIMITING: Monitor for missed opportunities")
        else:
            recommendations.append("✅ LOW RATE LIMITING: Free tier currently sufficient")
        
        # Performance recommendations
        if value_analysis['opportunity_value'] < 500:
            recommendations.append("🎯 FOCUS: Improve opportunity conversion rate")
        
        if value_analysis['connection_value'] < 1000:
            recommendations.append("🤝 FOCUS: Build more strategic relationships")
        
        return recommendations
    
    def create_roi_dashboard(self, report: Dict):
        """Create visual ROI dashboard"""
        try:
            import matplotlib.pyplot as plt
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Value breakdown pie chart
            value_data = report['value_analysis']
            values = [
                value_data['opportunity_value'],
                value_data['connection_value'], 
                value_data['time_savings_value'],
                value_data['engagement_value']
            ]
            labels = ['Opportunities', 'Connections', 'Time Savings', 'Engagement']
            ax1.pie(values, labels=labels, autopct='%1.1f%%')
            ax1.set_title('Monthly Value Breakdown')
            
            # ROI comparison bar chart
            tiers = ['Free Tier', 'Pro Tier']
            roi_values = [
                value_data['roi_current_tier'],
                value_data['roi_pro_tier']
            ]
            ax2.bar(tiers, roi_values, color=['green', 'blue'])
            ax2.set_title('ROI Comparison')
            ax2.set_ylabel('ROI %')
            
            # Monthly profit comparison
            costs = [0, 200]
            profits = [
                value_data['total_monthly_value'],
                value_data['total_monthly_value'] * 1.2 - 200
            ]
            x = range(len(tiers))
            ax3.bar([i - 0.2 for i in x], costs, 0.4, label='Cost', color='red', alpha=0.7)
            ax3.bar([i + 0.2 for i in x], profits, 0.4, label='Profit', color='green', alpha=0.7)
            ax3.set_title('Monthly Cost vs Profit')
            ax3.set_ylabel('USD')
            ax3.set_xticks(x)
            ax3.set_xticklabels(tiers)
            ax3.legend()
            
            # Opportunities timeline (if data available)
            data = self.load_monitoring_data()
            if data:
                timestamps = [item.get('timestamp', '') for item in data[-24:]]
                opportunities = [item.get('opportunities_found', 0) for item in data[-24:]]
                ax4.plot(range(len(opportunities)), opportunities, marker='o')
                ax4.set_title('Opportunities Found (Last 24 Hours)')
                ax4.set_ylabel('Opportunities')
                ax4.set_xlabel('Time Points')
            else:
                ax4.text(0.5, 0.5, 'No monitoring data available', 
                        ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('Monitoring Data')
            
            plt.tight_layout()
            plt.savefig('data/metrics/roi_dashboard.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print("📊 ROI dashboard saved to data/metrics/roi_dashboard.png")
            
        except ImportError:
            print("📊 Install matplotlib for visual dashboard: pip install matplotlib")
        except Exception as e:
            print(f"Dashboard creation error: {e}")

async def main():
    """Generate ROI analysis report"""
    
    print("💰 AI x Blockchain Monitoring ROI Analysis")
    print("=" * 60)
    
    analyzer = ROIAnalyzer()
    report = analyzer.generate_roi_report()
    
    print(f"\n📊 Analysis Results (based on {report['monitoring_data_points']} data points):")
    print("-" * 50)
    
    roi_metrics = report['roi_metrics']
    print(f"📈 Opportunities per day: {roi_metrics['opportunities_per_day']:.1f}")
    print(f"🔥 High priority per day: {roi_metrics['high_priority_per_day']:.1f}")
    print(f"✅ Conversion rate: {roi_metrics['conversion_rate']:.1%}")
    print(f"🤝 Strategic connections: {roi_metrics['strategic_connections']}")
    
    value_analysis = report['value_analysis']
    print(f"\n💰 Value Analysis:")
    print("-" * 30)
    print(f"Monthly value generated: ${value_analysis['total_monthly_value']:.0f}")
    print(f"Pro tier monthly cost: $200")
    print(f"Estimated monthly profit: ${value_analysis['monthly_profit']:.0f}")
    print(f"ROI on Pro tier: {value_analysis['roi_pro_tier']:.0f}%")
    
    rate_limiting = report['rate_limiting']
    print(f"\n🚨 Rate Limiting Analysis:")
    print("-" * 30)
    print(f"Current hit rate: {rate_limiting['current_hit_rate']:.1f}%")
    print(f"Free tier sufficient: {'✅ Yes' if rate_limiting['free_tier_sufficient'] else '❌ No'}")
    
    print(f"\n🎯 Recommendations:")
    print("-" * 30)
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    # Create visual dashboard
    analyzer.create_roi_dashboard(report)
    
    # Decision summary
    print(f"\n🎯 DECISION SUMMARY:")
    print("=" * 40)
    
    if value_analysis['monthly_profit'] > 0:
        print(f"✅ UPGRADE TO PRO TIER RECOMMENDED")
        print(f"   Expected monthly profit: ${value_analysis['monthly_profit']:.0f}")
        print(f"   ROI: {value_analysis['roi_pro_tier']:.0f}%")
    else:
        print(f"⏳ CONTINUE WITH FREE TIER")
        print(f"   Need ${abs(value_analysis['monthly_profit']):.0f} more monthly value")
        print(f"   Focus on improving conversion and strategic connections")
    
    print(f"\n📊 Full analysis saved to: {analyzer.roi_file}")

if __name__ == "__main__":
    asyncio.run(main())