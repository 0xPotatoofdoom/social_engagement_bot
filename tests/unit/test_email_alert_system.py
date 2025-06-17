"""
Tests for Email Alert System

Tests for the enhanced email alert system with AI-generated content,
action links, and opportunity formatting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart

from src.bot.scheduling.cron_monitor import CronMonitorSystem, AlertConfiguration, AlertOpportunity


class TestEmailAlertSystem:
    """Test email alert functionality."""
    
    @pytest.fixture
    def alert_config(self):
        """Create test alert configuration."""
        return AlertConfiguration(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email_username="test@test.com",
            email_password="testpass",
            from_email="test@test.com",
            to_email="recipient@test.com",
            immediate_threshold=0.8,
            priority_threshold=0.6,
            digest_threshold=0.4
        )
    
    @pytest.fixture
    def sample_opportunities(self):
        """Create sample opportunities focused on Uniswap v4 + Unichain + AI intersection."""
        return [
            AlertOpportunity(
                account_username="saucepoint",
                account_tier=1,
                content_text="v4 hooks with AI-powered routing optimization are showing 40% better execution than traditional AMMs. The intelligent MEV protection patterns are fascinating.",
                content_url="https://twitter.com/saucepoint/status/123456789",
                timestamp=datetime.now().isoformat(),
                overall_score=0.94,
                ai_blockchain_relevance=0.97,
                technical_depth=0.91,
                opportunity_type="uniswap_v4_ai_innovation",
                suggested_response_type="technical_insight",
                time_sensitivity="immediate",
                strategic_context="Core v4 developer discussing AI integration breakthrough",
                suggested_response="Technical analysis of AI-powered hook architecture and MEV implications",
                generated_reply="The AI-routing integration is a game changer. Hooks that can predict and adapt to MEV patterns in real-time will fundamentally shift how we think about DEX architecture. Are you seeing similar improvements in gas optimization?",
                reply_reasoning="Shows deep v4 technical knowledge while adding MEV expertise angle",
                alternative_responses=[
                    "This validates the thesis that intelligent hooks will eat traditional AMM designs for breakfast",
                    "The MEV protection angle here is brilliant - predictive routing is the future"
                ],
                engagement_prediction=0.91,
                voice_alignment_score=0.96
            ),
            AlertOpportunity(
                account_username="VitalikButerin", 
                account_tier=1,
                content_text="Unichain's architecture enables autonomous trading agents that can operate with cryptographic guarantees. This is what we've been building toward.",
                content_url="https://twitter.com/VitalikButerin/status/987654321",
                timestamp=datetime.now().isoformat(),
                overall_score=0.89,
                ai_blockchain_relevance=0.93,
                technical_depth=0.87,
                opportunity_type="unichain_ai_agents",
                suggested_response_type="forward_thinking_analysis",
                time_sensitivity="immediate",
                strategic_context="Ethereum founder highlighting Unichain AI capabilities",
                suggested_response="Deep dive into autonomous agent architecture on Unichain",
                generated_reply="The cryptographic guarantees for autonomous agents on Unichain unlock entirely new design spaces. I'm particularly excited about the implications for cross-chain AI coordination and trustless agent interactions.",
                reply_reasoning="Combines Unichain technical depth with forward-thinking AI analysis",
                alternative_responses=[
                    "This is the infrastructure foundation needed for truly autonomous DeFi protocols",
                    "Unichain + AI agents = the rails for the next generation of crypto-native applications"
                ],
                engagement_prediction=0.88,
                voice_alignment_score=0.92
            )
        ]
    
    @pytest.fixture
    def monitor_system(self, alert_config):
        """Create monitor system for testing."""
        x_client = AsyncMock()
        claude_client = AsyncMock()
        strategic_tracker = AsyncMock()
        return CronMonitorSystem(x_client, claude_client, strategic_tracker, alert_config)
    
    @pytest.mark.unit
    def test_alert_configuration_validation(self, alert_config):
        """Test alert configuration is properly validated."""
        assert alert_config.smtp_server == "smtp.gmail.com"
        assert alert_config.smtp_port == 587
        assert alert_config.immediate_threshold == 0.8
        assert alert_config.priority_threshold == 0.6
        assert alert_config.digest_threshold == 0.4
    
    @pytest.mark.unit
    def test_detailed_email_system_active(self, monitor_system, sample_opportunities):
        """Test detailed email system is active and concise methods are removed."""
        # Verify the current detailed system works
        assert hasattr(monitor_system, '_send_priority_alerts')
        assert hasattr(monitor_system, '_generate_original_content')
        assert hasattr(monitor_system, '_send_detailed_alert_with_original_content')
        
        # Verify concise methods are gone (dead code cleanup successful)
        assert not hasattr(monitor_system, '_send_concise_alert')
        assert not hasattr(monitor_system, '_generate_concise_email')
        assert not hasattr(monitor_system, '_generate_concise_html')
        assert not hasattr(monitor_system, '_generate_concise_subject')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_original_content_generation(self, monitor_system):
        """Test original content generation for trending topics and unhinged takes."""
        # Test trending topic generation
        trending_content = await monitor_system._generate_original_content(content_type="trending_topic")
        
        assert trending_content is not None
        assert trending_content['content_type'] == 'trending_topic'
        assert 'content' in trending_content
        assert len(trending_content['content']) <= 280  # Twitter character limit
        assert any(keyword in trending_content['content'].lower() 
                  for keyword in ['uniswap', 'unichain', 'ai', 'blockchain', 'defi'])
        
        # Test unhinged take generation
        unhinged_content = await monitor_system._generate_original_content(content_type="unhinged_take")
        
        assert unhinged_content is not None
        assert unhinged_content['content_type'] == 'unhinged_take'
        assert 'content' in unhinged_content
        assert len(unhinged_content['content']) <= 280
        assert unhinged_content['engagement_bait'] is True
    
    @pytest.mark.unit
    def test_focused_keyword_filtering(self, monitor_system):
        """Test filtering focuses on Uniswap v4/Unichain/AI intersection."""
        keywords = monitor_system._get_focused_keywords()
        
        # Should contain specific v4/Unichain/AI intersection terms
        expected_keywords = [
            "uniswap v4 ai",
            "unichain autonomous trading", 
            "v4 hooks ai",
            "unichain ai agents",
            "intelligent hooks",
            "ai-powered routing"
        ]
        
        for keyword in expected_keywords:
            assert keyword in keywords
        
        # Should be a concise list (not overwhelming)
        assert len(keywords) <= 10
    
    @pytest.mark.unit
    def test_detailed_html_system_active(self, monitor_system):
        """Test detailed HTML generation system is active."""
        # Verify the current detailed HTML system works
        assert hasattr(monitor_system, '_generate_detailed_alert_with_original_html')
        
        # Verify old concise HTML method is gone
        assert not hasattr(monitor_system, '_generate_concise_html')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unhinged_content_generation(self, monitor_system):
        """Test system generates unhinged content properly."""
        # Test unhinged take generation (now part of detailed system)
        unhinged_content = await monitor_system._generate_original_content('unhinged_take')
        
        # Should have proper structure
        assert 'content_type' in unhinged_content
        assert 'content' in unhinged_content
        assert unhinged_content['content_type'] == 'unhinged_take'
        
        # Content should be present
        content = unhinged_content['content']
        assert content is not None
        assert content != ""
        assert isinstance(content, str)
    
    @pytest.mark.unit
    def test_generate_twitter_intent_urls(self, monitor_system, sample_opportunities):
        """Test Twitter intent URL generation."""
        opportunity = sample_opportunities[0]
        
        # Test reply URL generation
        reply_url = monitor_system._generate_reply_url(opportunity)
        assert "twitter.com/intent/tweet" in reply_url
        assert "in_reply_to=123456789" in reply_url
        
        # Test quote URL generation  
        quote_url = monitor_system._generate_quote_url(opportunity)
        assert "twitter.com/intent/tweet" in quote_url
        assert "url=https://twitter.com/VitalikButerin/status/123456789" in quote_url
        
        # Test follow URL generation
        follow_url = monitor_system._generate_follow_url(opportunity)
        assert "twitter.com/intent/follow" in follow_url
        assert "screen_name=VitalikButerin" in follow_url
        
        # Test like URL generation
        like_url = monitor_system._generate_like_url(opportunity)
        assert "twitter.com/intent/like" in like_url
        assert "tweet_id=123456789" in like_url
    
    @pytest.mark.unit
    def test_ai_generated_content_inclusion(self, monitor_system, sample_opportunities):
        """Test AI-generated content is properly included in alerts."""
        html_content = monitor_system._generate_alert_html(
            opportunities=sample_opportunities[:1], 
            alert_type="IMMEDIATE",
            summary_stats={'total_opportunities': 1, 'avg_score': 0.92}
        )
        
        opportunity = sample_opportunities[0]
        
        # Check that AI-generated content is included
        assert opportunity.generated_reply in html_content
        assert opportunity.reply_reasoning in html_content
        assert str(opportunity.engagement_prediction) in html_content
        assert str(opportunity.voice_alignment_score) in html_content
        
        # Check alternative responses are included
        for alt_response in opportunity.alternative_responses:
            assert alt_response in html_content
    
    @pytest.mark.unit
    def test_email_subject_system_active(self, monitor_system):
        """Test email subject system is properly integrated."""
        # Verify the current detailed system handles subjects
        assert hasattr(monitor_system, '_send_detailed_alert_with_original_content')
        
        # Verify old concise subject method is gone
        assert not hasattr(monitor_system, '_generate_concise_subject')
    
    @pytest.mark.unit
    def test_immediate_alert_method_removed(self, monitor_system):
        """Test immediate alert method was removed as dead code."""
        # Verify immediate alert method is gone (dead code cleanup)
        assert not hasattr(monitor_system, '_send_immediate_alert')
        
        # Verify current priority alert system is active
        assert hasattr(monitor_system, '_send_priority_alerts')
    
    @pytest.mark.unit
    def test_opportunity_with_enhanced_content(self):
        """Test opportunity with all enhanced content fields."""
        opportunity = AlertOpportunity(
            account_username="testuser",
            account_tier=1,
            content_text="Test AI blockchain content",
            content_url="https://twitter.com/test/status/123",
            timestamp=datetime.now().isoformat(),
            overall_score=0.85,
            ai_blockchain_relevance=0.9,
            technical_depth=0.8,
            opportunity_type="technical_discussion",
            suggested_response_type="technical_insight",
            time_sensitivity="immediate",
            strategic_context="Test context",
            suggested_response="Test response",
            generated_reply="AI-generated reply with technical insights",
            reply_reasoning="Demonstrates expertise while adding value",
            alternative_responses=["Alternative 1", "Alternative 2"],
            engagement_prediction=0.87,
            voice_alignment_score=0.91
        )
        
        # Verify all enhanced fields are present
        assert opportunity.generated_reply == "AI-generated reply with technical insights"
        assert opportunity.reply_reasoning == "Demonstrates expertise while adding value"
        assert len(opportunity.alternative_responses) == 2
        assert opportunity.engagement_prediction == 0.87
        assert opportunity.voice_alignment_score == 0.91
    
    @pytest.mark.unit
    def test_alert_history_tracking(self, monitor_system, sample_opportunities):
        """Test alert history is properly tracked."""
        initial_history_count = len(monitor_system.alert_history)
        
        monitor_system._record_alert("immediate", len(sample_opportunities))
        
        assert len(monitor_system.alert_history) == initial_history_count + 1
        
        latest_alert = monitor_system.alert_history[-1]
        assert latest_alert['type'] == "immediate"
        assert latest_alert['opportunity_count'] == len(sample_opportunities)
        assert 'timestamp' in latest_alert
    
    @pytest.mark.unit
    def test_email_content_safety(self, monitor_system):
        """Test email content is properly sanitized."""
        # Test with potentially problematic content
        opportunity = AlertOpportunity(
            account_username="test<script>alert('xss')</script>",
            account_tier=1,
            content_text="Test content with <b>HTML</b> & special chars",
            content_url="https://twitter.com/test",
            timestamp=datetime.now().isoformat(),
            overall_score=0.8,
            ai_blockchain_relevance=0.8,
            technical_depth=0.7,
            opportunity_type="test",
            suggested_response_type="test",
            time_sensitivity="test",
            strategic_context="test",
            suggested_response="test"
        )
        
        html_content = monitor_system._generate_alert_html(
            opportunities=[opportunity],
            alert_type="TEST",
            summary_stats={'total_opportunities': 1, 'avg_score': 0.8}
        )
        
        # Verify HTML is escaped or sanitized
        assert "<script>" not in html_content
        assert "&lt;b&gt;" in html_content or "<b>" in html_content  # Either escaped or allowed
    
    @pytest.mark.unit
    def test_performance_metrics_inclusion(self, monitor_system, sample_opportunities):
        """Test performance metrics are included in email alerts."""
        summary_stats = {
            'total_opportunities': len(sample_opportunities),
            'avg_score': sum(opp.overall_score for opp in sample_opportunities) / len(sample_opportunities),
            'avg_voice_alignment': sum(opp.voice_alignment_score or 0 for opp in sample_opportunities) / len(sample_opportunities),
            'avg_engagement_prediction': sum(opp.engagement_prediction or 0 for opp in sample_opportunities) / len(sample_opportunities)
        }
        
        html_content = monitor_system._generate_alert_html(
            opportunities=sample_opportunities,
            alert_type="PERFORMANCE_TEST",
            summary_stats=summary_stats
        )
        
        # Check that performance metrics are included
        assert str(summary_stats['total_opportunities']) in html_content
        assert f"{summary_stats['avg_score']:.2f}" in html_content


class TestEmailErrorHandling:
    """Test email system error handling."""
    
    @pytest.fixture
    def monitor_system_with_invalid_config(self):
        """Create monitor system with invalid email config."""
        invalid_config = AlertConfiguration(
            smtp_server="invalid.smtp.server",
            smtp_port=999,
            email_username="invalid@invalid.com",
            email_password="wrongpass",
            from_email="invalid@invalid.com",
            to_email="invalid@invalid.com"
        )
        
        x_client = AsyncMock()
        claude_client = AsyncMock()
        strategic_tracker = AsyncMock()
        return CronMonitorSystem(x_client, claude_client, strategic_tracker, invalid_config)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_sending_with_smtp_error(self, monitor_system_with_invalid_config):
        """Test graceful handling of SMTP errors."""
        opportunity = AlertOpportunity(
            account_username="test", account_tier=1, content_text="test",
            content_url="test", timestamp="test", overall_score=0.8,
            ai_blockchain_relevance=0.8, technical_depth=0.7,
            opportunity_type="test", suggested_response_type="test",
            time_sensitivity="test", strategic_context="test",
            suggested_response="test"
        )
        
        # Mock SMTP to raise an exception
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
            
            # Should not raise exception, but handle gracefully
            await monitor_system_with_invalid_config._send_immediate_alert([opportunity])
            
            # Verify the system attempted to connect
            mock_smtp.assert_called_once()


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "unit"
    ])