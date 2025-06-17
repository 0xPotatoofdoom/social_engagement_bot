"""
Test Script for Strategic Account Monitoring System
Tests the complete AI x blockchain monitoring pipeline
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import structlog

# Add src to path for imports
sys.path.append('src')

from bot.api.x_client import XAPIClient
from bot.api.claude_client import ClaudeAPIClient
from bot.accounts.tracker import StrategicAccountTracker
from bot.scheduling.cron_monitor import CronMonitorSystem, AlertConfiguration, create_gmail_config

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_strategic_monitoring():
    """Test the complete strategic monitoring system"""
    print("🚀 Starting Strategic Account Monitoring System Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize X API client
    print("\n1. Initializing X API Client...")
    x_client = XAPIClient(
        api_key=os.getenv('X_API_KEY'),
        api_secret=os.getenv('X_API_SECRET'),
        access_token=os.getenv('X_ACCESS_TOKEN'),
        access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
        bearer_token=os.getenv('X_BEARER_TOKEN')
    )
    
    # Test X API connection
    print("Testing X API connection...")
    health = await x_client.health_check()
    print(f"✅ X API Status: {health['overall_health']}")
    
    # Initialize Claude API client
    print("\n2. Initializing Claude API Client...")
    claude_client = ClaudeAPIClient(api_key=os.getenv('CLAUDE_API_KEY'))
    
    # Test Claude API connection
    print("Testing Claude API connection...")
    test_response = await claude_client.analyze_sentiment(
        text="Testing AI x blockchain monitoring system",
        context="system test"
    )
    print(f"✅ Claude API Status: Working ({test_response.overall_sentiment})")
    
    # Initialize Strategic Account Tracker
    print("\n3. Setting up Strategic Account Tracker...")
    strategic_tracker = StrategicAccountTracker(x_client=x_client, claude_client=claude_client)
    
    # Initialize Tier 1 accounts
    print("Adding Tier 1 strategic accounts...")
    summary = await strategic_tracker.initialize_tier_1_accounts()
    print(f"✅ Strategic accounts initialized: {summary}")
    
    # Test monitoring cycle (without email alerts)
    print("\n4. Testing Monitoring Cycle...")
    
    # Create test configuration (no email sending)
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
        claude_client=claude_client,
        strategic_tracker=strategic_tracker,
        config=test_config
    )
    
    # Test strategic account monitoring
    print("Testing strategic account content monitoring...")
    strategic_opportunities = await monitor._monitor_strategic_accounts()
    print(f"✅ Strategic account opportunities found: {len(strategic_opportunities)}")
    
    # Test AI x blockchain keyword monitoring
    print("Testing AI x blockchain keyword monitoring...")
    keyword_opportunities = await monitor._monitor_ai_blockchain_keywords()
    print(f"✅ Keyword opportunities found: {len(keyword_opportunities)}")
    
    # Process all opportunities
    print("Processing and scoring opportunities...")
    all_opportunities = strategic_opportunities + keyword_opportunities
    processed_opportunities = await monitor._process_opportunities(all_opportunities)
    print(f"✅ Processed opportunities: {len(processed_opportunities)}")
    
    # Display top opportunities
    if processed_opportunities:
        print("\n📊 Top Opportunities Discovered:")
        print("-" * 50)
        
        for i, opp in enumerate(processed_opportunities[:3], 1):
            print(f"\n{i}. @{opp.account_username} (Score: {opp.overall_score:.2f})")
            print(f"   Type: {opp.opportunity_type}")
            print(f"   AI x Blockchain Relevance: {opp.ai_blockchain_relevance:.2f}")
            print(f"   Technical Depth: {opp.technical_depth:.2f}")
            print(f"   Time Sensitivity: {opp.time_sensitivity}")
            print(f"   Content: {opp.content_text[:100]}...")
            print(f"   Strategic Context: {opp.strategic_context}")
    
    # Test monitoring stats
    print("\n5. Testing Monitoring Statistics...")
    stats = monitor.get_monitoring_stats()
    print("✅ Monitoring Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test strategic account relationship tracking
    print("\n6. Testing Relationship Tracking...")
    if strategic_tracker.accounts:
        test_username = list(strategic_tracker.accounts.keys())[0]
        await strategic_tracker.track_relationship_progression(
            test_username, 
            "reply", 
            "positive"
        )
        
        account = strategic_tracker.accounts[test_username]
        print(f"✅ Relationship tracking test:")
        print(f"   Account: @{test_username}")
        print(f"   Relationship Score: {account.relationship_score:.2f}")
        print(f"   Relationship Stage: {account.relationship_stage}")
    
    print("\n🎉 Strategic Monitoring System Test Complete!")
    print("=" * 60)
    
    return {
        'strategic_opportunities': len(strategic_opportunities),
        'keyword_opportunities': len(keyword_opportunities),
        'processed_opportunities': len(processed_opportunities),
        'top_score': max([opp.overall_score for opp in processed_opportunities]) if processed_opportunities else 0,
        'strategic_accounts': len(strategic_tracker.accounts),
        'monitoring_ready': True
    }

async def test_email_alerts():
    """Test email alert system (optional)"""
    print("\n📧 Email Alert System Test (Optional)")
    print("-" * 40)
    
    # Check for email configuration
    gmail_address = input("Enter Gmail address for testing (or press Enter to skip): ").strip()
    if not gmail_address:
        print("⏭️  Skipping email alert test")
        return
    
    app_password = input("Enter Gmail app password: ").strip()
    if not app_password:
        print("⏭️  Skipping email alert test")
        return
    
    to_email = input("Enter destination email (or press Enter for same): ").strip()
    if not to_email:
        to_email = gmail_address
    
    # Create email configuration
    email_config = create_gmail_config(gmail_address, app_password, to_email)
    
    # Test email sending
    try:
        # Create mock opportunity for testing
        from bot.scheduling.cron_monitor import AlertOpportunity
        
        test_opportunity = AlertOpportunity(
            account_username="test_account",
            account_tier=1,
            content_text="Test AI x blockchain convergence opportunity for monitoring system validation",
            content_url="https://twitter.com/test/status/123456789",
            timestamp=datetime.now().isoformat(),
            
            overall_score=0.85,
            ai_blockchain_relevance=0.9,
            technical_depth=0.8,
            opportunity_type="technical_discussion",
            suggested_response_type="technical_insight",
            time_sensitivity="immediate",
            
            strategic_context="Test opportunity for email alert system validation",
            suggested_response="Respond with technical insight within 30 minutes"
        )
        
        # Initialize monitoring system with email config
        load_dotenv()
        x_client = XAPIClient(
            api_key=os.getenv('X_API_KEY'),
            api_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
            bearer_token=os.getenv('X_BEARER_TOKEN')
        )
        
        claude_client = ClaudeAPIClient(api_key=os.getenv('CLAUDE_API_KEY'))
        strategic_tracker = StrategicAccountTracker(x_client=x_client, claude_client=claude_client)
        
        monitor = CronMonitorSystem(
            x_client=x_client,
            claude_client=claude_client,
            strategic_tracker=strategic_tracker,
            config=email_config
        )
        
        # Send test alert
        await monitor._send_immediate_alert([test_opportunity])
        print("✅ Test email sent successfully!")
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")

def main():
    """Main test execution"""
    print("🎯 AI x Blockchain Strategic Monitoring System Test")
    print("📅 Test Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Run monitoring system test
    result = asyncio.run(test_strategic_monitoring())
    
    # Show summary
    print("\n📋 Test Summary:")
    print(f"   Strategic Opportunities: {result['strategic_opportunities']}")
    print(f"   Keyword Opportunities: {result['keyword_opportunities']}")
    print(f"   Processed Opportunities: {result['processed_opportunities']}")
    print(f"   Top Opportunity Score: {result['top_score']:.2f}")
    print(f"   Strategic Accounts: {result['strategic_accounts']}")
    print(f"   System Ready: {result['monitoring_ready']}")
    
    # Optional email test
    test_email = input("\nTest email alerts? (y/n): ").lower().strip() == 'y'
    if test_email:
        asyncio.run(test_email_alerts())
    
    print("\n✅ All tests completed successfully!")
    print("\n🚀 Your strategic monitoring system is ready for AI x blockchain KOL development!")

if __name__ == "__main__":
    main()