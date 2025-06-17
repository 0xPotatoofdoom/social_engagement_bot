"""
TDD Tests for Claude API Client

These tests define the expected behavior of our Claude API client before implementation.
All tests should FAIL initially until we implement the actual ClaudeClient class.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import anthropic

# Import will fail initially - this is expected in TDD
try:
    from src.bot.api.claude_client import ClaudeClient, ContentPrompts, TokenUsageTracker
except ImportError:
    # Expected to fail initially in TDD
    pass


class TestClaudeClientInitialization:
    """Test Claude API client initialization and configuration."""
    
    @pytest.mark.unit
    def test_claude_client_requires_api_key(self):
        """Claude client should require API key for initialization."""
        # This test will fail until we implement ClaudeClient
        with pytest.raises(TypeError):
            ClaudeClient()  # Should fail without API key
    
    @pytest.mark.unit
    def test_claude_client_initializes_with_api_key(self):
        """Claude client should initialize successfully with API key."""
        api_key = "test_api_key"
        
        client = ClaudeClient(api_key=api_key)
        
        assert client is not None
        assert hasattr(client, 'client')
        assert hasattr(client, 'model')
        assert hasattr(client, 'model_premium')
    
    @pytest.mark.unit
    def test_claude_client_validates_api_key_format(self):
        """Claude client should validate API key format."""
        invalid_api_key = ""  # Empty string should be invalid
        
        with pytest.raises(ValueError):
            ClaudeClient(api_key=invalid_api_key)
    
    @pytest.mark.unit
    def test_claude_client_sets_default_models(self):
        """Claude client should set default models for different use cases."""
        client = ClaudeClient(api_key="test_key")
        
        assert client.model == "claude-3-haiku-20240307"  # Fast model for tweets
        assert client.model_premium == "claude-3-sonnet-20240229"  # Premium model
    
    @pytest.mark.unit
    def test_claude_client_allows_custom_models(self):
        """Claude client should allow custom model configuration."""
        custom_model = "claude-3-opus-20240229"
        
        client = ClaudeClient(
            api_key="test_key",
            default_model=custom_model
        )
        
        assert client.model == custom_model


class TestClaudeClientContentGeneration:
    """Test content generation functionality."""
    
    @pytest.fixture
    def claude_client(self):
        """Create Claude client for testing."""
        return ClaudeClient(api_key="test_api_key")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_success(self, claude_client):
        """Should successfully generate content with Claude API."""
        prompt = "Create a tweet about blockchain innovation"
        
        with patch.object(claude_client.client, 'messages') as mock_messages:
            mock_messages.create.return_value = MagicMock(
                content=[MagicMock(text="Blockchain innovation is reshaping digital finance #web3")],
                usage=MagicMock(input_tokens=20, output_tokens=15)
            )
            
            result = await claude_client.generate_content(prompt)
            
            assert result['success'] is True
            assert 'content' in result
            assert 'usage' in result
            assert result['model'] == claude_client.model
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_with_context(self, claude_client, sample_voice_profile):
        """Should generate content using provided context."""
        prompt = "Create a tweet about DeFi"
        context = {
            'voice_profile': sample_voice_profile,
            'topics': ['blockchain', 'DeFi']
        }
        
        with patch.object(claude_client.client, 'messages') as mock_messages:
            mock_messages.create.return_value = MagicMock(
                content=[MagicMock(text="DeFi protocols are evolving rapidly #blockchain")],
                usage=MagicMock(input_tokens=25, output_tokens=12)
            )
            
            result = await claude_client.generate_content(prompt, context=context)
            
            assert result['success'] is True
            # Should call with system prompt that includes context
            mock_messages.create.assert_called_once()
            call_args = mock_messages.create.call_args
            assert 'system' in call_args.kwargs
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_with_premium_model(self, claude_client):
        """Should use premium model when requested."""
        prompt = "Create detailed analysis about blockchain trends"
        
        with patch.object(claude_client.client, 'messages') as mock_messages:
            mock_messages.create.return_value = MagicMock(
                content=[MagicMock(text="Detailed blockchain analysis content")],
                usage=MagicMock(input_tokens=30, output_tokens=25)
            )
            
            result = await claude_client.generate_content(prompt, use_premium=True)
            
            assert result['success'] is True
            assert result['model'] == claude_client.model_premium
            call_args = mock_messages.create.call_args
            assert call_args.kwargs['model'] == claude_client.model_premium
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_handles_rate_limit(self, claude_client):
        """Should handle rate limiting gracefully."""
        prompt = "Create a tweet"
        
        with patch.object(claude_client.client, 'messages') as mock_messages:
            mock_messages.create.side_effect = anthropic.RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(),
                body={}
            )
            
            result = await claude_client.generate_content(prompt)
            
            assert result['success'] is False
            assert result['error'] == 'rate_limit'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_handles_api_error(self, claude_client):
        """Should handle API errors gracefully."""
        prompt = "Create a tweet"
        
        with patch.object(claude_client.client, 'messages') as mock_messages:
            mock_messages.create.side_effect = anthropic.APIError(
                message="API error occurred",
                response=MagicMock(),
                body={}
            )
            
            result = await claude_client.generate_content(prompt)
            
            assert result['success'] is False
            assert result['error'] == 'api_error'
            assert 'message' in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_validates_prompt(self, claude_client):
        """Should validate prompt before making API call."""
        empty_prompt = ""
        
        result = await claude_client.generate_content(empty_prompt)
        
        assert result['success'] is False
        assert result['error'] == 'invalid_prompt'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_respects_max_tokens(self, claude_client):
        """Should respect max tokens parameter."""
        prompt = "Create a long tweet"
        max_tokens = 500
        
        with patch.object(claude_client.client, 'messages') as mock_messages:
            mock_messages.create.return_value = MagicMock(
                content=[MagicMock(text="Generated content")],
                usage=MagicMock(input_tokens=20, output_tokens=15)
            )
            
            result = await claude_client.generate_content(prompt, max_tokens=max_tokens)
            
            call_args = mock_messages.create.call_args
            assert call_args.kwargs['max_tokens'] == max_tokens


class TestClaudeClientContentVariations:
    """Test content variation generation for A/B testing."""
    
    @pytest.fixture
    def claude_client(self):
        """Create Claude client for testing."""
        return ClaudeClient(api_key="test_api_key")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_variations_success(self, claude_client):
        """Should generate multiple content variations."""
        prompt = "Create a tweet about AI innovation"
        count = 3
        
        with patch.object(claude_client, 'generate_content') as mock_generate:
            mock_generate.side_effect = [
                {'success': True, 'content': 'AI variation 1', 'usage': {'tokens': 10}},
                {'success': True, 'content': 'AI variation 2', 'usage': {'tokens': 12}},
                {'success': True, 'content': 'AI variation 3', 'usage': {'tokens': 11}}
            ]
            
            variations = await claude_client.generate_content_variations(prompt, count=count)
            
            assert len(variations) == count
            assert all('content' in v for v in variations)
            assert all('temperature' in v for v in variations)
            assert all('variation_id' in v for v in variations)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_variations_different_temperatures(self, claude_client):
        """Should use different temperatures for variation diversity."""
        prompt = "Create a tweet"
        count = 3
        
        with patch.object(claude_client, 'generate_content') as mock_generate:
            mock_generate.return_value = {'success': True, 'content': 'test', 'usage': {}}
            
            variations = await claude_client.generate_content_variations(prompt, count=count)
            
            temperatures = [v['temperature'] for v in variations]
            assert len(set(temperatures)) == count  # All temperatures should be different
            assert all(0.3 <= temp <= 1.0 for temp in temperatures)  # Reasonable range
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_variations_handles_failures(self, claude_client):
        """Should handle partial failures in variation generation."""
        prompt = "Create a tweet"
        count = 3
        
        with patch.object(claude_client, 'generate_content') as mock_generate:
            mock_generate.side_effect = [
                {'success': True, 'content': 'variation 1', 'usage': {}},
                {'success': False, 'error': 'rate_limit'},
                {'success': True, 'content': 'variation 3', 'usage': {}}
            ]
            
            variations = await claude_client.generate_content_variations(prompt, count=count)
            
            # Should only return successful variations
            assert len(variations) == 2
            assert all(v['content'] in ['variation 1', 'variation 3'] for v in variations)


class TestClaudeClientContentScoring:
    """Test content quality scoring functionality."""
    
    @pytest.fixture
    def claude_client(self):
        """Create Claude client for testing."""
        return ClaudeClient(api_key="test_api_key")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_content_quality_success(self, claude_client, sample_voice_profile):
        """Should score content quality against voice profile."""
        content = "Blockchain innovation is fascinating #web3"
        
        with patch.object(claude_client, 'generate_content') as mock_generate:
            mock_scores = {
                "voice_consistency": 0.8,
                "engagement_potential": 0.7,
                "authenticity": 0.9,
                "topic_relevance": 0.85,
                "overall_score": 0.8
            }
            mock_generate.return_value = {
                'success': True,
                'content': json.dumps(mock_scores)
            }
            
            result = await claude_client.score_content_quality(content, sample_voice_profile)
            
            assert result['success'] is True
            assert 'scores' in result
            assert all(key in result['scores'] for key in mock_scores.keys())
            assert 0 <= result['scores']['overall_score'] <= 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_content_quality_invalid_json(self, claude_client, sample_voice_profile):
        """Should handle invalid JSON response from scoring."""
        content = "Test content"
        
        with patch.object(claude_client, 'generate_content') as mock_generate:
            mock_generate.return_value = {
                'success': True,
                'content': 'Invalid JSON response'
            }
            
            result = await claude_client.score_content_quality(content, sample_voice_profile)
            
            assert result['success'] is False
            assert result['error'] == 'invalid_json'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_content_quality_generation_failure(self, claude_client, sample_voice_profile):
        """Should handle content generation failure during scoring."""
        content = "Test content"
        
        with patch.object(claude_client, 'generate_content') as mock_generate:
            mock_generate.return_value = {
                'success': False,
                'error': 'rate_limit'
            }
            
            result = await claude_client.score_content_quality(content, sample_voice_profile)
            
            assert result['success'] is False
            assert result['error'] == 'rate_limit'


class TestContentPrompts:
    """Test content prompt generation functionality."""
    
    @pytest.mark.unit
    def test_original_post_prompt(self, sample_voice_profile):
        """Should generate prompt for original post creation."""
        topic = "blockchain innovation"
        trending_context = "New consensus mechanism trending"
        
        prompt = ContentPrompts.original_post(topic, sample_voice_profile, trending_context)
        
        assert topic in prompt
        assert str(sample_voice_profile) in prompt
        assert trending_context in prompt
        assert "280 characters" in prompt
        assert "hashtags" in prompt.lower()
    
    @pytest.mark.unit
    def test_reply_to_mention_prompt(self, sample_voice_profile):
        """Should generate prompt for reply creation."""
        original_tweet = "What do you think about DeFi protocols?"
        context = "User asking about DeFi security"
        
        prompt = ContentPrompts.reply_to_mention(original_tweet, sample_voice_profile, context)
        
        assert original_tweet in prompt
        assert str(sample_voice_profile) in prompt
        assert context in prompt
        assert "280 characters" in prompt
        assert "conversational" in prompt.lower()
    
    @pytest.mark.unit
    def test_trend_response_prompt(self, sample_voice_profile):
        """Should generate prompt for trend response."""
        trend_name = "#blockchain"
        trend_context = "New blockchain protocol launch"
        
        prompt = ContentPrompts.trend_response(trend_name, trend_context, sample_voice_profile)
        
        assert trend_name in prompt
        assert trend_context in prompt
        assert str(sample_voice_profile) in prompt
        assert "trending" in prompt.lower()
        assert "relevant" in prompt.lower()
    
    @pytest.mark.unit
    def test_build_system_prompt_with_context(self, sample_voice_profile):
        """Should build system prompt with provided context."""
        context = {
            'voice_profile': sample_voice_profile,
            'topics': ['blockchain', 'AI', 'web3']
        }
        
        system_prompt = ContentPrompts._build_system_prompt(context)
        
        assert "social media" in system_prompt.lower()
        assert "Brand Voice:" in system_prompt
        assert "Key Topics:" in system_prompt
        assert all(topic in system_prompt for topic in context['topics'])
    
    @pytest.mark.unit
    def test_build_system_prompt_without_context(self):
        """Should build basic system prompt without context."""
        system_prompt = ContentPrompts._build_system_prompt(None)
        
        assert "social media" in system_prompt.lower()
        assert "authentic" in system_prompt.lower()
        assert "engaging" in system_prompt.lower()
        assert "Brand Voice:" not in system_prompt


class TestTokenUsageTracker:
    """Test token usage tracking functionality."""
    
    @pytest.mark.unit
    def test_token_tracker_initialization(self):
        """Token tracker should initialize with zero usage."""
        tracker = TokenUsageTracker()
        
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert len(tracker.usage_history) == 0
    
    @pytest.mark.unit
    def test_track_usage_records_tokens(self):
        """Should record token usage correctly."""
        tracker = TokenUsageTracker()
        usage = {'input_tokens': 20, 'output_tokens': 15}
        model = "claude-3-haiku-20240307"
        
        tracker.track_usage(usage, model)
        
        assert tracker.total_input_tokens == 20
        assert tracker.total_output_tokens == 15
        assert len(tracker.usage_history) == 1
        assert tracker.usage_history[0]['model'] == model
    
    @pytest.mark.unit
    def test_track_usage_accumulates_tokens(self):
        """Should accumulate token usage across multiple calls."""
        tracker = TokenUsageTracker()
        
        tracker.track_usage({'input_tokens': 20, 'output_tokens': 15}, "model1")
        tracker.track_usage({'input_tokens': 10, 'output_tokens': 8}, "model2")
        
        assert tracker.total_input_tokens == 30
        assert tracker.total_output_tokens == 23
        assert len(tracker.usage_history) == 2
    
    @pytest.mark.unit
    def test_get_usage_stats_calculates_correctly(self):
        """Should calculate usage statistics correctly."""
        tracker = TokenUsageTracker()
        
        tracker.track_usage({'input_tokens': 20, 'output_tokens': 15}, "model1")
        tracker.track_usage({'input_tokens': 10, 'output_tokens': 8}, "model1")
        
        stats = tracker.get_usage_stats()
        
        assert stats['total_tokens'] == 53  # 20+15+10+8
        assert stats['total_requests'] == 2
        assert stats['avg_tokens_per_request'] == 26.5
        assert 'model1' in stats['by_model']
    
    @pytest.mark.unit
    def test_estimate_cost_calculates_correctly(self):
        """Should estimate costs based on token usage."""
        tracker = TokenUsageTracker()
        
        tracker.track_usage({'input_tokens': 1000, 'output_tokens': 500}, "claude-3-haiku-20240307")
        
        cost = tracker.estimate_cost()
        
        assert cost > 0
        assert isinstance(cost, float)
    
    @pytest.mark.unit
    def test_reset_usage_clears_tracking(self):
        """Should reset all usage tracking."""
        tracker = TokenUsageTracker()
        
        tracker.track_usage({'input_tokens': 20, 'output_tokens': 15}, "model1")
        tracker.reset_usage()
        
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert len(tracker.usage_history) == 0


class TestClaudeClientIntegration:
    """Integration tests for Claude client functionality."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_content_generation_pipeline(self, sample_voice_profile):
        """Should handle complete content generation pipeline."""
        client = ClaudeClient(api_key="test_key")
        
        with patch.object(client.client, 'messages') as mock_messages:
            mock_messages.create.return_value = MagicMock(
                content=[MagicMock(text="Generated tweet content #blockchain")],
                usage=MagicMock(input_tokens=25, output_tokens=12)
            )
            
            # Generate content
            result = await client.generate_content(
                "Create a tweet about blockchain",
                context={'voice_profile': sample_voice_profile}
            )
            
            assert result['success'] is True
            assert len(result['content']) <= 280  # Twitter limit
            assert '#' in result['content']  # Should include hashtags
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_content_scoring_integration(self, sample_voice_profile):
        """Should integrate content generation with quality scoring."""
        client = ClaudeClient(api_key="test_key")
        content = "Blockchain innovation is reshaping finance #web3"
        
        with patch.object(client, 'generate_content') as mock_generate:
            mock_scores = {
                "voice_consistency": 0.85,
                "engagement_potential": 0.75,
                "authenticity": 0.9,
                "topic_relevance": 0.8,
                "overall_score": 0.825
            }
            mock_generate.return_value = {
                'success': True,
                'content': json.dumps(mock_scores)
            }
            
            result = await client.score_content_quality(content, sample_voice_profile)
            
            assert result['success'] is True
            assert result['scores']['overall_score'] > 0.8  # High quality content
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rate_limit_handling_with_retry(self):
        """Should handle rate limits with proper retry logic."""
        client = ClaudeClient(api_key="test_key")
        
        with patch.object(client.client, 'messages') as mock_messages:
            # Simulate rate limit followed by success
            mock_messages.create.side_effect = [
                anthropic.RateLimitError(message="Rate limited", response=MagicMock(), body={}),
                MagicMock(
                    content=[MagicMock(text="Success after retry")],
                    usage=MagicMock(input_tokens=20, output_tokens=10)
                )
            ]
            
            result = await client.generate_content_with_retry("Test prompt")
            
            assert result['success'] is True
            assert result['content'] == "Success after retry"
            assert mock_messages.create.call_count == 2