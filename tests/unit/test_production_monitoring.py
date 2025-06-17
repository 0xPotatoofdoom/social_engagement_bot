"""
Tests for Production X Engagement Bot Monitoring System

Comprehensive tests for the live 24/7 monitoring system including:
- Monitoring cycle execution
- Opportunity detection and processing  
- Email alert system
- Rate limiting and metrics tracking
- Content generation and voice alignment
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

from src.bot.scheduling.cron_monitor import CronMonitorSystem, AlertConfiguration, AlertOpportunity
from x_engagement_service import XEngagementService, RateLimitManager, MetricsTracker


class TestAlertOpportunity:
    """Test AlertOpportunity data structure."""
    
    @pytest.mark.unit
    def test_alert_opportunity_creation(self):
        """Test AlertOpportunity can be created with required fields."""
        opportunity = AlertOpportunity(
            account_username="testuser",
            account_tier=1,
            content_text="Test AI x blockchain content",
            content_url="https://twitter.com/test/status/123",
            timestamp=datetime.now().isoformat(),
            overall_score=0.85,
            ai_blockchain_relevance=0.9,
            technical_depth=0.8,
            opportunity_type="technical_discussion",
            suggested_response_type="technical_insight",
            time_sensitivity="immediate",
            strategic_context="High-value AI x blockchain opportunity",
            suggested_response="Technical response approach"
        )
        
        assert opportunity.account_username == "testuser"
        assert opportunity.overall_score == 0.85
        assert opportunity.ai_blockchain_relevance == 0.9
        assert opportunity.opportunity_type == "technical_discussion"
    
    @pytest.mark.unit
    def test_alert_opportunity_to_dict(self):
        """Test AlertOpportunity can be converted to dictionary."""
        opportunity = AlertOpportunity(
            account_username="testuser",
            account_tier=2,
            content_text="Test content",
            content_url="https://twitter.com/test/status/456",
            timestamp=datetime.now().isoformat(),
            overall_score=0.75,
            ai_blockchain_relevance=0.8,
            technical_depth=0.7,
            opportunity_type="collaboration",
            suggested_response_type="question",
            time_sensitivity="moderate",
            strategic_context="Medium priority opportunity",
            suggested_response="Engage with question"
        )
        
        data = opportunity.to_dict()
        assert isinstance(data, dict)
        assert data['account_username'] == "testuser"
        assert data['overall_score'] == 0.75


class TestRateLimitManager:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def rate_manager(self):
        """Create RateLimitManager instance."""
        return RateLimitManager()
    
    @pytest.mark.unit
    def test_rate_limit_manager_initialization(self, rate_manager):
        """Test RateLimitManager initializes with correct defaults."""
        assert 'search_tweets' in rate_manager.rate_limits
        assert 'user_timeline' in rate_manager.rate_limits
        assert 'user_lookup' in rate_manager.rate_limits
        
        # Check default limits
        assert rate_manager.rate_limits['search_tweets']['limit'] == 300
        assert rate_manager.rate_limits['user_timeline']['limit'] == 1500
        assert rate_manager.rate_limits['user_lookup']['limit'] == 300
    
    @pytest.mark.unit
    def test_can_make_call_initial_state(self, rate_manager):
        """Test can_make_call returns True initially."""
        assert rate_manager.can_make_call('search_tweets') is True
        assert rate_manager.can_make_call('user_timeline') is True
        assert rate_manager.can_make_call('user_lookup') is True
    
    @pytest.mark.unit
    def test_record_call_tracking(self, rate_manager):
        """Test record_call properly tracks API calls."""
        initial_calls = len(rate_manager.rate_limits['search_tweets']['calls'])
        
        rate_manager.record_call('search_tweets')
        
        updated_calls = len(rate_manager.rate_limits['search_tweets']['calls'])
        assert updated_calls == initial_calls + 1
    
    @pytest.mark.unit
    def test_rate_limit_enforcement(self, rate_manager):
        """Test rate limit enforcement when limit is reached."""
        # Fill up the rate limit
        endpoint = 'search_tweets'
        limit = rate_manager.rate_limits[endpoint]['limit']
        
        for _ in range(limit):
            rate_manager.record_call(endpoint)
        
        # Should not be able to make more calls
        assert rate_manager.can_make_call(endpoint) is False
    
    @pytest.mark.unit
    def test_handle_rate_limit_backoff(self, rate_manager):
        """Test rate limit backoff functionality."""
        endpoint = 'search_tweets'
        rate_manager.handle_rate_limit(endpoint, retry_after=900)
        
        assert endpoint in rate_manager.backoff_until
        assert rate_manager.can_make_call(endpoint) is False
    
    @pytest.mark.unit
    def test_get_status_format(self, rate_manager):
        """Test get_status returns properly formatted status."""
        status = rate_manager.get_status()
        
        assert isinstance(status, dict)
        assert 'search_tweets' in status
        assert 'user_timeline' in status
        assert 'user_lookup' in status
        
        for endpoint_status in status.values():
            assert 'calls_made' in endpoint_status
            assert 'remaining' in endpoint_status
            assert 'backoff_seconds' in endpoint_status


class TestMetricsTracker:
    """Test metrics tracking functionality."""
    
    @pytest.fixture
    def metrics_tracker(self):
        """Create MetricsTracker instance."""
        return MetricsTracker()
    
    @pytest.mark.unit
    def test_metrics_tracker_initialization(self, metrics_tracker):
        """Test MetricsTracker initializes with correct defaults."""
        assert metrics_tracker.session_metrics['api_calls_made'] == 0
        assert metrics_tracker.session_metrics['rate_limit_hits'] == 0
        assert metrics_tracker.session_metrics['opportunities_found'] == 0
        assert isinstance(metrics_tracker.session_metrics['opportunity_scores'], list)
    
    @pytest.mark.unit
    def test_record_api_call(self, metrics_tracker):
        """Test API call recording."""
        initial_calls = metrics_tracker.session_metrics['api_calls_made']
        
        metrics_tracker.record_api_call()
        
        assert metrics_tracker.session_metrics['api_calls_made'] == initial_calls + 1
    
    @pytest.mark.unit
    def test_record_opportunity_high_priority(self, metrics_tracker):
        """Test opportunity recording for high-priority opportunity."""
        opportunity = AlertOpportunity(
            account_username="testuser",
            account_tier=1,
            content_text="Test content",
            content_url="https://twitter.com/test",
            timestamp=datetime.now().isoformat(),
            overall_score=0.85,
            ai_blockchain_relevance=0.9,
            technical_depth=0.8,
            opportunity_type="test",
            suggested_response_type="test",
            time_sensitivity="immediate",
            strategic_context="test",
            suggested_response="test",
            voice_alignment_score=0.88
        )
        
        initial_opportunities = metrics_tracker.session_metrics['opportunities_found']
        initial_high_priority = metrics_tracker.session_metrics['high_priority_opportunities']
        initial_tier_1 = metrics_tracker.session_metrics['tier_1_interactions']
        
        metrics_tracker.record_opportunity(opportunity)
        
        assert metrics_tracker.session_metrics['opportunities_found'] == initial_opportunities + 1
        assert metrics_tracker.session_metrics['high_priority_opportunities'] == initial_high_priority + 1
        assert metrics_tracker.session_metrics['tier_1_interactions'] == initial_tier_1 + 1
        assert 0.85 in metrics_tracker.session_metrics['opportunity_scores']
        assert 0.88 in metrics_tracker.session_metrics['voice_alignments']
    
    @pytest.mark.unit
    def test_get_current_snapshot_format(self, metrics_tracker):
        """Test current snapshot returns proper format."""
        snapshot = metrics_tracker.get_current_snapshot()
        
        assert hasattr(snapshot, 'timestamp')
        assert hasattr(snapshot, 'api_calls_made')
        assert hasattr(snapshot, 'opportunities_found')
        assert hasattr(snapshot, 'api_efficiency')
        assert hasattr(snapshot, 'cost_per_opportunity')
        
        # Test with some data
        metrics_tracker.record_api_call()
        metrics_tracker.record_opportunity(AlertOpportunity(
            account_username="test", account_tier=1, content_text="test",
            content_url="test", timestamp="test", overall_score=0.8,
            ai_blockchain_relevance=0.8, technical_depth=0.7,
            opportunity_type="test", suggested_response_type="test",
            time_sensitivity="test", strategic_context="test",
            suggested_response="test"
        ))
        
        snapshot = metrics_tracker.get_current_snapshot()
        assert snapshot.api_efficiency > 0
        assert snapshot.cost_per_opportunity > 0


class TestCronMonitorSystem:
    """Test cron monitoring system functionality."""
    
    @pytest.fixture
    def alert_config(self):
        """Create test alert configuration."""
        return AlertConfiguration(
            smtp_server="smtp.test.com",
            smtp_port=587,
            email_username="test@test.com",
            email_password="testpass",
            from_email="test@test.com",
            to_email="recipient@test.com"
        )
    
    @pytest.fixture
    def mock_clients(self):
        """Create mock API clients."""
        x_client = AsyncMock()
        claude_client = AsyncMock()
        strategic_tracker = AsyncMock()
        
        return x_client, claude_client, strategic_tracker
    
    @pytest.fixture
    def monitor_system(self, mock_clients, alert_config):
        """Create CronMonitorSystem instance with mocks."""
        x_client, claude_client, strategic_tracker = mock_clients
        return CronMonitorSystem(x_client, claude_client, strategic_tracker, alert_config)
    
    @pytest.mark.unit
    def test_cron_monitor_initialization(self, monitor_system, alert_config):
        """Test CronMonitorSystem initializes correctly."""
        assert monitor_system.config == alert_config
        assert monitor_system.monitoring_active is False
        assert isinstance(monitor_system.alert_history, list)
        assert isinstance(monitor_system.daily_opportunities, list)
    
    @pytest.mark.unit
    def test_convert_time_sensitivity(self, monitor_system):
        """Test time sensitivity conversion."""
        assert monitor_system._convert_time_sensitivity(0.9) == "immediate"
        assert monitor_system._convert_time_sensitivity(0.6) == "high"
        assert monitor_system._convert_time_sensitivity(0.4) == "moderate" 
        assert monitor_system._convert_time_sensitivity(0.2) == "low"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_keyword_tweets_structure(self, monitor_system):
        """Test keyword tweet search returns proper structure."""
        # Mock the X client search response
        mock_tweets = [
            {'id': '123', 'text': 'AI blockchain test tweet', 'author_id': 'user1'},
            {'id': '456', 'text': 'Uniswap v4 innovation', 'author_id': 'user2'}
        ]
        
        monitor_system.x_client.read_client.search_recent_tweets.return_value.data = mock_tweets
        
        results = await monitor_system._search_keyword_tweets("ai blockchain", max_results=10)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]['id'] == '123'
        assert 'AI blockchain' in results[0]['text']
    
    @pytest.mark.unit
    def test_analyze_ai_blockchain_content_basic(self, monitor_system):
        """Test basic AI blockchain content analysis."""
        text = "AI agents on blockchain networks are revolutionizing autonomous trading"
        
        analysis = monitor_system._analyze_ai_blockchain_content_basic(text)
        
        assert isinstance(analysis, dict)
        assert 'ai_blockchain_relevance' in analysis
        assert 'technical_depth' in analysis
        assert 'overall_ai_blockchain_score' in analysis
        assert analysis['ai_blockchain_relevance'] > 0
        assert analysis['overall_ai_blockchain_score'] > 0
    
    @pytest.mark.unit 
    @pytest.mark.asyncio
    async def test_process_opportunities_structure(self, monitor_system):
        """Test opportunity processing returns AlertOpportunity objects."""
        raw_opportunities = [
            {
                'keyword': 'ai blockchain',
                'tweet_data': {'id': '123', 'text': 'Test AI blockchain tweet'},
                'analysis': {
                    'ai_blockchain_relevance': 0.8,
                    'technical_depth': 0.7,
                    'innovation_score': 0.6,
                    'engagement_opportunity': 0.9,
                    'time_sensitivity': 0.8,
                    'content_themes': ['ai', 'blockchain'],
                    'opportunity_type': 'technical_discussion',
                    'strategic_value': 'high',
                    'suggested_approach': 'technical_insight',
                    'overall_ai_blockchain_score': 0.8
                },
                'discovered_at': datetime.now().isoformat()
            }
        ]
        
        # Mock content generation
        monitor_system.claude_client.generate_content = AsyncMock()
        monitor_system.claude_client.generate_content.return_value.content = json.dumps({
            'primary_reply': 'Great insight on AI blockchain convergence!',
            'reasoning': 'Technical expertise demonstration',
            'alternatives': ['Alt 1', 'Alt 2'],
            'engagement_prediction': 0.8,
            'voice_alignment': 0.85
        })
        
        processed = await monitor_system._process_opportunities(raw_opportunities)
        
        assert isinstance(processed, list)
        assert len(processed) == 1
        assert isinstance(processed[0], AlertOpportunity)
        assert processed[0].overall_score == 0.8
        assert processed[0].ai_blockchain_relevance == 0.8


class TestXEngagementService:
    """Test main engagement service functionality."""
    
    @pytest.fixture
    def engagement_service(self):
        """Create XEngagementService instance."""
        return XEngagementService()
    
    @pytest.mark.unit
    def test_engagement_service_initialization(self, engagement_service):
        """Test XEngagementService initializes correctly."""
        assert engagement_service.running is True
        assert isinstance(engagement_service.rate_manager, RateLimitManager)
        assert isinstance(engagement_service.metrics, MetricsTracker)
        assert engagement_service.monitoring_interval == 30 * 60  # 30 minutes
        assert engagement_service.metrics_interval == 60 * 60     # 1 hour
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_clients_success(self, engagement_service):
        """Test successful client initialization."""
        # Mock environment variables
        with patch.dict('os.environ', {
            'X_API_KEY': 'test_key',
            'X_API_SECRET': 'test_secret', 
            'X_ACCESS_TOKEN': 'test_token',
            'X_ACCESS_TOKEN_SECRET': 'test_token_secret',
            'X_BEARER_TOKEN': 'test_bearer',
            'CLAUDE_API_KEY': 'test_claude_key',
            'SENDER_EMAIL': 'test@test.com',
            'SENDER_PASSWORD': 'testpass'
        }):
            # Mock the client classes
            with patch('x_engagement_service.XAPIClient') as mock_x_client, \
                 patch('x_engagement_service.ClaudeAPIClient') as mock_claude_client, \
                 patch('x_engagement_service.StrategicAccountTracker') as mock_tracker, \
                 patch('x_engagement_service.CronMonitorSystem') as mock_monitor:
                
                result = await engagement_service.initialize_clients()
                
                assert result is True
                assert engagement_service.x_client is not None
                assert engagement_service.claude_client is not None
                assert engagement_service.strategic_tracker is not None
                assert engagement_service.monitor is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitoring_cycle_rate_limited(self, engagement_service):
        """Test monitoring cycle respects rate limits."""
        # Set up rate manager to indicate no calls can be made
        engagement_service.rate_manager.can_make_call = MagicMock(return_value=False)
        
        # Initialize mock monitor
        engagement_service.monitor = AsyncMock()
        
        await engagement_service.monitoring_cycle()
        
        # Should not attempt any API calls when rate limited
        engagement_service.monitor._monitor_ai_blockchain_keywords.assert_not_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitoring_cycle_successful_execution(self, engagement_service):
        """Test successful monitoring cycle execution."""
        # Mock successful rate limiting
        engagement_service.rate_manager.can_make_call = MagicMock(return_value=True)
        engagement_service.rate_manager.record_call = MagicMock()
        
        # Mock monitor with successful response
        engagement_service.monitor = AsyncMock()
        engagement_service.monitor._monitor_ai_blockchain_keywords.return_value = [
            {'keyword': 'test', 'score': 0.8}  # Raw opportunity format
        ]
        engagement_service.monitor._process_opportunities.return_value = [
            AlertOpportunity(
                account_username="test", account_tier=1, content_text="test",
                content_url="test", timestamp="test", overall_score=0.9,
                ai_blockchain_relevance=0.8, technical_depth=0.7,
                opportunity_type="test", suggested_response_type="test",
                time_sensitivity="test", strategic_context="test",
                suggested_response="test"
            )
        ]
        engagement_service.monitor._send_immediate_alert = AsyncMock()
        
        await engagement_service.monitoring_cycle()
        
        # Verify the flow executed correctly
        engagement_service.rate_manager.record_call.assert_called()
        engagement_service.monitor._monitor_ai_blockchain_keywords.assert_called_once()
        engagement_service.monitor._process_opportunities.assert_called_once()
        engagement_service.monitor._send_immediate_alert.assert_called_once()


class TestIntegrationScenarios:
    """Integration tests for common monitoring scenarios."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_opportunity_pipeline(self):
        """Test complete opportunity detection and processing pipeline."""
        # This would test the full flow from keyword search to email alert
        # Mock all external dependencies and verify the complete pipeline
        pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limit_recovery_scenario(self):
        """Test system behavior during and after rate limit recovery."""
        # Test how the system handles rate limit hits and recovery
        pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_email_alert_generation_with_content(self):
        """Test email alert generation with AI-generated content."""
        # Test the complete email generation with Claude API content
        pass


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "unit"  # Run only unit tests by default
    ])