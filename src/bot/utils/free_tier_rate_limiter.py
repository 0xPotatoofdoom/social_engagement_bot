"""
Free Tier Rate Limiter - Extreme Conservative Strategy
Designed for X API Free Tier with very limited search quotas
"""

import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class RateLimitState:
    """Track rate limit state for an endpoint"""
    endpoint: str
    daily_quota: int
    daily_used: int
    last_reset: str  # Date string
    blocked_until: Optional[float] = None
    last_success: Optional[float] = None
    consecutive_failures: int = 0

class FreeTierRateLimiter:
    """
    Ultra-conservative rate limiter for X API Free Tier
    
    Strategy:
    - Very limited daily quotas
    - Long delays between requests
    - Intelligent backoff on failures
    - Daily quota tracking
    - Persistent state across restarts
    """
    
    def __init__(self, state_dir: str = "data/rate_limits"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "free_tier_limits.json"
        
        # Authentic 42-year-old dad quotas - realistic usage patterns
        self.daily_quotas = {
            'search_tweets': 3,         # Morning + evening + maybe weekend check
            'user_timeline': 8,         # Check a few key accounts occasionally  
            'user_lookup': 5,           # Lookup interesting people mentioned
            'get_me': 2,               # Profile checks very rarely
        }
        
        # Realistic delays between requests (dad checking phone periodically)
        self.min_delays = {
            'search_tweets': 6 * 3600,  # 6 hours between searches (morning/evening pattern)
            'user_timeline': 2 * 3600,  # 2 hours between timeline checks
            'user_lookup': 30 * 60,     # 30 minutes between user lookups
            'get_me': 12 * 3600,       # 12 hours between profile checks
        }
        
        # Load persistent state
        self.limits_state: Dict[str, RateLimitState] = {}
        self._load_state()
        
        # Initialize default states
        for endpoint, quota in self.daily_quotas.items():
            if endpoint not in self.limits_state:
                self.limits_state[endpoint] = RateLimitState(
                    endpoint=endpoint,
                    daily_quota=quota,
                    daily_used=0,
                    last_reset=datetime.now().strftime('%Y-%m-%d')
                )
        
        logger.info("Free Tier Rate Limiter initialized with ultra-conservative quotas")
    
    def _load_state(self):
        """Load persistent rate limit state"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    
                for endpoint, data in state_data.items():
                    self.limits_state[endpoint] = RateLimitState(**data)
                    
                logger.info(f"Loaded rate limit state for {len(self.limits_state)} endpoints")
        except Exception as e:
            logger.error(f"Error loading rate limit state: {e}")
    
    def _save_state(self):
        """Save persistent rate limit state"""
        try:
            state_data = {
                endpoint: asdict(state) 
                for endpoint, state in self.limits_state.items()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rate limit state: {e}")
    
    def _reset_daily_quotas_if_needed(self):
        """Reset daily quotas if it's a new day"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        for endpoint, state in self.limits_state.items():
            if state.last_reset != today:
                old_used = state.daily_used
                state.daily_used = 0
                state.last_reset = today
                state.consecutive_failures = 0
                
                logger.info(f"Reset daily quota for {endpoint}: {old_used} → 0")
        
        self._save_state()
    
    def can_make_request(self, endpoint: str) -> tuple[bool, str]:
        """
        Check if we can make a request to the endpoint
        Returns: (can_make_request, reason_if_not)
        """
        self._reset_daily_quotas_if_needed()
        
        if endpoint not in self.limits_state:
            return False, f"Unknown endpoint: {endpoint}"
        
        state = self.limits_state[endpoint]
        now = time.time()
        
        # Check if blocked due to rate limit
        if state.blocked_until and now < state.blocked_until:
            remaining = int(state.blocked_until - now)
            return False, f"Blocked for {remaining}s due to rate limit"
        
        # Check daily quota
        if state.daily_used >= state.daily_quota:
            return False, f"Daily quota exhausted: {state.daily_used}/{state.daily_quota}"
        
        # Check minimum delay since last request
        if state.last_success:
            min_delay = self.min_delays.get(endpoint, 600)
            time_since_last = now - state.last_success
            
            if time_since_last < min_delay:
                remaining = int(min_delay - time_since_last)
                return False, f"Minimum delay not met: {remaining}s remaining"
        
        # Check exponential backoff for consecutive failures
        if state.consecutive_failures > 0:
            backoff_delay = min(3600, 300 * (2 ** state.consecutive_failures))  # Max 1 hour
            if state.last_success and (now - state.last_success) < backoff_delay:
                remaining = int(backoff_delay - (now - state.last_success))
                return False, f"Exponential backoff: {remaining}s remaining"
        
        return True, "OK"
    
    def record_request_attempt(self, endpoint: str):
        """Record that we're attempting a request"""
        if endpoint not in self.limits_state:
            return
        
        state = self.limits_state[endpoint]
        state.daily_used += 1
        self._save_state()
        
        logger.info(f"Request attempt recorded for {endpoint}: {state.daily_used}/{state.daily_quota}")
    
    def record_request_success(self, endpoint: str):
        """Record successful request"""
        if endpoint not in self.limits_state:
            return
        
        state = self.limits_state[endpoint]
        state.last_success = time.time()
        state.consecutive_failures = 0
        state.blocked_until = None  # Clear any blocks
        
        self._save_state()
        
        logger.info(f"Successful request recorded for {endpoint}")
    
    def record_rate_limit_hit(self, endpoint: str, retry_after: Optional[int] = None):
        """Record rate limit hit with intelligent backoff"""
        if endpoint not in self.limits_state:
            return
        
        state = self.limits_state[endpoint]
        state.consecutive_failures += 1
        
        # Use provided retry_after or calculate smart backoff
        if retry_after:
            backoff_time = retry_after
        else:
            # Smart backoff: start with 1 hour, double for each failure, max 4 hours
            backoff_time = min(14400, 3600 * (2 ** (state.consecutive_failures - 1)))
        
        state.blocked_until = time.time() + backoff_time
        
        self._save_state()
        
        logger.warning(f"Rate limit hit for {endpoint}: blocked for {backoff_time}s, failure #{state.consecutive_failures}")
    
    def get_next_available_time(self, endpoint: str) -> Optional[float]:
        """Get next time when request will be available"""
        can_request, reason = self.can_make_request(endpoint)
        
        if can_request:
            return time.time()  # Available now
        
        if endpoint not in self.limits_state:
            return None
        
        state = self.limits_state[endpoint]
        now = time.time()
        
        # Calculate next available time based on various constraints
        next_times = []
        
        # If blocked, use that time
        if state.blocked_until:
            next_times.append(state.blocked_until)
        
        # If we have daily quota issues, wait until tomorrow
        if state.daily_used >= state.daily_quota:
            tomorrow = datetime.now() + timedelta(days=1)
            midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            next_times.append(midnight.timestamp())
        
        # If minimum delay not met
        if state.last_success:
            min_delay = self.min_delays.get(endpoint, 600)
            next_times.append(state.last_success + min_delay)
        
        return max(next_times) if next_times else now + 3600  # Default 1 hour
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get status summary of all endpoints"""
        self._reset_daily_quotas_if_needed()
        
        summary = {
            'endpoints': {},
            'total_daily_requests': 0,
            'total_daily_quota': 0,
            'next_reset': self._get_next_reset_time()
        }
        
        now = time.time()
        
        for endpoint, state in self.limits_state.items():
            can_request, reason = self.can_make_request(endpoint)
            next_available = self.get_next_available_time(endpoint)
            
            endpoint_status = {
                'daily_used': state.daily_used,
                'daily_quota': state.daily_quota,
                'can_request': can_request,
                'reason': reason,
                'next_available_in': int(next_available - now) if next_available else None,
                'consecutive_failures': state.consecutive_failures,
                'last_success': datetime.fromtimestamp(state.last_success).isoformat() if state.last_success else None
            }
            
            summary['endpoints'][endpoint] = endpoint_status
            summary['total_daily_requests'] += state.daily_used
            summary['total_daily_quota'] += state.daily_quota
        
        return summary
    
    def _get_next_reset_time(self) -> str:
        """Get next quota reset time"""
        tomorrow = datetime.now() + timedelta(days=1)
        midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight.isoformat()
    
    def force_reset_endpoint(self, endpoint: str):
        """Force reset an endpoint (emergency use)"""
        if endpoint in self.limits_state:
            state = self.limits_state[endpoint]
            state.daily_used = 0
            state.consecutive_failures = 0
            state.blocked_until = None
            state.last_success = None
            
            self._save_state()
            
            logger.warning(f"Force reset endpoint: {endpoint}")
    
    def get_optimal_search_strategy(self) -> Dict[str, Any]:
        """Get optimal search strategy for current quotas"""
        can_search, reason = self.can_make_request('search_tweets')
        
        if not can_search:
            next_search_time = self.get_next_available_time('search_tweets')
            return {
                'can_search_now': False,
                'reason': reason,
                'next_search_in_seconds': int(next_search_time - time.time()) if next_search_time else None,
                'next_search_time': datetime.fromtimestamp(next_search_time).isoformat() if next_search_time else None,
                'strategy': 'wait'
            }
        
        # If we can search, provide conservative strategy
        state = self.limits_state['search_tweets']
        remaining_quota = state.daily_quota - state.daily_used
        
        return {
            'can_search_now': True,
            'remaining_quota_today': remaining_quota,
            'recommended_keywords_per_search': 1,  # Only 1 focused topic per search
            'recommended_delay_between_keywords': 6 * 3600,  # 6 hours between searches (morning/evening)
            'strategy': 'authentic_dad_usage',
            'content_generation_preferred': True  # Prefer Claude content over API searches
        }

    async def wait_until_available(self, endpoint: str, max_wait: int = 7200) -> bool:
        """
        Wait until endpoint is available for request
        Returns True if available, False if max_wait exceeded
        """
        start_time = time.time()
        
        while True:
            can_request, reason = self.can_make_request(endpoint)
            
            if can_request:
                return True
            
            # Check if we've exceeded max wait time
            if time.time() - start_time > max_wait:
                logger.warning(f"Max wait time {max_wait}s exceeded for {endpoint}")
                return False
            
            # Wait a bit before checking again
            await asyncio.sleep(60)  # Check every minute