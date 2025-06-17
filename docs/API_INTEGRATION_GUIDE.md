# API Integration Guide

## 🐦 X API v2 Integration

### Authentication Setup

```python
import tweepy
from typing import Optional, Dict, Any

class XAPIClient:
    def __init__(self, 
                 api_key: str,
                 api_secret: str, 
                 access_token: str,
                 access_token_secret: str,
                 bearer_token: str):
        
        # OAuth 1.0a User Context (for posting)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=bearer_token,
            wait_on_rate_limit=True
        )
        
        # OAuth 2.0 App-Only (for reading)
        self.read_client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True
        )
```

### Core Methods

#### Tweet Operations
```python
async def post_tweet(self, text: str, media_ids: Optional[List[str]] = None) -> Dict:
    """Post a tweet with optional media attachments"""
    try:
        response = self.client.create_tweet(
            text=text,
            media_ids=media_ids
        )
        return {
            'success': True,
            'tweet_id': response.data['id'],
            'text': response.data['text']
        }
    except tweepy.TooManyRequests:
        # Rate limit hit - queue for later
        return {'success': False, 'error': 'rate_limit', 'retry_after': 900}
    except tweepy.Forbidden:
        # Tweet rejected (duplicate, spam, etc.)
        return {'success': False, 'error': 'forbidden', 'message': 'Tweet rejected'}
    except Exception as e:
        return {'success': False, 'error': 'unknown', 'message': str(e)}

async def create_thread(self, tweets: List[str]) -> Dict:
    """Create a tweet thread"""
    thread_ids = []
    reply_to_id = None
    
    for tweet_text in tweets:
        response = await self.post_tweet(
            text=tweet_text,
            in_reply_to_tweet_id=reply_to_id
        )
        if response['success']:
            tweet_id = response['tweet_id']
            thread_ids.append(tweet_id)
            reply_to_id = tweet_id
        else:
            break
    
    return {'success': len(thread_ids) == len(tweets), 'thread_ids': thread_ids}
```

#### Monitoring and Engagement
```python
async def get_mentions(self, since_id: Optional[str] = None) -> List[Dict]:
    """Get recent mentions"""
    try:
        mentions = self.client.get_mentions(
            since_id=since_id,
            expansions=['author_id', 'in_reply_to_user_id'],
            tweet_fields=['created_at', 'context_annotations', 'public_metrics']
        )
        return [self._format_tweet(tweet) for tweet in mentions.data or []]
    except Exception as e:
        logger.error(f"Error fetching mentions: {e}")
        return []

async def get_trending_topics(self, woeid: int = 1) -> List[Dict]:
    """Get trending topics (requires Twitter API v1.1 for trends)"""
    # Note: Trends require v1.1 API
    api_v1 = tweepy.API(auth)
    trends = api_v1.get_place_trends(woeid)[0]['trends']
    return [{'name': trend['name'], 'volume': trend['tweet_volume']} 
            for trend in trends[:10]]

async def reply_to_tweet(self, tweet_id: str, reply_text: str) -> Dict:
    """Reply to a specific tweet"""
    return await self.post_tweet(
        text=reply_text,
        in_reply_to_tweet_id=tweet_id
    )
```

### Rate Limiting Strategy

```python
from datetime import datetime, timedelta
import asyncio

class RateLimitManager:
    def __init__(self):
        self.endpoints = {
            'create_tweet': {'limit': 300, 'window': 900, 'used': 0, 'reset_time': None},
            'get_mentions': {'limit': 75, 'window': 900, 'used': 0, 'reset_time': None},
            'get_user_tweets': {'limit': 900, 'window': 900, 'used': 0, 'reset_time': None}
        }
    
    async def check_rate_limit(self, endpoint: str) -> bool:
        """Check if we can make a request to this endpoint"""
        now = datetime.now()
        endpoint_data = self.endpoints[endpoint]
        
        # Reset counter if window has passed
        if endpoint_data['reset_time'] and now > endpoint_data['reset_time']:
            endpoint_data['used'] = 0
            endpoint_data['reset_time'] = None
        
        # Check if we're under the limit
        if endpoint_data['used'] >= endpoint_data['limit']:
            if not endpoint_data['reset_time']:
                endpoint_data['reset_time'] = now + timedelta(seconds=endpoint_data['window'])
            return False
        
        return True
    
    async def record_request(self, endpoint: str):
        """Record that we made a request"""
        self.endpoints[endpoint]['used'] += 1
```

---

## 🤖 Claude API Integration

### Client Setup

```python
import anthropic
from typing import List, Dict, Optional
import json

class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"  # Fast model for tweets
        self.model_premium = "claude-3-sonnet-20240229"  # For complex content
        
    async def generate_content(self, 
                             prompt: str, 
                             context: Optional[Dict] = None,
                             use_premium: bool = False) -> Dict:
        """Generate content using Claude"""
        try:
            model = self.model_premium if use_premium else self.model
            
            system_prompt = self._build_system_prompt(context)
            
            message = self.client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = message.content[0].text
            return {
                'success': True,
                'content': content,
                'usage': message.usage,
                'model': model
            }
            
        except anthropic.RateLimitError:
            return {'success': False, 'error': 'rate_limit'}
        except anthropic.APIError as e:
            return {'success': False, 'error': 'api_error', 'message': str(e)}
        except Exception as e:
            return {'success': False, 'error': 'unknown', 'message': str(e)}
```

### Content Generation Prompts

```python
class ContentPrompts:
    
    @staticmethod
    def original_post(topic: str, voice_profile: Dict, trending_context: str = "") -> str:
        return f"""Create an engaging X (Twitter) post about {topic}.

Voice Profile: {voice_profile}
Current Trending Context: {trending_context}

Requirements:
- Maximum 280 characters
- Match the voice profile exactly
- Be engaging and likely to get interactions
- Include relevant hashtags (max 2-3)
- Make it feel authentic and human

Generate only the tweet text, no quotes or explanations."""

    @staticmethod
    def reply_to_mention(original_tweet: str, voice_profile: Dict, context: str = "") -> str:
        return f"""Generate a reply to this tweet: "{original_tweet}"

Voice Profile: {voice_profile}
Additional Context: {context}

Requirements:
- Maximum 280 characters  
- Match the voice profile
- Be helpful and engaging
- Stay on topic
- Feel natural and conversational

Generate only the reply text, no quotes or explanations."""

    @staticmethod 
    def trend_response(trend_name: str, trend_context: str, voice_profile: Dict) -> str:
        return f"""Create a post responding to the trending topic: {trend_name}

Trend Context: {trend_context}
Voice Profile: {voice_profile}

Requirements:
- Maximum 280 characters
- Stay relevant to the trend
- Match brand voice 
- Add unique perspective or insight
- Include trending hashtag if appropriate

Generate only the tweet text, no quotes or explanations."""

    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Build system prompt with context"""
        base_prompt = """You are an expert social media content creator specializing in X (Twitter). 
You create engaging, authentic content that drives high engagement rates.

Key principles:
- Write in an authentic, human voice
- Create content that encourages interaction
- Stay within character limits
- Use relevant hashtags strategically
- Maintain brand consistency"""

        if context:
            if 'voice_profile' in context:
                base_prompt += f"\n\nBrand Voice: {context['voice_profile']}"
            if 'topics' in context:
                base_prompt += f"\n\nKey Topics: {', '.join(context['topics'])}"
        
        return base_prompt
```

### Advanced Content Generation

```python
async def generate_content_variations(self, 
                                    base_prompt: str, 
                                    count: int = 3) -> List[Dict]:
    """Generate multiple variations for A/B testing"""
    variations = []
    
    for i in range(count):
        # Vary temperature for different styles
        temp = 0.5 + (i * 0.2)  # 0.5, 0.7, 0.9
        
        result = await self.generate_content(
            prompt=f"{base_prompt}\n\nVariation {i+1}: Use temperature {temp} for different style",
            use_premium=False
        )
        
        if result['success']:
            variations.append({
                'content': result['content'],
                'temperature': temp,
                'variation_id': i + 1
            })
    
    return variations

async def score_content_quality(self, content: str, voice_profile: Dict) -> Dict:
    """Score content against voice profile and engagement potential"""
    scoring_prompt = f"""Rate this X post on a scale of 1-10 for:
1. Voice consistency with profile: {voice_profile}
2. Engagement potential
3. Authenticity 
4. Topic relevance

Post: "{content}"

Return only a JSON object with scores: {{"voice_consistency": X, "engagement_potential": X, "authenticity": X, "topic_relevance": X, "overall_score": X}}"""
    
    result = await self.generate_content(scoring_prompt, use_premium=True)
    
    if result['success']:
        try:
            scores = json.loads(result['content'])
            return {'success': True, 'scores': scores}
        except json.JSONDecodeError:
            return {'success': False, 'error': 'invalid_json'}
    
    return result
```

---

## 🔄 Integration Patterns

### Unified Content Pipeline

```python
class ContentPipeline:
    def __init__(self, x_client: XAPIClient, claude_client: ClaudeClient):
        self.x_client = x_client
        self.claude_client = claude_client
        self.rate_limiter = RateLimitManager()
    
    async def create_and_post(self, 
                            content_type: str,
                            topic: str,
                            voice_profile: Dict,
                            auto_post: bool = False) -> Dict:
        """Complete pipeline: generate -> score -> post"""
        
        # Generate content variations
        if content_type == "original":
            prompt = ContentPrompts.original_post(topic, voice_profile)
        elif content_type == "trend_response":
            trends = await self.x_client.get_trending_topics()
            prompt = ContentPrompts.trend_response(topic, trends[0], voice_profile)
        
        variations = await self.claude_client.generate_content_variations(prompt, count=3)
        
        # Score each variation
        scored_content = []
        for variation in variations:
            score = await self.claude_client.score_content_quality(
                variation['content'], 
                voice_profile
            )
            if score['success']:
                variation['scores'] = score['scores']
                scored_content.append(variation)
        
        # Select best content
        best_content = max(scored_content, key=lambda x: x['scores']['overall_score'])
        
        # Post if auto_post enabled and score is high enough
        if auto_post and best_content['scores']['overall_score'] >= 7:
            if await self.rate_limiter.check_rate_limit('create_tweet'):
                post_result = await self.x_client.post_tweet(best_content['content'])
                await self.rate_limiter.record_request('create_tweet')
                return {
                    'success': True,
                    'content': best_content,
                    'posted': post_result['success'],
                    'tweet_id': post_result.get('tweet_id')
                }
        
        return {
            'success': True,
            'content': best_content,
            'posted': False,
            'all_variations': scored_content
        }
```

### Error Handling & Resilience

```python
import asyncio
from typing import Callable
import logging

class ResilientAPIClient:
    def __init__(self, x_client: XAPIClient, claude_client: ClaudeClient):
        self.x_client = x_client
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
    
    async def retry_with_backoff(self, 
                               func: Callable, 
                               max_retries: int = 3,
                               base_delay: float = 1.0) -> Dict:
        """Retry failed API calls with exponential backoff"""
        for attempt in range(max_retries):
            try:
                result = await func()
                if result.get('success', False):
                    return result
                
                # If rate limited, wait longer
                if result.get('error') == 'rate_limit':
                    wait_time = result.get('retry_after', base_delay * (2 ** attempt))
                    self.logger.info(f"Rate limited, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return {'success': False, 'error': 'max_retries_exceeded'}
                await asyncio.sleep(base_delay * (2 ** attempt))
        
        return {'success': False, 'error': 'all_retries_failed'}

    async def health_check(self) -> Dict:
        """Check API health and connectivity"""
        checks = {}
        
        # Test X API
        try:
            me = self.x_client.client.get_me()
            checks['x_api'] = {'status': 'healthy', 'user_id': me.data.id}
        except Exception as e:
            checks['x_api'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Test Claude API
        try:
            test_result = await self.claude_client.generate_content("Say 'API test successful'")
            checks['claude_api'] = {
                'status': 'healthy' if test_result['success'] else 'unhealthy',
                'error': test_result.get('error')
            }
        except Exception as e:
            checks['claude_api'] = {'status': 'unhealthy', 'error': str(e)}
        
        return {
            'overall_health': all(check['status'] == 'healthy' for check in checks.values()),
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
```

---

## 📊 Monitoring & Logging

### API Usage Tracking

```python
import time
from collections import defaultdict

class APIMetrics:
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'response_times': [],
            'rate_limits': 0,
            'last_reset': time.time()
        })
    
    def record_request(self, endpoint: str, response_time: float, success: bool, error_type: str = None):
        """Record API request metrics"""
        metrics = self.metrics[endpoint]
        metrics['requests'] += 1
        metrics['response_times'].append(response_time)
        
        if not success:
            metrics['errors'] += 1
            if error_type == 'rate_limit':
                metrics['rate_limits'] += 1
    
    def get_stats(self) -> Dict:
        """Get comprehensive API statistics"""
        stats = {}
        for endpoint, metrics in self.metrics.items():
            if metrics['requests'] > 0:
                avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
                error_rate = metrics['errors'] / metrics['requests']
                
                stats[endpoint] = {
                    'total_requests': metrics['requests'],
                    'error_rate': error_rate,
                    'avg_response_time': avg_response_time,
                    'rate_limit_hits': metrics['rate_limits']
                }
        return stats
```

This comprehensive API integration guide provides the foundation for robust, production-ready integration with both X API v2 and Claude API, including proper error handling, rate limiting, and monitoring.