"""Analytics package for feedback tracking and performance monitoring."""

# Only export the active feedback tracking system
from .feedback_tracker import get_feedback_tracker

__all__ = [
    'get_feedback_tracker'
]