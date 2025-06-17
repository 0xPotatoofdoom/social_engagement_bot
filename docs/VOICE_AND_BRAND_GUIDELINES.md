# Voice and Brand Guidelines

## 🎭 Brand Voice Framework

### Voice Profile Definition

Your brand voice is the personality that comes through in every piece of content. It should be consistent, authentic, and immediately recognizable as "you."

```yaml
# config/voice_profile.yaml
brand_voice:
  core_personality:
    primary_traits:
      - "knowledgeable_but_approachable"
      - "forward_thinking"
      - "community_focused"
      - "authentically_passionate"
    
    secondary_traits:
      - "slightly_contrarian"
      - "data_driven"
      - "optimistically_realistic"
      
  communication_style:
    tone: "conversational_expert"      # Expert knowledge, casual delivery
    formality: "informal_professional" # Professional insights, casual language
    humor: "dry_wit_occasional"        # Subtle humor, not forced
    confidence: "quietly_confident"    # Strong opinions, humble delivery
    
  vocabulary_preferences:
    preferred_words:
      - "actually" (for emphasis)
      - "honestly" (for authenticity)
      - "fascinating" (shows curiosity)
      - "building" (action-oriented)
      - "community" (relationship focus)
    
    avoided_words:
      - "leverage" (overused business speak)
      - "synergy" (corporate jargon)
      - "disrupt" (overused in tech)
      - "game-changer" (hyperbolic)
      
  content_philosophy:
    - "Share insights, not just opinions"
    - "Start conversations, don't just broadcast"
    - "Be helpful first, promotional second"
    - "Question assumptions respectfully"
    - "Celebrate community wins"
```

---

## 📝 Voice Guidelines by Content Type

### Original Content Voice

**Tone**: Thoughtful expert sharing insights
**Style**: "Here's what I've been thinking about..."

```markdown
**Good Examples:**
- "The most fascinating part of web3 adoption isn't the tech—it's watching communities form around shared beliefs rather than geography."
- "Unpopular opinion: The best developers I know spend more time deleting code than writing it."
- "Been tracking DeFi yields for 6 months. The pattern that emerges is pretty counterintuitive..."

**Avoid:**
- "Web3 is revolutionary and will change everything!" (too hyperbolic)
- "HUGE announcement coming soon!" (empty hype)
- "This will disrupt the entire industry!" (overused tech speak)
```

### Trend Response Voice

**Tone**: Informed perspective-giver
**Style**: "Here's what this actually means..."

```markdown
**Good Examples:**
- "While everyone's debating the surface-level drama, the real story is in the smart contract changes that happened quietly yesterday."
- "This trend confirms what we've been seeing in our community data for weeks."
- "Calling it: This 'controversy' will be forgotten in 48 hours, but the underlying tech improvement is permanent."

**Avoid:**
- "Finally someone said it!" (bandwagon jumping)
- "This is exactly why I've been saying..." (self-promotional)
- "Everyone's wrong except me!" (unnecessarily confrontational)
```

### Community Engagement Voice

**Tone**: Supportive community member
**Style**: "Let's figure this out together..."

```markdown
**Good Examples:**
- "Great question! The way I think about it is..."
- "Your point about scalability is spot on. Have you considered..."
- "This is exactly the kind of discussion our community needs more of."

**Avoid:**
- "You're wrong because..." (dismissive)
- "Let me educate you..." (condescending)
- "Obviously..." (assumes knowledge)
```

---

## 🎯 Voice Consistency System

### Automated Voice Scoring

```python
import re
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class VoiceMetrics:
    authenticity_score: float
    expertise_level: float
    community_focus: float
    brand_alignment: float
    overall_score: float

class VoiceConsistencyChecker:
    def __init__(self, voice_profile: dict):
        self.voice_profile = voice_profile
        self.preferred_words = voice_profile['vocabulary_preferences']['preferred_words']
        self.avoided_words = voice_profile['vocabulary_preferences']['avoided_words']
        
    async def score_content_voice(self, content: str) -> VoiceMetrics:
        """Score content against brand voice profile"""
        
        # Authenticity scoring
        authenticity = self._score_authenticity(content)
        
        # Expertise level scoring
        expertise = self._score_expertise_level(content)
        
        # Community focus scoring
        community_focus = self._score_community_focus(content)
        
        # Brand alignment scoring
        brand_alignment = self._score_brand_alignment(content)
        
        # Calculate overall score
        overall = (authenticity + expertise + community_focus + brand_alignment) / 4
        
        return VoiceMetrics(
            authenticity_score=authenticity,
            expertise_level=expertise,
            community_focus=community_focus,
            brand_alignment=brand_alignment,
            overall_score=overall
        )
    
    def _score_authenticity(self, content: str) -> float:
        """Score how authentic the content sounds"""
        score = 0.5  # Base score
        
        # Check for authentic language patterns
        authentic_patterns = [
            r'\bhonestly\b',
            r'\bactually\b', 
            r'\bin my experience\b',
            r'\bI\'ve been\b',
            r'\bwhat I\'ve learned\b'
        ]
        
        for pattern in authentic_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += 0.1
        
        # Penalize inauthentic patterns
        inauthentic_patterns = [
            r'HUGE\s+ANNOUNCEMENT',
            r'GAME[\s-]?CHANGER',
            r'REVOLUTIONARY',
            r'!!+'  # Multiple exclamation marks
        ]
        
        for pattern in inauthentic_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _score_expertise_level(self, content: str) -> float:
        """Score how well content demonstrates expertise"""
        score = 0.3  # Base score
        
        # Technical depth indicators
        expertise_indicators = [
            r'\bdata shows\b',
            r'\bpattern\b',
            r'\btracking\b',
            r'\banalysis\b',
            r'\bmeasured\b',
            r'\bobserved\b'
        ]
        
        for indicator in expertise_indicators:
            if re.search(indicator, content, re.IGNORECASE):
                score += 0.15
        
        # Specific metrics or numbers
        if re.search(r'\b\d+%\b|\b\d+x\b|\b\$\d+\b', content):
            score += 0.1
        
        return min(1.0, score)
    
    def _score_community_focus(self, content: str) -> float:
        """Score how community-focused the content is"""
        score = 0.2  # Base score
        
        community_words = [
            r'\bcommunity\b',
            r'\btogether\b',
            r'\bour\b',
            r'\bwe\b',
            r'\bus\b',
            r'\byour thoughts\b',
            r'\bwhat do you\b'
        ]
        
        for word in community_words:
            if re.search(word, content, re.IGNORECASE):
                score += 0.1
        
        # Questions indicate engagement focus
        if '?' in content:
            score += 0.2
        
        return min(1.0, score)
    
    def _score_brand_alignment(self, content: str) -> float:
        """Score alignment with brand vocabulary preferences"""
        score = 0.5  # Base score
        
        # Preferred words boost
        preferred_count = sum(
            1 for word in self.preferred_words 
            if word.lower() in content.lower()
        )
        score += preferred_count * 0.1
        
        # Avoided words penalty
        avoided_count = sum(
            1 for word in self.avoided_words
            if word.lower() in content.lower()
        )
        score -= avoided_count * 0.2
        
        return max(0.0, min(1.0, score))
```

### Voice Enhancement System

```python
class VoiceEnhancer:
    def __init__(self, voice_profile: dict, claude_client):
        self.voice_profile = voice_profile
        self.claude = claude_client
        self.checker = VoiceConsistencyChecker(voice_profile)
    
    async def enhance_content_voice(self, content: str, target_score: float = 0.8) -> dict:
        """Improve content to better match brand voice"""
        
        current_metrics = await self.checker.score_content_voice(content)
        
        if current_metrics.overall_score >= target_score:
            return {
                'success': True,
                'enhanced_content': content,
                'original_score': current_metrics.overall_score,
                'improvements_made': []
            }
        
        # Generate enhancement suggestions
        enhancement_prompt = self._build_enhancement_prompt(content, current_metrics)
        
        enhanced_result = await self.claude.generate_content(enhancement_prompt)
        
        if enhanced_result['success']:
            enhanced_content = enhanced_result['content']
            new_metrics = await self.checker.score_content_voice(enhanced_content)
            
            return {
                'success': True,
                'enhanced_content': enhanced_content,
                'original_score': current_metrics.overall_score,
                'enhanced_score': new_metrics.overall_score,
                'improvement': new_metrics.overall_score - current_metrics.overall_score
            }
        
        return {'success': False, 'error': enhanced_result.get('error')}
    
    def _build_enhancement_prompt(self, content: str, metrics: VoiceMetrics) -> str:
        """Build prompt to enhance voice consistency"""
        
        issues = []
        if metrics.authenticity_score < 0.7:
            issues.append("make it sound more authentic and genuine")
        if metrics.expertise_level < 0.7:
            issues.append("add more depth and expertise")
        if metrics.community_focus < 0.7:
            issues.append("make it more community-focused and engaging")
        if metrics.brand_alignment < 0.7:
            issues.append("better align with brand vocabulary preferences")
        
        return f"""Improve this content to better match our brand voice:

Original: "{content}"

Brand Voice Profile:
{self.voice_profile}

Specific improvements needed:
{', '.join(issues)}

Requirements:
- Keep the core message and meaning
- Maximum 280 characters
- Make it sound more like our authentic brand voice
- Use preferred vocabulary when possible
- Avoid corporate jargon and hype language

Generate only the improved version, no explanations."""
```

---

## 🎪 Content Examples by Voice Type

### Voice Spectrum Examples

#### **Highly On-Brand (Score: 0.9+)**
```
"Been tracking DeFi yields across 12 protocols for 3 months. The pattern that emerges is fascinating: community-driven projects consistently outperform VC-backed alternatives. What are you seeing in your corner of web3?"
```
*Why it works: Data-driven, community-focused, asks engaging question, uses "fascinating"*

#### **Good On-Brand (Score: 0.7-0.8)**
```
"Honestly, the most underrated skill in web3 isn't coding—it's community building. The best projects I've seen succeed not because of better tech, but because they built genuine relationships first."
```
*Why it works: Uses "honestly", authentic insight, community-focused, but could be more engaging*

#### **Needs Improvement (Score: 0.5-0.6)**
```
"Web3 is going to disrupt everything! This new protocol is a total game-changer that will revolutionize the entire industry. Big announcement coming soon! 🚀🚀🚀"
```
*Why it doesn't work: Hyperbolic language, avoided words, multiple emojis, empty hype*

---

## 📊 Voice Evolution and Learning

### Continuous Voice Improvement

```python
class VoiceLearningSystem:
    def __init__(self, voice_profile: dict):
        self.voice_profile = voice_profile
        self.performance_data = []
    
    async def analyze_content_performance(self, content: str, engagement_metrics: dict) -> dict:
        """Analyze which voice elements correlate with high engagement"""
        
        voice_metrics = await self.checker.score_content_voice(content)
        
        # Correlate voice metrics with engagement
        performance_record = {
            'content': content,
            'voice_metrics': voice_metrics,
            'engagement_rate': engagement_metrics.get('engagement_rate', 0),
            'reach': engagement_metrics.get('reach', 0),
            'replies': engagement_metrics.get('replies', 0),
            'timestamp': datetime.now()
        }
        
        self.performance_data.append(performance_record)
        
        return await self._identify_voice_patterns()
    
    async def _identify_voice_patterns(self) -> dict:
        """Identify which voice characteristics drive best performance"""
        if len(self.performance_data) < 10:
            return {'message': 'Insufficient data for pattern analysis'}
        
        # Analyze high-performing content (top 25%)
        sorted_data = sorted(
            self.performance_data,
            key=lambda x: x['engagement_rate'],
            reverse=True
        )
        
        top_performers = sorted_data[:len(sorted_data)//4]
        
        # Extract patterns from top performers
        patterns = {
            'avg_authenticity': sum(p['voice_metrics'].authenticity_score for p in top_performers) / len(top_performers),
            'avg_expertise': sum(p['voice_metrics'].expertise_level for p in top_performers) / len(top_performers),
            'avg_community_focus': sum(p['voice_metrics'].community_focus for p in top_performers) / len(top_performers),
            'common_elements': self._extract_common_elements(top_performers)
        }
        
        return {
            'high_performance_patterns': patterns,
            'recommendations': self._generate_voice_recommendations(patterns)
        }
    
    def _generate_voice_recommendations(self, patterns: dict) -> list:
        """Generate recommendations for voice optimization"""
        recommendations = []
        
        if patterns['avg_authenticity'] > 0.8:
            recommendations.append("Continue emphasizing authentic, personal language")
        
        if patterns['avg_community_focus'] > 0.7:
            recommendations.append("Community-focused content performs well - maintain this approach")
        
        if patterns['avg_expertise'] > 0.75:
            recommendations.append("Technical depth resonates with audience - include more data/insights")
        
        return recommendations
```

---

## 🎭 Voice Customization Templates

### Voice Adaptation by Context

```yaml
# config/voice_contexts.yaml
voice_contexts:
  crisis_communication:
    tone_adjustments:
      - "more_measured"
      - "less_promotional" 
      - "increased_empathy"
    additional_guidelines:
      - "Acknowledge uncertainty when appropriate"
      - "Focus on facts over speculation"
      - "Show support for affected community"
  
  celebration_moments:
    tone_adjustments:
      - "more_enthusiastic"
      - "community_spotlight"
      - "genuine_excitement"
    additional_guidelines:
      - "Highlight community contributions"
      - "Share in the excitement authentically"
      - "Connect success to broader mission"
  
  educational_content:
    tone_adjustments:
      - "patient_teacher"
      - "assumption_free"
      - "step_by_step"
    additional_guidelines:
      - "Define technical terms"
      - "Use analogies when helpful"
      - "Encourage questions"
      
  controversial_topics:
    tone_adjustments:
      - "respectfully_contrarian"
      - "data_focused"
      - "acknowledge_complexity"
    additional_guidelines:
      - "Present multiple perspectives"
      - "Back opinions with reasoning"
      - "Invite thoughtful disagreement"
```

This comprehensive voice and brand guidelines framework ensures consistent, authentic communication that builds genuine community engagement while maintaining your unique brand personality across all content.