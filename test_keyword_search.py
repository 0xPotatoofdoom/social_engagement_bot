#!/usr/bin/env python3
"""
Keyword Search & Sentiment Analysis Testing Script

Test proactive keyword search for "uniswap v4", "unichain", and other topics
with Claude-powered sentiment analysis to find the best engagement opportunities.
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
    from bot.api.claude_client import ClaudeAPIClient
    from bot.monitoring.trend_monitor import TrendMonitor, ContentOpportunity
    print("✅ Successfully imported keyword search and sentiment analysis components")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def get_credentials():
    """Get API credentials from environment."""
    x_credentials = {
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET'),
        'bearer_token': os.getenv('X_BEARER_TOKEN')
    }
    
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    
    # Validate X credentials
    missing_x = [k for k, v in x_credentials.items() if not v]
    if missing_x:
        print(f"❌ Missing X API credentials: {missing_x}")
        return None, None
    
    if not claude_api_key:
        print("❌ Missing Claude API key")
        return None, None
    
    print("✅ All API credentials loaded from environment")
    return x_credentials, claude_api_key


async def test_keyword_search_with_sentiment():
    """Test proactive keyword search with sentiment analysis."""
    print("🎯 PROACTIVE KEYWORD SEARCH + SENTIMENT ANALYSIS")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return False
    
    try:
        # Initialize clients
        x_client = XAPIClient(**x_credentials)
        print("✅ X API client initialized")
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            print("✅ Claude API client initialized")
            
            # Your specific keywords of interest
            search_keywords = [
                "uniswap v4",
                "unichain", 
                "defi",
                "blockchain development",
                "smart contracts"
            ]
            
            # Initialize trend monitor with both clients
            trend_monitor = TrendMonitor(
                x_client=x_client,
                claude_client=claude_client,
                target_topics=["defi", "uniswap", "blockchain"],
                search_keywords=search_keywords
            )
            
            print(f"✅ Trend monitor initialized with {len(search_keywords)} search keywords")
            print(f"🔍 Searching for: {', '.join(search_keywords)}")
            
            # Test keyword search
            print("\n🔍 Searching for keyword-based opportunities...")
            search_results = await trend_monitor.search_keyword_opportunities()
            
            print(f"\n📊 Search Results:")
            print(f"   Total tweets found: {len(search_results)}")
            
            if search_results:
                print(f"\n📝 Sample Tweets Found:")
                for i, tweet in enumerate(search_results[:3], 1):
                    keyword = tweet.get('keyword', 'unknown')
                    text = tweet.get('text', '')
                    author_id = tweet.get('author_id', 'unknown')
                    metrics = tweet.get('public_metrics', {})
                    
                    print(f"\n{i}. Keyword: '{keyword}'")
                    print(f"   Author: @{author_id}")
                    print(f"   Text: {text[:150]}{'...' if len(text) > 150 else ''}")
                    print(f"   Engagement: {metrics.get('like_count', 0)} likes, {metrics.get('retweet_count', 0)} RTs")
            
            # Get identified opportunities
            opportunities = trend_monitor.get_top_opportunities(limit=10)
            
            if opportunities:
                print(f"\n🎯 {len(opportunities)} ENGAGEMENT OPPORTUNITIES IDENTIFIED:")
                print("=" * 60)
                
                for i, opp in enumerate(opportunities, 1):
                    print(f"\n{i}. {opp.trigger_type.upper()} OPPORTUNITY")
                    print(f"   🎯 Keyword: {opp.context.get('keyword', 'N/A')}")
                    print(f"   📊 Relevance: {opp.relevance_score:.2f} | Urgency: {opp.urgency_score:.2f}")
                    
                    # Show sentiment analysis results
                    sentiment_score = opp.context.get('sentiment_score', 0.5)
                    engagement_potential = opp.context.get('engagement_potential', 0.5)
                    print(f"   😊 Sentiment: {sentiment_score:.2f} | Engagement Potential: {engagement_potential:.2f}")
                    
                    print(f"   🎭 Suggested Approach: {opp.suggested_approach}")
                    print(f"   📝 Original Tweet: {opp.context.get('text', 'No text')[:120]}...")
                    print(f"   👤 Author: @{opp.context.get('author_id', 'unknown')}")
                    
                    # Calculate combined score
                    combined_score = opp.relevance_score * opp.urgency_score * sentiment_score * engagement_potential
                    print(f"   🔥 Combined Score: {combined_score:.3f}")
                
                # Show the best opportunity
                best_opp = max(opportunities, key=lambda x: (
                    x.relevance_score * x.urgency_score * 
                    x.context.get('sentiment_score', 0.5) * 
                    x.context.get('engagement_potential', 0.5)
                ))
                
                print(f"\n🏆 BEST OPPORTUNITY:")
                print(f"   Keyword: '{best_opp.context.get('keyword')}'")
                print(f"   Tweet: {best_opp.context.get('text', '')[:200]}...")
                print(f"   Why it's good: High relevance ({best_opp.relevance_score:.2f}) + positive sentiment")
                print(f"   Suggested action: {best_opp.suggested_approach}")
                print(f"   Tweet ID: {best_opp.context.get('tweet_id')} (for direct engagement)")
                
            else:
                print("\n📊 No high-quality opportunities found")
                print("💡 This could mean:")
                print("   - Low activity on your keywords right now")
                print("   - Negative sentiment in current discussions")
                print("   - Low engagement potential in found tweets")
                print("   - API rate limits or access issues")
            
            # Show monitoring stats
            stats = trend_monitor.get_monitoring_stats()
            print(f"\n📈 Monitoring Statistics:")
            print(f"   Keywords searched: {len(search_keywords)}")
            print(f"   Active opportunities: {stats['active_opportunities']}")
            print(f"   Total opportunities found: {stats['total_opportunities_discovered']}")
            
            # Show Claude API usage
            usage_stats = claude_client.get_usage_stats()
            print(f"\n💰 Claude API Usage:")
            print(f"   Requests made: {usage_stats['total_requests']}")
            print(f"   Tokens used: {usage_stats['total_tokens_used']}")
            print(f"   Estimated cost: ${usage_stats['estimated_cost']:.4f}")
            
            return True
    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


async def test_single_keyword_deep_dive():
    """Deep dive into a single keyword for detailed analysis."""
    print("\n🔬 SINGLE KEYWORD DEEP DIVE")
    print("=" * 60)
    
    keyword = input("Enter a keyword to search for (or press Enter for 'uniswap v4'): ").strip()
    if not keyword:
        keyword = "uniswap v4"
    
    print(f"🔍 Deep diving into keyword: '{keyword}'")
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    try:
        x_client = XAPIClient(**x_credentials)
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            trend_monitor = TrendMonitor(
                x_client=x_client,
                claude_client=claude_client,
                search_keywords=[keyword]
            )
            
            # Search for this specific keyword
            print(f"\n🔍 Searching for tweets about '{keyword}'...")
            search_results = await trend_monitor.search_tweets_by_keyword(keyword, max_results=15)
            
            if search_results:
                print(f"\n📊 Found {len(search_results)} tweets about '{keyword}'")
                
                print(f"\n📝 Analyzing each tweet with Claude...")
                
                for i, tweet in enumerate(search_results, 1):
                    print(f"\n--- Tweet {i} ---")
                    print(f"ID: {tweet['id']}")
                    print(f"Author: @{tweet['author_id']}")
                    print(f"Text: {tweet['text']}")
                    
                    # Get detailed sentiment analysis
                    try:
                        sentiment = await claude_client.analyze_sentiment(
                            text=tweet['text'],
                            context=f"Tweet found when searching for '{keyword}'"
                        )
                        
                        print(f"Sentiment Analysis:")
                        print(f"  Overall: {sentiment.overall_sentiment} (confidence: {sentiment.confidence:.2f})")
                        print(f"  Emotional tone: {sentiment.emotional_tone}")
                        print(f"  Engagement potential: {sentiment.engagement_potential:.2f}")
                        print(f"  Key themes: {', '.join(sentiment.key_themes) if sentiment.key_themes else 'None detected'}")
                        
                        # Calculate if this is a good opportunity
                        relevance = await trend_monitor.calculate_keyword_relevance(keyword, tweet)
                        urgency = await trend_monitor.calculate_keyword_urgency(tweet)
                        approach = await trend_monitor.suggest_keyword_response_approach(keyword, tweet)
                        
                        total_score = relevance * urgency * sentiment.engagement_potential
                        
                        print(f"Opportunity Score:")
                        print(f"  Relevance: {relevance:.2f}")
                        print(f"  Urgency: {urgency:.2f}")
                        print(f"  Total Score: {total_score:.3f}")
                        print(f"  Suggested approach: {approach}")
                        
                        if total_score > 0.3:
                            print(f"  🔥 GOOD OPPORTUNITY!")
                        else:
                            print(f"  😐 Marginal opportunity")
                    
                    except Exception as e:
                        print(f"  ❌ Sentiment analysis failed: {e}")
                    
                    print("-" * 40)
            
            else:
                print(f"❌ No tweets found for '{keyword}'")
                print("💡 Try:")
                print(f"   - A more common keyword")
                print(f"   - Different spelling variations")
                print(f"   - Broader terms related to your niche")
    
    except Exception as e:
        print(f"❌ Error during deep dive: {e}")


async def export_opportunities_with_sentiment():
    """Export opportunities with full sentiment data for review."""
    print("\n💾 EXPORTING OPPORTUNITIES WITH SENTIMENT DATA")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    try:
        x_client = XAPIClient(**x_credentials)
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            # Your focus keywords
            keywords = ["uniswap v4", "unichain", "defi protocol", "blockchain"]
            
            trend_monitor = TrendMonitor(
                x_client=x_client,
                claude_client=claude_client,
                search_keywords=keywords
            )
            
            print(f"🔍 Searching for opportunities across {len(keywords)} keywords...")
            await trend_monitor.search_keyword_opportunities()
            
            opportunities = trend_monitor.get_top_opportunities(limit=20)
            
            if opportunities:
                # Export detailed data
                export_data = []
                for opp in opportunities:
                    export_item = {
                        'keyword': opp.context.get('keyword'),
                        'tweet_id': opp.context.get('tweet_id'),
                        'author_id': opp.context.get('author_id'),
                        'tweet_text': opp.context.get('text'),
                        'relevance_score': opp.relevance_score,
                        'urgency_score': opp.urgency_score,
                        'sentiment_score': opp.context.get('sentiment_score', 0.5),
                        'engagement_potential': opp.context.get('engagement_potential', 0.5),
                        'suggested_approach': opp.suggested_approach,
                        'combined_score': (
                            opp.relevance_score * opp.urgency_score * 
                            opp.context.get('sentiment_score', 0.5) * 
                            opp.context.get('engagement_potential', 0.5)
                        ),
                        'discovered_at': opp.discovered_at.isoformat(),
                        'expires_at': opp.expires_at.isoformat() if opp.expires_at else None
                    }
                    export_data.append(export_item)
                
                # Sort by combined score
                export_data.sort(key=lambda x: x['combined_score'], reverse=True)
                
                # Save to file
                filename = f"keyword_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                print(f"✅ Exported {len(export_data)} opportunities to {filename}")
                
                # Show top 3
                print(f"\n🏆 TOP 3 OPPORTUNITIES:")
                for i, item in enumerate(export_data[:3], 1):
                    print(f"\n{i}. Keyword: '{item['keyword']}'")
                    print(f"   Score: {item['combined_score']:.3f}")
                    print(f"   Text: {item['tweet_text'][:100]}...")
                    print(f"   Action: {item['suggested_approach']}")
                    print(f"   Tweet ID: {item['tweet_id']}")
            
            else:
                print("❌ No opportunities found to export")
    
    except Exception as e:
        print(f"❌ Export failed: {e}")


async def main():
    """Main test menu for keyword search and sentiment analysis."""
    while True:
        print("\n" + "="*60)
        print("🎯 KEYWORD SEARCH + SENTIMENT ANALYSIS TESTING")
        print("="*60)
        print()
        print("1. 🔍 Test Proactive Keyword Search (uniswap v4, unichain, etc.)")
        print("2. 🔬 Deep Dive Single Keyword Analysis")
        print("3. 💾 Export Top Opportunities with Sentiment Data")
        print("4. 📋 Show Current Search Keywords")
        print("5. 🚪 Exit")
        print()
        
        choice = input("Choose an option (1-5): ").strip()
        
        if choice == "1":
            await test_keyword_search_with_sentiment()
        elif choice == "2":
            await test_single_keyword_deep_dive()
        elif choice == "3":
            await export_opportunities_with_sentiment()
        elif choice == "4":
            keywords = ["uniswap v4", "unichain", "defi", "blockchain development", "smart contracts"]
            print(f"\n🎯 Current Search Keywords:")
            for i, keyword in enumerate(keywords, 1):
                print(f"   {i}. '{keyword}'")
            print("\n💡 These are perfect for finding conversations to join!")
            print("💡 Customize them in the script for your specific interests")
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