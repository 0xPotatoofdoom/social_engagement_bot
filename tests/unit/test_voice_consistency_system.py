"""
TDD Tests for Voice Consistency System

These tests define the expected behavior of our voice consistency system before implementation.
All tests should FAIL initially until we implement the actual voice consistency classes.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List

# Import will fail initially - this is expected in TDD
try:
    from src.bot.voice.consistency_checker import (
        VoiceConsistencyChecker, VoiceMetrics, VoiceEnhancer,
        VoiceLearningSystem, VoiceProfileManager
    )
except ImportError:
    # Expected to fail initially in TDD
    pass


class TestVoiceMetrics:
    """Test VoiceMetrics data structure."""
    
    @pytest.mark.unit
    def test_voice_metrics_initialization(self):
        """VoiceMetrics should initialize with all required scores."""
        metrics = VoiceMetrics(
            authenticity_score=0.8,
            expertise_level=0.7,
            community_focus=0.9,
            brand_alignment=0.85,
            overall_score=0.8
        )
        
        assert metrics.authenticity_score == 0.8
        assert metrics.expertise_level == 0.7
        assert metrics.community_focus == 0.9
        assert metrics.brand_alignment == 0.85
        assert metrics.overall_score == 0.8
    
    @pytest.mark.unit
    def test_voice_metrics_validation(self):
        """VoiceMetrics should validate score ranges."""
        # Scores should be between 0 and 1
        with pytest.raises(ValueError):
            VoiceMetrics(
                authenticity_score=1.5,  # Invalid score
                expertise_level=0.7,
                community_focus=0.9,
                brand_alignment=0.85,
                overall_score=0.8
            )
        
        with pytest.raises(ValueError):
            VoiceMetrics(
                authenticity_score=0.8,
                expertise_level=-0.1,  # Invalid score
                community_focus=0.9,
                brand_alignment=0.85,
                overall_score=0.8
            )
    
    @pytest.mark.unit
    def test_voice_metrics_average_calculation(self):
        """VoiceMetrics should calculate overall score from components."""
        metrics = VoiceMetrics.from_components(
            authenticity_score=0.8,
            expertise_level=0.6,
            community_focus=1.0,
            brand_alignment=0.9
        )
        
        expected_overall = (0.8 + 0.6 + 1.0 + 0.9) / 4
        assert abs(metrics.overall_score - expected_overall) < 0.001
    
    @pytest.mark.unit
    def test_voice_metrics_weighted_calculation(self):
        """VoiceMetrics should support weighted scoring."""
        weights = {
            'authenticity_score': 0.4,
            'expertise_level': 0.2,
            'community_focus': 0.2,
            'brand_alignment': 0.2
        }
        
        metrics = VoiceMetrics.from_components(
            authenticity_score=0.8,
            expertise_level=0.6,
            community_focus=1.0,
            brand_alignment=0.9,
            weights=weights
        )
        
        expected_overall = (0.8 * 0.4) + (0.6 * 0.2) + (1.0 * 0.2) + (0.9 * 0.2)
        assert abs(metrics.overall_score - expected_overall) < 0.001


class TestVoiceConsistencyChecker:
    """Test VoiceConsistencyChecker functionality."""
    
    @pytest.fixture
    def voice_profile(self, sample_voice_profile):
        """Voice profile for testing."""
        return sample_voice_profile
    
    @pytest.fixture
    def voice_checker(self, voice_profile):
        """Create VoiceConsistencyChecker for testing."""
        return VoiceConsistencyChecker(voice_profile)
    
    @pytest.mark.unit
    def test_voice_checker_initialization(self, voice_profile):
        """VoiceConsistencyChecker should initialize with voice profile."""
        checker = VoiceConsistencyChecker(voice_profile)
        
        assert checker.voice_profile == voice_profile
        assert hasattr(checker, 'preferred_words')
        assert hasattr(checker, 'avoided_words')
        assert checker.preferred_words == voice_profile['vocabulary_preferences']['preferred_words']
        assert checker.avoided_words == voice_profile['vocabulary_preferences']['avoided_words']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_content_voice_success(self, voice_checker):
        """Should successfully score content against voice profile."""
        content = "Actually, blockchain innovation is fascinating. What do you think about the community building around it?"
        
        metrics = await voice_checker.score_content_voice(content)
        
        assert isinstance(metrics, VoiceMetrics)
        assert 0 <= metrics.authenticity_score <= 1
        assert 0 <= metrics.expertise_level <= 1
        assert 0 <= metrics.community_focus <= 1
        assert 0 <= metrics.brand_alignment <= 1
        assert 0 <= metrics.overall_score <= 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_authenticity_high_score(self, voice_checker):
        """Should give high authenticity score for authentic language."""
        # Content with authentic language patterns
        authentic_content = "Honestly, I've been tracking this trend for months. Actually, the data shows something fascinating."
        
        score = voice_checker._score_authenticity(authentic_content)
        
        assert score > 0.7  # Should be high
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_authenticity_low_score(self, voice_checker):
        """Should give low authenticity score for inauthentic language."""
        # Content with hyperbolic, inauthentic language
        inauthentic_content = "HUGE ANNOUNCEMENT!!! This is a GAME-CHANGER that will REVOLUTIONIZE everything!!! 🚀🚀🚀"
        
        score = voice_checker._score_authenticity(inauthentic_content)
        
        assert score < 0.5  # Should be low
    
    @pytest.mark.unit
    def test_score_expertise_level_high(self, voice_checker):
        """Should give high expertise score for content with technical depth."""
        expert_content = "The data shows a 40% increase in DeFi protocol adoption. Analysis reveals pattern of migration from centralized to decentralized systems."
        
        score = voice_checker._score_expertise_level(expert_content)
        
        assert score > 0.6  # Should be high for expert content
    
    @pytest.mark.unit
    def test_score_expertise_level_low(self, voice_checker):
        """Should give low expertise score for surface-level content."""
        surface_content = "Crypto is cool and blockchain is the future!"
        
        score = voice_checker._score_expertise_level(surface_content)
        
        assert score < 0.5  # Should be low for surface content
    
    @pytest.mark.unit
    def test_score_community_focus_high(self, voice_checker):
        """Should give high community focus score for community-oriented content."""
        community_content = "What do you think about our community's approach to building together? Your thoughts would help us grow."
        
        score = voice_checker._score_community_focus(community_content)
        
        assert score > 0.7  # Should be high for community content
    
    @pytest.mark.unit
    def test_score_community_focus_low(self, voice_checker):
        """Should give low community focus score for self-focused content."""
        self_focused_content = "I am the best at blockchain development. My project is superior to all others."
        
        score = voice_checker._score_community_focus(self_focused_content)
        
        assert score < 0.4  # Should be low for self-focused content
    
    @pytest.mark.unit
    def test_score_brand_alignment_preferred_words(self, voice_checker):
        """Should boost score for preferred vocabulary."""
        content_with_preferred = "Actually, this is fascinating. Building community is honestly what matters most."
        
        score = voice_checker._score_brand_alignment(content_with_preferred)
        
        assert score > 0.7  # Should be boosted by preferred words
    
    @pytest.mark.unit
    def test_score_brand_alignment_avoided_words(self, voice_checker):
        """Should penalize score for avoided vocabulary."""
        content_with_avoided = "We need to leverage synergy to disrupt this game-changing opportunity."
        
        score = voice_checker._score_brand_alignment(content_with_avoided)
        
        assert score < 0.3  # Should be penalized by avoided words
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_score_content_comprehensive(self, voice_checker):
        """Should provide comprehensive scoring with detailed breakdown."""
        content = "Actually, the blockchain data I've been tracking shows fascinating community patterns. What are your thoughts on building together?"
        
        metrics = await voice_checker.score_content_voice(content)
        
        # Should score well across all dimensions
        assert metrics.authenticity_score > 0.7    # "Actually", "honestly"
        assert metrics.expertise_level > 0.6       # "data", "tracking"
        assert metrics.community_focus > 0.8       # "community", "your thoughts", "building together"
        assert metrics.brand_alignment > 0.7       # "actually", "fascinating", "building"
        assert metrics.overall_score > 0.7         # Overall high quality


class TestVoiceEnhancer:
    """Test VoiceEnhancer functionality for improving content voice."""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Mock Claude client for testing."""
        mock_client = AsyncMock()
        mock_client.generate_content.return_value = {
            "success": True,
            "content": "Enhanced content with better voice alignment"
        }
        return mock_client
    
    @pytest.fixture
    def voice_enhancer(self, sample_voice_profile, mock_claude_client):
        """Create VoiceEnhancer for testing."""
        return VoiceEnhancer(sample_voice_profile, mock_claude_client)
    
    @pytest.mark.unit
    def test_voice_enhancer_initialization(self, sample_voice_profile, mock_claude_client):
        """VoiceEnhancer should initialize with voice profile and Claude client."""
        enhancer = VoiceEnhancer(sample_voice_profile, mock_claude_client)
        
        assert enhancer.voice_profile == sample_voice_profile
        assert enhancer.claude == mock_claude_client
        assert hasattr(enhancer, 'checker')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enhance_content_voice_success(self, voice_enhancer):
        """Should successfully enhance content voice."""
        content = "Blockchain will disrupt everything and leverage synergy!"
        target_score = 0.8
        
        # Mock current score below target
        with patch.object(voice_enhancer.checker, 'score_content_voice') as mock_score:
            mock_score.side_effect = [
                VoiceMetrics(0.4, 0.3, 0.2, 0.3, 0.3),  # Original low score
                VoiceMetrics(0.8, 0.7, 0.9, 0.8, 0.8)   # Enhanced high score
            ]
            
            result = await voice_enhancer.enhance_content_voice(content, target_score)
            
            assert result['success'] is True
            assert result['enhanced_content'] == "Enhanced content with better voice alignment"
            assert result['original_score'] == 0.3
            assert result['enhanced_score'] == 0.8
            assert result['improvement'] == 0.5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enhance_content_voice_already_good(self, voice_enhancer):
        """Should skip enhancement if content already meets target score."""
        content = "Actually, blockchain innovation is fascinating for our community."
        target_score = 0.8
        
        # Mock high current score
        with patch.object(voice_enhancer.checker, 'score_content_voice') as mock_score:
            mock_score.return_value = VoiceMetrics(0.9, 0.8, 0.9, 0.9, 0.9)
            
            result = await voice_enhancer.enhance_content_voice(content, target_score)
            
            assert result['success'] is True
            assert result['enhanced_content'] == content  # Unchanged
            assert result['original_score'] == 0.9
            assert len(result['improvements_made']) == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enhance_content_voice_claude_failure(self, voice_enhancer):
        """Should handle Claude API failure during enhancement."""
        content = "Poor voice content"
        
        # Mock low current score and Claude failure
        with patch.object(voice_enhancer.checker, 'score_content_voice') as mock_score:
            mock_score.return_value = VoiceMetrics(0.3, 0.2, 0.1, 0.2, 0.2)
            
            voice_enhancer.claude.generate_content.return_value = {
                "success": False,
                "error": "rate_limit"
            }
            
            result = await voice_enhancer.enhance_content_voice(content)
            
            assert result['success'] is False
            assert result['error'] == 'rate_limit'
    
    @pytest.mark.unit
    def test_build_enhancement_prompt(self, voice_enhancer):
        """Should build appropriate enhancement prompt based on metrics."""
        content = "Poor voice content with issues"
        metrics = VoiceMetrics(
            authenticity_score=0.3,     # Low - needs improvement
            expertise_level=0.8,        # Good - no improvement needed
            community_focus=0.4,        # Low - needs improvement
            brand_alignment=0.2,        # Low - needs improvement
            overall_score=0.4
        )
        
        prompt = voice_enhancer._build_enhancement_prompt(content, metrics)
        
        assert content in prompt
        assert str(voice_enhancer.voice_profile) in prompt
        assert "more authentic" in prompt
        assert "more community-focused" in prompt
        assert "better align with brand vocabulary" in prompt
        assert "add more depth" not in prompt  # Expertise is good


class TestVoiceLearningSystem:
    """Test VoiceLearningSystem for continuous voice improvement."""
    
    @pytest.fixture
    def voice_learning_system(self, sample_voice_profile):
        """Create VoiceLearningSystem for testing."""
        return VoiceLearningSystem(sample_voice_profile)
    
    @pytest.mark.unit
    def test_voice_learning_system_initialization(self, sample_voice_profile):
        """VoiceLearningSystem should initialize with voice profile."""
        system = VoiceLearningSystem(sample_voice_profile)
        
        assert system.voice_profile == sample_voice_profile
        assert system.performance_data == []
        assert hasattr(system, 'checker')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_content_performance(self, voice_learning_system):
        """Should analyze content performance and store data."""
        content = "Great blockchain insight that got high engagement"
        engagement_metrics = {
            "engagement_rate": 0.08,  # 8% engagement rate
            "reach": 1000,
            "replies": 15
        }
        
        with patch.object(voice_learning_system.checker, 'score_content_voice') as mock_score:
            mock_score.return_value = VoiceMetrics(0.8, 0.7, 0.9, 0.8, 0.8)
            
            result = await voice_learning_system.analyze_content_performance(content, engagement_metrics)
            
            assert len(voice_learning_system.performance_data) == 1
            record = voice_learning_system.performance_data[0]
            assert record['content'] == content
            assert record['engagement_rate'] == 0.08
            assert record['voice_metrics'].overall_score == 0.8
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_identify_voice_patterns_insufficient_data(self, voice_learning_system):
        """Should handle insufficient data gracefully."""
        # Only add a few data points (less than minimum required)
        for i in range(5):
            await voice_learning_system.analyze_content_performance(
                f"Content {i}",
                {"engagement_rate": 0.05, "reach": 100, "replies": 2}
            )
        
        result = await voice_learning_system._identify_voice_patterns()
        
        assert 'Insufficient data' in result['message']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_identify_voice_patterns_success(self, voice_learning_system):
        """Should identify patterns from sufficient performance data."""
        # Add sufficient data points with varying performance
        performance_data = []
        
        # High-performing content
        for i in range(5):
            performance_data.append({
                'content': f'High performing content {i}',
                'voice_metrics': VoiceMetrics(0.9, 0.8, 0.9, 0.9, 0.9),
                'engagement_rate': 0.10,  # High engagement
                'reach': 2000,
                'replies': 20
            })
        
        # Low-performing content
        for i in range(5):
            performance_data.append({
                'content': f'Low performing content {i}',
                'voice_metrics': VoiceMetrics(0.4, 0.3, 0.4, 0.4, 0.4),
                'engagement_rate': 0.02,  # Low engagement
                'reach': 200,
                'replies': 1
            })
        
        voice_learning_system.performance_data = performance_data
        
        result = await voice_learning_system._identify_voice_patterns()
        
        assert 'high_performance_patterns' in result
        patterns = result['high_performance_patterns']
        assert patterns['avg_authenticity'] > 0.8  # High performers have high authenticity
        assert patterns['avg_community_focus'] > 0.8
        assert 'recommendations' in result
    
    @pytest.mark.unit
    def test_generate_voice_recommendations(self, voice_learning_system):
        """Should generate actionable voice recommendations."""
        patterns = {
            'avg_authenticity': 0.85,      # High - should recommend continuing
            'avg_expertise': 0.90,         # High - should recommend continuing
            'avg_community_focus': 0.75,   # Good - should recommend continuing
        }
        
        recommendations = voice_learning_system._generate_voice_recommendations(patterns)
        
        assert len(recommendations) > 0
        assert any("authentic" in rec.lower() for rec in recommendations)
        assert any("technical depth" in rec.lower() for rec in recommendations)
        assert any("community" in rec.lower() for rec in recommendations)


class TestVoiceProfileManager:
    """Test VoiceProfileManager for dynamic voice profile management."""
    
    @pytest.mark.unit
    def test_voice_profile_manager_initialization(self, sample_voice_profile):
        """VoiceProfileManager should initialize with base profile."""
        manager = VoiceProfileManager(sample_voice_profile)
        
        assert manager.base_profile == sample_voice_profile
        assert manager.current_profile == sample_voice_profile
        assert len(manager.profile_history) == 1
    
    @pytest.mark.unit
    def test_update_voice_profile(self, sample_voice_profile):
        """Should update voice profile with new elements."""
        manager = VoiceProfileManager(sample_voice_profile)
        
        updates = {
            'vocabulary_preferences': {
                'preferred_words': ['innovation', 'breakthrough', 'community'],
                'avoided_words': ['disruption', 'revolutionary']
            }
        }
        
        manager.update_voice_profile(updates)
        
        assert manager.current_profile['vocabulary_preferences']['preferred_words'] == updates['vocabulary_preferences']['preferred_words']
        assert len(manager.profile_history) == 2
    
    @pytest.mark.unit
    def test_rollback_voice_profile(self, sample_voice_profile):
        """Should rollback to previous voice profile version."""
        manager = VoiceProfileManager(sample_voice_profile)
        
        # Make update
        updates = {'test_field': 'test_value'}
        manager.update_voice_profile(updates)
        
        # Rollback
        manager.rollback_voice_profile()
        
        assert manager.current_profile == sample_voice_profile
        assert 'test_field' not in manager.current_profile
    
    @pytest.mark.unit
    def test_adapt_voice_for_context(self, sample_voice_profile):
        """Should adapt voice profile for specific contexts."""
        manager = VoiceProfileManager(sample_voice_profile)
        
        context = "crisis_communication"
        adaptations = {
            'tone_adjustments': ['more_measured', 'less_promotional'],
            'additional_guidelines': ['Focus on facts', 'Show empathy']
        }
        
        adapted_profile = manager.adapt_voice_for_context(context, adaptations)
        
        assert 'context_adaptations' in adapted_profile
        assert adapted_profile['context_adaptations'][context] == adaptations
    
    @pytest.mark.unit
    def test_get_voice_evolution_metrics(self, sample_voice_profile):
        """Should track voice profile evolution over time."""
        manager = VoiceProfileManager(sample_voice_profile)
        
        # Make several updates
        for i in range(3):
            updates = {f'update_{i}': f'value_{i}'}
            manager.update_voice_profile(updates)
        
        metrics = manager.get_voice_evolution_metrics()
        
        assert metrics['total_updates'] == 3
        assert metrics['profile_versions'] == 4  # Base + 3 updates
        assert 'evolution_timeline' in metrics


class TestVoiceConsistencyIntegration:
    """Integration tests for voice consistency system."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_voice_consistency_workflow(self, sample_voice_profile):
        """Should handle complete voice consistency workflow."""
        # Initialize system components
        checker = VoiceConsistencyChecker(sample_voice_profile)
        mock_claude = AsyncMock()
        mock_claude.generate_content.return_value = {
            "success": True,
            "content": "Actually, blockchain innovation is fascinating for our community. What are your thoughts?"
        }
        enhancer = VoiceEnhancer(sample_voice_profile, mock_claude)
        learning_system = VoiceLearningSystem(sample_voice_profile)
        
        # Test content with poor voice alignment
        poor_content = "HUGE blockchain disruption will leverage synergy to revolutionize everything!!!"
        
        # Step 1: Score original content
        original_metrics = await checker.score_content_voice(poor_content)
        assert original_metrics.overall_score < 0.5  # Should be low
        
        # Step 2: Enhance content
        enhancement_result = await enhancer.enhance_content_voice(poor_content, target_score=0.8)
        assert enhancement_result['success'] is True
        enhanced_content = enhancement_result['enhanced_content']
        
        # Step 3: Score enhanced content
        enhanced_metrics = await checker.score_content_voice(enhanced_content)
        assert enhanced_metrics.overall_score > original_metrics.overall_score
        
        # Step 4: Learn from performance
        engagement_metrics = {"engagement_rate": 0.08, "reach": 1000, "replies": 15}
        await learning_system.analyze_content_performance(enhanced_content, engagement_metrics)
        
        assert len(learning_system.performance_data) == 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_voice_consistency_with_different_content_types(self, sample_voice_profile):
        """Should handle voice consistency across different content types."""
        checker = VoiceConsistencyChecker(sample_voice_profile)
        
        content_types = {
            "original": "Actually, I've been tracking blockchain adoption patterns. The data shows fascinating community growth.",
            "reply": "That's a great question about DeFi! Honestly, the security considerations are worth exploring together.",
            "trend_response": "This blockchain development is exactly what our community has been building toward. Thoughts?",
            "educational": "Smart contracts work by automatically executing when conditions are met. What aspects interest you most?"
        }
        
        scores = {}
        for content_type, content in content_types.items():
            metrics = await checker.score_content_voice(content)
            scores[content_type] = metrics.overall_score
        
        # All content should maintain reasonable voice consistency
        assert all(score > 0.6 for score in scores.values())
        
        # Educational content might score differently than casual content
        assert 'original' in scores
        assert 'educational' in scores
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_voice_learning_and_adaptation_over_time(self, sample_voice_profile):
        """Should learn and adapt voice profile over time based on performance."""
        learning_system = VoiceLearningSystem(sample_voice_profile)
        profile_manager = VoiceProfileManager(sample_voice_profile)
        
        # Simulate content performance over time
        content_samples = [
            ("High authenticity content with community focus", {"engagement_rate": 0.12}),
            ("Technical depth with data-driven insights", {"engagement_rate": 0.08}),
            ("Community question sparking discussion", {"engagement_rate": 0.15}),
            ("Trend response with brand voice", {"engagement_rate": 0.06}),
            ("Educational content helping others", {"engagement_rate": 0.09})
        ]
        
        # Analyze performance for each content type
        for content, engagement in content_samples:
            await learning_system.analyze_content_performance(content, engagement)
        
        # Should have sufficient data for pattern analysis
        patterns = await learning_system._identify_voice_patterns()
        
        # Should generate recommendations for voice improvement
        assert 'recommendations' in patterns
        assert len(patterns['recommendations']) > 0
        
        # Could use recommendations to update voice profile
        assert patterns['high_performance_patterns']['avg_authenticity'] > 0