"""
TDD Tests for X API Client

These tests define the expected behavior of our X API client before implementation.
All tests should FAIL initially until we implement the actual XAPIClient class.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import tweepy

# Import will fail initially - this is expected in TDD
try:
    from src.bot.api.x_client import XAPIClient, RateLimitManager, APIMetrics
except ImportError:
    # Expected to fail initially in TDD
    pass


class TestXAPIClientInitialization:
    """Test X API client initialization and configuration."""
    
    @pytest.mark.unit
    def test_x_api_client_requires_all_credentials(self):
        """X API client should require all necessary credentials."""
        # This test will fail until we implement XAPIClient
        with pytest.raises(TypeError):
            XAPIClient()  # Should fail without credentials
    
    @pytest.mark.unit
    def test_x_api_client_initializes_with_valid_credentials(self):
        """X API client should initialize successfully with valid credentials."""
        credentials = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret",
            "bearer_token": "test_bearer"
        }
        
        # This will fail until we implement XAPIClient
        client = XAPIClient(**credentials)
        assert client is not None
        assert hasattr(client, 'client')
        assert hasattr(client, 'read_client')
    
    @pytest.mark.unit
    def test_x_api_client_validates_credentials_format(self):
        """X API client should validate credential formats."""
        invalid_credentials = {
            "api_key": "",  # Empty string should be invalid
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret",
            "bearer_token": "test_bearer"
        }
        
        # Should raise ValueError for invalid credentials
        with pytest.raises(ValueError):
            XAPIClient(**invalid_credentials)


class TestXAPIClientTweetOperations:
    """Test tweet posting and management operations."""
    
    @pytest.fixture
    def x_client(self):
        """Create X API client for testing."""
        credentials = {
            "api_key": "test_key",
            "api_secret": "test_secret", 
            "access_token": "test_token",
            "access_token_secret": "test_token_secret",
            "bearer_token": "test_bearer"
        }
        return XAPIClient(**credentials)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_tweet_success(self, x_client):
        """Should successfully post a tweet and return tweet data."""
        tweet_text = "This is a test tweet about web3 #blockchain"
        
        with patch.object(x_client.client, 'create_tweet') as mock_create:
            mock_create.return_value = MagicMock(
                data={'id': '1234567890', 'text': tweet_text}
            )
            
            result = await x_client.post_tweet(tweet_text)
            
            assert result['success'] is True
            assert result['tweet_id'] == '1234567890'
            assert result['text'] == tweet_text
            mock_create.assert_called_once_with(text=tweet_text, media_ids=None)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_tweet_with_media(self, x_client):
        """Should successfully post tweet with media attachments."""
        tweet_text = "Check out this image!"
        media_ids = ["media_123", "media_456"]
        
        with patch.object(x_client.client, 'create_tweet') as mock_create:
            mock_create.return_value = MagicMock(
                data={'id': '1234567890', 'text': tweet_text}
            )
            
            result = await x_client.post_tweet(tweet_text, media_ids=media_ids)
            
            assert result['success'] is True
            mock_create.assert_called_once_with(text=tweet_text, media_ids=media_ids)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_tweet_rate_limit_handling(self, x_client):
        """Should handle rate limiting gracefully."""
        tweet_text = "This will hit rate limit"
        
        with patch.object(x_client.client, 'create_tweet') as mock_create:
            mock_create.side_effect = tweepy.TooManyRequests(response=MagicMock())
            
            result = await x_client.post_tweet(tweet_text)
            
            assert result['success'] is False
            assert result['error'] == 'rate_limit'
            assert 'retry_after' in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_tweet_forbidden_content(self, x_client):
        """Should handle forbidden content (spam, duplicate, etc.)."""
        tweet_text = "This is duplicate content"
        
        with patch.object(x_client.client, 'create_tweet') as mock_create:
            mock_create.side_effect = tweepy.Forbidden(response=MagicMock())
            
            result = await x_client.post_tweet(tweet_text)
            
            assert result['success'] is False
            assert result['error'] == 'forbidden'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_tweet_validates_character_limit(self, x_client):
        """Should validate tweet character limit before posting."""
        # Tweet longer than 280 characters
        long_tweet = "x" * 281
        
        result = await x_client.post_tweet(long_tweet)
        
        assert result['success'] is False
        assert result['error'] == 'character_limit_exceeded'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_thread_success(self, x_client):
        """Should successfully create a tweet thread."""
        tweets = [
            "First tweet in thread about blockchain technology",
            "Second tweet continuing the discussion about DeFi",
            "Final tweet with conclusions and call to action"
        ]
        
        with patch.object(x_client, 'post_tweet') as mock_post:
            # Mock successful posts with different IDs
            mock_post.side_effect = [
                {'success': True, 'tweet_id': '123'},
                {'success': True, 'tweet_id': '124'}, 
                {'success': True, 'tweet_id': '125'}
            ]
            
            result = await x_client.create_thread(tweets)
            
            assert result['success'] is True
            assert len(result['thread_ids']) == 3
            assert result['thread_ids'] == ['123', '124', '125']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_thread_partial_failure(self, x_client):
        """Should handle partial thread creation failures."""
        tweets = ["First tweet", "Second tweet", "Third tweet"]
        
        with patch.object(x_client, 'post_tweet') as mock_post:
            # First two succeed, third fails
            mock_post.side_effect = [
                {'success': True, 'tweet_id': '123'},
                {'success': True, 'tweet_id': '124'},
                {'success': False, 'error': 'rate_limit'}
            ]
            
            result = await x_client.create_thread(tweets)
            
            assert result['success'] is False
            assert len(result['thread_ids']) == 2  # Only partial thread created


class TestXAPIClientMonitoring:
    """Test monitoring and engagement detection."""
    
    @pytest.fixture
    def x_client(self):
        """Create X API client for testing."""
        credentials = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token", 
            "access_token_secret": "test_token_secret",
            "bearer_token": "test_bearer"
        }
        return XAPIClient(**credentials)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_mentions_success(self, x_client, sample_tweet_data):
        """Should successfully retrieve mentions."""
        with patch.object(x_client.client, 'get_mentions') as mock_mentions:
            mock_mentions.return_value = MagicMock(
                data=[MagicMock(**sample_tweet_data)]
            )
            
            mentions = await x_client.get_mentions()
            
            assert isinstance(mentions, list)
            assert len(mentions) == 1
            assert mentions[0]['id'] == sample_tweet_data['id']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_mentions_with_since_id(self, x_client):
        """Should retrieve mentions since specific tweet ID."""
        since_id = "1234567889"
        
        with patch.object(x_client.client, 'get_mentions') as mock_mentions:
            mock_mentions.return_value = MagicMock(data=[])
            
            await x_client.get_mentions(since_id=since_id)
            
            mock_mentions.assert_called_once_with(
                since_id=since_id,
                expansions=['author_id', 'in_reply_to_user_id'],
                tweet_fields=['created_at', 'context_annotations', 'public_metrics']
            )
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_trending_topics_success(self, x_client):
        """Should successfully retrieve trending topics."""
        mock_trends = [
            {'name': '#blockchain', 'tweet_volume': 15000},
            {'name': '#AI', 'tweet_volume': 25000}
        ]
        
        with patch('tweepy.API') as mock_api:
            mock_api.return_value.get_place_trends.return_value = [
                {'trends': [
                    {'name': '#blockchain', 'tweet_volume': 15000},
                    {'name': '#AI', 'tweet_volume': 25000}
                ]}
            ]
            
            trends = await x_client.get_trending_topics()
            
            assert isinstance(trends, list)
            assert len(trends) == 2
            assert trends[0]['name'] == '#blockchain'
            assert trends[0]['volume'] == 15000
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reply_to_tweet_success(self, x_client):
        """Should successfully reply to a tweet."""
        tweet_id = "1234567890"
        reply_text = "Thanks for sharing this insight!"
        
        with patch.object(x_client, 'post_tweet') as mock_post:
            mock_post.return_value = {
                'success': True,
                'tweet_id': 'reply123'
            }
            
            result = await x_client.reply_to_tweet(tweet_id, reply_text)
            
            assert result['success'] is True
            assert result['tweet_id'] == 'reply123'


class TestRateLimitManager:
    """Test rate limiting functionality."""
    
    @pytest.mark.unit
    def test_rate_limit_manager_initialization(self):
        """Rate limit manager should initialize with default endpoints."""
        manager = RateLimitManager()
        
        assert 'create_tweet' in manager.endpoints
        assert 'get_mentions' in manager.endpoints
        assert manager.endpoints['create_tweet']['limit'] == 300
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_request(self):
        """Should allow request when under rate limit."""
        manager = RateLimitManager()
        
        can_request = await manager.check_rate_limit('create_tweet')
        
        assert can_request is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_when_exceeded(self):
        """Should block request when rate limit exceeded."""
        manager = RateLimitManager()
        
        # Simulate hitting rate limit
        manager.endpoints['create_tweet']['used'] = 300
        
        can_request = await manager.check_rate_limit('create_tweet')
        
        assert can_request is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_record_request_increments_counter(self):
        """Should increment request counter when recording request."""
        manager = RateLimitManager()
        initial_count = manager.endpoints['create_tweet']['used']
        
        await manager.record_request('create_tweet')
        
        assert manager.endpoints['create_tweet']['used'] == initial_count + 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(self):
        """Should reset rate limit counter after time window."""
        manager = RateLimitManager()
        
        # Simulate rate limit hit in the past
        past_time = datetime.now() - timedelta(seconds=1000)
        manager.endpoints['create_tweet']['used'] = 300
        manager.endpoints['create_tweet']['reset_time'] = past_time
        
        can_request = await manager.check_rate_limit('create_tweet')
        
        assert can_request is True
        assert manager.endpoints['create_tweet']['used'] == 0


class TestAPIMetrics:
    """Test API metrics tracking."""
    
    @pytest.mark.unit
    def test_api_metrics_initialization(self):
        """API metrics should initialize with empty metrics."""
        metrics = APIMetrics()
        
        assert isinstance(metrics.metrics, dict)
        assert len(metrics.metrics) == 0
    
    @pytest.mark.unit
    def test_record_request_success(self):
        """Should record successful API request metrics."""
        metrics = APIMetrics()
        
        metrics.record_request('create_tweet', 0.5, True)
        
        endpoint_metrics = metrics.metrics['create_tweet']
        assert endpoint_metrics['requests'] == 1
        assert endpoint_metrics['errors'] == 0
        assert len(endpoint_metrics['response_times']) == 1
        assert endpoint_metrics['response_times'][0] == 0.5
    
    @pytest.mark.unit
    def test_record_request_failure(self):
        """Should record failed API request metrics."""
        metrics = APIMetrics()
        
        metrics.record_request('create_tweet', 1.0, False, 'rate_limit')
        
        endpoint_metrics = metrics.metrics['create_tweet']
        assert endpoint_metrics['requests'] == 1
        assert endpoint_metrics['errors'] == 1
        assert endpoint_metrics['rate_limits'] == 1
    
    @pytest.mark.unit
    def test_get_stats_calculates_correctly(self):
        """Should calculate API statistics correctly."""
        metrics = APIMetrics()
        
        # Record multiple requests
        metrics.record_request('create_tweet', 0.5, True)
        metrics.record_request('create_tweet', 1.0, False, 'rate_limit')
        metrics.record_request('create_tweet', 0.3, True)
        
        stats = metrics.get_stats()
        
        assert 'create_tweet' in stats
        endpoint_stats = stats['create_tweet']
        assert endpoint_stats['total_requests'] == 3
        assert endpoint_stats['error_rate'] == 1/3
        assert endpoint_stats['avg_response_time'] == (0.5 + 1.0 + 0.3) / 3
        assert endpoint_stats['rate_limit_hits'] == 1


class TestXAPIClientIntegration:
    """Integration tests for X API client functionality."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_all_services(self):
        """Should perform comprehensive health check of all API services."""
        credentials = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret", 
            "bearer_token": "test_bearer"
        }
        client = XAPIClient(**credentials)
        
        with patch.object(client.client, 'get_me') as mock_get_me:
            mock_get_me.return_value = MagicMock(data=MagicMock(id='user123'))
            
            health_status = await client.health_check()
            
            assert 'x_api' in health_status['checks']
            assert health_status['checks']['x_api']['status'] == 'healthy'
            assert 'timestamp' in health_status
    
    @pytest.mark.integration  
    @pytest.mark.asyncio
    async def test_full_posting_workflow(self, sample_tweet_data):
        """Should handle complete tweet posting workflow with monitoring."""
        credentials = {
            "api_key": "test_key", 
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret",
            "bearer_token": "test_bearer"
        }
        client = XAPIClient(**credentials)
        
        tweet_text = "Integration test tweet about blockchain #web3"
        
        with patch.object(client.client, 'create_tweet') as mock_create:
            mock_create.return_value = MagicMock(
                data={'id': '1234567890', 'text': tweet_text}
            )
            
            # Post tweet
            result = await client.post_tweet(tweet_text)
            
            # Verify successful posting
            assert result['success'] is True
            assert result['tweet_id'] == '1234567890'
            
            # Verify rate limiting was checked
            assert hasattr(client, 'rate_limiter')
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_error_recovery_and_retry_logic(self):
        """Should handle errors gracefully and implement retry logic."""
        credentials = {
            "api_key": "test_key",
            "api_secret": "test_secret", 
            "access_token": "test_token",
            "access_token_secret": "test_token_secret",
            "bearer_token": "test_bearer"
        }
        client = XAPIClient(**credentials)
        
        # This test will verify that our client can recover from various error conditions
        # Implementation will be driven by this test requirement
        with patch.object(client.client, 'create_tweet') as mock_create:
            # Simulate transient error followed by success
            mock_create.side_effect = [
                tweepy.TooManyRequests(response=MagicMock()),
                MagicMock(data={'id': '1234567890', 'text': 'test'})
            ]
            
            result = await client.post_tweet_with_retry("Test tweet")
            
            # Should succeed after retry
            assert result['success'] is True
            assert mock_create.call_count == 2