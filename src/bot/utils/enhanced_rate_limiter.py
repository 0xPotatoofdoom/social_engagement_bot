"""
Enhanced Rate Limiting System for X API Optimization
Ultra-smart rate limiting with caching, priority queuing, and follower growth optimization
"""

import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
import hashlib
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class CachedRequest:
    """Cached API request to avoid duplicates"""
    endpoint: str
    params_hash: str
    response_data: Any
    cached_at: float
    expires_at: float

@dataclass
class PriorityRequest:
    """Priority-queued API request"""
    endpoint: str
    params: Dict
    priority: int  # 1=highest, 5=lowest
    scheduled_at: float
    retry_count: int = 0

@dataclass
class RateLimitMetrics:
    """Rate limit usage analytics"""
    endpoint: str
    calls_made: int
    calls_remaining: int
    window_reset: float
    efficiency_score: float
    backoff_time: float

class EnhancedRateLimiter:
    """
    Ultra-smart rate limiting for follower growth optimization
    Features:
    - Request caching to avoid duplicates
    - Priority queuing for high-value opportunities  
    - Smart time distribution
    - Endpoint-specific optimization
    - Predictive rate limiting
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced rate limits based on real X API limits
        self.rate_limits = {
            # Read operations (high limits)
            'search_tweets': {'limit': 300, 'window': 900},      # 300 per 15 min
            'user_timeline': {'limit': 1500, 'window': 900},     # 1500 per 15 min
            'user_lookup': {'limit': 300, 'window': 900},        # 300 per 15 min
            'tweet_lookup': {'limit': 300, 'window': 900},       # 300 per 15 min
            
            # Write operations (limited by daily budget)
            'create_tweet': {'limit': 50, 'window': 86400},      # 50 per day (real limit)
            'create_reply': {'limit': 50, 'window': 86400},      # 50 per day
            'retweet': {'limit': 50, 'window': 86400},           # 50 per day
        }
        
        # Request tracking
        self.request_history = defaultdict(list)
        self.backoff_until = {}
        self.priority_queue = []
        
        # Caching system
        self.request_cache = {}
        self.cache_file = self.cache_dir / "request_cache.json"
        self._load_cache()
        
        # Analytics
        self.daily_usage = defaultdict(int)
        self.usage_analytics = {}
        
        # Follower growth optimization
        self.peak_engagement_hours = [12, 18, 21]  # 12pm, 6pm, 9pm EST
        self.min_interval_between_posts = 1800  # 30 minutes minimum
        self.last_post_time = 0
        
        logger.info("Enhanced rate limiter initialized with follower growth optimization")
    
    def _load_cache(self):
        """Load request cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                now = time.time()
                for key, data in cache_data.items():
                    if data['expires_at'] > now:
                        self.request_cache[key] = CachedRequest(**data)
                        
                logger.info(f"Loaded {len(self.request_cache)} cached requests")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
    
    def _save_cache(self):
        """Save request cache to disk"""
        try:
            cache_data = {
                key: asdict(cached_req) 
                for key, cached_req in self.request_cache.items()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _generate_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for request"""
        # Create deterministic hash of endpoint + params
        content = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_or_request(self, endpoint: str, params: Dict, 
                                  cache_ttl: int = 300, priority: int = 3) -> Tuple[Any, bool]:
        """
        Get cached result or queue new request with priority
        Returns: (result, from_cache)
        """
        cache_key = self._generate_cache_key(endpoint, params)
        
        # Check cache first
        if cache_key in self.request_cache:
            cached_req = self.request_cache[cache_key]
            if cached_req.expires_at > time.time():
                logger.debug(f"Cache hit for {endpoint}")
                return cached_req.response_data, True
            else:
                del self.request_cache[cache_key]
        
        # Queue new request
        return await self._queue_priority_request(endpoint, params, priority, cache_ttl)
    
    async def _queue_priority_request(self, endpoint: str, params: Dict, 
                                    priority: int, cache_ttl: int) -> Tuple[Any, bool]:
        """Queue a priority request and wait for execution"""
        
        # Check if we can make request immediately
        if self.can_make_request(endpoint):
            return await self._execute_request(endpoint, params, cache_ttl), False
        
        # Add to priority queue
        request = PriorityRequest(
            endpoint=endpoint,
            params=params,
            priority=priority,
            scheduled_at=self._calculate_optimal_time(endpoint, priority)
        )
        
        self.priority_queue.append(request)
        self.priority_queue.sort(key=lambda x: (x.priority, x.scheduled_at))
        
        # Wait for execution
        return await self._wait_for_request_execution(request)
    
    def can_make_request(self, endpoint: str) -> bool:
        """Check if we can make a request to endpoint"""
        
        # Check backoff
        if endpoint in self.backoff_until:
            if time.time() < self.backoff_until[endpoint]:
                return False
            else:
                del self.backoff_until[endpoint]
        
        # Check rate limits
        now = time.time()
        limit_info = self.rate_limits.get(endpoint, {'limit': 300, 'window': 900})
        
        # Clean old requests
        window_start = now - limit_info['window']
        self.request_history[endpoint] = [
            req_time for req_time in self.request_history[endpoint]
            if req_time > window_start
        ]
        
        current_count = len(self.request_history[endpoint])
        
        # Special handling for posting endpoints (follower growth optimization)
        if endpoint in ['create_tweet', 'create_reply', 'retweet']:
            return self._can_make_post_request(endpoint, current_count, limit_info['limit'])
        
        return current_count < limit_info['limit']
    
    def _can_make_post_request(self, endpoint: str, current_count: int, limit: int) -> bool:
        """Smart posting limits for follower growth"""
        
        # Respect daily limits
        if current_count >= limit:
            return False
        
        # Minimum interval between posts (avoid spam appearance)
        if time.time() - self.last_post_time < self.min_interval_between_posts:
            return False
        
        # Prefer peak engagement hours
        current_hour = datetime.now().hour
        if current_hour not in self.peak_engagement_hours:
            # Allow but with reduced frequency outside peak hours
            if current_count >= limit * 0.7:  # Use 70% of daily limit outside peak
                return False
        
        return True
    
    def _calculate_optimal_time(self, endpoint: str, priority: int) -> float:
        """Calculate optimal time to execute request"""
        now = time.time()
        
        if endpoint in ['create_tweet', 'create_reply', 'retweet']:
            # For posts, schedule during peak engagement hours
            current_hour = datetime.now().hour
            
            if current_hour in self.peak_engagement_hours:
                # During peak hours, schedule ASAP but respect intervals
                return max(now, self.last_post_time + self.min_interval_between_posts)
            else:
                # Outside peak hours, schedule for next peak hour
                next_peak = min([h for h in self.peak_engagement_hours if h > current_hour] + 
                              [h + 24 for h in self.peak_engagement_hours])
                next_peak_time = now + (next_peak - current_hour) * 3600
                return next_peak_time
        else:
            # For read operations, distribute evenly with priority consideration
            base_delay = (6 - priority) * 60  # Higher priority = less delay
            return now + base_delay
    
    async def _execute_request(self, endpoint: str, params: Dict, cache_ttl: int) -> Any:
        """Execute the actual API request"""
        
        # Record the call
        self.record_call(endpoint)
        
        # TODO: Integrate with actual X API client
        # For now, return mock data
        mock_response = {
            'endpoint': endpoint,
            'params': params,
            'timestamp': time.time(),
            'success': True
        }
        
        # Cache the response
        if cache_ttl > 0:
            cache_key = self._generate_cache_key(endpoint, params)
            self.request_cache[cache_key] = CachedRequest(
                endpoint=endpoint,
                params_hash=cache_key,
                response_data=mock_response,
                cached_at=time.time(),
                expires_at=time.time() + cache_ttl
            )
            self._save_cache()
        
        return mock_response
    
    async def _wait_for_request_execution(self, request: PriorityRequest) -> Any:
        """Wait for queued request to be executed"""
        
        while True:
            # Check if it's time to execute
            if time.time() >= request.scheduled_at and self.can_make_request(request.endpoint):
                try:
                    result = await self._execute_request(request.endpoint, request.params, 300)
                    self.priority_queue.remove(request)
                    return result
                except Exception as e:
                    request.retry_count += 1
                    if request.retry_count >= 3:
                        logger.error(f"Request failed after 3 retries: {e}")
                        self.priority_queue.remove(request)
                        raise
                    
                    # Exponential backoff
                    request.scheduled_at = time.time() + (2 ** request.retry_count * 60)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def record_call(self, endpoint: str):
        """Record an API call"""
        now = time.time()
        self.request_history[endpoint].append(now)
        self.daily_usage[endpoint] += 1
        
        if endpoint in ['create_tweet', 'create_reply', 'retweet']:
            self.last_post_time = now
        
        logger.debug(f"Recorded call to {endpoint}, daily usage: {self.daily_usage[endpoint]}")
    
    def handle_rate_limit_error(self, endpoint: str, retry_after: int = None):
        """Handle rate limit error with smart backoff"""
        backoff_time = retry_after or self._calculate_smart_backoff(endpoint)
        self.backoff_until[endpoint] = time.time() + backoff_time
        
        logger.warning(f"Rate limit hit for {endpoint}, backing off for {backoff_time}s")
    
    def _calculate_smart_backoff(self, endpoint: str) -> int:
        """Calculate smart backoff time based on usage patterns"""
        base_backoff = self.rate_limits.get(endpoint, {}).get('window', 900)
        
        # Adjust based on endpoint type
        if endpoint in ['create_tweet', 'create_reply', 'retweet']:
            # For posting, longer backoff to avoid daily limit exhaustion
            return base_backoff * 2
        else:
            # For reads, shorter backoff
            return base_backoff
    
    def get_usage_analytics(self) -> Dict[str, RateLimitMetrics]:
        """Get detailed usage analytics"""
        analytics = {}
        now = time.time()
        
        for endpoint, limit_info in self.rate_limits.items():
            # Clean old requests
            window_start = now - limit_info['window']
            recent_calls = [
                req_time for req_time in self.request_history[endpoint]
                if req_time > window_start
            ]
            
            calls_made = len(recent_calls)
            calls_remaining = limit_info['limit'] - calls_made
            efficiency_score = calls_made / limit_info['limit'] if limit_info['limit'] > 0 else 0
            
            analytics[endpoint] = RateLimitMetrics(
                endpoint=endpoint,
                calls_made=calls_made,
                calls_remaining=calls_remaining,
                window_reset=window_start + limit_info['window'],
                efficiency_score=efficiency_score,
                backoff_time=max(0, self.backoff_until.get(endpoint, 0) - now)
            )
        
        return analytics
    
    def optimize_for_follower_growth(self) -> Dict[str, Any]:
        """Get follower growth optimization recommendations"""
        analytics = self.get_usage_analytics()
        
        recommendations = {
            'next_optimal_post_time': self._get_next_optimal_post_time(),
            'daily_posts_remaining': 50 - self.daily_usage.get('create_tweet', 0),
            'engagement_window_status': self._get_engagement_window_status(),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'queue_size': len(self.priority_queue),
            'backoff_endpoints': [ep for ep, time_left in self.backoff_until.items() if time_left > time.time()]
        }
        
        return recommendations
    
    def _get_next_optimal_post_time(self) -> float:
        """Get next optimal time to post for maximum engagement"""
        now = time.time()
        current_dt = datetime.now()
        current_hour = current_dt.hour
        
        # If we can post now and it's peak hour, do it
        if (current_hour in self.peak_engagement_hours and 
            time.time() - self.last_post_time >= self.min_interval_between_posts):
            return now
        
        # Otherwise, find next peak hour
        next_peak_hours = [h for h in self.peak_engagement_hours if h > current_hour]
        if not next_peak_hours:
            next_peak_hours = [h + 24 for h in self.peak_engagement_hours]
        
        next_peak = min(next_peak_hours)
        next_peak_dt = current_dt.replace(hour=next_peak % 24, minute=0, second=0, microsecond=0)
        if next_peak >= 24:
            next_peak_dt += timedelta(days=1)
        
        return next_peak_dt.timestamp()
    
    def _get_engagement_window_status(self) -> str:
        """Get current engagement window status"""
        current_hour = datetime.now().hour
        if current_hour in self.peak_engagement_hours:
            return "PEAK_HOURS"
        else:
            return "OFF_PEAK"
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would track actual cache hits vs misses in a real implementation
        return len(self.request_cache) / max(1, sum(self.daily_usage.values()))
    
    def reset_daily_usage(self):
        """Reset daily usage counters (call at midnight)"""
        self.daily_usage.clear()
        logger.info("Daily usage counters reset")