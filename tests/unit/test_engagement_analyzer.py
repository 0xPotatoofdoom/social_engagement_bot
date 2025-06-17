"""
TDD Tests for Engagement Analyzer

These tests define the expected behavior of our engagement analysis system before implementation.
All tests should FAIL initially until we implement the actual EngagementAnalyzer class.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import will fail initially - this is expected in TDD
try:
    from src.bot.engagement.analyzer import (
        EngagementAnalyzer, EngagementMetrics, EngagementPredictor,
        CommunityEngagementBot, ViralContentDetector, EngagementOptimizer
    )
except ImportError:
    # Expected to fail initially in TDD
    pass


class TestEngagementMetrics:
    """Test EngagementMetrics data structure."""
    
    @pytest.mark.unit
    def test_engagement_metrics_initialization(self):
        """EngagementMetrics should initialize with all required fields."""
        metrics = EngagementMetrics(
            tweet_id="1234567890",
            engagement_rate=0.05,
            likes=25,
            retweets=8,
            replies=12,
            quotes=3,
            impressions=960,
            clicks=45,
            profile_visits=15,
            timestamp=datetime.now()
        )
        
        assert metrics.tweet_id == "1234567890"
        assert metrics.engagement_rate == 0.05
        assert metrics.likes == 25
        assert metrics.total_engagements == 48  # likes + retweets + replies + quotes
        assert metrics.impressions == 960
    
    @pytest.mark.unit
    def test_engagement_metrics_calculated_properties(self):
        """EngagementMetrics should calculate derived properties."""
        metrics = EngagementMetrics(
            tweet_id="123",
            engagement_rate=0.08,
            likes=100,
            retweets=20,
            replies=30,
            quotes=5,
            impressions=1000,
            clicks=80,
            profile_visits=25
        )
        
        assert metrics.total_engagements == 155
        assert metrics.click_through_rate == 0.08  # 80/1000
        assert metrics.reply_rate == 0.03  # 30/1000
        assert metrics.viral_score > 0  # Should calculate viral potential
    
    @pytest.mark.unit
    def test_engagement_metrics_validation(self):
        """EngagementMetrics should validate input data."""
        # Negative values should be invalid
        with pytest.raises(ValueError):
            EngagementMetrics(
                tweet_id="123",
                engagement_rate=0.05,
                likes=-5,  # Invalid
                retweets=2,
                replies=1,
                impressions=100
            )
        
        # Engagement rate above 1.0 should be invalid
        with pytest.raises(ValueError):
            EngagementMetrics(
                tweet_id="123",
                engagement_rate=1.5,  # Invalid
                likes=5,
                retweets=2,
                replies=1,
                impressions=100
            )
    
    @pytest.mark.unit
    def test_engagement_metrics_quality_score(self):
        """EngagementMetrics should calculate quality score."""
        # High quality engagement (many replies and meaningful interactions)
        high_quality = EngagementMetrics(
            tweet_id="123",
            engagement_rate=0.12,
            likes=50,
            retweets=15,
            replies=25,  # High reply count indicates quality
            quotes=8,
            impressions=800,
            clicks=96
        )
        
        # Low quality engagement (mostly likes, few replies)
        low_quality = EngagementMetrics(
            tweet_id="456",
            engagement_rate=0.10,
            likes=95,
            retweets=5,
            replies=2,   # Low reply count
            quotes=1,
            impressions=1000,
            clicks=50
        )
        
        assert high_quality.quality_score > low_quality.quality_score
        assert high_quality.quality_score > 0.7
        assert low_quality.quality_score < 0.6
    
    @pytest.mark.unit
    def test_engagement_metrics_is_viral(self):
        """EngagementMetrics should identify viral content."""
        viral_metrics = EngagementMetrics(
            tweet_id="viral",
            engagement_rate=0.15,  # Very high engagement
            likes=500,
            retweets=200,
            replies=150,
            quotes=50,
            impressions=6000,
            clicks=900
        )
        
        normal_metrics = EngagementMetrics(
            tweet_id="normal",
            engagement_rate=0.04,
            likes=20,
            retweets=3,
            replies=2,
            quotes=0,
            impressions=625,
            clicks=25
        )
        
        assert viral_metrics.is_viral(threshold=0.10) is True
        assert normal_metrics.is_viral(threshold=0.10) is False


class TestEngagementAnalyzer:
    """Test EngagementAnalyzer core functionality."""
    
    @pytest.fixture
    def mock_x_client(self):
        """Mock X API client for testing."""
        mock_client = AsyncMock()
        mock_client.get_tweet_metrics.return_value = {
            "public_metrics": {
                "retweet_count": 8,
                "like_count": 25,
                "reply_count": 12,
                "quote_count": 3
            },
            "organic_metrics": {
                "impression_count": 960,
                "url_link_clicks": 45,
                "user_profile_clicks": 15
            }
        }
        return mock_client
    
    @pytest.fixture
    def engagement_analyzer(self, mock_x_client):
        """Create EngagementAnalyzer for testing."""
        return EngagementAnalyzer(mock_x_client)
    
    @pytest.mark.unit
    def test_engagement_analyzer_initialization(self, mock_x_client):
        """EngagementAnalyzer should initialize with X client."""
        analyzer = EngagementAnalyzer(mock_x_client)
        
        assert analyzer.x_client == mock_x_client
        assert hasattr(analyzer, 'metrics_cache')
        assert hasattr(analyzer, 'performance_history')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_tweet_engagement_success(self, engagement_analyzer):
        """Should successfully analyze tweet engagement."""
        tweet_id = "1234567890"
        
        metrics = await engagement_analyzer.analyze_tweet_engagement(tweet_id)
        
        assert isinstance(metrics, EngagementMetrics)
        assert metrics.tweet_id == tweet_id
        assert metrics.likes == 25
        assert metrics.retweets == 8
        assert metrics.replies == 12
        assert metrics.impressions == 960
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_tweet_engagement_cached(self, engagement_analyzer):
        """Should use cached metrics when available."""
        tweet_id = "1234567890"
        
        # First call should fetch from API
        metrics1 = await engagement_analyzer.analyze_tweet_engagement(tweet_id)
        
        # Second call should use cache
        metrics2 = await engagement_analyzer.analyze_tweet_engagement(tweet_id)
        
        assert metrics1.tweet_id == metrics2.tweet_id
        # Should only call API once
        engagement_analyzer.x_client.get_tweet_metrics.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_tweet_engagement_api_failure(self, engagement_analyzer):
        """Should handle API failure gracefully."""
        tweet_id = "1234567890"
        engagement_analyzer.x_client.get_tweet_metrics.side_effect = Exception("API Error")
        
        metrics = await engagement_analyzer.analyze_tweet_engagement(tweet_id)
        
        assert metrics is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_content_engagement_potential(self, engagement_analyzer):
        """Should predict engagement potential of content before posting."""
        content = "Blockchain innovation is reshaping finance. What trends are you seeing? #DeFi #web3"
        
        prediction = await engagement_analyzer.analyze_content_engagement_potential(content)
        
        assert 'engagement_score' in prediction
        assert 'contributing_factors' in prediction
        assert 'recommendations' in prediction
        assert 0 <= prediction['engagement_score'] <= 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_performance_trends(self, engagement_analyzer):
        """Should analyze performance trends over time."""
        # Mock historical data
        engagement_analyzer.performance_history = [
            EngagementMetrics("1", 0.05, 20, 5, 8, 2, 500, 25, 10, datetime.now() - timedelta(days=7)),
            EngagementMetrics("2", 0.08, 40, 12, 15, 5, 800, 64, 20, datetime.now() - timedelta(days=6)),
            EngagementMetrics("3", 0.06, 30, 8, 10, 3, 600, 36, 15, datetime.now() - timedelta(days=5))
        ]
        
        trends = await engagement_analyzer.get_performance_trends(days=7)
        
        assert 'avg_engagement_rate' in trends
        assert 'trend_direction' in trends
        assert 'best_performing_content' in trends
        assert 'improvement_suggestions' in trends
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_identify_high_performing_patterns(self, engagement_analyzer):
        """Should identify patterns in high-performing content."""
        # Mock content with performance data
        content_performance = [
            {"content": "Question about blockchain? #crypto", "metrics": EngagementMetrics("1", 0.12, 60, 20, 25, 8, 1000, 120, 30)},
            {"content": "Statement about DeFi trends #DeFi", "metrics": EngagementMetrics("2", 0.04, 20, 3, 5, 1, 600, 24, 8)},
            {"content": "Community discussion starter? #web3", "metrics": EngagementMetrics("3", 0.10, 50, 15, 20, 6, 800, 80, 24)}
        ]
        
        patterns = await engagement_analyzer.identify_high_performing_patterns(content_performance)
        
        assert 'content_patterns' in patterns
        assert 'optimal_characteristics' in patterns
        assert 'engagement_drivers' in patterns
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compare_content_performance(self, engagement_analyzer):
        """Should compare performance between different content pieces."""
        tweet_ids = ["1234567890", "1234567891", "1234567892"]
        
        # Mock different performance levels
        engagement_analyzer.x_client.get_tweet_metrics.side_effect = [
            {"public_metrics": {"like_count": 50, "retweet_count": 15, "reply_count": 20, "quote_count": 5},
             "organic_metrics": {"impression_count": 1000, "url_link_clicks": 100, "user_profile_clicks": 30}},
            {"public_metrics": {"like_count": 20, "retweet_count": 3, "reply_count": 5, "quote_count": 1},
             "organic_metrics": {"impression_count": 500, "url_link_clicks": 25, "user_profile_clicks": 8}},
            {"public_metrics": {"like_count": 100, "retweet_count": 30, "reply_count": 40, "quote_count": 12},
             "organic_metrics": {"impression_count": 2000, "url_link_clicks": 200, "user_profile_clicks": 60}}
        ]
        
        comparison = await engagement_analyzer.compare_content_performance(tweet_ids)
        
        assert 'rankings' in comparison
        assert 'performance_gaps' in comparison
        assert 'success_factors' in comparison
        assert len(comparison['rankings']) == 3


class TestEngagementPredictor:
    """Test EngagementPredictor functionality."""
    
    @pytest.fixture
    def engagement_predictor(self):
        """Create EngagementPredictor for testing."""
        return EngagementPredictor()
    
    @pytest.mark.unit
    def test_engagement_predictor_initialization(self):
        """EngagementPredictor should initialize with default model."""
        predictor = EngagementPredictor()
        
        assert hasattr(predictor, 'model')
        assert hasattr(predictor, 'feature_extractors')
        assert hasattr(predictor, 'training_data')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_predict_engagement_score(self, engagement_predictor):
        """Should predict engagement score for content."""
        content = "What do you think about the latest blockchain developments? #crypto #DeFi"
        
        prediction = await engagement_predictor.predict_engagement_score(content)
        
        assert 'engagement_score' in prediction
        assert 'confidence' in prediction
        assert 'feature_scores' in prediction
        assert 0 <= prediction['engagement_score'] <= 1
        assert 0 <= prediction['confidence'] <= 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_predict_viral_potential(self, engagement_predictor):
        """Should predict viral potential of content."""
        high_viral_content = "BREAKING: Major blockchain breakthrough changes everything! What are your thoughts? 🚀 #blockchain #crypto #web3"
        low_viral_content = "Posted an update about blockchain."
        
        high_prediction = await engagement_predictor.predict_viral_potential(high_viral_content)
        low_prediction = await engagement_predictor.predict_viral_potential(low_viral_content)
        
        assert high_prediction['viral_score'] > low_prediction['viral_score']
        assert high_prediction['viral_probability'] > 0.3
        assert low_prediction['viral_probability'] < 0.2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_engagement_features(self, engagement_predictor):
        """Should extract features that correlate with engagement."""
        content = "Fascinating blockchain development! What do you think about DeFi growth? #crypto #innovation"
        
        features = await engagement_predictor.extract_engagement_features(content)
        
        expected_features = [
            'has_question', 'has_hashtags', 'has_exclamation', 'word_count',
            'sentiment_score', 'readability_score', 'emotion_words_count'
        ]
        
        for feature in expected_features:
            assert feature in features
        
        assert features['has_question'] is True  # Contains "What do you think"
        assert features['has_hashtags'] is True  # Contains hashtags
        assert features['hashtag_count'] == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_train_prediction_model(self, engagement_predictor):
        """Should train prediction model with historical data."""
        training_data = [
            {"content": "Great blockchain news! #crypto", "engagement_rate": 0.08},
            {"content": "What are your thoughts on DeFi?", "engagement_rate": 0.12},
            {"content": "Posted an update", "engagement_rate": 0.02},
            {"content": "Amazing developments in web3! Thoughts?", "engagement_rate": 0.15}
        ]
        
        training_result = await engagement_predictor.train_prediction_model(training_data)
        
        assert training_result['success'] is True
        assert 'model_accuracy' in training_result
        assert 'feature_importance' in training_result
        assert training_result['model_accuracy'] > 0.5  # Should beat random chance
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_optimization_suggestions(self, engagement_predictor):
        """Should provide suggestions to optimize content for engagement."""
        content = "blockchain update"
        
        suggestions = await engagement_predictor.get_optimization_suggestions(content)
        
        assert 'suggestions' in suggestions
        assert 'predicted_improvement' in suggestions
        assert len(suggestions['suggestions']) > 0
        
        # Should suggest specific improvements
        suggestion_text = ' '.join(suggestions['suggestions'])
        assert any(word in suggestion_text.lower() for word in ['question', 'hashtag', 'emotion', 'call-to-action'])


class TestCommunityEngagementBot:
    """Test CommunityEngagementBot for automated interactions."""
    
    @pytest.fixture
    def mock_x_client(self):
        """Mock X API client for testing."""
        mock_client = AsyncMock()
        mock_client.get_mentions.return_value = [
            {
                "id": "mention1",
                "text": "What do you think about the latest blockchain news?",
                "author": {"username": "user1", "id": "author1"},
                "created_at": "2024-01-01T12:00:00Z"
            }
        ]
        mock_client.reply_to_tweet.return_value = {"success": True, "tweet_id": "reply123"}
        return mock_client
    
    @pytest.fixture
    def mock_claude_client(self):
        """Mock Claude API client for testing."""
        mock_client = AsyncMock()
        mock_client.generate_content.return_value = {
            "success": True,
            "content": "Great question! Blockchain development is moving fast. What specific aspects interest you most?"
        }
        return mock_client
    
    @pytest.fixture
    def community_bot(self, mock_x_client, mock_claude_client, sample_voice_profile):
        """Create CommunityEngagementBot for testing."""
        return CommunityEngagementBot(mock_x_client, mock_claude_client, sample_voice_profile)
    
    @pytest.mark.unit
    def test_community_bot_initialization(self, mock_x_client, mock_claude_client, sample_voice_profile):
        """CommunityEngagementBot should initialize with required clients."""
        bot = CommunityEngagementBot(mock_x_client, mock_claude_client, sample_voice_profile)
        
        assert bot.x_client == mock_x_client
        assert bot.claude_client == mock_claude_client
        assert bot.voice_profile == sample_voice_profile
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_mentions_success(self, community_bot):
        """Should successfully process and respond to mentions."""
        result = await community_bot.handle_mentions()
        
        assert result['mentions_processed'] == 1
        assert len(result['responses_sent']) == 1
        assert result['responses_sent'][0]['posted'] is True
        
        # Should call Claude to generate response
        community_bot.claude_client.generate_content.assert_called_once()
        # Should post reply
        community_bot.x_client.reply_to_tweet.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_respond_to_mention_question(self, community_bot):
        """Should respond to mentions that are questions."""
        mention = {
            "id": "123",
            "text": "What do you think about DeFi protocols?",
            "author": {"username": "user1"},
            "is_retweet": False
        }
        
        should_respond = await community_bot._should_respond_to_mention(mention)
        
        assert should_respond is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_respond_to_mention_retweet(self, community_bot):
        """Should not respond to retweets."""
        mention = {
            "id": "123", 
            "text": "RT @someone: Great blockchain post",
            "author": {"username": "user1"},
            "is_retweet": True
        }
        
        should_respond = await community_bot._should_respond_to_mention(mention)
        
        assert should_respond is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_should_respond_to_mention_spam(self, community_bot):
        """Should not respond to spam accounts."""
        mention = {
            "id": "123",
            "text": "What do you think?",
            "author": {"username": "spambot123"},
            "is_retweet": False
        }
        
        with patch.object(community_bot, '_is_spam_account') as mock_spam_check:
            mock_spam_check.return_value = True
            
            should_respond = await community_bot._should_respond_to_mention(mention)
            
            assert should_respond is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_mention_response(self, community_bot):
        """Should generate contextual response to mention."""
        mention = {
            "id": "123",
            "text": "What are your thoughts on blockchain scalability?",
            "author": {"username": "crypto_dev"},
            "conversation_context": "Discussion about blockchain technology"
        }
        
        response = await community_bot._generate_mention_response(mention)
        
        assert response['success'] is True
        assert "blockchain" in response['content'].lower()
        assert len(response['content']) <= 280  # Twitter limit
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_conversation_context(self, community_bot):
        """Should track ongoing conversation context."""
        conversation_id = "conv123"
        new_message = "Follow-up question about DeFi security"
        
        community_bot.track_conversation_context(conversation_id, new_message)
        
        context = community_bot.get_conversation_context(conversation_id)
        
        assert conversation_id in community_bot.conversation_history
        assert new_message in context


class TestViralContentDetector:
    """Test ViralContentDetector functionality."""
    
    @pytest.fixture
    def viral_detector(self, mock_x_client):
        """Create ViralContentDetector for testing."""
        return ViralContentDetector(mock_x_client)
    
    @pytest.mark.unit
    def test_viral_detector_initialization(self, mock_x_client):
        """ViralContentDetector should initialize with X client."""
        detector = ViralContentDetector(mock_x_client)
        
        assert detector.x_client == mock_x_client
        assert hasattr(detector, 'viral_thresholds')
        assert hasattr(detector, 'monitoring_tweets')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detect_early_viral_signals(self, viral_detector):
        """Should detect early signals of viral content."""
        tweet_id = "1234567890"
        
        # Mock rapid engagement growth
        viral_detector.x_client.get_tweet_metrics.side_effect = [
            {"public_metrics": {"like_count": 10, "retweet_count": 2}, "timestamp": "2024-01-01T12:00:00Z"},
            {"public_metrics": {"like_count": 50, "retweet_count": 15}, "timestamp": "2024-01-01T12:05:00Z"},
            {"public_metrics": {"like_count": 200, "retweet_count": 80}, "timestamp": "2024-01-01T12:10:00Z"}
        ]
        
        viral_signals = await viral_detector.detect_early_viral_signals(tweet_id)
        
        assert viral_signals['is_viral_candidate'] is True
        assert viral_signals['growth_rate'] > 2.0  # Rapid growth
        assert viral_signals['viral_probability'] > 0.7
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_content_performance(self, viral_detector):
        """Should continuously monitor content for viral potential."""
        tweet_ids = ["123", "456", "789"]
        
        monitoring_result = await viral_detector.monitor_content_performance(tweet_ids)
        
        assert 'monitored_tweets' in monitoring_result
        assert 'viral_candidates' in monitoring_result
        assert 'performance_summary' in monitoring_result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_predict_viral_potential_pre_post(self, viral_detector):
        """Should predict viral potential before posting."""
        content = "BREAKING: Revolutionary blockchain breakthrough! This changes everything! 🚀 #crypto #blockchain #revolution"
        
        prediction = await viral_detector.predict_viral_potential_pre_post(content)
        
        assert 'viral_score' in prediction
        assert 'viral_indicators' in prediction
        assert 'optimization_suggestions' in prediction
        assert prediction['viral_score'] > 0.5  # Should be high for viral-style content
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_viral_patterns(self, viral_detector):
        """Should analyze patterns in viral content."""
        viral_content_samples = [
            {"content": "BREAKING news! Amazing development! 🚀", "viral_score": 0.9},
            {"content": "What do you think about this trend?", "viral_score": 0.7},
            {"content": "Regular update post", "viral_score": 0.2}
        ]
        
        patterns = await viral_detector.analyze_viral_patterns(viral_content_samples)
        
        assert 'content_characteristics' in patterns
        assert 'linguistic_patterns' in patterns
        assert 'optimal_elements' in patterns


class TestEngagementOptimizer:
    """Test EngagementOptimizer functionality."""
    
    @pytest.fixture
    def engagement_optimizer(self, mock_x_client):
        """Create EngagementOptimizer for testing."""
        return EngagementOptimizer(mock_x_client)
    
    @pytest.mark.unit
    def test_engagement_optimizer_initialization(self, mock_x_client):
        """EngagementOptimizer should initialize with X client."""
        optimizer = EngagementOptimizer(mock_x_client)
        
        assert optimizer.x_client == mock_x_client
        assert hasattr(optimizer, 'optimization_strategies')
        assert hasattr(optimizer, 'performance_baseline')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_optimize_posting_times(self, engagement_optimizer):
        """Should optimize posting times based on audience activity."""
        historical_performance = [
            {"time": "09:00", "avg_engagement": 0.08},
            {"time": "12:00", "avg_engagement": 0.12},
            {"time": "15:00", "avg_engagement": 0.06},
            {"time": "18:00", "avg_engagement": 0.15},
            {"time": "21:00", "avg_engagement": 0.10}
        ]
        
        optimal_times = await engagement_optimizer.optimize_posting_times(historical_performance)
        
        assert len(optimal_times) > 0
        assert optimal_times[0]['time'] == "18:00"  # Highest engagement
        assert optimal_times[1]['time'] == "12:00"  # Second highest
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_optimize_content_for_engagement(self, engagement_optimizer):
        """Should optimize content elements for higher engagement."""
        content = "blockchain update"
        current_score = 0.3
        
        optimization = await engagement_optimizer.optimize_content_for_engagement(content, current_score)
        
        assert 'optimized_content' in optimization
        assert 'improvements_made' in optimization
        assert 'predicted_score' in optimization
        assert optimization['predicted_score'] > current_score
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ab_test_content_variations(self, engagement_optimizer):
        """Should run A/B tests on content variations."""
        variations = [
            "Blockchain innovation is changing finance #crypto",
            "What do you think about blockchain in finance? #crypto", 
            "BREAKING: Blockchain revolutionizes finance! 🚀 #crypto"
        ]
        
        ab_test_result = await engagement_optimizer.ab_test_content_variations(variations)
        
        assert 'winning_variation' in ab_test_result
        assert 'performance_comparison' in ab_test_result
        assert 'statistical_significance' in ab_test_result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_engagement_recommendations(self, engagement_optimizer):
        """Should provide actionable engagement recommendations."""
        performance_data = {
            "avg_engagement_rate": 0.04,
            "best_performing_time": "18:00",
            "top_content_type": "questions",
            "audience_size": 1000
        }
        
        recommendations = await engagement_optimizer.get_engagement_recommendations(performance_data)
        
        assert 'immediate_actions' in recommendations
        assert 'content_strategy' in recommendations
        assert 'posting_strategy' in recommendations
        assert len(recommendations['immediate_actions']) > 0


class TestEngagementAnalyzerIntegration:
    """Integration tests for engagement analysis system."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_engagement_analysis(self, sample_voice_profile):
        """Should handle complete engagement analysis workflow."""
        # Mock X client with realistic data
        mock_x_client = AsyncMock()
        mock_x_client.get_tweet_metrics.return_value = {
            "public_metrics": {"like_count": 45, "retweet_count": 12, "reply_count": 18, "quote_count": 6},
            "organic_metrics": {"impression_count": 1200, "url_link_clicks": 96, "user_profile_clicks": 24}
        }
        mock_x_client.get_mentions.return_value = [
            {"id": "mention1", "text": "Great insight! What's your take on DeFi?", "author": {"username": "user1"}}
        ]
        
        # Mock Claude client
        mock_claude = AsyncMock()
        mock_claude.generate_content.return_value = {
            "success": True,
            "content": "Thanks for the question! DeFi is evolving rapidly..."
        }
        
        # Initialize components
        analyzer = EngagementAnalyzer(mock_x_client)
        community_bot = CommunityEngagementBot(mock_x_client, mock_claude, sample_voice_profile)
        predictor = EngagementPredictor()
        
        # Analyze existing tweet engagement
        tweet_id = "1234567890"
        metrics = await analyzer.analyze_tweet_engagement(tweet_id)
        
        assert metrics.engagement_rate > 0.05  # Good engagement
        assert metrics.total_engagements == 81  # 45+12+18+6
        
        # Handle community engagement
        mentions_result = await community_bot.handle_mentions()
        assert mentions_result['mentions_processed'] == 1
        
        # Predict engagement for new content
        new_content = "What trends are you seeing in blockchain adoption? #crypto #DeFi"
        prediction = await predictor.predict_engagement_score(new_content)
        assert prediction['engagement_score'] > 0.4  # Should predict decent engagement
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_viral_content_detection_and_amplification(self):
        """Should detect viral content and amplify appropriately."""
        # Mock X client with viral content data
        mock_x_client = AsyncMock()
        mock_x_client.get_tweet_metrics.side_effect = [
            {"public_metrics": {"like_count": 50, "retweet_count": 15}, "timestamp": "12:00"},
            {"public_metrics": {"like_count": 200, "retweet_count": 80}, "timestamp": "12:15"},
            {"public_metrics": {"like_count": 500, "retweet_count": 250}, "timestamp": "12:30"}
        ]
        
        # Initialize viral detector
        viral_detector = ViralContentDetector(mock_x_client)
        
        # Detect viral signals
        tweet_id = "viral_tweet_123"
        viral_signals = await viral_detector.detect_early_viral_signals(tweet_id)
        
        assert viral_signals['is_viral_candidate'] is True
        assert viral_signals['growth_rate'] > 3.0  # Exponential growth
        
        # Should trigger amplification strategies
        if viral_signals['is_viral_candidate']:
            amplification = await viral_detector.get_amplification_strategy(tweet_id)
            assert 'follow_up_content' in amplification
            assert 'engagement_tactics' in amplification
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_engagement_optimization_feedback_loop(self):
        """Should continuously optimize engagement based on performance feedback."""
        # Mock components
        mock_x_client = AsyncMock()
        optimizer = EngagementOptimizer(mock_x_client)
        
        # Simulate performance data over time
        performance_history = []
        for i in range(30):  # 30 days of data
            performance_history.append({
                "date": f"2024-01-{i+1:02d}",
                "engagement_rate": 0.04 + (i * 0.001),  # Gradual improvement
                "best_time": "18:00" if i < 15 else "12:00",  # Shift in optimal time
                "content_type": "question" if i % 3 == 0 else "statement"
            })
        
        # Analyze trends and get optimization recommendations
        trends = await optimizer.analyze_performance_trends(performance_history)
        
        assert trends['overall_trend'] == 'improving'
        assert 'optimal_posting_time' in trends
        assert 'best_content_types' in trends
        
        # Get actionable recommendations
        recommendations = await optimizer.get_engagement_recommendations(trends)
        
        assert len(recommendations['immediate_actions']) > 0
        assert 'content_strategy' in recommendations
        assert 'posting_strategy' in recommendations