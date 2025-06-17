#!/usr/bin/env python3
"""
Test script for X API client implementation.

This script will:
1. Run our failing tests to see which ones now pass
2. Test basic functionality with mock data
3. Generate logs to understand real behavior
4. Identify gaps between tests and implementation
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path so we can import our implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging to see our structured logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import our implementation
try:
    from bot.api.x_client import XAPIClient, RateLimitManager, APIMetrics
    print("✅ Successfully imported X API client components")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic functionality with mocked API calls."""
    print("\n🧪 Testing basic functionality...")
    
    # Test credentials validation
    print("Testing credential validation...")
    try:
        XAPIClient()  # Should fail
        print("❌ Should have failed without credentials")
    except TypeError:
        print("✅ Correctly requires credentials")
    
    try:
        XAPIClient("", "secret", "token", "token_secret", "bearer")
        print("❌ Should have failed with empty credentials")
    except ValueError:
        print("✅ Correctly validates credential format")
    
    # Test with valid credentials
    print("Testing with valid credentials...")
    credentials = {
        "api_key": "test_key_123",
        "api_secret": "test_secret_456", 
        "access_token": "test_token_789",
        "access_token_secret": "test_token_secret_abc",
        "bearer_token": "test_bearer_def"
    }
    
    # Mock tweepy to avoid real API calls
    with patch('bot.api.x_client.tweepy.Client'):
        client = XAPIClient(**credentials)
        print("✅ Successfully initialized X API client")
        
        # Test rate limiter
        rate_limiter = client.rate_limiter
        can_post = await rate_limiter.check_rate_limit('create_tweet')
        print(f"✅ Rate limiter check: {can_post}")
        
        # Test metrics
        metrics = client.metrics
        stats = metrics.get_stats()
        print(f"✅ Metrics initialized: {len(stats)} endpoints tracked")


async def test_tweet_posting():
    """Test tweet posting with mocked API."""
    print("\n📝 Testing tweet posting...")
    
    credentials = {
        "api_key": "test_key",
        "api_secret": "test_secret",
        "access_token": "test_token", 
        "access_token_secret": "test_token_secret",
        "bearer_token": "test_bearer"
    }
    
    # Mock tweepy Client
    with patch('bot.api.x_client.tweepy.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful tweet response
        mock_response = MagicMock()
        mock_response.data = {'id': '1234567890', 'text': 'Test tweet content'}
        mock_client.create_tweet.return_value = mock_response
        
        client = XAPIClient(**credentials)
        
        # Test successful tweet posting
        result = await client.post_tweet("Test tweet content #testing")
        print(f"✅ Tweet posting result: {result}")
        
        # Test character limit validation
        long_tweet = "x" * 281
        result = await client.post_tweet(long_tweet)
        print(f"✅ Character limit validation: {result['error']}")
        
        # Test empty tweet
        result = await client.post_tweet("")
        print(f"✅ Empty tweet handling: {result['error']}")


async def test_rate_limiting():
    """Test rate limiting logic."""
    print("\n⏱️ Testing rate limiting...")
    
    rate_limiter = RateLimitManager()
    
    # Test normal operation
    for i in range(5):
        can_post = await rate_limiter.check_rate_limit('create_tweet')
        if can_post:
            await rate_limiter.record_request('create_tweet')
        print(f"Request {i+1}: Can post = {can_post}")
    
    # Check status
    status = rate_limiter.get_status()
    print(f"✅ Rate limit status: {status['create_tweet']}")


async def test_error_handling():
    """Test error handling scenarios."""
    print("\n🚨 Testing error handling...")
    
    credentials = {
        "api_key": "test_key",
        "api_secret": "test_secret",
        "access_token": "test_token",
        "access_token_secret": "test_token_secret", 
        "bearer_token": "test_bearer"
    }
    
    with patch('bot.api.x_client.tweepy.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Test rate limit error
        mock_client.create_tweet.side_effect = Exception("Rate limit exceeded")
        
        client = XAPIClient(**credentials)
        
        # This should handle the exception gracefully
        result = await client.post_tweet("Test tweet")
        print(f"✅ Error handling: {result}")


async def test_health_check():
    """Test health check functionality."""
    print("\n🏥 Testing health check...")
    
    credentials = {
        "api_key": "test_key",
        "api_secret": "test_secret",
        "access_token": "test_token",
        "access_token_secret": "test_token_secret",
        "bearer_token": "test_bearer"
    }
    
    with patch('bot.api.x_client.tweepy.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock get_me response
        mock_me = MagicMock()
        mock_me.data.id = "user123"
        mock_me.data.username = "testuser"
        mock_client.get_me.return_value = mock_me
        
        client = XAPIClient(**credentials)
        
        health = await client.health_check()
        print(f"✅ Health check: {health['overall_health']}")
        print(f"   User: {health['checks']['authentication']['username']}")


async def run_actual_tests():
    """Run some of our actual unit tests to see what passes."""
    print("\n🎯 Running actual unit tests...")
    
    # Import test modules to see what we can run
    sys.path.insert(0, 'tests')
    
    try:
        # Try importing our test file
        import pytest
        
        # Run specific tests
        exit_code = pytest.main([
            'tests/unit/test_x_api_client.py::TestXAPIClientInitialization::test_x_api_client_initializes_with_valid_credentials',
            '-v',
            '--tb=short'
        ])
        
        if exit_code == 0:
            print("✅ Some tests are passing!")
        else:
            print("❌ Tests still failing - need more implementation")
            
    except ImportError:
        print("⚠️ pytest not available or tests not importable")


def analyze_implementation_gaps():
    """Analyze what we've implemented vs what tests expect."""
    print("\n📊 Analyzing implementation gaps...")
    
    implemented_features = [
        "✅ XAPIClient initialization with credentials",
        "✅ Credential validation", 
        "✅ Rate limiting manager",
        "✅ API metrics tracking",
        "✅ Basic tweet posting",
        "✅ Character limit validation",
        "✅ Error handling with logging",
        "✅ Health check functionality",
        "✅ Retry logic with exponential backoff"
    ]
    
    missing_features = [
        "❌ Thread creation with reply_to functionality",
        "❌ Trending topics fetching", 
        "❌ Advanced mention processing",
        "❌ Real API integration testing",
        "❌ Comprehensive error type handling",
        "❌ Performance optimization",
        "❌ Integration with content pipeline"
    ]
    
    print("Implemented features:")
    for feature in implemented_features:
        print(f"  {feature}")
    
    print("\nMissing features:")
    for feature in missing_features:
        print(f"  {feature}")
    
    print(f"\nImplementation progress: {len(implemented_features)}/{len(implemented_features) + len(missing_features)} features")


async def main():
    """Run all tests and analysis."""
    print("🚀 X API Client Implementation Test")
    print("=" * 50)
    
    await test_basic_functionality()
    await test_tweet_posting()
    await test_rate_limiting()
    await test_error_handling()
    await test_health_check()
    
    # Try running actual tests
    await run_actual_tests()
    
    # Analyze what we have vs what we need
    analyze_implementation_gaps()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Run pytest tests/unit/test_x_api_client.py to see current status")
    print("2. Add missing features based on failing tests")
    print("3. Test with real API credentials (carefully)")
    print("4. Collect and analyze logs for optimization")
    print("5. Refine tests based on real API behavior")


if __name__ == "__main__":
    asyncio.run(main())