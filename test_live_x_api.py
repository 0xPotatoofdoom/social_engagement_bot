#!/usr/bin/env python3
"""
Live X API Testing Script

This script tests our X API client implementation with REAL X API credentials.
We'll start with read-only operations and gradually test more functionality.

SAFETY FEATURES:
- Comprehensive logging of all API calls
- Rate limit respect
- Error handling and recovery
- Gradual testing (read-only first)
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add src to path so we can import our implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Configure logging to capture everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('live_api_test.log')
    ]
)

# Import our implementation
try:
    from bot.api.x_client import XAPIClient, RateLimitManager, APIMetrics
    print("✅ Successfully imported X API client components")
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


async def test_authentication_and_health(client):
    """Test authentication and basic health check with live API."""
    print("\n🔐 Testing Authentication & Health Check...")
    
    try:
        health = await client.health_check()
        
        if health['overall_health']:
            print("✅ Authentication successful!")
            auth_info = health['checks']['authentication']
            print(f"   User ID: {auth_info.get('user_id')}")
            print(f"   Username: {auth_info.get('username')}")
            print(f"   Response Time: {auth_info.get('response_time', 0):.3f}s")
        else:
            print("❌ Authentication failed!")
            print(f"   Error: {health['checks']['authentication'].get('error')}")
        
        return health['overall_health']
        
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_rate_limiting_status(client):
    """Check current rate limit status."""
    print("\n⏱️ Checking Rate Limit Status...")
    
    try:
        status = client.rate_limiter.get_status()
        
        for endpoint, data in status.items():
            print(f"   {endpoint}:")
            print(f"     Used: {data['used']}/{data['limit']}")
            print(f"     Remaining: {data['remaining']}")
            print(f"     Reset: {data['reset_time'] or 'Not set'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit check error: {e}")
        return False


async def test_mentions_fetching(client):
    """Test fetching mentions (read-only operation)."""
    print("\n📥 Testing Mentions Fetching...")
    
    try:
        mentions = await client.get_mentions()
        
        print(f"✅ Fetched {len(mentions)} mentions")
        
        if mentions:
            print("   Recent mentions:")
            for i, mention in enumerate(mentions[:3]):  # Show first 3
                print(f"     {i+1}. @{mention.get('author_id', 'unknown')}: {mention.get('text', '')[:100]}...")
        else:
            print("   No recent mentions found")
        
        return True
        
    except Exception as e:
        print(f"❌ Mentions fetch error: {e}")
        return False


async def test_api_metrics(client):
    """Check API usage metrics."""
    print("\n📊 Checking API Metrics...")
    
    try:
        stats = client.metrics.get_stats()
        
        if stats:
            print("✅ API metrics collected:")
            for endpoint, metrics in stats.items():
                print(f"   {endpoint}:")
                print(f"     Requests: {metrics['total_requests']}")
                print(f"     Error Rate: {metrics['error_rate']:.2%}")
                print(f"     Avg Response Time: {metrics['avg_response_time']:.3f}s")
                print(f"     Rate Limit Hits: {metrics['rate_limit_hits']}")
        else:
            print("   No API metrics yet (expected for first run)")
        
        return True
        
    except Exception as e:
        print(f"❌ Metrics error: {e}")
        return False


async def test_content_validation(client):
    """Test content validation without posting."""
    print("\n✅ Testing Content Validation...")
    
    test_cases = [
        ("Valid tweet", "This is a test tweet for validation #testing"),
        ("Too long", "x" * 281),
        ("Empty", ""),
        ("Just whitespace", "   \n\t   "),
        ("With media", "Tweet with media", ["fake_media_id"]),
    ]
    
    for test_name, content, *media in test_cases:
        print(f"   Testing: {test_name}")
        
        # We'll test validation logic without actually posting
        try:
            if len(content) > 280:
                print(f"     ❌ Content too long ({len(content)} chars)")
            elif not content.strip():
                print(f"     ❌ Content empty or whitespace")
            else:
                print(f"     ✅ Content valid ({len(content)} chars)")
                
        except Exception as e:
            print(f"     ❌ Validation error: {e}")


async def test_safe_posting(client):
    """Test posting with a safe test tweet (if user confirms)."""
    print("\n📝 Testing Safe Tweet Posting...")
    
    # Ask for confirmation before posting
    print("⚠️  This will post a real tweet to your X account!")
    confirm = input("Type 'YES' to proceed with posting a test tweet: ")
    
    if confirm != 'YES':
        print("   Skipping tweet posting (user declined)")
        return False
    
    test_tweet = f"🤖 Testing X API client - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} #APITest"
    
    try:
        print(f"   Posting: '{test_tweet}'")
        result = await client.post_tweet(test_tweet)
        
        if result['success']:
            print(f"✅ Tweet posted successfully!")
            print(f"   Tweet ID: {result['tweet_id']}")
            print(f"   Final text: {result['text']}")
            return True
        else:
            print(f"❌ Tweet posting failed: {result.get('error')}")
            print(f"   Message: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Tweet posting error: {e}")
        return False


async def test_error_handling(client):
    """Test error handling with various scenarios."""
    print("\n🚨 Testing Error Handling...")
    
    # Test character limit (should not post)
    print("   Testing character limit validation...")
    long_tweet = "x" * 281
    result = await client.post_tweet(long_tweet)
    
    if not result['success'] and result['error'] == 'character_limit_exceeded':
        print("   ✅ Character limit validation working")
    else:
        print("   ❌ Character limit validation failed")
    
    # Test empty content (should not post)
    print("   Testing empty content validation...")
    result = await client.post_tweet("")
    
    if not result['success'] and result['error'] == 'empty_content':
        print("   ✅ Empty content validation working")
    else:
        print("   ❌ Empty content validation failed")


async def comprehensive_live_test():
    """Run comprehensive live API testing."""
    print("🚀 Live X API Testing Started")
    print("=" * 60)
    
    # Get credentials
    credentials = get_credentials()
    if not credentials:
        return False
    
    # Initialize client
    try:
        client = XAPIClient(**credentials)
        print("✅ X API client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Run test suite
    test_results = {}
    
    # 1. Test authentication (critical first step)
    test_results['auth'] = await test_authentication_and_health(client)
    if not test_results['auth']:
        print("❌ Authentication failed - stopping tests")
        return False
    
    # 2. Check rate limits
    test_results['rate_limits'] = await test_rate_limiting_status(client)
    
    # 3. Test read-only operations
    test_results['mentions'] = await test_mentions_fetching(client)
    
    # 4. Check metrics
    test_results['metrics'] = await test_api_metrics(client)
    
    # 5. Test validation (no API calls)
    await test_content_validation(client)
    
    # 6. Test error handling
    await test_error_handling(client)
    
    # 7. Optional: Test actual posting
    test_results['posting'] = await test_safe_posting(client)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Live API Test Results Summary")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All live API tests passed!")
    else:
        print("⚠️  Some tests failed - check logs for details")
    
    print(f"\n📋 Detailed logs saved to: live_api_test.log")
    
    return passed == total


async def main():
    """Main test execution."""
    try:
        success = await comprehensive_live_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())