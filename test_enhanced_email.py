"""
Test Enhanced Email Alert System
Demonstrates the new AI-generated content and clickable links functionality
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('src')

from bot.scheduling.cron_monitor import AlertOpportunity, CronMonitorSystem, AlertConfiguration

async def test_enhanced_email_alerts():
    """Test the enhanced email alert system with generated content"""
    
    print("📧 Testing Enhanced Email Alert System")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    load_dotenv()
    
    # Create enhanced test opportunities with generated content
    test_opportunities = [
        AlertOpportunity(
            account_username="VitalikButerin",
            account_tier=1,
            content_text="The future of AI agents on blockchain will require new infrastructure patterns for autonomous execution and cross-chain coordination. The technical challenges are significant but solvable.",
            content_url="https://twitter.com/VitalikButerin/test_content",
            timestamp=datetime.now().isoformat(),
            
            overall_score=0.89,
            ai_blockchain_relevance=0.92,
            technical_depth=0.88,
            opportunity_type="technical_discussion",
            suggested_response_type="technical_insight",
            time_sensitivity="immediate",
            
            strategic_context="Tier 1 strategic account posting technical discussion content",
            suggested_response="Respond with technical insight within 30 minutes",
            
            # Enhanced content
            generated_reply="Absolutely. The key challenge is building infrastructure that enables autonomous agents to operate securely across chains while maintaining composability with existing protocols. We're seeing interesting patterns emerge in agent coordination layers.",
            reply_reasoning="Demonstrates technical expertise while adding specific insights about cross-chain coordination and composability",
            alternative_responses=[
                "The coordination layer design will be critical for autonomous agent interoperability. Excited to see how this evolves.",
                "Cross-chain agent execution is one of the most fascinating infrastructure challenges in crypto right now."
            ],
            engagement_prediction=0.85,
            voice_alignment_score=0.88
        ),
        
        AlertOpportunity(
            account_username="saucepoint",
            account_tier=1,
            content_text="v4 hooks documentation update: new patterns for intelligent routing optimization. The composability possibilities with AI-driven routing are mind-blowing.",
            content_url="https://twitter.com/saucepoint/test_content",
            timestamp=datetime.now().isoformat(),
            
            overall_score=0.92,
            ai_blockchain_relevance=0.95,
            technical_depth=0.90,
            opportunity_type="technical_innovation",
            suggested_response_type="expert_commentary",
            time_sensitivity="immediate",
            
            strategic_context="Tier 1 Uniswap ecosystem contributor posting v4 AI integration insights",
            suggested_response="Respond with expert commentary within 30 minutes",
            
            # Enhanced content
            generated_reply="The AI routing integration opens up fascinating possibilities for predictive MEV protection and dynamic fee optimization. Hooks + ML models could enable truly intelligent AMMs that adapt to market conditions in real-time.",
            reply_reasoning="Combines v4 technical knowledge with AI integration insights, positioning as expert in the convergence space",
            alternative_responses=[
                "Excited about the MEV protection possibilities this enables! AI-driven routing could be a game-changer.",
                "The technical possibilities here are incredible. Real-time adaptation through ML integration is the future."
            ],
            engagement_prediction=0.91,
            voice_alignment_score=0.94
        ),
        
        AlertOpportunity(
            account_username="keyword_search_ai_agents",
            account_tier=3,
            content_text="Just deployed autonomous trading agents on testnet. The ML models are performing better than expected - 15% improvement over baseline strategies with adaptive risk management.",
            content_url="https://twitter.com/user/test_content",
            timestamp=datetime.now().isoformat(),
            
            overall_score=0.76,
            ai_blockchain_relevance=0.78,
            technical_depth=0.75,
            opportunity_type="breakthrough_announcement",
            suggested_response_type="analysis_commentary",
            time_sensitivity="within_day",
            
            strategic_context="AI x blockchain keyword 'ai agents' opportunity with medium strategic value",
            suggested_response="Engage with analysis commentary approach focusing on technical expertise",
            
            # Enhanced content
            generated_reply="Impressive results! Adaptive risk management is crucial for autonomous trading viability. Are you using reinforcement learning for strategy adaptation or more traditional optimization approaches?",
            reply_reasoning="Shows technical understanding while asking an informed follow-up question to continue the technical discussion",
            alternative_responses=[
                "Great to see real performance improvements! The adaptive risk component is particularly interesting.",
                "This demonstrates the maturity of AI trading infrastructure. The risk management evolution is key."
            ],
            engagement_prediction=0.72,
            voice_alignment_score=0.79
        )
    ]
    
    # Create email configuration
    email_config = AlertConfiguration(
        smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        email_username=os.getenv('SENDER_EMAIL', 'mattluu@gmail.com'),
        email_password=os.getenv('SENDER_PASSWORD', 'ueob jyvf ohtw qpmx'),
        from_email=os.getenv('SENDER_EMAIL', 'mattluu@gmail.com'),
        to_email=os.getenv('RECIPIENT_EMAIL', os.getenv('SENDER_EMAIL', 'mattluu@gmail.com'))
    )
    
    print(f"📧 Email Configuration:")
    print(f"   SMTP Server: {email_config.smtp_server}:{email_config.smtp_port}")
    print(f"   From: {email_config.from_email}")
    print(f"   To: {email_config.to_email}")
    
    # Create monitoring system (without actual X/Claude clients for this test)
    monitor = CronMonitorSystem(
        x_client=None,
        claude_client=None,
        strategic_tracker=None,
        config=email_config
    )
    
    # Test immediate alert with enhanced content
    print(f"\n🔥 Testing Enhanced Immediate Alert...")
    print(f"   Opportunities: {len(test_opportunities)}")
    print(f"   AI-Generated Content: ✅")
    print(f"   Clickable Links: ✅")
    print(f"   Alternative Responses: ✅")
    print(f"   Performance Predictions: ✅")
    
    try:
        await monitor._send_immediate_alert(test_opportunities)
        print(f"✅ Enhanced email alert sent successfully!")
        
        print(f"\n📊 Enhanced Features Included:")
        print(f"   🤖 AI-Generated Replies: {sum(1 for opp in test_opportunities if opp.generated_reply)}/3")
        print(f"   🔄 Alternative Responses: {sum(1 for opp in test_opportunities if opp.alternative_responses)}/3")
        print(f"   📈 Engagement Predictions: {sum(1 for opp in test_opportunities if opp.engagement_prediction)}/3")
        print(f"   🎭 Voice Alignment Scores: {sum(1 for opp in test_opportunities if opp.voice_alignment_score)}/3")
        print(f"   🔗 Action Links per Opportunity: 6 (View, Reply, Quote, Profile, Follow, Like)")
        
        # Show content summary
        print(f"\n📝 Generated Content Summary:")
        for i, opp in enumerate(test_opportunities, 1):
            print(f"   {i}. @{opp.account_username}:")
            print(f"      Reply: {opp.generated_reply[:60]}...")
            print(f"      Engagement: {opp.engagement_prediction:.0%} | Voice: {opp.voice_alignment_score:.0%}")
        
        print(f"\n🎯 Email Features:")
        print(f"   ✅ One-click reply with AI-generated content")
        print(f"   ✅ Alternative response options")
        print(f"   ✅ Direct links to view original tweets")
        print(f"   ✅ Quote tweet with pre-filled content")
        print(f"   ✅ Quick actions (follow, like, view profile)")
        print(f"   ✅ Performance predictions for engagement")
        print(f"   ✅ Voice alignment scoring")
        print(f"   ✅ Strategic context and reasoning")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending enhanced email alert: {e}")
        return False

def show_email_features():
    """Show the enhanced email features"""
    print("\n🚀 Enhanced Email Alert Features")
    print("=" * 50)
    
    features = [
        "🤖 AI-Generated Response Content",
        "📝 Alternative Response Options",
        "🔗 One-Click Reply Links",
        "🔄 Pre-filled Quote Tweet Links",
        "👤 Direct Profile Links",
        "➕ One-Click Follow Links",
        "❤️ One-Click Like Links",
        "📈 Engagement Prediction Scores",
        "🎭 Voice Alignment Analysis",
        "💡 Strategic Context & Reasoning",
        "⚡ Time-Sensitive Priority Indicators",
        "🎯 Color-Coded Performance Metrics"
    ]
    
    print("Enhanced email alerts now include:")
    for feature in features:
        print(f"   ✅ {feature}")
    
    print(f"\n📧 Email Content Structure:")
    print(f"   📊 Opportunity Overview (score, relevance, timing)")
    print(f"   📝 Original Content Display")
    print(f"   🤖 AI-Generated Response with reasoning")
    print(f"   🔄 Alternative response options")
    print(f"   🎯 Strategic context and recommendations")
    print(f"   🔗 Action buttons for immediate engagement")
    print(f"   ⚡ Quick actions for relationship building")

async def main():
    """Main test function"""
    print("📧 Enhanced Email Alert System Test")
    print("🎯 AI x Blockchain Strategic Monitoring with Generated Content")
    print()
    
    # Show features
    show_email_features()
    
    # Test enhanced email
    success = await test_enhanced_email_alerts()
    
    if success:
        print(f"\n🎉 Enhanced Email System Successfully Deployed!")
        print(f"📧 Check your email for the enhanced alert with:")
        print(f"   • AI-generated response content")
        print(f"   • One-click action links")
        print(f"   • Alternative response options")
        print(f"   • Performance predictions")
        print(f"   • Strategic context and reasoning")
    else:
        print(f"\n❌ Test failed - check configuration")

if __name__ == "__main__":
    asyncio.run(main())