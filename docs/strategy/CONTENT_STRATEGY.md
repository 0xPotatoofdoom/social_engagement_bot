# Content Strategy Documentation

## 🎯 Content Strategy Framework

### Core Strategy Principles

1. **Voice-First Approach**: Every piece of content must sound authentically like your brand
2. **Topic Relevance**: Stay focused on your key topic areas while being responsive to trends
3. **Engagement Optimization**: Create content designed to drive interactions, not just impressions
4. **Community Building**: Focus on building relationships, not just broadcasting messages
5. **Data-Driven Iteration**: Use performance data to continuously refine strategy

---

## 📋 Topic Configuration System

### Primary Topic Areas

Define 3-5 core topic areas that align with your brand and audience interests:

```yaml
# config/topics.yaml
primary_topics:
  - name: "web3_innovation"
    keywords: ["blockchain", "DeFi", "NFT", "crypto", "smart contracts"]
    hashtags: ["#web3", "#blockchain", "#DeFi", "#crypto"]
    relevance_weight: 0.9
    content_types: ["original", "trend_response", "educational"]
    
  - name: "tech_trends"
    keywords: ["AI", "machine learning", "automation", "future tech"]
    hashtags: ["#AI", "#tech", "#innovation", "#automation"]
    relevance_weight: 0.8
    content_types: ["original", "trend_response", "opinion"]
    
  - name: "community_building"
    keywords: ["community", "networking", "collaboration", "growth"]
    hashtags: ["#community", "#networking", "#growth"]
    relevance_weight: 0.7
    content_types: ["engagement", "community", "support"]

secondary_topics:
  - name: "market_insights"
    keywords: ["market", "analysis", "trends", "predictions"]
    hashtags: ["#markets", "#analysis", "#insights"]
    relevance_weight: 0.6
    trigger_conditions: ["high_volatility", "major_news"]

trending_response_rules:
  - topic: "web3_innovation"
    min_tweet_volume: 10000
    relevance_threshold: 0.7
    response_delay: "5-15 minutes"
  
  - topic: "tech_trends" 
    min_tweet_volume: 50000
    relevance_threshold: 0.6
    response_delay: "10-30 minutes"
```

### Topic Relevance Scoring

```python
class TopicRelevanceScorer:
    def __init__(self, topics_config: dict):
        self.topics = topics_config
        
    async def score_trend_relevance(self, trend: dict) -> dict:
        """Score how relevant a trending topic is to our brand"""
        trend_name = trend['name'].lower()
        trend_context = trend.get('context', '')
        
        scores = {}
        for topic_name, topic_config in self.topics['primary_topics'].items():
            score = 0.0
            
            # Keyword matching
            for keyword in topic_config['keywords']:
                if keyword.lower() in trend_name:
                    score += 0.3
                if keyword.lower() in trend_context.lower():
                    score += 0.2
            
            # Hashtag presence
            for hashtag in topic_config['hashtags']:
                if hashtag.lower() in trend_name:
                    score += 0.2
            
            # Apply topic weight
            final_score = min(score * topic_config['relevance_weight'], 1.0)
            scores[topic_name] = final_score
        
        return {
            'trend': trend,
            'relevance_scores': scores,
            'max_relevance': max(scores.values()) if scores else 0,
            'best_topic': max(scores.keys(), key=scores.get) if scores else None
        }
    
    async def should_respond_to_trend(self, trend_analysis: dict) -> bool:
        """Determine if we should create content for this trend"""
        best_topic = trend_analysis['best_topic']
        if not best_topic:
            return False
        
        topic_config = self.topics['primary_topics'][best_topic]
        rules = self.topics.get('trending_response_rules', {}).get(best_topic, {})
        
        # Check minimum relevance threshold
        if trend_analysis['max_relevance'] < rules.get('relevance_threshold', 0.5):
            return False
        
        # Check tweet volume threshold
        if trend_analysis['trend'].get('volume', 0) < rules.get('min_tweet_volume', 1000):
            return False
        
        return True
```

---

## 📝 Content Type Definitions

### Content Type Framework

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class ContentType(Enum):
    ORIGINAL = "original"           # Original thoughts/insights
    TREND_RESPONSE = "trend_response"  # Response to trending topics
    ENGAGEMENT = "engagement"       # Community interaction content
    EDUCATIONAL = "educational"     # Teaching/explaining content
    OPINION = "opinion"            # Hot takes and perspectives
    COMMUNITY = "community"        # Community building content
    SUPPORT = "support"           # Helping/answering questions

@dataclass
class ContentTemplate:
    type: ContentType
    topic_areas: List[str]
    prompt_template: str
    max_length: int = 280
    hashtag_count: tuple = (1, 3)
    engagement_hooks: List[str] = None
    posting_schedule: Dict = None
    
    def __post_init__(self):
        if self.engagement_hooks is None:
            self.engagement_hooks = []
```

### Content Templates by Type

```yaml
# config/content_templates.yaml
templates:
  original:
    web3_innovation:
      prompt: "Share an original insight about {topic} that would interest the web3 community"
      hooks: ["What do you think about", "Hot take:", "Unpopular opinion:", "Here's why"]
      optimal_times: ["09:00", "13:00", "18:00"]
      
    tech_trends:
      prompt: "Create original content about {topic} with a forward-looking perspective"
      hooks: ["The future of", "Why", "Here's what's coming", "Prediction:"]
      optimal_times: ["08:00", "12:00", "16:00"]

  trend_response:
    quick_response:
      prompt: "Respond to trending topic '{trend}' with our brand perspective in under 280 chars"
      hooks: ["This is exactly why", "Calling it:", "As predicted", "Finally!"]
      response_delay: "5-15 minutes"
      
    analytical_response:
      prompt: "Provide analytical take on '{trend}' showing industry expertise"
      hooks: ["Here's what this means", "Breaking this down:", "The real story:", "Context matters"]
      response_delay: "15-30 minutes"

  engagement:
    community_question:
      prompt: "Ask an engaging question about {topic} to spark community discussion"
      hooks: ["What's your take on", "Quick poll:", "Thoughts?", "Agree or disagree:"]
      optimal_times: ["12:00", "19:00"]
      
    conversation_starter:
      prompt: "Create a conversation starter about {topic} that encourages replies"
      hooks: ["Change my mind:", "Unpopular opinion:", "Hot debate:", "Let's discuss:"]
      optimal_times: ["18:00", "20:00"]
```

### Dynamic Content Generation

```python
class ContentGenerator:
    def __init__(self, claude_client, templates_config, voice_profile):
        self.claude = claude_client
        self.templates = templates_config
        self.voice_profile = voice_profile
    
    async def generate_content(self, 
                             content_type: ContentType,
                             topic: str,
                             context: dict = None) -> dict:
        """Generate content based on type and topic"""
        
        template = self._get_template(content_type, topic)
        if not template:
            return {'success': False, 'error': 'no_template_found'}
        
        # Build dynamic prompt
        prompt = self._build_content_prompt(template, topic, context)
        
        # Generate multiple variations
        variations = await self.claude.generate_content_variations(prompt, count=3)
        
        # Score and rank variations
        scored_variations = []
        for variation in variations:
            score = await self._score_content(variation, content_type, topic)
            if score['success']:
                variation.update(score)
                scored_variations.append(variation)
        
        # Return best variation
        if scored_variations:
            best = max(scored_variations, key=lambda x: x['overall_score'])
            return {
                'success': True,
                'content': best,
                'all_variations': scored_variations,
                'template_used': template['name']
            }
        
        return {'success': False, 'error': 'no_valid_content_generated'}
    
    def _build_content_prompt(self, template: dict, topic: str, context: dict = None) -> str:
        """Build comprehensive prompt for content generation"""
        base_prompt = template['prompt'].format(topic=topic)
        
        # Add context if available
        if context:
            if 'trending_info' in context:
                base_prompt += f"\n\nTrending Context: {context['trending_info']}"
            if 'community_mood' in context:
                base_prompt += f"\n\nCommunity Mood: {context['community_mood']}"
        
        # Add engagement hooks
        hooks = template.get('hooks', [])
        if hooks:
            base_prompt += f"\n\nConsider using one of these engagement hooks: {', '.join(hooks)}"
        
        # Add voice profile
        base_prompt += f"\n\nBrand Voice Profile: {self.voice_profile}"
        
        # Add constraints
        base_prompt += f"""
        
Requirements:
- Maximum {template.get('max_length', 280)} characters
- Include {template.get('hashtag_count', (1, 3))[0]}-{template.get('hashtag_count', (1, 3))[1]} relevant hashtags
- Make it engaging and likely to get interactions
- Match the brand voice exactly
- Stay focused on the topic

Generate only the tweet text, no quotes or explanations."""
        
        return base_prompt
```

---

## 🗓️ Content Scheduling & Timing

### Optimal Posting Strategy

```python
from datetime import datetime, timedelta
import pytz

class ContentScheduler:
    def __init__(self, timezone: str = "US/Eastern"):
        self.timezone = pytz.timezone(timezone)
        
        # Peak engagement times by content type
        self.optimal_times = {
            ContentType.ORIGINAL: ["09:00", "13:00", "18:00"],
            ContentType.TREND_RESPONSE: ["immediate", "5-15min", "30min"],
            ContentType.ENGAGEMENT: ["12:00", "19:00", "21:00"],
            ContentType.EDUCATIONAL: ["10:00", "14:00", "16:00"],
            ContentType.COMMUNITY: ["18:00", "20:00", "22:00"]
        }
        
        # Content frequency limits
        self.frequency_limits = {
            'max_posts_per_hour': 3,
            'max_posts_per_day': 12,
            'min_gap_between_posts': 20,  # minutes
            'max_replies_per_hour': 10
        }
    
    async def get_next_posting_time(self, 
                                  content_type: ContentType,
                                  urgency: str = "normal") -> datetime:
        """Calculate optimal posting time for content"""
        now = datetime.now(self.timezone)
        
        if urgency == "immediate" or content_type == ContentType.TREND_RESPONSE:
            # Post ASAP for trending content
            return now + timedelta(minutes=2)
        
        # Get optimal times for content type
        optimal_times = self.optimal_times.get(content_type, ["12:00", "18:00"])
        
        # Find next optimal time
        for time_str in optimal_times:
            posting_time = datetime.strptime(time_str, "%H:%M").time()
            today_posting = now.replace(
                hour=posting_time.hour, 
                minute=posting_time.minute, 
                second=0, 
                microsecond=0
            )
            
            if today_posting > now:
                return today_posting
        
        # If no times today, use first time tomorrow
        tomorrow = now + timedelta(days=1)
        first_time = datetime.strptime(optimal_times[0], "%H:%M").time()
        return tomorrow.replace(
            hour=first_time.hour,
            minute=first_time.minute,
            second=0,
            microsecond=0
        )
    
    async def can_post_now(self, content_type: ContentType) -> dict:
        """Check if we can post based on frequency limits"""
        # This would integrate with your database to check recent posts
        # Simplified version:
        
        recent_posts = await self._get_recent_posts(hours=1)
        posts_this_hour = len(recent_posts)
        
        if posts_this_hour >= self.frequency_limits['max_posts_per_hour']:
            next_available = recent_posts[0]['timestamp'] + timedelta(hours=1)
            return {
                'can_post': False, 
                'reason': 'hourly_limit_reached',
                'next_available': next_available
            }
        
        # Check minimum gap
        if recent_posts:
            last_post_time = recent_posts[-1]['timestamp']
            min_gap = timedelta(minutes=self.frequency_limits['min_gap_between_posts'])
            if datetime.now() - last_post_time < min_gap:
                return {
                    'can_post': False,
                    'reason': 'minimum_gap_not_met',
                    'next_available': last_post_time + min_gap
                }
        
        return {'can_post': True}
```

---

## 🎪 Engagement Strategies

### Engagement Pattern Analysis

```python
class EngagementAnalyzer:
    def __init__(self):
        self.engagement_patterns = {
            'high_engagement_indicators': [
                'questions_in_content',
                'controversial_but_tasteful_takes',
                'community_shoutouts',
                'behind_the_scenes_content',
                'polls_and_surveys'
            ],
            'optimal_hashtag_strategies': {
                'trending_hashtags': 1,  # Max 1 trending hashtag
                'brand_hashtags': 1,     # Max 1 brand hashtag  
                'topic_hashtags': 2      # Max 2 topic-specific hashtags
            }
        }
    
    async def analyze_post_potential(self, content: str, topic: str) -> dict:
        """Predict engagement potential of content"""
        score = 0.0
        factors = []
        
        # Question detection
        if '?' in content:
            score += 0.2
            factors.append('contains_question')
        
        # Call-to-action detection
        cta_words = ['thoughts?', 'agree?', 'what do you think', 'your take']
        if any(cta in content.lower() for cta in cta_words):
            score += 0.15
            factors.append('has_call_to_action')
        
        # Emotional hooks
        emotion_words = ['excited', 'amazing', 'incredible', 'shocked', 'surprised']
        if any(word in content.lower() for word in emotion_words):
            score += 0.1
            factors.append('emotional_hook')
        
        # Length optimization (Twitter sweet spot: 100-140 chars)
        if 100 <= len(content) <= 140:
            score += 0.1
            factors.append('optimal_length')
        
        # Hashtag analysis
        hashtag_count = content.count('#')
        if 1 <= hashtag_count <= 3:
            score += 0.1
            factors.append('good_hashtag_count')
        
        return {
            'engagement_score': min(score, 1.0),
            'contributing_factors': factors,
            'recommendations': self._get_engagement_recommendations(content, score)
        }
    
    def _get_engagement_recommendations(self, content: str, current_score: float) -> list:
        """Provide recommendations to improve engagement"""
        recommendations = []
        
        if '?' not in content and current_score < 0.7:
            recommendations.append("Add a question to encourage responses")
        
        if content.count('#') == 0:
            recommendations.append("Add 1-2 relevant hashtags")
        elif content.count('#') > 3:
            recommendations.append("Reduce hashtags to 2-3 for better readability")
        
        if len(content) > 200:
            recommendations.append("Consider shortening for better engagement")
        
        emotion_words = ['excited', 'amazing', 'love', 'hate', 'shocked']
        if not any(word in content.lower() for word in emotion_words):
            recommendations.append("Add emotional language to increase engagement")
        
        return recommendations
```

### Community Engagement Automation

```python
class CommunityEngagementBot:
    def __init__(self, x_client, claude_client, voice_profile):
        self.x_client = x_client
        self.claude = claude_client
        self.voice_profile = voice_profile
        
    async def handle_mentions(self) -> dict:
        """Process and respond to mentions"""
        mentions = await self.x_client.get_mentions()
        responses = []
        
        for mention in mentions:
            if await self._should_respond_to_mention(mention):
                response = await self._generate_mention_response(mention)
                if response['success']:
                    # Post reply
                    reply_result = await self.x_client.reply_to_tweet(
                        mention['id'], 
                        response['content']
                    )
                    responses.append({
                        'mention_id': mention['id'],
                        'response': response['content'],
                        'posted': reply_result['success']
                    })
        
        return {'mentions_processed': len(mentions), 'responses_sent': responses}
    
    async def _should_respond_to_mention(self, mention: dict) -> bool:
        """Determine if we should respond to this mention"""
        # Skip if it's a retweet
        if mention.get('is_retweet', False):
            return False
        
        # Skip if from a blocked/spam account
        if await self._is_spam_account(mention['author']):
            return False
        
        # Skip if it's purely promotional
        if await self._is_promotional_content(mention['text']):
            return False
        
        # Respond if it's a question or needs engagement
        return (
            '?' in mention['text'] or
            any(word in mention['text'].lower() for word in ['help', 'question', 'thoughts'])
        )
    
    async def _generate_mention_response(self, mention: dict) -> dict:
        """Generate contextual response to mention"""
        context = {
            'original_tweet': mention['text'],
            'author': mention['author']['username'],
            'conversation_context': mention.get('conversation_context', ''),
            'voice_profile': self.voice_profile
        }
        
        prompt = f"""Generate a helpful, engaging reply to this mention: "{mention['text']}"

Author: @{mention['author']['username']}
Context: {context.get('conversation_context', 'None')}
Voice Profile: {self.voice_profile}

Requirements:
- Maximum 280 characters
- Be helpful and genuine
- Match brand voice
- Encourage further conversation if appropriate
- Don't be overly promotional

Generate only the reply text, no quotes or explanations."""
        
        return await self.claude.generate_content(prompt)
```

This comprehensive content strategy framework provides the structure for creating engaging, on-brand content that drives meaningful community engagement while maintaining authentic voice consistency.