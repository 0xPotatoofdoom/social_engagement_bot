#!/usr/bin/env python3
"""
Content Generation Testing Script

Test the complete pipeline: keyword search → sentiment analysis → content generation
Shows the full workflow from finding opportunities to generating responses.
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
    from bot.monitoring.trend_monitor import TrendMonitor
    from bot.content.generator import ContentGenerator, ContentGenerationRequest, ContentType, VoiceTone
    print("✅ Successfully imported all content generation components")
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


async def test_full_content_pipeline():
    """Test the complete pipeline: search → analyze → generate content."""
    print("🚀 FULL CONTENT GENERATION PIPELINE TEST")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return False
    
    try:
        # Initialize all clients
        x_client = XAPIClient(**x_credentials)
        print("✅ X API client initialized")
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            print("✅ Claude API client initialized")
            
            # Initialize content generator
            content_generator = ContentGenerator(claude_client)
            print("✅ Content generator initialized")
            
            # Search for opportunities
            search_keywords = ["uniswap v4", "defi protocol", "blockchain"]
            trend_monitor = TrendMonitor(
                x_client=x_client,
                claude_client=claude_client,
                search_keywords=search_keywords
            )
            
            print(f"\n🔍 Step 1: Searching for opportunities...")
            print(f"Keywords: {', '.join(search_keywords)}")
            
            await trend_monitor.search_keyword_opportunities()
            opportunities = trend_monitor.get_top_opportunities(limit=5)
            
            if not opportunities:
                print("❌ No opportunities found to generate content for")
                print("💡 Try running the keyword search test first to ensure opportunities are being found")
                return False
            
            print(f"✅ Found {len(opportunities)} high-quality opportunities")
            
            # Generate content for each opportunity
            print(f"\n🎨 Step 2: Generating content for opportunities...")
            generated_content = []
            
            for i, opportunity in enumerate(opportunities, 1):
                print(f"\n--- Opportunity {i} ---")
                print(f"Keyword: {opportunity.context.get('keyword')}")
                print(f"Original Tweet: {opportunity.context.get('text', '')[:100]}...")
                print(f"Suggested Approach: {opportunity.suggested_approach}")
                
                try:
                    # Generate content for this opportunity
                    generated = await content_generator.generate_for_opportunity(opportunity)
                    generated_content.append((opportunity, generated))
                    
                    print(f"✅ Generated Content:")
                    print(f"   Text: {generated.text}")
                    print(f"   Type: {generated.content_type.value}")
                    print(f"   Characters: {generated.character_count}/280")
                    print(f"   Voice Score: {generated.voice_score:.2f}/1.0")
                    print(f"   Quality Score: {generated.quality_score:.2f}/1.0")
                    
                    if generated.hashtags:
                        print(f"   Hashtags: {', '.join(generated.hashtags)}")
                    
                    # Rate limit between generations
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Content generation failed: {e}")
            
            if generated_content:
                print(f"\n🏆 Step 3: Content Quality Analysis")
                print("=" * 50)
                
                # Analyze the generated content
                total_voice_score = sum(content.voice_score for _, content in generated_content)
                total_quality_score = sum(content.quality_score for _, content in generated_content)
                avg_voice = total_voice_score / len(generated_content)
                avg_quality = total_quality_score / len(generated_content)
                
                print(f"📊 Generation Statistics:")
                print(f"   Total content pieces: {len(generated_content)}")
                print(f"   Average voice score: {avg_voice:.2f}/1.0")
                print(f"   Average quality score: {avg_quality:.2f}/1.0")
                
                # Show best content
                best_content = max(generated_content, key=lambda x: x[1].voice_score * x[1].quality_score)
                best_opp, best_gen = best_content
                
                print(f"\n🥇 BEST GENERATED CONTENT:")
                print(f"   Responding to: {best_opp.context.get('keyword')}")
                print(f"   Original: {best_opp.context.get('text', '')[:80]}...")
                print(f"   Generated: {best_gen.text}")
                print(f"   Combined Score: {best_gen.voice_score * best_gen.quality_score:.3f}")
                print(f"   Why it's good: High voice consistency + quality")
                
                # Show generation stats
                gen_stats = content_generator.get_generation_stats()
                print(f"\n📈 Generator Performance:")
                print(f"   Total generated: {gen_stats['total_generated']}")
                print(f"   By type: {gen_stats['by_type']}")
                print(f"   Avg voice score: {gen_stats['avg_voice_score']:.2f}")
                print(f"   Avg quality score: {gen_stats['avg_quality_score']:.2f}")
                
                return True
            
            else:
                print("❌ No content was successfully generated")
                return False
    
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False


async def test_single_content_generation():
    """Test generating content for a single example opportunity."""
    print("\n🎯 SINGLE CONTENT GENERATION TEST")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    # Create a sample opportunity for testing
    sample_opportunity = {
        'text': "Has anyone tried the new uniswap v4 hooks yet? Looking for feedback on the developer experience.",
        'keyword': 'uniswap v4',
        'author_id': 'test_user',
        'tweet_id': '12345'
    }
    
    print(f"📝 Sample Opportunity:")
    print(f"   Text: {sample_opportunity['text']}")
    print(f"   Keyword: {sample_opportunity['keyword']}")
    
    try:
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            content_generator = ContentGenerator(claude_client)
            
            # Test different content types
            content_types = [
                (ContentType.REPLY, VoiceTone.HELPFUL),
                (ContentType.QUOTE_TWEET, VoiceTone.TECHNICAL),
                (ContentType.REPLY, VoiceTone.ENTHUSIASTIC)
            ]
            
            for content_type, voice_tone in content_types:
                print(f"\n🎨 Generating {content_type.value} with {voice_tone.value} tone...")
                
                request = ContentGenerationRequest(
                    opportunity_id="test_123",
                    content_type=content_type,
                    context=sample_opportunity,
                    voice_tone=voice_tone
                )
                
                try:
                    generated = await content_generator.generate_content(request)
                    
                    print(f"✅ Generated {content_type.value}:")
                    print(f"   Content: {generated.text}")
                    print(f"   Characters: {generated.character_count}/280")
                    print(f"   Voice Score: {generated.voice_score:.2f}")
                    print(f"   Quality Score: {generated.quality_score:.2f}")
                    
                    if generated.revision_notes:
                        print(f"   Revision Notes: {', '.join(generated.revision_notes)}")
                
                except Exception as e:
                    print(f"❌ Generation failed for {content_type.value}: {e}")
                
                # Rate limit
                await asyncio.sleep(1)
    
    except Exception as e:
        print(f"❌ Single content generation test failed: {e}")


async def test_batch_content_generation():
    """Test generating content for multiple opportunities at once."""
    print("\n📦 BATCH CONTENT GENERATION TEST")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    # Create multiple sample opportunities
    sample_opportunities = [
        {
            'text': "Just deployed my first smart contract on mainnet! 🎉",
            'keyword': 'smart contracts',
            'author_id': 'dev_user',
            'tweet_id': '11111'
        },
        {
            'text': "The gas fees are getting ridiculous... when will layer 2 solutions really take off?",
            'keyword': 'defi',
            'author_id': 'frustrated_user', 
            'tweet_id': '22222'
        },
        {
            'text': "Can someone explain how impermanent loss works in simple terms?",
            'keyword': 'defi protocol',
            'author_id': 'learning_user',
            'tweet_id': '33333'
        }
    ]
    
    print(f"📝 Testing with {len(sample_opportunities)} sample opportunities")
    
    try:
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            content_generator = ContentGenerator(claude_client)
            
            # Create batch requests
            requests = []
            for i, opp in enumerate(sample_opportunities):
                request = ContentGenerationRequest(
                    opportunity_id=f"batch_{i}",
                    content_type=ContentType.REPLY,
                    context=opp,
                    voice_tone=VoiceTone.HELPFUL
                )
                requests.append(request)
            
            print(f"\n🚀 Generating content for batch of {len(requests)} opportunities...")
            
            # Generate batch content
            generated_batch = await content_generator.generate_batch_content(requests)
            
            print(f"\n📊 Batch Results:")
            print(f"   Requested: {len(requests)}")
            print(f"   Generated: {len(generated_batch)}")
            print(f"   Success Rate: {len(generated_batch)/len(requests)*100:.1f}%")
            
            for i, (original, generated) in enumerate(zip(sample_opportunities, generated_batch)):
                print(f"\n{i+1}. Original: {original['text'][:60]}...")
                print(f"   Generated: {generated.text}")
                print(f"   Scores: Voice {generated.voice_score:.2f} | Quality {generated.quality_score:.2f}")
            
            # Show stats
            stats = content_generator.get_generation_stats()
            print(f"\n📈 Final Generator Stats:")
            print(f"   Total generated: {stats['total_generated']}")
            print(f"   Average voice score: {stats['avg_voice_score']:.2f}")
            print(f"   Average quality score: {stats['avg_quality_score']:.2f}")
    
    except Exception as e:
        print(f"❌ Batch generation test failed: {e}")


async def export_generated_content():
    """Export generated content with full details for review."""
    print("\n💾 EXPORT GENERATED CONTENT")
    print("=" * 60)
    
    # Get credentials
    x_credentials, claude_api_key = get_credentials()
    if not x_credentials or not claude_api_key:
        return
    
    try:
        # Initialize systems
        x_client = XAPIClient(**x_credentials)
        
        async with ClaudeAPIClient(claude_api_key) as claude_client:
            content_generator = ContentGenerator(claude_client)
            
            # Find opportunities
            trend_monitor = TrendMonitor(
                x_client=x_client,
                claude_client=claude_client,
                search_keywords=["defi", "uniswap", "blockchain"]
            )
            
            print("🔍 Finding opportunities...")
            await trend_monitor.search_keyword_opportunities()
            opportunities = trend_monitor.get_top_opportunities(limit=8)
            
            if opportunities:
                print(f"📝 Generating content for {len(opportunities)} opportunities...")
                
                export_data = []
                for i, opp in enumerate(opportunities):
                    try:
                        generated = await content_generator.generate_for_opportunity(opp)
                        
                        export_item = {
                            'opportunity': {
                                'keyword': opp.context.get('keyword'),
                                'original_text': opp.context.get('text'),
                                'author_id': opp.context.get('author_id'),
                                'tweet_id': opp.context.get('tweet_id'),
                                'relevance_score': opp.relevance_score,
                                'urgency_score': opp.urgency_score,
                                'suggested_approach': opp.suggested_approach
                            },
                            'generated_content': {
                                'text': generated.text,
                                'content_type': generated.content_type.value,
                                'character_count': generated.character_count,
                                'voice_score': generated.voice_score,
                                'quality_score': generated.quality_score,
                                'hashtags': generated.hashtags,
                                'mentions': generated.mentions,
                                'generated_at': generated.generated_at.isoformat()
                            },
                            'combined_score': opp.relevance_score * opp.urgency_score * generated.voice_score * generated.quality_score,
                            'ready_to_post': generated.voice_score > 0.7 and generated.quality_score > 0.7
                        }
                        export_data.append(export_item)
                        
                    except Exception as e:
                        print(f"❌ Failed to generate content for opportunity {i+1}: {e}")
                    
                    await asyncio.sleep(1)  # Rate limit
                
                if export_data:
                    # Sort by combined score
                    export_data.sort(key=lambda x: x['combined_score'], reverse=True)
                    
                    # Save to file
                    filename = f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                    
                    print(f"✅ Exported {len(export_data)} generated content pieces to {filename}")
                    
                    # Show summary
                    ready_to_post = sum(1 for item in export_data if item['ready_to_post'])
                    print(f"\n📊 Export Summary:")
                    print(f"   Total generated: {len(export_data)}")
                    print(f"   Ready to post: {ready_to_post}")
                    print(f"   Needs review: {len(export_data) - ready_to_post}")
                    
                    # Show top 3
                    print(f"\n🏆 TOP 3 READY-TO-POST CONTENT:")
                    for i, item in enumerate([x for x in export_data if x['ready_to_post']][:3], 1):
                        print(f"\n{i}. Score: {item['combined_score']:.3f}")
                        print(f"   Original: {item['opportunity']['original_text'][:60]}...")
                        print(f"   Generated: {item['generated_content']['text']}")
                        print(f"   Type: {item['generated_content']['content_type']}")
                
                else:
                    print("❌ No content was successfully generated for export")
            
            else:
                print("❌ No opportunities found to generate content for")
    
    except Exception as e:
        print(f"❌ Export failed: {e}")


async def main():
    """Main test menu for content generation."""
    while True:
        print("\n" + "=" * 60)
        print("🎨 CONTENT GENERATION TESTING")
        print("=" * 60)
        print()
        print("1. 🚀 Test Full Pipeline (Search → Analyze → Generate)")
        print("2. 🎯 Test Single Content Generation")
        print("3. 📦 Test Batch Content Generation")
        print("4. 💾 Export Generated Content for Review")
        print("5. 📊 Show Content Generation Examples")
        print("6. 🚪 Exit")
        print()
        
        choice = input("Choose an option (1-6): ").strip()
        
        if choice == "1":
            await test_full_content_pipeline()
        elif choice == "2":
            await test_single_content_generation()
        elif choice == "3":
            await test_batch_content_generation()
        elif choice == "4":
            await export_generated_content()
        elif choice == "5":
            print("\n📚 CONTENT GENERATION EXAMPLES")
            print("=" * 50)
            print("🎯 REPLY Example:")
            print("  Original: 'Has anyone tried Uniswap v4 hooks yet?'")
            print("  Generated: 'Great question! V4 hooks unlock amazing composability. The pre/post swap hooks let you build custom logic directly into the DEX. Perfect for MEV protection, dynamic fees, or custom oracles. What specific use case are you exploring? #DeFi'")
            print()
            print("🔁 QUOTE TWEET Example:")
            print("  Original: 'DeFi yields are dropping everywhere'")
            print("  Generated: 'This is actually healthy market maturation. As DeFi protocols optimize and competition increases, yields normalize to reflect real economic value rather than unsustainable incentives. Focus on protocol fundamentals and long-term utility.'")
            print()
            print("🧵 THREAD Example:")
            print("  Original: 'Can someone explain impermanent loss?'")  
            print("  Generated: 'Thread: Understanding Impermanent Loss 🧵\n\n1/ IL happens when token prices in your LP position diverge from when you deposited. The \"loss\" is compared to just holding the tokens...'")
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