#!/usr/bin/env python3
"""
Manual Testing Guide - What You Can Test Right Now

Run this script to interactively test current X API functionality.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
load_dotenv()

from bot.api.x_client import XAPIClient

async def interactive_test_menu():
    """Interactive menu for testing current functionality."""
    
    # Initialize client
    credentials = {
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET'),
        'bearer_token': os.getenv('X_BEARER_TOKEN')
    }
    
    client = XAPIClient(**credentials)
    
    while True:
        print("\n" + "="*60)
        print("🤖 X API CLIENT - MANUAL TESTING MENU")
        print("="*60)
        print()
        print("Current Working Features:")
        print("1. 🔐 Test Authentication & Health Check")
        print("2. 📥 Fetch Your Recent Mentions")
        print("3. ⏱️  Check Rate Limit Status")
        print("4. 📊 View API Performance Metrics")
        print("5. ✅ Test Content Validation")
        print("6. 📝 Test Tweet Posting (REAL POSTS!)")
        print("7. 🧵 Test Thread Creation (REAL POSTS!)")
        print("8. 🔄 Test Retry Logic")
        print("9. 🚪 Exit")
        print()
        
        choice = input("Choose an option (1-9): ").strip()
        
        if choice == "1":
            await test_authentication(client)
        elif choice == "2":
            await test_mentions(client)
        elif choice == "3":
            await test_rate_limits(client)
        elif choice == "4":
            await test_metrics(client)
        elif choice == "5":
            await test_validation(client)
        elif choice == "6":
            await test_posting(client)
        elif choice == "7":
            await test_threads(client)
        elif choice == "8":
            await test_retry(client)
        elif choice == "9":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

async def test_authentication(client):
    """Test authentication and get user info."""
    print("\n🔐 Testing Authentication...")
    
    health = await client.health_check()
    
    if health['overall_health']:
        auth = health['checks']['authentication']
        print(f"✅ Authentication successful!")
        print(f"   👤 Username: @{auth['username']}")
        print(f"   🆔 User ID: {auth['user_id']}")
        print(f"   ⚡ Response Time: {auth['response_time']:.3f}s")
    else:
        print(f"❌ Authentication failed!")
        print(f"   Error: {health['checks']['authentication'].get('error')}")

async def test_mentions(client):
    """Fetch and display recent mentions."""
    print("\n📥 Fetching Recent Mentions...")
    
    mentions = await client.get_mentions()
    
    if mentions:
        print(f"✅ Found {len(mentions)} recent mentions:")
        print()
        for i, mention in enumerate(mentions[:5], 1):  # Show first 5
            print(f"{i}. From: @{mention.get('author_id', 'unknown')}")
            print(f"   Text: {mention.get('text', 'No text')[:100]}...")
            print(f"   ID: {mention.get('id', 'unknown')}")
            print()
    else:
        print("📭 No recent mentions found.")

async def test_rate_limits(client):
    """Check current rate limit status."""
    print("\n⏱️ Checking Rate Limit Status...")
    
    status = client.rate_limiter.get_status()
    
    for endpoint, data in status.items():
        remaining = data['remaining']
        total = data['limit']
        used = data['used']
        
        print(f"📡 {endpoint}:")
        print(f"   Used: {used}/{total}")
        print(f"   Remaining: {remaining}")
        if data['reset_time']:
            print(f"   Resets: {data['reset_time']}")
        print()

async def test_metrics(client):
    """Display API performance metrics."""
    print("\n📊 API Performance Metrics...")
    
    stats = client.metrics.get_stats()
    
    if stats:
        for endpoint, metrics in stats.items():
            print(f"📈 {endpoint}:")
            print(f"   Total Requests: {metrics['total_requests']}")
            print(f"   Error Rate: {metrics['error_rate']:.2%}")
            print(f"   Avg Response Time: {metrics['avg_response_time']:.3f}s")
            print(f"   Rate Limit Hits: {metrics['rate_limit_hits']}")
            print()
    else:
        print("📊 No metrics data yet. Make some API calls first!")

async def test_validation(client):
    """Test content validation without posting."""
    print("\n✅ Testing Content Validation...")
    
    test_cases = [
        ("Short tweet", "Hello world! 👋"),
        ("Long tweet", "x" * 281),
        ("Empty tweet", ""),
        ("Just spaces", "   "),
        ("Perfect length", "x" * 280),
    ]
    
    for name, content in test_cases:
        print(f"\n🧪 Testing: {name}")
        print(f"   Content: '{content[:50]}{'...' if len(content) > 50 else ''}'")
        print(f"   Length: {len(content)} chars")
        
        # Test without actually posting
        if len(content) > 280:
            print("   ❌ Too long (>280 chars)")
        elif not content.strip():
            print("   ❌ Empty or whitespace only")
        else:
            print("   ✅ Valid content")

async def test_posting(client):
    """Test actual tweet posting with confirmation."""
    print("\n📝 Testing Tweet Posting...")
    print("⚠️  WARNING: This will post a REAL tweet to your X account!")
    
    confirm = input("Type 'YES' to proceed with posting: ").strip()
    
    if confirm != 'YES':
        print("🚫 Tweet posting cancelled.")
        return
    
    # Get custom tweet or use default
    custom = input("Enter tweet text (or press Enter for default): ").strip()
    
    if custom:
        tweet_text = custom
    else:
        tweet_text = f"🤖 Testing X API integration - {datetime.now().strftime('%H:%M:%S')} #APITest"
    
    print(f"\n📤 Posting tweet: '{tweet_text}'")
    
    result = await client.post_tweet(tweet_text)
    
    if result['success']:
        print("✅ Tweet posted successfully!")
        print(f"   🆔 Tweet ID: {result['tweet_id']}")
        print(f"   📝 Final text: {result['text']}")
    else:
        print("❌ Tweet posting failed!")
        print(f"   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")

async def test_threads(client):
    """Test thread creation with confirmation."""
    print("\n🧵 Testing Thread Creation...")
    print("⚠️  WARNING: This will post a REAL thread to your X account!")
    
    confirm = input("Type 'YES' to proceed with thread posting: ").strip()
    
    if confirm != 'YES':
        print("🚫 Thread posting cancelled.")
        return
    
    # Default thread
    thread_tweets = [
        f"🧵 Testing thread creation 1/3 - {datetime.now().strftime('%H:%M:%S')}",
        "This is the second tweet in the thread. Testing continuation...",
        "And this is the third and final tweet! 🎉 #ThreadTest"
    ]
    
    print(f"\n📤 Posting {len(thread_tweets)} tweet thread...")
    
    result = await client.create_thread(thread_tweets)
    
    if result['success']:
        print("✅ Thread posted successfully!")
        print(f"   🆔 Thread IDs: {result['thread_ids']}")
    else:
        print("❌ Thread posting failed!")
        if result.get('partial_success'):
            print(f"   ⚠️  Partial success: {len(result['thread_ids'])} tweets posted")

async def test_retry(client):
    """Test retry logic with intentionally problematic content."""
    print("\n🔄 Testing Retry Logic...")
    
    print("Testing with content that will fail validation...")
    
    # This should fail quickly (no retries needed)
    result = await client.post_tweet_with_retry("x" * 281, max_retries=3)
    
    print(f"Result: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Error: {result.get('error', 'None')}")
    print(f"Message: {result.get('message', 'None')}")

if __name__ == "__main__":
    asyncio.run(interactive_test_menu())