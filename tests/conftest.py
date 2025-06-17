"""Test configuration and fixtures for the X engagement bot."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

# Test fixtures for common data structures


@pytest.fixture
def sample_tweet_data():
    """Sample tweet data for testing."""
    return {
        "id": "1234567890",
        "text": "This is a sample tweet about web3 innovation #blockchain",
        "author": {
            "id": "author123",
            "username": "testuser",
            "name": "Test User"
        },
        "created_at": "2024-01-01T12:00:00Z",
        "public_metrics": {
            "retweet_count": 5,
            "like_count": 15,
            "reply_count": 3,
            "quote_count": 1
        },
        "context_annotations": [
            {
                "domain": {"name": "Technology"},
                "entity": {"name": "Blockchain"}
            }
        ]
    }


@pytest.fixture
def sample_voice_profile():
    """Sample voice profile configuration."""
    return {
        "core_personality": {
            "primary_traits": [
                "knowledgeable_but_approachable",
                "forward_thinking",
                "community_focused"
            ],
            "secondary_traits": [
                "slightly_contrarian",
                "data_driven"
            ]
        },
        "communication_style": {
            "tone": "conversational_expert",
            "formality": "informal_professional",
            "humor": "dry_wit_occasional",
            "confidence": "quietly_confident"
        },
        "vocabulary_preferences": {
            "preferred_words": ["actually", "honestly", "fascinating", "building", "community"],
            "avoided_words": ["leverage", "synergy", "disrupt", "game-changer"]
        }
    }


@pytest.fixture
def sample_topics_config():
    """Sample topics configuration."""
    return {
        "primary_topics": {
            "web3_innovation": {
                "keywords": ["blockchain", "DeFi", "NFT", "crypto", "smart contracts"],
                "hashtags": ["#web3", "#blockchain", "#DeFi"],
                "relevance_weight": 0.9,
                "content_types": ["original", "trend_response"]
            },
            "tech_trends": {
                "keywords": ["AI", "machine learning", "automation"],
                "hashtags": ["#AI", "#tech", "#innovation"],
                "relevance_weight": 0.8,
                "content_types": ["original", "opinion"]
            }
        },
        "trending_response_rules": {
            "web3_innovation": {
                "min_tweet_volume": 10000,
                "relevance_threshold": 0.7,
                "response_delay": "5-15 minutes"
            }
        }
    }


@pytest.fixture
def sample_trending_topics():
    """Sample trending topics data."""
    return [
        {
            "name": "#blockchain",
            "volume": 15000,
            "context": "New blockchain protocol launches with innovative consensus mechanism"
        },
        {
            "name": "#AI",
            "volume": 25000,
            "context": "AI breakthrough in natural language processing"
        },
        {
            "name": "#unrelated",
            "volume": 50000,
            "context": "Celebrity gossip trending topic"
        }
    ]


@pytest.fixture
def mock_x_api_client():
    """Mock X API client for testing."""
    mock_client = AsyncMock()
    
    # Default successful responses
    mock_client.post_tweet.return_value = {
        "success": True,
        "tweet_id": "1234567890",
        "text": "Test tweet content"
    }
    
    mock_client.get_mentions.return_value = []
    mock_client.get_trending_topics.return_value = []
    mock_client.reply_to_tweet.return_value = {
        "success": True,
        "tweet_id": "reply123"
    }
    
    return mock_client


@pytest.fixture
def mock_claude_client():
    """Mock Claude API client for testing."""
    mock_client = AsyncMock()
    
    # Default successful content generation
    mock_client.generate_content.return_value = {
        "success": True,
        "content": "This is AI-generated content about the topic",
        "usage": {"tokens": 50},
        "model": "claude-3-haiku-20240307"
    }
    
    mock_client.generate_content_variations.return_value = [
        {
            "content": "Variation 1: AI-generated content",
            "temperature": 0.5,
            "variation_id": 1
        },
        {
            "content": "Variation 2: Different AI-generated content", 
            "temperature": 0.7,
            "variation_id": 2
        }
    ]
    
    mock_client.score_content_quality.return_value = {
        "success": True,
        "scores": {
            "voice_consistency": 0.8,
            "engagement_potential": 0.7,
            "authenticity": 0.9,
            "topic_relevance": 0.85,
            "overall_score": 0.8
        }
    }
    
    return mock_client


@pytest.fixture
def sample_engagement_metrics():
    """Sample engagement metrics for testing."""
    return {
        "engagement_rate": 0.05,  # 5%
        "reach": 1000,
        "likes": 15,
        "retweets": 5,
        "replies": 3,
        "clicks": 10,
        "profile_visits": 8
    }


@pytest.fixture
def sample_content_variations():
    """Sample content variations for A/B testing."""
    return [
        {
            "content": "The future of web3 is fascinating. What trends are you seeing? #blockchain",
            "voice_score": 0.85,
            "engagement_score": 0.7,
            "variation_id": 1
        },
        {
            "content": "Web3 innovation is accelerating. Thoughts on the latest developments? #crypto",
            "voice_score": 0.8,
            "engagement_score": 0.75,
            "variation_id": 2
        },
        {
            "content": "Honestly, the blockchain space is evolving faster than ever. Your take? #DeFi",
            "voice_score": 0.9,
            "engagement_score": 0.8,
            "variation_id": 3
        }
    ]


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    mock_db = MagicMock()
    
    # Mock common database operations
    mock_db.save_tweet.return_value = True
    mock_db.get_recent_posts.return_value = []
    mock_db.save_engagement_metrics.return_value = True
    mock_db.get_performance_data.return_value = []
    
    return mock_db


@pytest.fixture
def sample_rate_limit_status():
    """Sample rate limit status for testing."""
    return {
        "create_tweet": {
            "limit": 300,
            "remaining": 250,
            "reset_time": datetime.now() + timedelta(minutes=15)
        },
        "get_mentions": {
            "limit": 75,
            "remaining": 60,
            "reset_time": datetime.now() + timedelta(minutes=15)
        }
    }


# Async fixtures and utilities

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_mock_setup():
    """Setup for async mocks."""
    return {
        "setup_complete": True,
        "timestamp": datetime.now()
    }