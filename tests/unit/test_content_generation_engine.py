"""
TDD Tests for Content Generation Engine

These tests define the expected behavior of our content generation system before implementation.
All tests should FAIL initially until we implement the actual ContentGenerationEngine class.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from enum import Enum

# Import will fail initially - this is expected in TDD
try:
    from src.bot.content.generation_engine import (
        ContentGenerationEngine, ContentType, ContentTemplate, 
        ContentPipeline, ContentQualityFilter
    )
except ImportError:
    # Expected to fail initially in TDD
    pass


class TestContentType:
    """Test ContentType enum functionality."""
    
    @pytest.mark.unit
    def test_content_type_enum_exists(self):
        """ContentType enum should define all content types."""
        # Test will fail until we implement ContentType enum
        assert ContentType.ORIGINAL == "original"
        assert ContentType.TREND_RESPONSE == "trend_response"
        assert ContentType.ENGAGEMENT == "engagement"
        assert ContentType.EDUCATIONAL == "educational"
        assert ContentType.OPINION == "opinion"
        assert ContentType.COMMUNITY == "community"
        assert ContentType.SUPPORT == "support"
    
    @pytest.mark.unit
    def test_content_type_enum_completeness(self):
        """ContentType enum should have all required content types."""
        expected_types = {
            "original", "trend_response", "engagement", "educational",
            "opinion", "community", "support"
        }
        
        actual_types = {ct.value for ct in ContentType}
        assert actual_types == expected_types


class TestContentTemplate:
    """Test ContentTemplate data structure."""
    
    @pytest.mark.unit
    def test_content_template_initialization(self):
        """ContentTemplate should initialize with required fields."""
        template = ContentTemplate(
            type=ContentType.ORIGINAL,
            topic_areas=["blockchain", "web3"],
            prompt_template="Create content about {topic}",
            max_length=280,
            hashtag_count=(1, 3),
            engagement_hooks=["What do you think?"],
            posting_schedule={"optimal_times": ["12:00", "18:00"]}
        )
        
        assert template.type == ContentType.ORIGINAL
        assert template.topic_areas == ["blockchain", "web3"]
        assert template.prompt_template == "Create content about {topic}"
        assert template.max_length == 280
        assert template.hashtag_count == (1, 3)
        assert template.engagement_hooks == ["What do you think?"]
        assert template.posting_schedule == {"optimal_times": ["12:00", "18:00"]}
    
    @pytest.mark.unit
    def test_content_template_defaults(self):
        """ContentTemplate should set reasonable defaults."""
        template = ContentTemplate(
            type=ContentType.ORIGINAL,
            topic_areas=["test"],
            prompt_template="test prompt"
        )
        
        assert template.max_length == 280  # Twitter default
        assert template.hashtag_count == (1, 3)  # Reasonable default
        assert template.engagement_hooks == []
        assert template.posting_schedule is None
    
    @pytest.mark.unit
    def test_content_template_validation(self):
        """ContentTemplate should validate input parameters."""
        # Invalid hashtag count
        with pytest.raises(ValueError):
            ContentTemplate(
                type=ContentType.ORIGINAL,
                topic_areas=["test"],
                prompt_template="test",
                hashtag_count=(5, 2)  # min > max
            )
        
        # Invalid max_length
        with pytest.raises(ValueError):
            ContentTemplate(
                type=ContentType.ORIGINAL,
                topic_areas=["test"],
                prompt_template="test",
                max_length=0  # Invalid length
            )


class TestContentGenerationEngine:
    """Test ContentGenerationEngine core functionality."""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Mock Claude client for testing."""
        mock_client = AsyncMock()
        mock_client.generate_content_variations.return_value = [
            {"content": "Variation 1", "temperature": 0.5, "variation_id": 1},
            {"content": "Variation 2", "temperature": 0.7, "variation_id": 2},
            {"content": "Variation 3", "temperature": 0.9, "variation_id": 3}
        ]
        mock_client.score_content_quality.return_value = {
            "success": True,
            "scores": {"overall_score": 0.8}
        }
        return mock_client
    
    @pytest.fixture
    def content_templates(self):
        """Sample content templates for testing."""
        return {
            ContentType.ORIGINAL: {
                "web3": ContentTemplate(
                    type=ContentType.ORIGINAL,
                    topic_areas=["blockchain", "web3", "DeFi"],
                    prompt_template="Create original insight about {topic}",
                    engagement_hooks=["What do you think?", "Thoughts?"]
                )
            },
            ContentType.TREND_RESPONSE: {
                "quick": ContentTemplate(
                    type=ContentType.TREND_RESPONSE,
                    topic_areas=["trending"],
                    prompt_template="Respond to trending topic {trend}",
                    max_length=280
                )
            }
        }
    
    @pytest.fixture
    def content_engine(self, mock_claude_client, content_templates, sample_voice_profile):
        """Create ContentGenerationEngine for testing."""
        return ContentGenerationEngine(
            claude_client=mock_claude_client,
            templates=content_templates,
            voice_profile=sample_voice_profile
        )
    
    @pytest.mark.unit
    def test_content_engine_initialization(self, mock_claude_client, content_templates, sample_voice_profile):
        """ContentGenerationEngine should initialize with required components."""
        engine = ContentGenerationEngine(
            claude_client=mock_claude_client,
            templates=content_templates,
            voice_profile=sample_voice_profile
        )
        
        assert engine.claude_client == mock_claude_client
        assert engine.templates == content_templates
        assert engine.voice_profile == sample_voice_profile
        assert hasattr(engine, 'quality_filter')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_engine):
        """Should successfully generate content for specified type and topic."""
        content_type = ContentType.ORIGINAL
        topic = "blockchain innovation"
        
        result = await content_engine.generate_content(content_type, topic)
        
        assert result['success'] is True
        assert 'content' in result
        assert 'all_variations' in result
        assert 'template_used' in result
        assert result['content']['content'] in ["Variation 1", "Variation 2", "Variation 3"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_with_context(self, content_engine):
        """Should generate content using provided context."""
        content_type = ContentType.TREND_RESPONSE
        topic = "blockchain"
        context = {
            "trending_info": "New blockchain protocol trending",
            "community_mood": "excited"
        }
        
        result = await content_engine.generate_content(content_type, topic, context)
        
        assert result['success'] is True
        # Should pass context to Claude client
        content_engine.claude_client.generate_content_variations.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_no_template_found(self, content_engine):
        """Should handle case when no template is found for content type."""
        content_type = ContentType.EDUCATIONAL  # Not in our test templates
        topic = "blockchain"
        
        result = await content_engine.generate_content(content_type, topic)
        
        assert result['success'] is False
        assert result['error'] == 'no_template_found'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_claude_failure(self, content_engine):
        """Should handle Claude API generation failure."""
        content_engine.claude_client.generate_content_variations.return_value = []
        
        result = await content_engine.generate_content(ContentType.ORIGINAL, "blockchain")
        
        assert result['success'] is False
        assert result['error'] == 'no_valid_content_generated'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_quality_filtering(self, content_engine):
        """Should filter content based on quality scores."""
        # Mock one high-quality and one low-quality variation
        content_engine.claude_client.generate_content_variations.return_value = [
            {"content": "High quality", "temperature": 0.5, "variation_id": 1},
            {"content": "Low quality", "temperature": 0.7, "variation_id": 2}
        ]
        content_engine.claude_client.score_content_quality.side_effect = [
            {"success": True, "scores": {"overall_score": 0.9}},  # High quality
            {"success": True, "scores": {"overall_score": 0.3}}   # Low quality
        ]
        
        result = await content_engine.generate_content(ContentType.ORIGINAL, "blockchain")
        
        assert result['success'] is True
        assert result['content']['content'] == "High quality"  # Should select best
    
    @pytest.mark.unit
    def test_get_template_for_content_type(self, content_engine):
        """Should retrieve appropriate template for content type and topic."""
        template = content_engine._get_template(ContentType.ORIGINAL, "blockchain")
        
        assert template is not None
        assert template.type == ContentType.ORIGINAL
        assert "blockchain" in template.topic_areas
    
    @pytest.mark.unit
    def test_get_template_topic_matching(self, content_engine):
        """Should match topics to appropriate templates."""
        # Should find web3 template for blockchain topic
        template = content_engine._get_template(ContentType.ORIGINAL, "DeFi")
        assert template is not None
        
        # Should not find template for unrelated topic
        template = content_engine._get_template(ContentType.ORIGINAL, "cooking")
        assert template is None
    
    @pytest.mark.unit
    def test_build_content_prompt(self, content_engine, content_templates):
        """Should build comprehensive prompt from template and context."""
        template = content_templates[ContentType.ORIGINAL]["web3"]
        topic = "blockchain innovation"
        context = {"trending_info": "New consensus mechanism"}
        
        prompt = content_engine._build_content_prompt(template, topic, context)
        
        assert topic in prompt
        assert "blockchain innovation" in prompt
        assert "New consensus mechanism" in prompt
        assert str(content_engine.voice_profile) in prompt
        assert "280 characters" in prompt
        assert "hashtags" in prompt.lower()


class TestContentPipeline:
    """Test ContentPipeline orchestration functionality."""
    
    @pytest.fixture
    def mock_x_client(self):
        """Mock X API client for testing."""
        mock_client = AsyncMock()
        mock_client.post_tweet.return_value = {
            "success": True,
            "tweet_id": "1234567890"
        }
        return mock_client
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter for testing."""
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit.return_value = True
        return mock_limiter
    
    @pytest.fixture
    def content_pipeline(self, mock_x_client, mock_claude_client, mock_rate_limiter):
        """Create ContentPipeline for testing."""
        return ContentPipeline(
            x_client=mock_x_client,
            claude_client=mock_claude_client,
            rate_limiter=mock_rate_limiter
        )
    
    @pytest.mark.unit
    def test_content_pipeline_initialization(self, mock_x_client, mock_claude_client, mock_rate_limiter):
        """ContentPipeline should initialize with required clients."""
        pipeline = ContentPipeline(
            x_client=mock_x_client,
            claude_client=mock_claude_client,
            rate_limiter=mock_rate_limiter
        )
        
        assert pipeline.x_client == mock_x_client
        assert pipeline.claude_client == mock_claude_client
        assert pipeline.rate_limiter == mock_rate_limiter
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_and_post_success(self, content_pipeline, sample_voice_profile):
        """Should successfully create and post content."""
        content_type = "original"
        topic = "blockchain"
        
        # Mock content generation
        content_pipeline.claude_client.generate_content_variations.return_value = [
            {"content": "Great blockchain insight #web3", "temperature": 0.7, "variation_id": 1}
        ]
        content_pipeline.claude_client.score_content_quality.return_value = {
            "success": True,
            "scores": {"overall_score": 0.8}
        }
        
        result = await content_pipeline.create_and_post(
            content_type=content_type,
            topic=topic,
            voice_profile=sample_voice_profile,
            auto_post=True
        )
        
        assert result['success'] is True
        assert result['posted'] is True
        assert 'tweet_id' in result
        assert result['content']['scores']['overall_score'] == 0.8
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_and_post_low_quality_no_auto_post(self, content_pipeline, sample_voice_profile):
        """Should not auto-post low quality content."""
        content_type = "original"
        topic = "blockchain"
        
        # Mock low-quality content generation
        content_pipeline.claude_client.generate_content_variations.return_value = [
            {"content": "Poor quality content", "temperature": 0.5, "variation_id": 1}
        ]
        content_pipeline.claude_client.score_content_quality.return_value = {
            "success": True,
            "scores": {"overall_score": 0.5}  # Below threshold
        }
        
        result = await content_pipeline.create_and_post(
            content_type=content_type,
            topic=topic,
            voice_profile=sample_voice_profile,
            auto_post=True
        )
        
        assert result['success'] is True
        assert result['posted'] is False  # Should not post low quality
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_and_post_rate_limited(self, content_pipeline, sample_voice_profile):
        """Should handle rate limiting gracefully."""
        content_type = "original"
        topic = "blockchain"
        
        # Mock rate limit hit
        content_pipeline.rate_limiter.check_rate_limit.return_value = False
        
        # Mock high-quality content
        content_pipeline.claude_client.generate_content_variations.return_value = [
            {"content": "High quality content #blockchain", "temperature": 0.7, "variation_id": 1}
        ]
        content_pipeline.claude_client.score_content_quality.return_value = {
            "success": True,
            "scores": {"overall_score": 0.9}
        }
        
        result = await content_pipeline.create_and_post(
            content_type=content_type,
            topic=topic,
            voice_profile=sample_voice_profile,
            auto_post=True
        )
        
        assert result['success'] is True
        assert result['posted'] is False  # Should not post due to rate limit
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_and_post_trend_response(self, content_pipeline, sample_voice_profile):
        """Should handle trend response content type."""
        content_type = "trend_response"
        topic = "#blockchain"
        
        # Mock trending topics
        content_pipeline.x_client.get_trending_topics.return_value = [
            {"name": "#blockchain", "volume": 15000, "context": "New protocol launch"}
        ]
        
        result = await content_pipeline.create_and_post(
            content_type=content_type,
            topic=topic,
            voice_profile=sample_voice_profile,
            auto_post=False
        )
        
        assert result['success'] is True
        # Should call trending topics
        content_pipeline.x_client.get_trending_topics.assert_called_once()


class TestContentQualityFilter:
    """Test content quality filtering functionality."""
    
    @pytest.mark.unit
    def test_quality_filter_initialization(self):
        """ContentQualityFilter should initialize with thresholds."""
        quality_filter = ContentQualityFilter(
            min_overall_score=0.7,
            min_voice_consistency=0.8,
            min_engagement_potential=0.6
        )
        
        assert quality_filter.min_overall_score == 0.7
        assert quality_filter.min_voice_consistency == 0.8
        assert quality_filter.min_engagement_potential == 0.6
    
    @pytest.mark.unit
    def test_meets_quality_standards_success(self):
        """Should pass content that meets quality standards."""
        quality_filter = ContentQualityFilter()
        
        scores = {
            "overall_score": 0.8,
            "voice_consistency": 0.9,
            "engagement_potential": 0.7,
            "authenticity": 0.85,
            "topic_relevance": 0.8
        }
        
        result = quality_filter.meets_quality_standards(scores)
        
        assert result is True
    
    @pytest.mark.unit
    def test_meets_quality_standards_failure(self):
        """Should reject content that doesn't meet quality standards."""
        quality_filter = ContentQualityFilter()
        
        scores = {
            "overall_score": 0.5,  # Below threshold
            "voice_consistency": 0.6,
            "engagement_potential": 0.4,
            "authenticity": 0.7,
            "topic_relevance": 0.5
        }
        
        result = quality_filter.meets_quality_standards(scores)
        
        assert result is False
    
    @pytest.mark.unit
    def test_get_quality_feedback(self):
        """Should provide feedback on quality improvements needed."""
        quality_filter = ContentQualityFilter()
        
        scores = {
            "overall_score": 0.6,
            "voice_consistency": 0.5,  # Low
            "engagement_potential": 0.4,  # Low
            "authenticity": 0.8,  # Good
            "topic_relevance": 0.7   # Good
        }
        
        feedback = quality_filter.get_quality_feedback(scores)
        
        assert "voice_consistency" in feedback['improvements_needed']
        assert "engagement_potential" in feedback['improvements_needed']
        assert "authenticity" not in feedback['improvements_needed']
    
    @pytest.mark.unit
    def test_filter_content_variations(self):
        """Should filter content variations based on quality."""
        quality_filter = ContentQualityFilter(min_overall_score=0.7)
        
        variations = [
            {"content": "High quality", "scores": {"overall_score": 0.9}},
            {"content": "Medium quality", "scores": {"overall_score": 0.6}},
            {"content": "Another high quality", "scores": {"overall_score": 0.8}}
        ]
        
        filtered = quality_filter.filter_content_variations(variations)
        
        assert len(filtered) == 2  # Should keep only high quality
        assert all(v['scores']['overall_score'] >= 0.7 for v in filtered)


class TestContentGenerationIntegration:
    """Integration tests for content generation system."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_content_generation(self, sample_voice_profile, sample_topics_config):
        """Should handle complete content generation workflow."""
        # This test will verify the entire pipeline works together
        mock_claude = AsyncMock()
        mock_x = AsyncMock()
        mock_rate_limiter = AsyncMock()
        
        # Mock successful content generation
        mock_claude.generate_content_variations.return_value = [
            {"content": "Blockchain innovation is reshaping finance #web3", "temperature": 0.7, "variation_id": 1}
        ]
        mock_claude.score_content_quality.return_value = {
            "success": True,
            "scores": {
                "overall_score": 0.85,
                "voice_consistency": 0.9,
                "engagement_potential": 0.8,
                "authenticity": 0.85,
                "topic_relevance": 0.9
            }
        }
        mock_x.post_tweet.return_value = {"success": True, "tweet_id": "1234567890"}
        mock_rate_limiter.check_rate_limit.return_value = True
        
        # Create pipeline
        pipeline = ContentPipeline(
            x_client=mock_x,
            claude_client=mock_claude, 
            rate_limiter=mock_rate_limiter
        )
        
        # Execute full pipeline
        result = await pipeline.create_and_post(
            content_type="original",
            topic="blockchain innovation",
            voice_profile=sample_voice_profile,
            auto_post=True
        )
        
        # Verify complete workflow
        assert result['success'] is True
        assert result['posted'] is True
        assert result['tweet_id'] == "1234567890"
        assert result['content']['scores']['overall_score'] >= 0.8
        
        # Verify all components were called
        mock_claude.generate_content_variations.assert_called_once()
        mock_claude.score_content_quality.assert_called_once()
        mock_x.post_tweet.assert_called_once()
        mock_rate_limiter.check_rate_limit.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_content_generation_with_real_constraints(self):
        """Should handle real-world constraints and edge cases."""
        # Test character limits, hashtag requirements, etc.
        mock_claude = AsyncMock()
        
        # Mock content that's too long
        long_content = "x" * 300  # Exceeds Twitter limit
        mock_claude.generate_content_variations.return_value = [
            {"content": long_content, "temperature": 0.7, "variation_id": 1}
        ]
        
        engine = ContentGenerationEngine(
            claude_client=mock_claude,
            templates={},
            voice_profile={}
        )
        
        # Should handle length validation
        result = await engine.generate_content(ContentType.ORIGINAL, "test")
        
        # Implementation should handle this gracefully
        assert 'success' in result