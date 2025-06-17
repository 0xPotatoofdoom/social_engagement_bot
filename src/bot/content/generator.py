"""
Content Generation System

Generates responses for identified engagement opportunities using Claude API.
Ensures brand voice consistency and quality before suggesting content.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)


class ContentType(Enum):
    """Types of content that can be generated."""
    REPLY = "reply"
    QUOTE_TWEET = "quote"
    THREAD = "thread"
    ORIGINAL = "original"


class VoiceTone(Enum):
    """Brand voice tones for different contexts."""
    TECHNICAL = "technical"
    HELPFUL = "helpful"
    ENTHUSIASTIC = "enthusiastic"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"


@dataclass
class ContentGenerationRequest:
    """Request for content generation."""
    opportunity_id: str
    content_type: ContentType
    context: Dict
    target_audience: str = "crypto/defi community"
    voice_tone: VoiceTone = VoiceTone.HELPFUL
    max_length: int = 280
    include_hashtags: bool = True
    include_mentions: bool = True


@dataclass
class GeneratedContent:
    """Generated content with metadata."""
    text: str
    content_type: ContentType
    voice_score: float  # How well it matches brand voice (0-1)
    quality_score: float  # Overall quality score (0-1)
    character_count: int
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    revision_notes: List[str] = field(default_factory=list)


@dataclass
class VoiceGuidelines:
    """Brand voice guidelines for consistent content generation."""
    personality_traits: List[str]
    expertise_areas: List[str]
    preferred_tone: str
    avoid_topics: List[str]
    sample_tweets: List[str]
    hashtag_preferences: List[str]


class ContentGenerator:
    """
    Generates high-quality content for engagement opportunities.
    
    Features:
    - Claude-powered content generation
    - Brand voice consistency scoring
    - Multi-type content support (replies, quotes, threads, original)
    - Quality validation pipeline
    - Template-based generation with customization
    """
    
    def __init__(self, claude_client, voice_guidelines: Optional[VoiceGuidelines] = None):
        self.claude_client = claude_client
        self.voice_guidelines = voice_guidelines or self._get_default_voice_guidelines()
        
        # Content generation stats
        self.generation_stats = {
            'total_generated': 0,
            'by_type': {content_type.value: 0 for content_type in ContentType},
            'avg_quality_score': 0.0,
            'avg_voice_score': 0.0
        }
        
        logger.info(
            "content_generator_initialized",
            has_voice_guidelines=bool(voice_guidelines),
            expertise_areas=len(self.voice_guidelines.expertise_areas)
        )
    
    def _get_default_voice_guidelines(self) -> VoiceGuidelines:
        """Get AI x Blockchain KOL voice guidelines with Phase 1 evolution targets."""
        return VoiceGuidelines(
            personality_traits=[
                "AI x blockchain technical authority",
                "Forward-thinking innovation expert",
                "Conversational yet authoritative",
                "Educational but confident",
                "Community thought leader"
            ],
            expertise_areas=[
                "AI agents on blockchain",
                "Machine learning DeFi integration",
                "HFT and algorithmic trading",
                "Uniswap v4 and intelligent hooks",
                "Autonomous trading systems",
                "Predictive MEV protection",
                "AI-enhanced protocol design",
                "Blockchain infrastructure for AI"
            ],
            preferred_tone="Technical authority with conversational accessibility - positioning as AI x blockchain thought leader",
            avoid_topics=[
                "Financial advice",
                "Price predictions", 
                "Investment recommendations",
                "Regulatory speculation",
                "Basic blockchain explanations"
            ],
            sample_tweets=[
                "AI agents on Unichain will fundamentally change how we think about autonomous trading. The infrastructure pieces are finally coming together 🧵",
                "Hot take: The convergence of ML models and v4 hooks creates unprecedented opportunities for intelligent AMM design",
                "Building AI-powered MEV protection isn't just about better algorithms - it's about rethinking protocol architecture from first principles"
            ],
            hashtag_preferences=[
                "#AIxBlockchain", "#AutonomousTrading", "#AIAgents", "#UniswapV4", 
                "#IntelligentProtocols", "#MachineLearningDeFi", "#PredictiveMEV", "#AIInfrastructure"
            ]
        )
    
    async def generate_content(self, request: ContentGenerationRequest) -> GeneratedContent:
        """Generate content for a specific opportunity."""
        logger.info(
            "generating_content",
            opportunity_id=request.opportunity_id,
            content_type=request.content_type.value,
            voice_tone=request.voice_tone.value
        )
        
        try:
            # Generate initial content
            initial_content = await self._generate_initial_content(request)
            
            # Score voice consistency
            voice_score = await self._score_voice_consistency(initial_content, request)
            
            # Score overall quality
            quality_score = await self._score_content_quality(initial_content, request)
            
            # Refine if scores are too low
            if voice_score < 0.7 or quality_score < 0.7:
                logger.info(
                    "refining_content",
                    initial_voice_score=voice_score,
                    initial_quality_score=quality_score
                )
                refined_content = await self._refine_content(initial_content, request, voice_score, quality_score)
                voice_score = await self._score_voice_consistency(refined_content, request)
                quality_score = await self._score_content_quality(refined_content, request)
                initial_content = refined_content
            
            # Extract hashtags and mentions
            hashtags = self._extract_hashtags(initial_content)
            mentions = self._extract_mentions(initial_content)
            
            # Create final content object
            generated = GeneratedContent(
                text=initial_content,
                content_type=request.content_type,
                voice_score=voice_score,
                quality_score=quality_score,
                character_count=len(initial_content),
                hashtags=hashtags,
                mentions=mentions
            )
            
            # Update stats
            self._update_generation_stats(generated)
            
            logger.info(
                "content_generated_successfully",
                opportunity_id=request.opportunity_id,
                character_count=generated.character_count,
                voice_score=voice_score,
                quality_score=quality_score,
                content_type=request.content_type.value
            )
            
            return generated
            
        except Exception as e:
            logger.error(
                "content_generation_failed",
                opportunity_id=request.opportunity_id,
                error_type=type(e).__name__,
                error_details=str(e)
            )
            raise
    
    async def _generate_initial_content(self, request: ContentGenerationRequest) -> str:
        """Generate initial content using Claude API."""
        
        # Build context-specific prompt
        prompt = self._build_generation_prompt(request)
        
        # Generate content with Claude
        response = await self.claude_client.generate_content(
            opportunity_type=request.content_type.value,
            context=request.context,
            target_topics=self.voice_guidelines.expertise_areas,
            voice_guidelines=prompt
        )
        
        return response.content
    
    def _build_generation_prompt(self, request: ContentGenerationRequest) -> str:
        """Build a detailed prompt for content generation."""
        
        context = request.context
        opportunity_text = context.get('text', '')
        keyword = context.get('keyword', '')
        
        prompt = f"""
Generate a {request.content_type.value} for this engagement opportunity:

ORIGINAL TWEET: "{opportunity_text}"
KEYWORD CONTEXT: {keyword}
TARGET AUDIENCE: {request.target_audience}
VOICE TONE: {request.voice_tone.value}
MAX LENGTH: {request.max_length} characters

BRAND VOICE GUIDELINES:
Personality: {', '.join(self.voice_guidelines.personality_traits)}
Expertise: {', '.join(self.voice_guidelines.expertise_areas)}
Tone: {self.voice_guidelines.preferred_tone}

AVOID: {', '.join(self.voice_guidelines.avoid_topics)}

EXAMPLE STYLE (for reference):
{self.voice_guidelines.sample_tweets[0] if self.voice_guidelines.sample_tweets else 'Professional, helpful, and engaging'}

REQUIREMENTS:
1. Be genuinely helpful and add value to the conversation
2. Show expertise without being condescending  
3. Use technical knowledge appropriately for the audience
4. Be enthusiastic about innovation but not overly promotional
5. Keep under {request.max_length} characters
6. Include relevant hashtags if appropriate: {', '.join(self.voice_guidelines.hashtag_preferences[:3])}

Generate a {request.content_type.value} that would naturally contribute to this conversation:
"""
        
        return prompt
    
    async def _score_voice_consistency(self, content: str, request: ContentGenerationRequest) -> float:
        """Score how well content matches brand voice."""
        
        # Use Claude to analyze voice consistency
        analysis_prompt = f"""
Analyze how well this content matches the specified brand voice:

CONTENT: "{content}"

BRAND VOICE GUIDELINES:
- Personality: {', '.join(self.voice_guidelines.personality_traits)}
- Tone: {self.voice_guidelines.preferred_tone}
- Expertise Areas: {', '.join(self.voice_guidelines.expertise_areas)}

SAMPLE GOOD TWEETS:
{chr(10).join(f'- {tweet}' for tweet in self.voice_guidelines.sample_tweets[:2])}

Rate the voice consistency from 0.0 to 1.0 based on:
1. Personality alignment (professional yet approachable)
2. Technical accuracy and expertise demonstration
3. Tone appropriateness
4. Style consistency with samples

Return only a number between 0.0 and 1.0.
"""
        
        try:
            # For now, use a simplified scoring system
            # TODO: Implement Claude-based voice scoring
            
            score = 0.5  # Base score
            
            # Check for technical terms (shows expertise)
            technical_terms = ['defi', 'protocol', 'smart contract', 'blockchain', 'dex', 'amm', 'yield', 'liquidity']
            tech_matches = sum(1 for term in technical_terms if term.lower() in content.lower())
            score += min(tech_matches * 0.1, 0.2)
            
            # Check for helpful language
            helpful_words = ['how', 'why', 'explains', 'understand', 'learn', 'helpful', 'guide']
            helpful_matches = sum(1 for word in helpful_words if word.lower() in content.lower())
            score += min(helpful_matches * 0.05, 0.15)
            
            # Check for enthusiasm without hype
            if any(word in content.lower() for word in ['love', 'exciting', 'great', 'amazing', 'innovation']):
                score += 0.1
            
            # Penalize if too promotional or gives financial advice
            if any(word in content.lower() for word in ['buy', 'sell', 'invest', 'price', 'moon', 'ape']):
                score -= 0.2
            
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            logger.warning("voice_scoring_failed", error=str(e))
            return 0.6  # Default decent score
    
    async def _score_content_quality(self, content: str, request: ContentGenerationRequest) -> float:
        """Score overall content quality."""
        
        score = 0.5  # Base score
        
        # Length appropriateness
        if len(content) <= request.max_length:
            score += 0.2
        else:
            score -= 0.3  # Penalty for being too long
        
        # Check for complete sentences
        if content.endswith(('.', '!', '?')):
            score += 0.1
        
        # Check for relevant hashtags
        if request.include_hashtags:
            hashtags = self._extract_hashtags(content)
            if hashtags:
                score += 0.1
        
        # Check for questions or engagement drivers
        if '?' in content or any(word in content.lower() for word in ['thoughts', 'what do you think', 'agree']):
            score += 0.1
        
        # Penalize if too generic
        generic_phrases = ['great post', 'thanks for sharing', 'this is interesting']
        if any(phrase in content.lower() for phrase in generic_phrases):
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    async def _refine_content(self, content: str, request: ContentGenerationRequest, 
                            voice_score: float, quality_score: float) -> str:
        """Refine content based on scoring feedback."""
        
        refinement_prompt = f"""
Improve this content based on the feedback:

ORIGINAL CONTENT: "{content}"
VOICE SCORE: {voice_score:.2f} (target: 0.7+)
QUALITY SCORE: {quality_score:.2f} (target: 0.7+)

IMPROVEMENT AREAS:
{"- Make more aligned with brand voice (technical but approachable)" if voice_score < 0.7 else ""}
{"- Improve overall quality and engagement" if quality_score < 0.7 else ""}

REQUIREMENTS:
- Keep under {request.max_length} characters
- Be more specific and valuable
- Show technical expertise appropriately
- Use {request.voice_tone.value} tone
- Include relevant hashtags if helpful

Generate an improved version:
"""
        
        try:
            # For now, apply simple refinements
            # TODO: Implement Claude-based refinement
            
            refined = content
            
            # Add technical depth if voice score is low
            if voice_score < 0.7:
                if 'defi' in content.lower() and 'protocol' not in content.lower():
                    refined = refined.replace('DeFi', 'DeFi protocol')
            
            # Add engagement if quality is low
            if quality_score < 0.7 and not refined.endswith('?'):
                if len(refined) < request.max_length - 20:
                    refined += " What are your thoughts?"
            
            # Ensure length compliance
            if len(refined) > request.max_length:
                refined = refined[:request.max_length-3] + "..."
            
            return refined
            
        except Exception as e:
            logger.warning("content_refinement_failed", error=str(e))
            return content  # Return original if refinement fails
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content."""
        words = content.split()
        hashtags = [word for word in words if word.startswith('#')]
        return hashtags
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract mentions from content."""
        words = content.split()
        mentions = [word for word in words if word.startswith('@')]
        return mentions
    
    def _update_generation_stats(self, generated: GeneratedContent):
        """Update generation statistics."""
        self.generation_stats['total_generated'] += 1
        self.generation_stats['by_type'][generated.content_type.value] += 1
        
        # Update running averages
        total = self.generation_stats['total_generated']
        self.generation_stats['avg_quality_score'] = (
            (self.generation_stats['avg_quality_score'] * (total - 1) + generated.quality_score) / total
        )
        self.generation_stats['avg_voice_score'] = (
            (self.generation_stats['avg_voice_score'] * (total - 1) + generated.voice_score) / total
        )
    
    async def generate_batch_content(self, requests: List[ContentGenerationRequest]) -> List[GeneratedContent]:
        """Generate content for multiple opportunities."""
        logger.info("generating_batch_content", batch_size=len(requests))
        
        results = []
        for i, request in enumerate(requests):
            try:
                logger.debug("processing_batch_item", item=i+1, total=len(requests))
                content = await self.generate_content(request)
                results.append(content)
                
                # Rate limit between generations
                if i < len(requests) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(
                    "batch_item_failed",
                    item=i+1,
                    opportunity_id=request.opportunity_id,
                    error=str(e)
                )
        
        logger.info("batch_generation_completed", successful=len(results), failed=len(requests)-len(results))
        return results
    
    async def generate_for_opportunity(self, opportunity) -> GeneratedContent:
        """Generate content for a ContentOpportunity object."""
        
        # Determine content type from suggestion
        content_type_map = {
            'reply': ContentType.REPLY,
            'quote': ContentType.QUOTE_TWEET,
            'thread': ContentType.THREAD,
            'original': ContentType.ORIGINAL
        }
        
        content_type = content_type_map.get(
            opportunity.suggested_approach, 
            ContentType.REPLY
        )
        
        # Determine voice tone based on context
        voice_tone = VoiceTone.HELPFUL
        if opportunity.context.get('keyword') in ['innovation', 'launch', 'new']:
            voice_tone = VoiceTone.ENTHUSIASTIC
        elif any(tech in opportunity.context.get('text', '').lower() 
                for tech in ['protocol', 'smart contract', 'blockchain']):
            voice_tone = VoiceTone.TECHNICAL
        
        # Create generation request
        request = ContentGenerationRequest(
            opportunity_id=str(opportunity.context.get('tweet_id', 'unknown')),
            content_type=content_type,
            context=opportunity.context,
            voice_tone=voice_tone,
            max_length=280 if content_type != ContentType.THREAD else 560
        )
        
        return await self.generate_content(request)
    
    def get_generation_stats(self) -> Dict:
        """Get content generation statistics."""
        return self.generation_stats.copy()


# Export main classes
__all__ = ['ContentGenerator', 'ContentGenerationRequest', 'GeneratedContent', 'ContentType', 'VoiceTone', 'VoiceGuidelines']