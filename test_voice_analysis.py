#!/usr/bin/env python3
"""
Voice Analysis Testing Script

Analyzes your posting history to learn voice patterns, engagement drivers,
and provides recommendations for voice tuning to improve content generation.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add src to path so we can import our implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import our implementations
try:
    from bot.api.x_client import XAPIClient
    from bot.api.claude_client import ClaudeAPIClient
    from bot.analytics.voice_analyzer import VoiceAnalyzer
    from bot.content.generator import ContentGenerator, VoiceGuidelines
    print("✅ Successfully imported voice analysis components")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def get_credentials():
    """Get API credentials from environment."""
    x_credentials = {
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET'),
        'bearer_token': os.getenv('X_BEARER_TOKEN')
    }
    
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    
    # Validate credentials
    missing_x = [k for k, v in x_credentials.items() if not v]
    if missing_x:
        print(f"❌ Missing X API credentials: {missing_x}")
        return None, None
    
    if not claude_api_key:
        print("❌ Missing Claude API key")
        return None, None
    
    print("✅ All API credentials loaded from environment")
    return x_credentials, claude_api_key


async def analyze_posting_history():
    """Analyze user's posting history for voice patterns."""
    print("📊 POSTING HISTORY VOICE ANALYSIS")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return None
    
    try:
        # Initialize clients
        x_client = XAPIClient(**x_credentials)
        print("✅ X API client initialized")
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            print("✅ Claude API client initialized")
            
            # Initialize voice analyzer
            voice_analyzer = VoiceAnalyzer(x_client, claude_client)
            print("✅ Voice analyzer initialized")
            
            # Analyze posting history
            print("\n🔍 Fetching and analyzing your recent posts...")
            print("⏳ This will take a moment to analyze each post...")
            
            max_posts = int(input("How many recent posts to analyze? (recommended: 20-50): ") or "30")
            
            voice_profile = await voice_analyzer.analyze_posting_history(max_posts)
            
            if not voice_profile:
                print("❌ Failed to analyze posting history")
                return None
            
            # Display analysis results
            print(f"\n📈 VOICE ANALYSIS RESULTS")
            print("=" * 50)
            
            stats = voice_analyzer.get_analysis_stats()
            print(f"📊 Analysis Statistics:")
            print(f"   Posts analyzed: {stats['posts_analyzed']}")
            print(f"   Analysis completed: {stats['last_analysis']}")
            
            print(f"\n🎭 Voice Characteristics (Average):")
            tone_dist = voice_profile.tone_distribution
            for characteristic, score in tone_dist.items():
                emoji = "🔥" if score > 0.7 else "✅" if score > 0.5 else "📈"
                print(f"   {emoji} {characteristic.replace('_', ' ').title()}: {score:.2f}/1.0")
            
            print(f"\n🚀 Engagement Drivers:")
            for i, driver in enumerate(voice_profile.engagement_drivers, 1):
                print(f"   {i}. {driver.replace('_', ' ').title()}")
            
            if not voice_profile.engagement_drivers:
                print("   📊 Not enough engagement data to identify clear drivers")
            
            print(f"\n📱 Best Performing Content Themes:")
            for i, theme in enumerate(voice_profile.best_posting_themes[:5], 1):
                print(f"   {i}. {theme}")
            
            print(f"\n#️⃣ Most Successful Hashtags:")
            for i, hashtag in enumerate(voice_profile.preferred_hashtags[:8], 1):
                print(f"   {i}. {hashtag}")
            
            print(f"\n📏 Optimal Content Length:")
            min_len, max_len = voice_profile.optimal_length_range
            print(f"   Optimal range: {min_len}-{max_len} characters")
            
            print(f"\n🔗 Engagement Correlations:")
            correlations = voice_profile.engagement_correlations
            for characteristic, correlation in correlations.items():
                direction = "📈 Positive" if correlation > 0.3 else "📉 Negative" if correlation < -0.3 else "➡️ Neutral"
                print(f"   {direction} {characteristic.replace('_', ' ').title()}: {correlation:.2f}")
            
            # Show successful patterns
            patterns = voice_profile.successful_patterns
            if patterns.get('technical_terms'):
                print(f"\n🔧 Your Technical Vocabulary:")
                print(f"   {', '.join(patterns['technical_terms'][:10])}")
            
            if patterns.get('engagement_tactics'):
                print(f"\n💡 Your Engagement Tactics:")
                for tactic in patterns['engagement_tactics']:
                    print(f"   • {tactic.replace('_', ' ').title()}")
            
            return voice_profile
    
    except Exception as e:
        print(f"❌ Voice analysis failed: {e}")
        return None


async def get_voice_tuning_recommendations():
    """Get personalized voice tuning recommendations."""
    print("\n🎯 VOICE TUNING RECOMMENDATIONS")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    try:
        # Initialize clients
        x_client = XAPIClient(**x_credentials)
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            voice_analyzer = VoiceAnalyzer(x_client, claude_client)
            
            # Analyze posting history
            print("🔍 Analyzing your posting patterns...")
            voice_profile = await voice_analyzer.analyze_posting_history(30)
            
            if not voice_profile:
                print("❌ Could not generate recommendations without voice analysis")
                return
            
            # Generate recommendations
            recommendations = await voice_analyzer.generate_voice_tuning_recommendations()
            
            print(f"\n🔧 VOICE ADJUSTMENTS:")
            for i, adjustment in enumerate(recommendations.voice_adjustments, 1):
                print(f"   {i}. {adjustment}")
            
            print(f"\n📝 CONTENT SUGGESTIONS:")
            for i, suggestion in enumerate(recommendations.content_suggestions, 1):
                print(f"   {i}. {suggestion}")
            
            print(f"\n🚀 ENGAGEMENT OPTIMIZATIONS:")
            for i, optimization in enumerate(recommendations.engagement_optimizations, 1):
                print(f"   {i}. {optimization}")
            
            print(f"\n#️⃣ RECOMMENDED HASHTAGS:")
            hashtags = recommendations.hashtag_recommendations
            print(f"   {', '.join(hashtags)}")
            
            print(f"\n🎭 TONE RECOMMENDATIONS:")
            for aspect, recommendation in recommendations.tone_recommendations.items():
                print(f"   • {aspect.replace('_', ' ').title()}: {recommendation}")
            
            print(f"\n📏 LENGTH RECOMMENDATION:")
            print(f"   {recommendations.length_recommendations}")
            
            return recommendations
    
    except Exception as e:
        print(f"❌ Recommendation generation failed: {e}")


async def compare_voice_profiles():
    """Compare current voice with generated content voice."""
    print("\n⚖️ VOICE COMPARISON: YOUR POSTS vs GENERATED CONTENT")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    try:
        # Initialize clients
        x_client = XAPIClient(**x_credentials)
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            # Analyze user's voice
            print("🔍 Step 1: Analyzing your authentic voice...")
            voice_analyzer = VoiceAnalyzer(x_client, claude_client)
            user_voice_profile = await voice_analyzer.analyze_posting_history(20)
            
            if not user_voice_profile:
                print("❌ Could not analyze your voice profile")
                return
            
            # Create content generator with learned voice
            print("🎨 Step 2: Creating content generator with your voice profile...")
            
            # Convert voice profile to voice guidelines
            learned_guidelines = VoiceGuidelines(
                personality_traits=[
                    f"Technical expertise: {user_voice_profile.tone_distribution.get('technical_expertise', 0.5):.1f}/1.0",
                    f"Approachability: {user_voice_profile.tone_distribution.get('approachability', 0.5):.1f}/1.0",
                    f"Enthusiasm: {user_voice_profile.tone_distribution.get('enthusiasm', 0.5):.1f}/1.0"
                ],
                expertise_areas=user_voice_profile.best_posting_themes[:5],
                preferred_tone="Learned from your successful posts",
                avoid_topics=["Financial advice", "Price predictions"],
                sample_tweets=["Your voice pattern will be learned from analysis"],
                hashtag_preferences=user_voice_profile.preferred_hashtags[:8]
            )
            
            content_generator = ContentGenerator(claude_client, learned_guidelines)
            
            # Generate sample content with learned voice
            print("🎯 Step 3: Generating content with your learned voice...")
            
            sample_opportunity = {
                'text': "What are your thoughts on the latest DeFi protocol innovations?",
                'keyword': 'defi protocol',
                'author_id': 'test_user',
                'tweet_id': '12345'
            }
            
            from bot.content.generator import ContentGenerationRequest, ContentType, VoiceTone
            
            request = ContentGenerationRequest(
                opportunity_id="voice_test",
                content_type=ContentType.REPLY,
                context=sample_opportunity,
                voice_tone=VoiceTone.HELPFUL
            )
            
            generated = await content_generator.generate_content(request)
            
            # Compare characteristics
            print(f"\n📊 VOICE COMPARISON RESULTS:")
            print("=" * 50)
            
            print(f"🎭 Your Authentic Voice Profile:")
            user_characteristics = user_voice_profile.tone_distribution
            for char, score in user_characteristics.items():
                print(f"   {char.replace('_', ' ').title()}: {score:.2f}")
            
            print(f"\n🤖 Generated Content Analysis:")
            print(f"   Text: {generated.text}")
            print(f"   Voice Score: {generated.voice_score:.2f}/1.0")
            print(f"   Quality Score: {generated.quality_score:.2f}/1.0")
            
            # Voice alignment assessment
            alignment_score = generated.voice_score
            if alignment_score > 0.8:
                alignment_status = "🎯 Excellent alignment"
            elif alignment_score > 0.6:
                alignment_status = "✅ Good alignment"
            elif alignment_score > 0.4:
                alignment_status = "📈 Moderate alignment - needs tuning"
            else:
                alignment_status = "⚠️ Poor alignment - requires significant tuning"
            
            print(f"\n{alignment_status}")
            print(f"Voice Alignment Score: {alignment_score:.2f}/1.0")
            
            # Recommendations for improvement
            if alignment_score < 0.7:
                print(f"\n🔧 Improvement Recommendations:")
                print(f"   • Fine-tune voice guidelines based on your most successful posts")
                print(f"   • Incorporate your preferred hashtags: {', '.join(user_voice_profile.preferred_hashtags[:3])}")
                print(f"   • Match your optimal content length: {user_voice_profile.optimal_length_range[0]}-{user_voice_profile.optimal_length_range[1]} chars")
                
                if user_characteristics.get('technical_expertise', 0) > 0.7:
                    print(f"   • Increase technical depth in generated content")
                if user_characteristics.get('enthusiasm', 0) > 0.6:
                    print(f"   • Add more enthusiasm to match your natural tone")
                if user_characteristics.get('helpfulness', 0) > 0.7:
                    print(f"   • Emphasize helpful/educational aspects")
    
    except Exception as e:
        print(f"❌ Voice comparison failed: {e}")


async def export_voice_analysis():
    """Export detailed voice analysis for review."""
    print("\n💾 EXPORT VOICE ANALYSIS")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    try:
        x_client = XAPIClient(**x_credentials)
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            voice_analyzer = VoiceAnalyzer(x_client, claude_client)
            
            print("🔍 Analyzing posting history for export...")
            voice_profile = await voice_analyzer.analyze_posting_history(50)
            
            if not voice_profile:
                print("❌ No voice profile to export")
                return
            
            # Prepare export data
            export_data = {
                'analysis_metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'posts_analyzed': len(voice_analyzer.post_analyses),
                    'analysis_version': '1.0'
                },
                'voice_profile': {
                    'tone_distribution': voice_profile.tone_distribution,
                    'engagement_drivers': voice_profile.engagement_drivers,
                    'preferred_hashtags': voice_profile.preferred_hashtags,
                    'best_posting_themes': voice_profile.best_posting_themes,
                    'optimal_length_range': voice_profile.optimal_length_range,
                    'engagement_correlations': voice_profile.engagement_correlations,
                    'successful_patterns': voice_profile.successful_patterns
                },
                'individual_post_analyses': [
                    {
                        'tweet_id': analysis.tweet_id,
                        'text': analysis.text,
                        'engagement_score': analysis.engagement_score,
                        'engagement_metrics': analysis.engagement_metrics,
                        'content_themes': analysis.content_themes,
                        'hashtags': analysis.hashtags,
                        'voice_characteristics': analysis.voice_characteristics,
                        'technical_depth': analysis.technical_depth,
                        'enthusiasm_level': analysis.enthusiasm_level,
                        'helpfulness_score': analysis.helpfulness_score
                    }
                    for analysis in voice_analyzer.post_analyses
                ]
            }
            
            # Generate recommendations
            recommendations = await voice_analyzer.generate_voice_tuning_recommendations()
            export_data['recommendations'] = {
                'voice_adjustments': recommendations.voice_adjustments,
                'content_suggestions': recommendations.content_suggestions,
                'engagement_optimizations': recommendations.engagement_optimizations,
                'hashtag_recommendations': recommendations.hashtag_recommendations,
                'tone_recommendations': recommendations.tone_recommendations,
                'length_recommendations': recommendations.length_recommendations
            }
            
            # Save to file
            filename = f"voice_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"✅ Voice analysis exported to {filename}")
            
            # Show summary
            print(f"\n📊 Export Summary:")
            print(f"   Posts analyzed: {len(voice_analyzer.post_analyses)}")
            print(f"   Voice characteristics identified: {len(voice_profile.tone_distribution)}")
            print(f"   Engagement drivers found: {len(voice_profile.engagement_drivers)}")
            print(f"   Successful themes: {len(voice_profile.best_posting_themes)}")
            print(f"   Recommendations provided: {len(recommendations.voice_adjustments + recommendations.content_suggestions)}")
            
            # Show key insights
            print(f"\n🔑 Key Insights:")
            top_characteristic = max(voice_profile.tone_distribution.items(), key=lambda x: x[1])
            print(f"   • Strongest voice characteristic: {top_characteristic[0].replace('_', ' ').title()} ({top_characteristic[1]:.2f})")
            
            if voice_profile.engagement_drivers:
                print(f"   • Top engagement driver: {voice_profile.engagement_drivers[0].replace('_', ' ').title()}")
            
            if voice_profile.best_posting_themes:
                print(f"   • Best performing theme: {voice_profile.best_posting_themes[0]}")
    
    except Exception as e:
        print(f"❌ Export failed: {e}")


async def main():
    """Main test menu for voice analysis."""
    while True:
        print("\n" + "=" * 60)
        print("🎭 VOICE ANALYSIS & TUNING")
        print("=" * 60)
        print()
        print("1. 📊 Analyze My Posting History & Voice Patterns")
        print("2. 🎯 Get Voice Tuning Recommendations")
        print("3. ⚖️ Compare My Voice vs Generated Content")
        print("4. 💾 Export Detailed Voice Analysis")
        print("5. 📚 Show Voice Analysis Examples")
        print("6. 🚪 Exit")
        print()
        
        choice = input("Choose an option (1-6): ").strip()
        
        if choice == "1":
            await analyze_posting_history()
        elif choice == "2":
            await get_voice_tuning_recommendations()
        elif choice == "3":
            await compare_voice_profiles()
        elif choice == "4":
            await export_voice_analysis()
        elif choice == "5":
            print("\n📚 VOICE ANALYSIS EXAMPLES")
            print("=" * 50)
            print("🎭 Voice Characteristics We Analyze:")
            print("  • Technical Expertise: How much technical knowledge you show")
            print("  • Approachability: How accessible your language is")
            print("  • Enthusiasm: Your excitement/positivity level")
            print("  • Helpfulness: How much value you provide readers")
            print("  • Authority: How confident/authoritative you sound")
            print("  • Conversational: How casual vs formal your tone is")
            print()
            print("📈 Engagement Drivers We Identify:")
            print("  • Technical expertise correlation with likes/retweets")
            print("  • Question usage and reply generation")
            print("  • Hashtag strategy effectiveness")
            print("  • Content theme performance patterns")
            print()
            print("🎯 Tuning Recommendations We Provide:")
            print("  • 'Increase enthusiasm - your excited posts get 2x engagement'")
            print("  • 'Focus on DeFi protocol content - 40% higher engagement'")
            print("  • 'Use #DeFi and #Web3 hashtags - strong performance correlation'")
            print("  • 'Optimal length: 180-250 characters based on your best posts'")
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")