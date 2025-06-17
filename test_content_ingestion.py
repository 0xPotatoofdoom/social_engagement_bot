#!/usr/bin/env python3
"""
Content Ingestion Testing Script

Test the trend monitoring and content ingestion system with real data.
This will start identifying opportunities for banger posts!
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add src to path so we can import our implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import our implementations
try:
    from bot.api.x_client import XAPIClient
    from bot.monitoring.trend_monitor import TrendMonitor, ContentOpportunity
    print("✅ Successfully imported content ingestion components")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def get_credentials():
    """Get X API credentials from environment."""
    credentials = {
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET'),
        'bearer_token': os.getenv('X_BEARER_TOKEN')
    }
    
    # Validate all credentials are present
    missing = [k for k, v in credentials.items() if not v]
    if missing:
        print(f"❌ Missing credentials: {missing}")
        return None
    
    print("✅ All X API credentials loaded from environment")
    return credentials


async def test_content_ingestion():
    """Test content ingestion and opportunity identification."""
    print("🎯 Content Ingestion & Opportunity Detection Test")
    print("=" * 60)
    
    # Get credentials and initialize clients
    credentials = get_credentials()
    if not credentials:
        return False
    
    try:
        x_client = XAPIClient(**credentials)
        print("✅ X API client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize X client: {e}")
        return False
    
    # Define target topics for your banger posts
    target_topics = [
        "crypto", "defi", "blockchain", "web3", "nft", "ethereum", "bitcoin",
        "ai", "machine learning", "tech", "startup", "product", "design",
        "programming", "development", "coding", "python", "javascript"
    ]
    
    # Initialize trend monitor
    trend_monitor = TrendMonitor(x_client, target_topics=target_topics)
    print(f"✅ Trend monitor initialized with {len(target_topics)} target topics")
    
    # Test mention analysis
    print("\n📥 Analyzing Current Mentions for Opportunities...")
    
    mentions = await trend_monitor.check_mentions()
    
    if mentions:
        print(f"✅ Found {len(mentions)} mentions to analyze")
        
        # Show sample mentions
        print("\n📝 Recent Mentions:")
        for i, mention in enumerate(mentions[:3], 1):
            text = mention.get('text', 'No text')
            author_id = mention.get('author_id', 'unknown')
            print(f"{i}. From @{author_id}: {text[:100]}{'...' if len(text) > 100 else ''}")
        
    else:
        print("📭 No new mentions found")
    
    # Get identified opportunities
    opportunities = trend_monitor.get_top_opportunities(limit=10)
    
    if opportunities:
        print(f"\n🎯 Identified {len(opportunities)} Content Opportunities:")
        print("-" * 60)
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n{i}. {opp.trigger_type.upper()} OPPORTUNITY")
            print(f"   Relevance: {opp.relevance_score:.2f} | Urgency: {opp.urgency_score:.2f}")
            print(f"   Approach: {opp.suggested_approach}")
            print(f"   Context: {opp.context.get('text', 'No context')[:100]}...")
            
            if opp.expires_at:
                time_left = opp.expires_at - datetime.now()
                print(f"   Expires in: {time_left}")
        
        # Show the top opportunity in detail
        top_opp = opportunities[0]
        print(f"\n🔥 TOP OPPORTUNITY DETAILS:")
        print(f"   Type: {top_opp.trigger_type}")
        print(f"   Score: {top_opp.relevance_score * top_opp.urgency_score:.3f}")
        print(f"   Suggested Action: {top_opp.suggested_approach}")
        
        if top_opp.trigger_type == 'mention':
            mention_text = top_opp.context.get('text', '')
            print(f"   Original Text: {mention_text}")
            print(f"   Author: @{top_opp.context.get('author_id', 'unknown')}")
        
    else:
        print("\n📊 No high-priority content opportunities identified yet")
        print("   💡 Try:")
        print("   - Getting mentioned in conversations about your target topics")
        print("   - Engaging with trending topics in your niche")
        print("   - Running the monitor continuously to catch opportunities")
    
    # Show monitoring stats
    stats = trend_monitor.get_monitoring_stats()
    print(f"\n📊 Monitoring Statistics:")
    print(f"   Target Topics: {stats['target_topics']}")
    print(f"   Active Opportunities: {stats['active_opportunities']}")
    print(f"   Total Discovered: {stats['total_opportunities_discovered']}")
    print(f"   Last Mentions Check: {stats['last_mentions_check'] or 'Never'}")
    
    return True


async def test_continuous_monitoring():
    """Test continuous monitoring for a short period."""
    print("\n🔄 Testing Continuous Monitoring...")
    print("This will monitor for 2 minutes to show real-time opportunity detection")
    
    confirm = input("Start continuous monitoring? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Skipping continuous monitoring test")
        return
    
    # Get credentials and initialize
    credentials = get_credentials()
    if not credentials:
        return
    
    x_client = XAPIClient(**credentials)
    
    # Your target topics - customize these!
    target_topics = ["crypto", "ai", "web3", "startup", "tech"]
    trend_monitor = TrendMonitor(x_client, target_topics=target_topics)
    
    print(f"🚀 Starting monitoring for {len(target_topics)} topics...")
    print("Target topics:", ", ".join(target_topics))
    print("\nMonitoring will run for 2 minutes. Press Ctrl+C to stop early.")
    
    try:
        # Start monitoring in background
        monitoring_task = asyncio.create_task(
            trend_monitor.start_monitoring(check_interval=30)  # Check every 30 seconds
        )
        
        # Let it run for 2 minutes
        await asyncio.sleep(120)
        
        # Stop monitoring
        trend_monitor.stop_monitoring()
        await monitoring_task
        
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring stopped by user")
        trend_monitor.stop_monitoring()
    
    # Show final results
    final_opportunities = trend_monitor.get_top_opportunities()
    final_stats = trend_monitor.get_monitoring_stats()
    
    print(f"\n📈 Final Results:")
    print(f"   Opportunities Found: {len(final_opportunities)}")
    print(f"   Total Mentions Processed: {final_stats['total_opportunities_discovered']}")
    
    if final_opportunities:
        print(f"\n🎯 Best Opportunity Found:")
        top = final_opportunities[0]
        print(f"   Type: {top.trigger_type}")
        print(f"   Score: {top.relevance_score * top.urgency_score:.3f}")
        print(f"   Action: {top.suggested_approach}")


async def export_opportunities_for_content_gen():
    """Export current opportunities to a file for content generation testing."""
    print("\n💾 Exporting Opportunities for Content Generation...")
    
    credentials = get_credentials()
    if not credentials:
        return
    
    x_client = XAPIClient(**credentials)
    target_topics = ["crypto", "ai", "web3", "blockchain", "startup", "tech", "defi"]
    trend_monitor = TrendMonitor(x_client, target_topics=target_topics)
    
    # Get current mentions and analyze
    await trend_monitor.check_mentions()
    opportunities = trend_monitor.get_top_opportunities(limit=5)
    
    if opportunities:
        # Export to JSON for content generation
        export_data = []
        for opp in opportunities:
            export_data.append({
                'trigger_type': opp.trigger_type,
                'relevance_score': opp.relevance_score,
                'urgency_score': opp.urgency_score,
                'suggested_approach': opp.suggested_approach,
                'context': opp.context,
                'discovered_at': opp.discovered_at.isoformat(),
                'combined_score': opp.relevance_score * opp.urgency_score
            })
        
        # Save to file
        with open('content_opportunities.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Exported {len(export_data)} opportunities to content_opportunities.json")
        print("This file can be used to test content generation next!")
        
        # Show summary
        print(f"\n📋 Opportunity Summary:")
        for i, data in enumerate(export_data, 1):
            print(f"{i}. {data['trigger_type']} (score: {data['combined_score']:.3f})")
            if data['trigger_type'] == 'mention':
                context_text = data['context'].get('text', '')[:100]
                print(f"   Context: {context_text}...")
    
    else:
        print("❌ No opportunities found to export")
        print("💡 Try getting mentioned in some conversations first!")


async def main():
    """Main test menu."""
    while True:
        print("\n" + "="*60)
        print("🎯 CONTENT INGESTION TESTING MENU")
        print("="*60)
        print()
        print("1. 📥 Test Current Mention Analysis")
        print("2. 🔄 Test Continuous Monitoring (2 min)")
        print("3. 💾 Export Opportunities for Content Generation")
        print("4. 📊 Show Current Target Topics")
        print("5. 🚪 Exit")
        print()
        
        choice = input("Choose an option (1-5): ").strip()
        
        if choice == "1":
            await test_content_ingestion()
        elif choice == "2":
            await test_continuous_monitoring()
        elif choice == "3":
            await export_opportunities_for_content_gen()
        elif choice == "4":
            print("\n🎯 Current Target Topics:")
            topics = ["crypto", "ai", "web3", "blockchain", "startup", "tech", "defi", "nft", "ethereum"]
            for i, topic in enumerate(topics, 1):
                print(f"   {i}. {topic}")
            print("\n💡 You can customize these in the script!")
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")