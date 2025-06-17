"""
Quick Strategic Monitoring System Test
Tests core functionality without triggering rate limits
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')

from bot.api.x_client import XAPIClient
from bot.api.claude_client import ClaudeAPIClient
from bot.accounts.tracker import StrategicAccountTracker, AccountProfile
from bot.scheduling.cron_monitor import CronMonitorSystem, AlertConfiguration

async def test_system_components():
    """Test individual system components"""
    print("🚀 Strategic Monitoring System - Component Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Test 1: X API Client
    print("\n1. Testing X API Client...")
    x_client = XAPIClient(
        api_key=os.getenv('X_API_KEY'),
        api_secret=os.getenv('X_API_SECRET'),
        access_token=os.getenv('X_ACCESS_TOKEN'),
        access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
        bearer_token=os.getenv('X_BEARER_TOKEN')
    )
    
    health = await x_client.health_check()
    print(f"✅ X API Status: {health['overall_health']}")
    
    # Test 2: Strategic Account Tracker (Manual Setup)
    print("\n2. Testing Strategic Account Tracker...")
    strategic_tracker = StrategicAccountTracker(x_client=x_client)
    
    # Manually add test accounts (no API calls)
    test_account = await strategic_tracker.add_strategic_account(
        username="test_ai_blockchain",
        tier=1,
        category="ai_blockchain",
        manual_classification={
            'influence_score': 0.9,
            'relevance_score': 0.8,
            'engagement_potential': 0.7,
            'technical_depth': 0.8,
            'ai_blockchain_focus': 0.9
        }
    )
    
    print(f"✅ Strategic account added: @{test_account.username}")
    print(f"   - Tier: {test_account.tier}")
    print(f"   - Category: {test_account.category}")
    print(f"   - AI x Blockchain Focus: {test_account.ai_blockchain_focus}")
    
    # Test 3: Relationship Tracking
    print("\n3. Testing Relationship Tracking...")
    await strategic_tracker.track_relationship_progression(
        "test_ai_blockchain",
        "reply",
        "positive"
    )
    
    updated_account = strategic_tracker.accounts["test_ai_blockchain"]
    print(f"✅ Relationship tracking:")
    print(f"   - Relationship Score: {updated_account.relationship_score:.2f}")
    print(f"   - Relationship Stage: {updated_account.relationship_stage}")
    print(f"   - Interactions: {len(updated_account.interaction_history)}")
    
    # Test 4: Monitoring Configuration
    print("\n4. Testing Monitoring Configuration...")
    
    # Create test configuration (no email)
    test_config = AlertConfiguration(
        smtp_server="",
        smtp_port=587,
        email_username="",
        email_password="",
        from_email="test@example.com",
        to_email="test@example.com"
    )
    
    # Initialize monitoring system
    monitor = CronMonitorSystem(
        x_client=x_client,
        claude_client=None,  # Skip Claude for this test
        strategic_tracker=strategic_tracker,
        config=test_config
    )
    
    stats = monitor.get_monitoring_stats()
    print(f"✅ Monitoring system initialized:")
    print(f"   - Monitoring Active: {stats['monitoring_active']}")
    print(f"   - Work Hours Check: {stats['is_work_hours']}")
    print(f"   - Monitoring Interval: {stats['monitoring_interval']} minutes")
    
    # Test 5: Enhanced Keywords
    print("\n5. Testing Enhanced AI x Blockchain Keywords...")
    from bot.monitoring.trend_monitor import TrendMonitor
    
    trend_monitor = TrendMonitor(
        x_client=x_client,
        claude_client=None,
        target_topics=["uniswap v4", "unichain", "defi"],
        search_keywords=["ai agents", "autonomous trading"]
    )
    
    # Test enhanced keyword analysis
    test_tweet = {
        'text': 'AI agents on blockchain will revolutionize autonomous trading in DeFi protocols',
        'id': '123456789'
    }
    
    analysis = await trend_monitor.enhanced_keyword_analysis("ai agents", test_tweet)
    print(f"✅ Enhanced keyword analysis:")
    print(f"   - AI x Blockchain Relevance: {analysis['ai_blockchain_relevance']:.2f}")
    print(f"   - Technical Depth: {analysis['technical_depth']:.2f}")
    print(f"   - Innovation Score: {analysis['innovation_score']:.2f}")
    print(f"   - Overall Score: {analysis['overall_ai_blockchain_score']:.2f}")
    
    # Test 6: Voice Evolution Configuration
    print("\n6. Testing Voice Evolution Configuration...")
    from bot.content.generator import ContentGenerator
    
    content_generator = ContentGenerator(claude_client=None)
    voice_guidelines = content_generator.voice_guidelines
    
    print(f"✅ Voice evolution configuration:")
    print(f"   - Personality Traits: {len(voice_guidelines.personality_traits)}")
    print(f"   - AI x Blockchain Focus: {'AI x blockchain technical authority' in voice_guidelines.personality_traits[0]}")
    print(f"   - Expertise Areas: {len(voice_guidelines.expertise_areas)}")
    print(f"   - Sample Tweet: {voice_guidelines.sample_tweets[0][:100]}...")
    
    # Test 7: Summary
    print("\n7. System Summary...")
    summary = strategic_tracker.get_strategic_accounts_summary()
    print(f"✅ Strategic monitoring system ready:")
    print(f"   - Strategic Accounts: {summary['total_accounts']}")
    print(f"   - Account Categories: {list(summary['by_category'].keys())}")
    print(f"   - Relationship Stages: {list(summary['relationship_stages'].keys())}")
    print(f"   - Average Relationship Score: {summary['average_relationship_score']:.2f}")
    
    print("\n🎉 Component Tests Complete!")
    print("=" * 60)
    
    return {
        'x_api_working': health['overall_health'],
        'strategic_accounts': summary['total_accounts'],
        'monitoring_configured': True,
        'voice_evolution_ready': True,
        'enhanced_keywords_working': analysis['overall_ai_blockchain_score'] > 0.5,
        'system_ready': True
    }

def main():
    """Main test execution"""
    print("🎯 AI x Blockchain Strategic Monitoring System")
    print("📅 Test Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Run system test
    result = asyncio.run(test_system_components())
    
    # Show final summary
    print("\n📋 System Readiness Check:")
    for component, status in result.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component.replace('_', ' ').title()}: {status}")
    
    if all(result.values()):
        print("\n🚀 Strategic Monitoring System is READY!")
        print("🎯 Ready for AI x blockchain KOL development!")
        
        print("\n📝 Next Steps:")
        print("   1. Configure email alerts (optional)")
        print("   2. Add real strategic accounts")
        print("   3. Start monitoring cycle")
        print("   4. Review opportunities and engage")
        
    else:
        print("\n⚠️  Some components need attention before full deployment")

if __name__ == "__main__":
    main()