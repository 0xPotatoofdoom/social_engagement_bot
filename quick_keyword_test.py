#!/usr/bin/env python3
"""
Quick automated test of keyword search functionality
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path so we can import our implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import our implementations
from bot.api.x_client import XAPIClient
from bot.api.claude_client import ClaudeAPIClient
from bot.monitoring.trend_monitor import TrendMonitor

async def quick_test():
    """Quick test of the keyword search system."""
    print("🔍 Quick Keyword Search Test")
    print("=" * 40)
    
    # Get credentials
    x_credentials = {
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET'),
        'bearer_token': os.getenv('X_BEARER_TOKEN')
    }
    
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    
    if not all(x_credentials.values()) or not claude_api_key:
        print("❌ Missing credentials")
        return
    
    try:
        # Initialize clients
        x_client = XAPIClient(**x_credentials)
        print("✅ X API client initialized")
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            print("✅ Claude API client initialized")
            
            # Test search functionality
            keywords = ["defi", "uniswap"]
            trend_monitor = TrendMonitor(
                x_client=x_client,
                claude_client=claude_client,
                search_keywords=keywords
            )
            print(f"✅ Trend monitor with {len(keywords)} keywords ready")
            
            # Quick search test (limiting to 1 keyword to avoid rate limits)
            print("\n🔍 Testing search for 'defi'...")
            results = await trend_monitor.search_tweets_by_keyword("defi", max_results=10)
            
            if results:
                print(f"✅ Found {len(results)} tweets about 'defi'")
                for i, tweet in enumerate(results, 1):
                    print(f"   {i}. @{tweet['author_id']}: {tweet['text'][:80]}...")
            else:
                print("ℹ️  No tweets found (may be rate limited or no recent activity)")
            
            # Test sentiment analysis
            if results:
                sample_tweet = results[0]
                print(f"\n😊 Testing sentiment analysis on first tweet...")
                sentiment = await claude_client.analyze_sentiment(
                    text=sample_tweet['text'],
                    context="Testing sentiment analysis"
                )
                print(f"   Sentiment: {sentiment.overall_sentiment} ({sentiment.confidence:.2f})")
                print(f"   Engagement potential: {sentiment.engagement_potential:.2f}")
                print(f"   Themes: {sentiment.key_themes}")
            
            print("\n🎉 All systems operational!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())