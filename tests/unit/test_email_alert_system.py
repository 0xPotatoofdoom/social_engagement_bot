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
        """Create sample opportunities for testing."""
        return [
            AlertOpportunity(
                account_username="VitalikButerin",
                account_tier=1,
                content_text="AI agents on blockchain networks are revolutionizing how we think about autonomous systems",
                content_url="https://twitter.com/VitalikButerin/status/123456789",
                timestamp=datetime.now().isoformat(),
                overall_score=0.92,
                ai_blockchain_relevance=0.95,
                technical_depth=0.88,
                opportunity_type="technical_innovation",
                suggested_response_type="technical_insight",
                time_sensitivity="immediate",
                strategic_context="High-value technical discussion from Ethereum founder",
                suggested_response="Engage with technical expertise on AI x blockchain convergence",
                generated_reply="The convergence of AI agents and blockchain infrastructure opens fascinating possibilities for truly autonomous economic systems. The implications for MEV protection and predictive routing are particularly intriguing.",
                reply_reasoning="Demonstrates deep technical understanding while adding unique insights",
                alternative_responses=[
                    "This aligns with emerging patterns in autonomous protocol design we're seeing across DeFi",
                    "The technical architecture for AI-driven blockchain systems is evolving rapidly"
                ],
                engagement_prediction=0.89,
                voice_alignment_score=0.94
            ),
            AlertOpportunity(
                account_username="dabit3",
                account_tier=1,
                content_text="Building the next generation of decentralized applications with AI integration",
                content_url="https://twitter.com/dabit3/status/987654321",
                timestamp=datetime.now().isoformat(),
                overall_score=0.78,
                ai_blockchain_relevance=0.82,
                technical_depth=0.75,
                opportunity_type="development_discussion",
                suggested_response_type="collaboration",
                time_sensitivity="high",
                strategic_context="Development-focused opportunity from key developer advocate",
                suggested_response="Share technical insights on AI x DeFi integration patterns",
                generated_reply="The developer experience for AI-integrated dApps is still evolving. What frameworks are you finding most effective for handling off-chain AI computations with on-chain verification?",
                reply_reasoning="Technical question that demonstrates expertise while encouraging dialogue",
                alternative_responses=[
                    "Fascinating approach to AI x dApp integration. The verification challenges are particularly interesting",
                    "This opens up interesting possibilities for hybrid AI/blockchain architectures"
                ],
                engagement_prediction=0.76,
                voice_alignment_score=0.81
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
    def test_opportunity_categorization(self, monitor_system, sample_opportunities):
        """Test opportunities are categorized correctly by score."""
        immediate, priority, digest = monitor_system._categorize_opportunities(sample_opportunities)
        
        # First opportunity (0.92 score) should be immediate
        assert len(immediate) == 1
        assert immediate[0].overall_score == 0.92
        assert immediate[0].account_username == "VitalikButerin"
        
        # Second opportunity (0.78 score) should be priority
        assert len(priority) == 1 
        assert priority[0].overall_score == 0.78
        assert priority[0].account_username == "dabit3"
        
        # No digest opportunities in this sample
        assert len(digest) == 0
    
    @pytest.mark.unit
    def test_generate_alert_html_structure(self, monitor_system, sample_opportunities):
        """Test HTML alert generation structure."""
        html_content = monitor_system._generate_alert_html(
            opportunities=sample_opportunities,
            alert_type="IMMEDIATE",
            summary_stats={'total_opportunities': 2, 'avg_score': 0.85}
        )
        
        assert isinstance(html_content, str)
        assert "IMMEDIATE" in html_content
        assert "VitalikButerin" in html_content
        assert "dabit3" in html_content
        assert "AI agents on blockchain" in html_content
        assert "Building the next generation" in html_content
    
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
    def test_email_subject_generation(self, monitor_system, sample_opportunities):
        """Test email subject line generation."""
        immediate_opportunities = [opp for opp in sample_opportunities if opp.overall_score >= 0.8]
        
        subject = monitor_system._generate_email_subject("immediate", len(immediate_opportunities))
        
        assert "🔥 IMMEDIATE" in subject
        assert str(len(immediate_opportunities)) in subject
        assert "High-Priority" in subject
        assert "AI x Blockchain" in subject
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_immediate_alert_flow(self, monitor_system, sample_opportunities):
        """Test immediate alert sending flow."""
        high_priority_opportunities = [opp for opp in sample_opportunities if opp.overall_score >= 0.8]
        
        # Mock SMTP components
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            await monitor_system._send_immediate_alert(high_priority_opportunities)
            
            # Verify SMTP connection was attempted
            mock_smtp.assert_called_once_with(monitor_system.config.smtp_server, monitor_system.config.smtp_port)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
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