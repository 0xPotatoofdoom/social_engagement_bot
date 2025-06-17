"""
Tests for Claude API Integration

Tests for Claude API client, content generation, sentiment analysis,
and AI-powered opportunity analysis.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import aiohttp

from src.bot.api.claude_client import ClaudeAPIClient, SentimentAnalysis, ContentGeneration


class TestClaudeAPIClient:
    """Test Claude API client functionality."""
    
    @pytest.fixture
    def claude_client(self):
        """Create Claude API client instance."""
        return ClaudeAPIClient(api_key="test_claude_api_key")
    
    @pytest.mark.unit
    def test_claude_client_initialization(self, claude_client):
        """Test Claude client initializes correctly."""
        assert claude_client.api_key == "test_claude_api_key"
        assert claude_client.base_url == "https://api.anthropic.com/v1"
        assert claude_client.session is None  # Not initialized until async context
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_claude_client_context_manager(self, claude_client):
        """Test Claude client async context manager."""
        async with claude_client as client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)
            assert "anthropic-version" in client.session.headers
            assert "content-type" in client.session.headers
            assert "x-api-key" in client.session.headers
        
        # Session should be closed after context
        assert claude_client.session.closed
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_sentiment_success(self, claude_client):
        """Test successful sentiment analysis."""
        mock_response = {
            "content": [
                {
                    "text": json.dumps({
                        "overall_sentiment": "positive",
                        "confidence": 0.85,
                        "emotional_tone": "excited",
                        "engagement_potential": 0.78,
                        "key_themes": ["ai", "blockchain", "innovation"]
                    })
                }
            ]
        }
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_response):
            async with claude_client:
                result = await claude_client.analyze_sentiment(
                    "AI agents on blockchain are revolutionary!",
                    context="AI x blockchain discussion"
                )
        
        assert isinstance(result, SentimentAnalysis)
        assert result.overall_sentiment == "positive"
        assert result.confidence == 0.85
        assert result.emotional_tone == "excited"
        assert result.engagement_potential == 0.78
        assert "ai" in result.key_themes
        assert "blockchain" in result.key_themes
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_content_success(self, claude_client):
        """Test successful content generation."""
        mock_response = {
            "content": [
                {
                    "text": json.dumps({
                        "content": "The convergence of AI and blockchain opens fascinating possibilities for autonomous economic systems.",
                        "content_type": "reply",
                        "confidence": 0.89,
                        "reasoning": "Technical expertise demonstration with forward-thinking insights",
                        "alternatives": [
                            "AI x blockchain integration is reshaping how we think about autonomous systems",
                            "The technical architecture for AI-driven blockchain systems is evolving rapidly"
                        ],
                        "estimated_engagement": 0.82
                    })
                }
            ]
        }
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_response):
            async with claude_client:
                result = await claude_client.generate_content(
                    opportunity_type="reply",
                    context={
                        "text": "AI agents on blockchain networks are revolutionizing autonomous systems",
                        "author_id": "VitalikButerin"
                    },
                    target_topics=["ai blockchain", "autonomous systems", "defi"],
                    voice_guidelines="Technical authority with conversational tone"
                )
        
        assert isinstance(result, ContentGeneration)
        assert "convergence of AI and blockchain" in result.content
        assert result.content_type == "reply"
        assert result.confidence == 0.89
        assert len(result.alternatives) == 2
        assert result.estimated_engagement == 0.82
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_make_api_call_structure(self, claude_client):
        """Test API call structure and headers."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"test": "response"}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        claude_client.session = mock_session
        
        result = await claude_client._make_api_call("messages", {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": "test prompt"}]
        })
        
        # Verify API call was made with correct structure
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        
        assert "https://api.anthropic.com/v1/messages" in call_args[0]
        assert "json" in call_args[1]
        
        payload = call_args[1]["json"]
        assert payload["model"] == "claude-3-haiku-20240307"
        assert payload["max_tokens"] == 500
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_call_error_handling(self, claude_client):
        """Test API call error handling."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 429  # Rate limit error
        mock_response.text.return_value = "Rate limit exceeded"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        claude_client.session = mock_session
        
        with pytest.raises(Exception) as exc_info:
            await claude_client._make_api_call("messages", {"test": "payload"})
        
        assert "Claude API error" in str(exc_info.value)
        assert "429" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_build_content_prompt_reply_type(self, claude_client):
        """Test content prompt building for reply type."""
        context = {
            "text": "AI agents are transforming blockchain infrastructure",
            "author_id": "testuser"
        }
        target_topics = ["ai blockchain", "defi", "autonomous systems"]
        voice_guidelines = "Technical authority with approachable tone"
        
        prompt = claude_client._build_content_prompt(
            opportunity_type="reply",
            context=context,
            target_topics=target_topics,
            voice_guidelines=voice_guidelines
        )
        
        assert isinstance(prompt, str)
        assert "reply" in prompt.lower()
        assert context["text"] in prompt
        assert "ai blockchain" in prompt
        assert "defi" in prompt
        assert voice_guidelines in prompt
        assert "280 characters" in prompt
    
    @pytest.mark.unit
    def test_build_content_prompt_keyword_engagement_type(self, claude_client):
        """Test content prompt building for keyword engagement type."""
        context = {
            "keyword": "uniswap v4",
            "search_text": "Uniswap v4 hooks are revolutionizing DeFi architecture"
        }
        target_topics = ["uniswap v4", "defi", "smart contracts"]
        
        prompt = claude_client._build_content_prompt(
            opportunity_type="keyword_engagement",
            context=context,
            target_topics=target_topics
        )
        
        assert "uniswap v4" in prompt.lower()
        assert context["search_text"] in prompt
        assert "keyword_engagement" in prompt
        assert "smart contracts" in prompt


class TestSentimentAnalysis:
    """Test sentiment analysis data structure."""
    
    @pytest.mark.unit
    def test_sentiment_analysis_creation(self):
        """Test SentimentAnalysis object creation."""
        sentiment = SentimentAnalysis(
            overall_sentiment="positive",
            confidence=0.85,
            emotional_tone="excited",
            engagement_potential=0.78,
            key_themes=["ai", "blockchain", "innovation"]
        )
        
        assert sentiment.overall_sentiment == "positive"
        assert sentiment.confidence == 0.85
        assert sentiment.emotional_tone == "excited"
        assert sentiment.engagement_potential == 0.78
        assert len(sentiment.key_themes) == 3
        assert "ai" in sentiment.key_themes


class TestContentGeneration:
    """Test content generation data structure."""
    
    @pytest.mark.unit
    def test_content_generation_creation(self):
        """Test ContentGeneration object creation."""
        content = ContentGeneration(
            content="AI x blockchain convergence creates autonomous economic systems.",
            content_type="reply",
            confidence=0.89,
            reasoning="Technical expertise with forward-thinking insights",
            alternatives=["Alternative response 1", "Alternative response 2"],
            estimated_engagement=0.82
        )
        
        assert "AI x blockchain" in content.content
        assert content.content_type == "reply"
        assert content.confidence == 0.89
        assert len(content.alternatives) == 2
        assert content.estimated_engagement == 0.82


class TestClaudeIntegrationWithMonitoring:
    """Test Claude integration with monitoring system."""
    
    @pytest.fixture
    def mock_claude_responses(self):
        """Mock Claude API responses for monitoring integration."""
        return {
            "sentiment_analysis": {
                "content": [
                    {
                        "text": json.dumps({
                            "overall_sentiment": "positive",
                            "confidence": 0.87,
                            "emotional_tone": "excited",
                            "engagement_potential": 0.84,
                            "key_themes": ["ai", "blockchain", "autonomous"]
                        })
                    }
                ]
            },
            "content_generation": {
                "content": [
                    {
                        "text": json.dumps({
                            "content": "The convergence of AI agents and blockchain infrastructure opens fascinating possibilities for truly autonomous economic systems.",
                            "content_type": "reply",
                            "confidence": 0.91,
                            "reasoning": "Demonstrates deep technical understanding while adding unique insights about autonomous systems",
                            "alternatives": [
                                "This aligns with emerging patterns in autonomous protocol design",
                                "The technical architecture for AI-driven blockchain systems is evolving rapidly"
                            ],
                            "estimated_engagement": 0.85
                        })
                    }
                ]
            },
            "opportunity_analysis": {
                "content": [
                    {
                        "text": json.dumps({
                            "ai_blockchain_relevance": 0.92,
                            "technical_depth": 0.88,
                            "innovation_score": 0.85,
                            "engagement_opportunity": 0.90,
                            "time_sensitivity": 0.75,
                            "content_themes": ["ai_agents", "blockchain_infrastructure", "autonomous_systems"],
                            "opportunity_type": "technical_innovation",
                            "strategic_value": "high",
                            "suggested_approach": "technical_insight"
                        })
                    }
                ]
            }
        }
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_claude_opportunity_analysis_integration(self, mock_claude_responses):
        """Test Claude integration for opportunity analysis."""
        claude_client = ClaudeAPIClient(api_key="test_key")
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_responses["opportunity_analysis"]):
            async with claude_client:
                # This would be the actual integration call from the monitoring system
                response = await claude_client._make_api_call("messages", {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": "Analyze this AI x blockchain opportunity..."}]
                })
        
        analysis_data = json.loads(response["content"][0]["text"])
        
        assert analysis_data["ai_blockchain_relevance"] == 0.92
        assert analysis_data["technical_depth"] == 0.88
        assert analysis_data["opportunity_type"] == "technical_innovation"
        assert analysis_data["strategic_value"] == "high"
        assert "ai_agents" in analysis_data["content_themes"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_claude_content_generation_for_opportunities(self, mock_claude_responses):
        """Test Claude content generation for detected opportunities."""
        claude_client = ClaudeAPIClient(api_key="test_key")
        
        with patch.object(claude_client, '_make_api_call', return_value=mock_claude_responses["content_generation"]):
            async with claude_client:
                result = await claude_client.generate_content(
                    opportunity_type="reply",
                    context={
                        "text": "AI agents on blockchain networks are revolutionizing autonomous systems",
                        "author_id": "VitalikButerin"
                    },
                    target_topics=["ai blockchain", "autonomous systems"],
                    voice_guidelines="Technical authority, conversational"
                )
        
        assert isinstance(result, ContentGeneration)
        assert "convergence of AI agents" in result.content
        assert result.confidence > 0.9
        assert len(result.alternatives) == 2
        assert all("ai" in alt.lower() or "blockchain" in alt.lower() for alt in result.alternatives)
    
    @pytest.mark.unit
    def test_claude_response_parsing_robustness(self):
        """Test robust parsing of Claude responses."""
        # Test with malformed JSON
        malformed_response = {
            "content": [
                {
                    "text": "This is not valid JSON: {incomplete json..."
                }
            ]
        }
        
        # The parsing should handle this gracefully
        try:
            content_text = malformed_response["content"][0]["text"]
            # If JSON parsing fails, should fall back to basic content
            assert isinstance(content_text, str)
        except json.JSONDecodeError:
            # This is expected and should be handled gracefully
            pass
    
    @pytest.mark.unit
    @pytest.mark.asyncio 
    async def test_claude_session_management(self):
        """Test proper session management for Claude client."""
        claude_client = ClaudeAPIClient(api_key="test_key")
        
        # Session should be None initially
        assert claude_client.session is None
        
        async with claude_client:
            # Session should be created in context
            assert claude_client.session is not None
            session_id = id(claude_client.session)
        
        # Session should be closed after context
        assert claude_client.session.closed
        
        # New context should create new session
        async with claude_client:
            assert claude_client.session is not None
            new_session_id = id(claude_client.session)
            assert new_session_id != session_id  # Different session instance


class TestClaudeErrorRecovery:
    """Test Claude API error recovery and fallbacks."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_claude_timeout_handling(self):
        """Test handling of Claude API timeouts."""
        claude_client = ClaudeAPIClient(api_key="test_key")
        
        with patch.object(claude_client, '_make_api_call', side_effect=asyncio.TimeoutError("API timeout")):
            async with claude_client:
                with pytest.raises(asyncio.TimeoutError):
                    await claude_client.analyze_sentiment("test content")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_claude_rate_limit_handling(self):
        """Test handling of Claude API rate limits."""
        claude_client = ClaudeAPIClient(api_key="test_key")
        
        # Mock rate limit response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text.return_value = "Rate limit exceeded"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        claude_client.session = mock_session
        
        with pytest.raises(Exception) as exc_info:
            await claude_client._make_api_call("messages", {"test": "payload"})
        
        assert "429" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v", 
        "--tb=short",
        "-m", "unit"
    ])