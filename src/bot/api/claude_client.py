"""
Claude API Client Implementation

Production-ready client for Claude API with content generation,
sentiment analysis, and comprehensive logging.
"""

import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
import structlog
import aiohttp
from dataclasses import dataclass

# Configure structured logging
logger = structlog.get_logger(__name__)


@dataclass
class SentimentAnalysis:
    """Represents sentiment analysis results."""
    overall_sentiment: str  # 'positive', 'negative', 'neutral'
    confidence: float
    emotional_tone: str  # 'excited', 'frustrated', 'curious', etc.
    engagement_potential: float  # How likely this is to generate engagement
    key_themes: List[str]


@dataclass
class ContentGeneration:
    """Represents generated content with metadata."""
    content: str
    content_type: str  # 'reply', 'quote', 'original', 'thread'
    confidence: float
    reasoning: str
    alternatives: List[str]
    estimated_engagement: float


class ClaudeAPIClient:
    """
    Production Claude API client with comprehensive logging and error handling.
    
    This client will generate detailed logs for:
    1. Content generation performance and quality
    2. Sentiment analysis accuracy
    3. API usage and cost tracking
    4. Response times and error patterns
    """
    
    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("Claude API key is required")
        
        self.api_key = api_key.strip()
        self.base_url = "https://api.anthropic.com/v1"
        self.session = None
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_requests = 0
        self.total_cost = 0.0
        
        logger.info(
            "claude_client_initializing",
            api_key_length=len(self.api_key),
            timestamp=datetime.now().isoformat()
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.api_key
            }
        )
        logger.info("claude_client_session_created")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            logger.info("claude_client_session_closed")
    
    async def analyze_sentiment(self, text: str, context: str = None) -> SentimentAnalysis:
        """
        Analyze sentiment and engagement potential of text.
        
        This helps identify:
        - Whether a conversation has positive/negative sentiment
        - How emotionally charged the discussion is
        - Whether it's worth engaging (high engagement potential)
        - Key themes we could contribute to
        """
        start_time = time.time()
        
        logger.info(
            "sentiment_analysis_started",
            text_length=len(text),
            has_context=bool(context),
            timestamp=datetime.now().isoformat()
        )
        
        # Construct prompt for sentiment analysis
        prompt = f"""Analyze the sentiment and engagement potential of this social media post/conversation:

TEXT: "{text}"

{f'CONTEXT: {context}' if context else ''}

Please provide a JSON response with:
1. overall_sentiment: "positive", "negative", or "neutral"
2. confidence: 0.0 to 1.0 (how confident you are)
3. emotional_tone: describe the emotional tone (excited, frustrated, curious, etc.)
4. engagement_potential: 0.0 to 1.0 (how likely this is to generate engagement if responded to)
5. key_themes: array of main topics/themes being discussed

Focus on whether this represents a good opportunity for meaningful engagement."""
        
        try:
            response_data = await self._make_api_call("messages", {
                "model": "claude-3-haiku-20240307",  # Fast model for sentiment analysis
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response_time = time.time() - start_time
            
            # Parse the response
            content = response_data.get("content", [{}])[0].get("text", "")
            
            try:
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result_json = json.loads(content[json_start:json_end])
                else:
                    raise ValueError("No JSON found in response")
                
                sentiment = SentimentAnalysis(
                    overall_sentiment=result_json.get("overall_sentiment", "neutral"),
                    confidence=float(result_json.get("confidence", 0.5)),
                    emotional_tone=result_json.get("emotional_tone", "neutral"),
                    engagement_potential=float(result_json.get("engagement_potential", 0.5)),
                    key_themes=result_json.get("key_themes", [])
                )
                
                logger.info(
                    "sentiment_analysis_completed",
                    sentiment=sentiment.overall_sentiment,
                    confidence=sentiment.confidence,
                    engagement_potential=sentiment.engagement_potential,
                    response_time=response_time,
                    themes_count=len(sentiment.key_themes)
                )
                
                return sentiment
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(
                    "sentiment_analysis_parsing_failed",
                    error=str(e),
                    raw_response=content[:200],
                    response_time=response_time
                )
                
                # Fallback sentiment analysis
                return SentimentAnalysis(
                    overall_sentiment="neutral",
                    confidence=0.3,
                    emotional_tone="unknown",
                    engagement_potential=0.5,
                    key_themes=[]
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                "sentiment_analysis_failed",
                error_type=type(e).__name__,
                error_details=str(e),
                response_time=response_time
            )
            
            # Return neutral sentiment on error
            return SentimentAnalysis(
                overall_sentiment="neutral",
                confidence=0.0,
                emotional_tone="error",
                engagement_potential=0.0,
                key_themes=[]
            )
    
    async def generate_content(self, 
                             opportunity_type: str,
                             context: Dict,
                             target_topics: List[str],
                             voice_guidelines: str = None) -> ContentGeneration:
        """
        Generate content for a specific opportunity.
        
        This will create engaging responses based on:
        - Type of opportunity (reply, quote, original, thread)
        - Context of the conversation
        - Your target topics and expertise
        - Your voice and brand guidelines
        """
        start_time = time.time()
        
        logger.info(
            "content_generation_started",
            opportunity_type=opportunity_type,
            target_topics=len(target_topics),
            has_voice_guidelines=bool(voice_guidelines),
            timestamp=datetime.now().isoformat()
        )
        
        # Build context-aware prompt
        prompt = self._build_content_prompt(opportunity_type, context, target_topics, voice_guidelines)
        
        try:
            response_data = await self._make_api_call("messages", {
                "model": "claude-3-sonnet-20240229",  # Higher quality model for content generation
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response_time = time.time() - start_time
            
            # Parse the response
            content = response_data.get("content", [{}])[0].get("text", "")
            
            try:
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    result_json = json.loads(content[json_start:json_end])
                else:
                    raise ValueError("No JSON found in response")
                
                generation = ContentGeneration(
                    content=result_json.get("content", ""),
                    content_type=result_json.get("content_type", opportunity_type),
                    confidence=float(result_json.get("confidence", 0.5)),
                    reasoning=result_json.get("reasoning", ""),
                    alternatives=result_json.get("alternatives", []),
                    estimated_engagement=float(result_json.get("estimated_engagement", 0.5))
                )
                
                logger.info(
                    "content_generation_completed",
                    content_length=len(generation.content),
                    confidence=generation.confidence,
                    estimated_engagement=generation.estimated_engagement,
                    response_time=response_time,
                    alternatives_count=len(generation.alternatives)
                )
                
                return generation
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(
                    "content_generation_parsing_failed",
                    error=str(e),
                    raw_response=content[:200],
                    response_time=response_time
                )
                
                # Extract plain text content as fallback
                return ContentGeneration(
                    content=content[:280],  # Truncate to tweet length
                    content_type=opportunity_type,
                    confidence=0.3,
                    reasoning="Fallback generation due to parsing error",
                    alternatives=[],
                    estimated_engagement=0.5
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                "content_generation_failed",
                error_type=type(e).__name__,
                error_details=str(e),
                response_time=response_time
            )
            
            return ContentGeneration(
                content="",
                content_type=opportunity_type,
                confidence=0.0,
                reasoning=f"Generation failed: {str(e)}",
                alternatives=[],
                estimated_engagement=0.0
            )
    
    def _build_content_prompt(self, opportunity_type: str, context: Dict, 
                            target_topics: List[str], voice_guidelines: str = None) -> str:
        """Build a context-aware prompt for content generation."""
        
        base_prompt = f"""You are helping create engaging social media content for someone with expertise in: {', '.join(target_topics)}.

OPPORTUNITY TYPE: {opportunity_type}

CONTEXT:
"""
        
        if opportunity_type == "reply" and context.get("text"):
            base_prompt += f"Original post: \"{context['text']}\"\n"
            base_prompt += f"Author: @{context.get('author_id', 'unknown')}\n"
        elif opportunity_type == "keyword_engagement" and context.get("search_text"):
            base_prompt += f"Found post about '{context['keyword']}': \"{context['search_text']}\"\n"
        
        base_prompt += f"""
YOUR EXPERTISE: {', '.join(target_topics)}

{f'VOICE GUIDELINES: {voice_guidelines}' if voice_guidelines else 'VOICE: Professional but approachable, knowledgeable without being condescending'}

Please generate engaging content and provide a JSON response with:
1. content: The actual tweet/post content (max 280 characters)
2. content_type: "{opportunity_type}"
3. confidence: 0.0 to 1.0 (how confident you are this will be well-received)
4. reasoning: Brief explanation of your approach
5. alternatives: Array of 2-3 alternative versions
6. estimated_engagement: 0.0 to 1.0 (predicted engagement potential)

Make it valuable, authentic, and likely to generate positive engagement."""
        
        return base_prompt
    
    async def _make_api_call(self, endpoint: str, payload: Dict) -> Dict:
        """Make API call to Claude with error handling and logging."""
        if not self.session:
            raise RuntimeError("Claude client session not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.post(url, json=payload) as response:
                response_data = await response.json()
                
                # Track usage
                self.total_requests += 1
                if "usage" in response_data:
                    tokens_used = response_data["usage"].get("input_tokens", 0) + response_data["usage"].get("output_tokens", 0)
                    self.total_tokens_used += tokens_used
                    
                    # Rough cost calculation (approximate)
                    self.total_cost += tokens_used * 0.000008  # Rough estimate
                
                if response.status == 200:
                    logger.debug(
                        "claude_api_call_success",
                        endpoint=endpoint,
                        status=response.status,
                        tokens_used=response_data.get("usage", {}).get("input_tokens", 0) + response_data.get("usage", {}).get("output_tokens", 0)
                    )
                    return response_data
                else:
                    logger.error(
                        "claude_api_call_failed",
                        endpoint=endpoint,
                        status=response.status,
                        error=response_data
                    )
                    raise Exception(f"API call failed with status {response.status}: {response_data}")
        
        except Exception as e:
            logger.error(
                "claude_api_call_error",
                endpoint=endpoint,
                error_type=type(e).__name__,
                error_details=str(e)
            )
            raise
    
    def get_usage_stats(self) -> Dict:
        """Get current API usage statistics."""
        stats = {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self.total_cost,
            "average_tokens_per_request": self.total_tokens_used / max(self.total_requests, 1)
        }
        
        logger.info("claude_usage_stats", stats=stats)
        return stats


# Export main classes
__all__ = ['ClaudeAPIClient', 'SentimentAnalysis', 'ContentGeneration']