"""
TDD Tests for Content Scheduler

These tests define the expected behavior of our content scheduling system before implementation.
All tests should FAIL initially until we implement the actual ContentScheduler class.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import will fail initially - this is expected in TDD
try:
    from src.bot.scheduling.scheduler import (
        ContentScheduler, ScheduledPost, PostingStrategy, OptimalTimingAnalyzer,
        QueueManager, SchedulingRules, ContentPriority
    )
except ImportError:
    # Expected to fail initially in TDD
    pass


class TestContentPriority:
    """Test ContentPriority enum functionality."""
    
    @pytest.mark.unit
    def test_content_priority_enum_exists(self):
        """ContentPriority enum should define all priority levels."""
        assert ContentPriority.URGENT == "urgent"
        assert ContentPriority.HIGH == "high"
        assert ContentPriority.NORMAL == "normal"
        assert ContentPriority.LOW == "low"
        assert ContentPriority.BACKGROUND == "background"
    
    @pytest.mark.unit
    def test_content_priority_ordering(self):
        """ContentPriority should have proper ordering."""
        priorities = [
            ContentPriority.URGENT,
            ContentPriority.HIGH,
            ContentPriority.NORMAL,
            ContentPriority.LOW,
            ContentPriority.BACKGROUND
        ]
        
        # Should be ordered by priority (urgent > high > normal > low > background)
        priority_values = [p.priority_value for p in priorities]
        assert priority_values == sorted(priority_values, reverse=True)


class TestScheduledPost:
    """Test ScheduledPost data structure."""
    
    @pytest.mark.unit
    def test_scheduled_post_initialization(self):
        """ScheduledPost should initialize with all required fields."""
        post_time = datetime.now() + timedelta(hours=2)
        
        scheduled_post = ScheduledPost(
            id="post_123",
            content="Great blockchain insight #crypto",
            scheduled_time=post_time,
            priority=ContentPriority.HIGH,
            content_type="original",
            topic="blockchain",
            created_at=datetime.now(),
            retry_count=0,
            max_retries=3
        )
        
        assert scheduled_post.id == "post_123"
        assert scheduled_post.content == "Great blockchain insight #crypto"
        assert scheduled_post.scheduled_time == post_time
        assert scheduled_post.priority == ContentPriority.HIGH
        assert scheduled_post.content_type == "original"
        assert scheduled_post.status == "pending"  # Default status
    
    @pytest.mark.unit
    def test_scheduled_post_validation(self):
        """ScheduledPost should validate input data."""
        # Scheduled time in the past should be invalid
        past_time = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(ValueError):
            ScheduledPost(
                id="test",
                content="test content",
                scheduled_time=past_time,  # Invalid
                priority=ContentPriority.NORMAL
            )
        
        # Empty content should be invalid
        with pytest.raises(ValueError):
            ScheduledPost(
                id="test",
                content="",  # Invalid
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=ContentPriority.NORMAL
            )
    
    @pytest.mark.unit
    def test_scheduled_post_status_transitions(self):
        """ScheduledPost should handle status transitions correctly."""
        post = ScheduledPost(
            id="test",
            content="test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=ContentPriority.NORMAL
        )
        
        # Valid transitions
        post.set_status("processing")
        assert post.status == "processing"
        
        post.set_status("posted")
        assert post.status == "posted"
        
        # Invalid transition (posted -> pending)
        with pytest.raises(ValueError):
            post.set_status("pending")
    
    @pytest.mark.unit
    def test_scheduled_post_is_due(self):
        """ScheduledPost should correctly identify when it's due for posting."""
        # Post due now
        due_post = ScheduledPost(
            id="due",
            content="due content",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=ContentPriority.NORMAL
        )
        
        # Post due in future
        future_post = ScheduledPost(
            id="future",
            content="future content", 
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=ContentPriority.NORMAL
        )
        
        assert due_post.is_due() is True
        assert future_post.is_due() is False
    
    @pytest.mark.unit
    def test_scheduled_post_can_retry(self):
        """ScheduledPost should track retry attempts."""
        post = ScheduledPost(
            id="retry_test",
            content="test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=ContentPriority.NORMAL,
            max_retries=3
        )
        
        assert post.can_retry() is True
        
        # Exhaust retries
        post.retry_count = 3
        assert post.can_retry() is False


class TestSchedulingRules:
    """Test SchedulingRules configuration."""
    
    @pytest.mark.unit
    def test_scheduling_rules_initialization(self):
        """SchedulingRules should initialize with default constraints."""
        rules = SchedulingRules()
        
        assert rules.max_posts_per_hour > 0
        assert rules.max_posts_per_day > 0
        assert rules.min_gap_between_posts > 0
        assert len(rules.quiet_hours) == 0  # Default no quiet hours
        assert hasattr(rules, 'content_type_limits')
    
    @pytest.mark.unit
    def test_scheduling_rules_custom_configuration(self):
        """SchedulingRules should accept custom configuration."""
        rules = SchedulingRules(
            max_posts_per_hour=5,
            max_posts_per_day=20,
            min_gap_between_posts=15,  # minutes
            quiet_hours=[("22:00", "08:00")],
            content_type_limits={"trend_response": 10, "original": 5}
        )
        
        assert rules.max_posts_per_hour == 5
        assert rules.max_posts_per_day == 20
        assert rules.min_gap_between_posts == 15
        assert len(rules.quiet_hours) == 1
        assert rules.content_type_limits["trend_response"] == 10
    
    @pytest.mark.unit
    def test_scheduling_rules_validation(self):
        """SchedulingRules should validate configuration values."""
        # Invalid negative values
        with pytest.raises(ValueError):
            SchedulingRules(max_posts_per_hour=-1)
        
        # Invalid quiet hours format
        with pytest.raises(ValueError):
            SchedulingRules(quiet_hours=[("25:00", "08:00")])  # Invalid hour
    
    @pytest.mark.unit
    def test_can_post_at_time(self):
        """SchedulingRules should determine if posting is allowed at specific time."""
        rules = SchedulingRules(
            quiet_hours=[("22:00", "08:00")]  # Quiet from 10 PM to 8 AM
        )
        
        # During quiet hours
        quiet_time = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
        assert rules.can_post_at_time(quiet_time) is False
        
        # During active hours
        active_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        assert rules.can_post_at_time(active_time) is True
    
    @pytest.mark.unit
    def test_check_posting_frequency(self):
        """SchedulingRules should check if posting frequency is within limits."""
        rules = SchedulingRules(max_posts_per_hour=3)
        
        recent_posts = [
            datetime.now() - timedelta(minutes=10),
            datetime.now() - timedelta(minutes=30),
            datetime.now() - timedelta(minutes=45)
        ]
        
        # At limit
        assert rules.check_posting_frequency(recent_posts) is False
        
        # Under limit
        recent_posts_under = recent_posts[:2]
        assert rules.check_posting_frequency(recent_posts_under) is True


class TestOptimalTimingAnalyzer:
    """Test OptimalTimingAnalyzer functionality."""
    
    @pytest.fixture
    def timing_analyzer(self):
        """Create OptimalTimingAnalyzer for testing."""
        return OptimalTimingAnalyzer(timezone="US/Eastern")
    
    @pytest.mark.unit
    def test_timing_analyzer_initialization(self):
        """OptimalTimingAnalyzer should initialize with timezone."""
        analyzer = OptimalTimingAnalyzer(timezone="US/Pacific")
        
        assert analyzer.timezone == pytz.timezone("US/Pacific")
        assert hasattr(analyzer, 'optimal_times')
        assert hasattr(analyzer, 'audience_patterns')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_audience_activity_patterns(self, timing_analyzer):
        """Should analyze when audience is most active."""
        # Mock engagement data by time
        engagement_data = [
            {"hour": 9, "engagement_rate": 0.06, "reach": 800},
            {"hour": 12, "engagement_rate": 0.12, "reach": 1200},
            {"hour": 15, "engagement_rate": 0.08, "reach": 1000},
            {"hour": 18, "engagement_rate": 0.15, "reach": 1500},
            {"hour": 21, "engagement_rate": 0.10, "reach": 900}
        ]
        
        patterns = await timing_analyzer.analyze_audience_activity_patterns(engagement_data)
        
        assert 'peak_hours' in patterns
        assert 'optimal_posting_times' in patterns
        assert 'audience_timezone_distribution' in patterns
        assert patterns['peak_hours'][0] == 18  # Highest engagement
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_optimal_posting_time(self, timing_analyzer):
        """Should determine optimal posting time for content type."""
        content_type = "original"
        current_time = datetime.now(timing_analyzer.timezone)
        
        optimal_time = await timing_analyzer.get_optimal_posting_time(content_type, current_time)
        
        assert isinstance(optimal_time, datetime)
        assert optimal_time.tzinfo == timing_analyzer.timezone
        assert optimal_time > current_time  # Should be in the future
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_optimal_posting_time_urgent(self, timing_analyzer):
        """Should handle urgent content with immediate posting."""
        content_type = "trend_response"
        current_time = datetime.now(timing_analyzer.timezone)
        urgency = "immediate"
        
        optimal_time = await timing_analyzer.get_optimal_posting_time(content_type, current_time, urgency)
        
        # Should be very soon (within 5 minutes)
        time_diff = optimal_time - current_time
        assert time_diff.total_seconds() < 300  # Less than 5 minutes
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_predict_engagement_by_time(self, timing_analyzer):
        """Should predict engagement based on posting time."""
        post_time = datetime.now(timing_analyzer.timezone).replace(hour=18, minute=0)  # Peak hour
        content_type = "original"
        
        prediction = await timing_analyzer.predict_engagement_by_time(post_time, content_type)
        
        assert 'predicted_engagement_rate' in prediction
        assert 'confidence' in prediction
        assert 'factors' in prediction
        assert 0 <= prediction['predicted_engagement_rate'] <= 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_adjust_for_timezone_distribution(self, timing_analyzer):
        """Should adjust timing for global audience timezones."""
        base_time = datetime.now(timing_analyzer.timezone).replace(hour=12)
        audience_timezones = {
            "US/Eastern": 0.4,
            "US/Pacific": 0.3,
            "Europe/London": 0.2,
            "Asia/Tokyo": 0.1
        }
        
        adjusted_time = await timing_analyzer.adjust_for_timezone_distribution(
            base_time, 
            audience_timezones
        )
        
        assert isinstance(adjusted_time, datetime)
        # Should be adjusted to maximize global reach
        assert adjusted_time != base_time


class TestQueueManager:
    """Test QueueManager functionality."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create QueueManager for testing."""
        rules = SchedulingRules(max_posts_per_hour=3, min_gap_between_posts=20)
        return QueueManager(rules)
    
    @pytest.mark.unit
    def test_queue_manager_initialization(self):
        """QueueManager should initialize with scheduling rules."""
        rules = SchedulingRules()
        manager = QueueManager(rules)
        
        assert manager.rules == rules
        assert len(manager.queue) == 0
        assert hasattr(manager, 'posted_times')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_to_queue_success(self, queue_manager):
        """Should successfully add post to queue."""
        post = ScheduledPost(
            id="test_post",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=ContentPriority.NORMAL
        )
        
        result = await queue_manager.add_to_queue(post)
        
        assert result['success'] is True
        assert len(queue_manager.queue) == 1
        assert queue_manager.queue[0] == post
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_to_queue_priority_ordering(self, queue_manager):
        """Should maintain priority ordering in queue."""
        posts = [
            ScheduledPost("low", "Low priority", datetime.now() + timedelta(hours=1), ContentPriority.LOW),
            ScheduledPost("urgent", "Urgent", datetime.now() + timedelta(hours=1), ContentPriority.URGENT),
            ScheduledPost("normal", "Normal", datetime.now() + timedelta(hours=1), ContentPriority.NORMAL),
            ScheduledPost("high", "High priority", datetime.now() + timedelta(hours=1), ContentPriority.HIGH)
        ]
        
        for post in posts:
            await queue_manager.add_to_queue(post)
        
        # Should be ordered by priority: urgent, high, normal, low
        priorities = [post.priority for post in queue_manager.queue]
        expected_order = [ContentPriority.URGENT, ContentPriority.HIGH, ContentPriority.NORMAL, ContentPriority.LOW]
        assert priorities == expected_order
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_to_queue_scheduling_conflict(self, queue_manager):
        """Should handle scheduling conflicts appropriately."""
        # Add post that violates frequency rules
        for i in range(4):  # Exceeds max_posts_per_hour (3)
            post = ScheduledPost(
                id=f"post_{i}",
                content=f"Content {i}",
                scheduled_time=datetime.now() + timedelta(minutes=i*10),
                priority=ContentPriority.NORMAL
            )
            result = await queue_manager.add_to_queue(post)
            
            if i < 3:
                assert result['success'] is True
            else:
                assert result['success'] is False
                assert 'frequency_limit' in result['reason']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_due_posts(self, queue_manager):
        """Should return posts that are due for posting."""
        # Add posts with different times
        past_post = ScheduledPost("past", "Past", datetime.now() - timedelta(minutes=5), ContentPriority.NORMAL)
        due_post = ScheduledPost("due", "Due now", datetime.now(), ContentPriority.NORMAL)
        future_post = ScheduledPost("future", "Future", datetime.now() + timedelta(hours=1), ContentPriority.NORMAL)
        
        await queue_manager.add_to_queue(past_post)
        await queue_manager.add_to_queue(due_post)
        await queue_manager.add_to_queue(future_post)
        
        due_posts = await queue_manager.get_due_posts()
        
        assert len(due_posts) == 2  # past_post and due_post
        assert past_post in due_posts
        assert due_post in due_posts
        assert future_post not in due_posts
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_remove_from_queue(self, queue_manager):
        """Should remove post from queue."""
        post = ScheduledPost("test", "Test", datetime.now() + timedelta(hours=1), ContentPriority.NORMAL)
        await queue_manager.add_to_queue(post)
        
        removed = await queue_manager.remove_from_queue("test")
        
        assert removed == post
        assert len(queue_manager.queue) == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reschedule_post(self, queue_manager):
        """Should reschedule post to new time."""
        original_time = datetime.now() + timedelta(hours=1)
        new_time = datetime.now() + timedelta(hours=2)
        
        post = ScheduledPost("reschedule", "Test", original_time, ContentPriority.NORMAL)
        await queue_manager.add_to_queue(post)
        
        result = await queue_manager.reschedule_post("reschedule", new_time)
        
        assert result['success'] is True
        assert queue_manager.queue[0].scheduled_time == new_time
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_queue_statistics(self, queue_manager):
        """Should provide queue statistics and insights."""
        # Add various posts
        posts = [
            ScheduledPost("urgent", "Urgent", datetime.now() + timedelta(hours=1), ContentPriority.URGENT),
            ScheduledPost("normal1", "Normal 1", datetime.now() + timedelta(hours=2), ContentPriority.NORMAL),
            ScheduledPost("normal2", "Normal 2", datetime.now() + timedelta(hours=3), ContentPriority.NORMAL)
        ]
        
        for post in posts:
            await queue_manager.add_to_queue(post)
        
        stats = await queue_manager.get_queue_statistics()
        
        assert stats['total_posts'] == 3
        assert stats['posts_by_priority'][ContentPriority.URGENT] == 1
        assert stats['posts_by_priority'][ContentPriority.NORMAL] == 2
        assert 'next_posting_time' in stats
        assert 'estimated_completion_time' in stats


class TestPostingStrategy:
    """Test PostingStrategy functionality."""
    
    @pytest.mark.unit
    def test_posting_strategy_initialization(self):
        """PostingStrategy should initialize with strategy configuration."""
        strategy = PostingStrategy(
            name="aggressive_growth",
            daily_post_target=15,
            content_distribution={
                "original": 0.4,
                "trend_response": 0.3,
                "engagement": 0.2,
                "educational": 0.1
            },
            optimal_times=["09:00", "12:00", "15:00", "18:00", "21:00"],
            priority_weights={
                ContentPriority.URGENT: 1.0,
                ContentPriority.HIGH: 0.8,
                ContentPriority.NORMAL: 0.6,
                ContentPriority.LOW: 0.4
            }
        )
        
        assert strategy.name == "aggressive_growth"
        assert strategy.daily_post_target == 15
        assert strategy.content_distribution["original"] == 0.4
        assert len(strategy.optimal_times) == 5
    
    @pytest.mark.unit
    def test_posting_strategy_validation(self):
        """PostingStrategy should validate configuration."""
        # Content distribution should sum to 1.0
        with pytest.raises(ValueError):
            PostingStrategy(
                name="invalid",
                daily_post_target=10,
                content_distribution={"original": 0.6, "trend": 0.6}  # Sums to 1.2
            )
        
        # Daily target should be positive
        with pytest.raises(ValueError):
            PostingStrategy(
                name="invalid",
                daily_post_target=0,  # Invalid
                content_distribution={"original": 1.0}
            )
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_posting_schedule(self):
        """Should calculate posting schedule based on strategy."""
        strategy = PostingStrategy(
            name="balanced",
            daily_post_target=8,
            content_distribution={"original": 0.5, "trend": 0.5},
            optimal_times=["09:00", "12:00", "18:00", "21:00"]
        )
        
        schedule = await strategy.calculate_posting_schedule(days=1)
        
        assert len(schedule) == 8  # daily_post_target
        assert all('time' in slot for slot in schedule)
        assert all('content_type' in slot for slot in schedule)
        
        # Should follow content distribution
        original_count = sum(1 for slot in schedule if slot['content_type'] == 'original')
        trend_count = sum(1 for slot in schedule if slot['content_type'] == 'trend')
        assert abs(original_count - 4) <= 1  # Should be approximately 50%
        assert abs(trend_count - 4) <= 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_adapt_strategy_based_on_performance(self):
        """Should adapt strategy based on performance feedback."""
        strategy = PostingStrategy(
            name="adaptive",
            daily_post_target=10,
            content_distribution={"original": 0.5, "trend": 0.5},
            optimal_times=["12:00", "18:00"]
        )
        
        performance_data = {
            "content_type_performance": {
                "original": {"avg_engagement": 0.08},
                "trend": {"avg_engagement": 0.12}  # Trend performs better
            },
            "time_performance": {
                "12:00": {"avg_engagement": 0.06},
                "18:00": {"avg_engagement": 0.10}  # 18:00 performs better
            }
        }
        
        adapted_strategy = await strategy.adapt_strategy_based_on_performance(performance_data)
        
        # Should shift distribution toward better performing content
        assert adapted_strategy.content_distribution["trend"] > strategy.content_distribution["trend"]
        
        # Should prioritize better performing times
        assert "18:00" in adapted_strategy.optimal_times[:2]  # Should be in top times


class TestContentScheduler:
    """Test ContentScheduler main functionality."""
    
    @pytest.fixture
    def mock_x_client(self):
        """Mock X API client for testing."""
        mock_client = AsyncMock()
        mock_client.post_tweet.return_value = {"success": True, "tweet_id": "1234567890"}
        return mock_client
    
    @pytest.fixture
    def content_scheduler(self, mock_x_client):
        """Create ContentScheduler for testing."""
        rules = SchedulingRules(max_posts_per_hour=5, min_gap_between_posts=15)
        return ContentScheduler(mock_x_client, rules, timezone="US/Eastern")
    
    @pytest.mark.unit
    def test_content_scheduler_initialization(self, mock_x_client):
        """ContentScheduler should initialize with required components."""
        rules = SchedulingRules()
        scheduler = ContentScheduler(mock_x_client, rules)
        
        assert scheduler.x_client == mock_x_client
        assert scheduler.rules == rules
        assert hasattr(scheduler, 'queue_manager')
        assert hasattr(scheduler, 'timing_analyzer')
        assert hasattr(scheduler, 'posting_strategy')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_schedule_content_success(self, content_scheduler):
        """Should successfully schedule content for posting."""
        content = "Great blockchain insight #crypto"
        content_type = "original"
        priority = ContentPriority.NORMAL
        
        result = await content_scheduler.schedule_content(
            content=content,
            content_type=content_type,
            priority=priority
        )
        
        assert result['success'] is True
        assert 'scheduled_time' in result
        assert 'post_id' in result
        assert result['scheduled_time'] > datetime.now()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_schedule_content_with_specific_time(self, content_scheduler):
        """Should schedule content for specific time when provided."""
        content = "Scheduled post content"
        specific_time = datetime.now() + timedelta(hours=3)
        
        result = await content_scheduler.schedule_content(
            content=content,
            content_type="original",
            priority=ContentPriority.NORMAL,
            scheduled_time=specific_time
        )
        
        assert result['success'] is True
        assert abs((result['scheduled_time'] - specific_time).total_seconds()) < 60  # Within 1 minute
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_schedule_urgent_content(self, content_scheduler):
        """Should handle urgent content with immediate posting."""
        urgent_content = "BREAKING: Important blockchain news #crypto"
        
        result = await content_scheduler.schedule_content(
            content=urgent_content,
            content_type="trend_response",
            priority=ContentPriority.URGENT
        )
        
        assert result['success'] is True
        # Should be scheduled very soon (within 5 minutes)
        time_diff = result['scheduled_time'] - datetime.now()
        assert time_diff.total_seconds() < 300
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_due_posts(self, content_scheduler):
        """Should process posts that are due for posting."""
        # Schedule a post that's due
        past_time = datetime.now() - timedelta(minutes=1)
        await content_scheduler.schedule_content(
            content="Due post",
            content_type="original",
            priority=ContentPriority.NORMAL,
            scheduled_time=past_time
        )
        
        result = await content_scheduler.process_due_posts()
        
        assert result['posts_processed'] == 1
        assert result['successful_posts'] == 1
        assert result['failed_posts'] == 0
        
        # Should have posted to X
        content_scheduler.x_client.post_tweet.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_due_posts_with_failure(self, content_scheduler):
        """Should handle posting failures gracefully."""
        # Mock X client failure
        content_scheduler.x_client.post_tweet.return_value = {"success": False, "error": "rate_limit"}
        
        # Schedule a due post
        await content_scheduler.schedule_content(
            content="Failed post",
            content_type="original",
            priority=ContentPriority.NORMAL,
            scheduled_time=datetime.now() - timedelta(minutes=1)
        )
        
        result = await content_scheduler.process_due_posts()
        
        assert result['posts_processed'] == 1
        assert result['successful_posts'] == 0
        assert result['failed_posts'] == 1
        
        # Should retry the post
        queue_stats = await content_scheduler.get_queue_statistics()
        assert queue_stats['total_posts'] == 1  # Post should still be in queue for retry
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reschedule_post(self, content_scheduler):
        """Should reschedule existing post to new time."""
        # Schedule initial post
        result = await content_scheduler.schedule_content(
            content="Original post",
            content_type="original",
            priority=ContentPriority.NORMAL
        )
        post_id = result['post_id']
        
        # Reschedule to new time
        new_time = datetime.now() + timedelta(hours=5)
        reschedule_result = await content_scheduler.reschedule_post(post_id, new_time)
        
        assert reschedule_result['success'] is True
        assert reschedule_result['new_scheduled_time'] == new_time
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_scheduled_post(self, content_scheduler):
        """Should cancel scheduled post."""
        # Schedule post
        result = await content_scheduler.schedule_content(
            content="To be cancelled",
            content_type="original",
            priority=ContentPriority.NORMAL
        )
        post_id = result['post_id']
        
        # Cancel post
        cancel_result = await content_scheduler.cancel_scheduled_post(post_id)
        
        assert cancel_result['success'] is True
        
        # Post should be removed from queue
        queue_stats = await content_scheduler.get_queue_statistics()
        assert queue_stats['total_posts'] == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_posting_schedule_preview(self, content_scheduler):
        """Should provide preview of upcoming posting schedule."""
        # Schedule multiple posts
        for i in range(5):
            await content_scheduler.schedule_content(
                content=f"Scheduled post {i}",
                content_type="original",
                priority=ContentPriority.NORMAL
            )
        
        preview = await content_scheduler.get_posting_schedule_preview(hours=24)
        
        assert 'scheduled_posts' in preview
        assert 'posting_frequency' in preview
        assert 'next_available_slot' in preview
        assert len(preview['scheduled_posts']) <= 5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_optimize_posting_schedule(self, content_scheduler):
        """Should optimize posting schedule based on performance data."""
        # Mock performance data
        performance_data = {
            "optimal_times": ["09:00", "12:00", "18:00"],
            "best_content_types": ["original", "engagement"],
            "audience_timezone": "US/Eastern"
        }
        
        optimization_result = await content_scheduler.optimize_posting_schedule(performance_data)
        
        assert optimization_result['success'] is True
        assert 'adjustments_made' in optimization_result
        assert 'projected_improvement' in optimization_result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bulk_schedule_content(self, content_scheduler):
        """Should handle bulk scheduling of multiple posts."""
        posts_to_schedule = [
            {"content": "Post 1", "content_type": "original", "priority": "normal"},
            {"content": "Post 2", "content_type": "trend_response", "priority": "high"},
            {"content": "Post 3", "content_type": "engagement", "priority": "normal"}
        ]
        
        result = await content_scheduler.bulk_schedule_content(posts_to_schedule)
        
        assert result['success'] is True
        assert result['scheduled_count'] == 3
        assert result['failed_count'] == 0
        assert len(result['scheduled_posts']) == 3


class TestContentSchedulerIntegration:
    """Integration tests for content scheduling system."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_scheduling_workflow(self):
        """Should handle complete scheduling workflow."""
        # Mock X client
        mock_x_client = AsyncMock()
        mock_x_client.post_tweet.return_value = {"success": True, "tweet_id": "1234567890"}
        
        # Create scheduler with realistic configuration
        rules = SchedulingRules(
            max_posts_per_hour=3,
            max_posts_per_day=15,
            min_gap_between_posts=20,
            quiet_hours=[("22:00", "08:00")]
        )
        
        scheduler = ContentScheduler(mock_x_client, rules, timezone="US/Eastern")
        
        # Schedule various types of content
        content_items = [
            {"content": "Original blockchain insight", "type": "original", "priority": ContentPriority.NORMAL},
            {"content": "BREAKING: Crypto news!", "type": "trend_response", "priority": ContentPriority.URGENT},
            {"content": "What do you think about DeFi?", "type": "engagement", "priority": ContentPriority.HIGH}
        ]
        
        scheduled_posts = []
        for item in content_items:
            result = await scheduler.schedule_content(
                content=item["content"],
                content_type=item["type"], 
                priority=item["priority"]
            )
            assert result['success'] is True
            scheduled_posts.append(result['post_id'])
        
        # Get schedule preview
        preview = await scheduler.get_posting_schedule_preview(hours=24)
        assert len(preview['scheduled_posts']) == 3
        
        # Process any due posts
        process_result = await scheduler.process_due_posts()
        
        # Should have processed urgent post immediately
        assert process_result['posts_processed'] >= 1
        
        # Verify queue management
        queue_stats = await scheduler.get_queue_statistics()
        assert queue_stats['total_posts'] >= 0  # Some posts may have been processed
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scheduling_with_rate_limits_and_conflicts(self):
        """Should handle rate limits and scheduling conflicts appropriately."""
        # Mock X client with rate limiting
        mock_x_client = AsyncMock()
        mock_x_client.post_tweet.side_effect = [
            {"success": True, "tweet_id": "1"},
            {"success": True, "tweet_id": "2"},
            {"success": False, "error": "rate_limit"},  # Hit rate limit
            {"success": True, "tweet_id": "3"}  # Retry success
        ]
        
        # Strict scheduling rules
        rules = SchedulingRules(max_posts_per_hour=2, min_gap_between_posts=30)
        scheduler = ContentScheduler(mock_x_client, rules)
        
        # Try to schedule many posts quickly
        posts_to_schedule = 5
        successful_schedules = 0
        
        for i in range(posts_to_schedule):
            result = await scheduler.schedule_content(
                content=f"Post {i}",
                content_type="original",
                priority=ContentPriority.NORMAL,
                scheduled_time=datetime.now() + timedelta(minutes=i*5)  # Very close together
            )
            
            if result['success']:
                successful_schedules += 1
        
        # Should respect rate limits
        assert successful_schedules <= rules.max_posts_per_hour
        
        # Process posts and handle retries
        process_result = await scheduler.process_due_posts()
        
        # Should handle rate limit gracefully and retry
        assert 'failed_posts' in process_result
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_adaptive_scheduling_optimization(self):
        """Should adapt scheduling strategy based on performance feedback."""
        mock_x_client = AsyncMock()
        mock_x_client.post_tweet.return_value = {"success": True, "tweet_id": "123"}
        
        # Start with basic strategy
        rules = SchedulingRules()
        scheduler = ContentScheduler(mock_x_client, rules)
        
        # Simulate posting and performance tracking over time
        performance_data = []
        
        # Schedule and "post" content over several days
        for day in range(7):
            for hour in [9, 12, 15, 18, 21]:
                # Schedule post for specific time
                post_time = datetime.now().replace(hour=hour, minute=0) + timedelta(days=day)
                
                result = await scheduler.schedule_content(
                    content=f"Day {day} Hour {hour} post",
                    content_type="original" if hour % 2 == 0 else "engagement",
                    priority=ContentPriority.NORMAL,
                    scheduled_time=post_time
                )
                
                # Simulate engagement performance (18:00 and 21:00 perform better)
                engagement_rate = 0.08 if hour in [18, 21] else 0.04
                performance_data.append({
                    "time": f"{hour:02d}:00",
                    "content_type": "original" if hour % 2 == 0 else "engagement",
                    "engagement_rate": engagement_rate
                })
        
        # Optimize schedule based on performance
        optimization_result = await scheduler.optimize_posting_schedule({
            "time_performance": {
                "18:00": {"avg_engagement": 0.08},
                "21:00": {"avg_engagement": 0.08},
                "09:00": {"avg_engagement": 0.04},
                "12:00": {"avg_engagement": 0.04},
                "15:00": {"avg_engagement": 0.04}
            }
        })
        
        assert optimization_result['success'] is True
        assert 'projected_improvement' in optimization_result
        
        # Future scheduling should prefer optimal times
        future_result = await scheduler.schedule_content(
            content="Optimized timing post",
            content_type="original",
            priority=ContentPriority.NORMAL
        )
        
        # Should be scheduled for a high-performance time
        scheduled_hour = future_result['scheduled_time'].hour
        assert scheduled_hour in [18, 21]  # Should prefer optimal times