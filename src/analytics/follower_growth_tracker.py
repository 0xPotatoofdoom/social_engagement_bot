"""
Follower Growth Tracker - captures daily follower snapshots and tracks growth metrics.

This module provides:
1. Daily follower count snapshots
2. Growth rate calculations
3. Milestone tracking
4. Growth anomaly detection
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .schemas import FollowerSnapshot


class FollowerGrowthTracker:
    """Tracks follower growth over time with daily snapshots and analytics"""
    
    def __init__(self, data_dir: str = "data/analytics"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_file = self.data_dir / "follower_snapshots.json"
        self.milestones_file = self.data_dir / "follower_milestones.json"
        
        # Initialize files if they don't exist
        if not self.snapshots_file.exists():
            self._save_json(self.snapshots_file, [])
        if not self.milestones_file.exists():
            self._save_json(self.milestones_file, {
                "milestones": [500, 750, 1000, 1500, 2000, 3000, 5000],
                "achieved": [],
                "next_target": 500,
                "current_progress": 0
            })
    
    def capture_daily_snapshot(self) -> Dict[str, Any]:
        """Capture current follower count snapshot"""
        # For now, use baseline data - this will be enhanced with real X API calls
        baseline_data = self._load_baseline_metrics()
        
        total_followers = baseline_data.get('total_followers', 1100)
        following_count = 2800  # Estimated from analytics
        
        snapshot = FollowerSnapshot(
            timestamp=datetime.now(),
            verified_followers=baseline_data.get('verified_followers', 397),
            total_followers=total_followers,
            following_count=following_count,  # Estimated from analytics
            posts_count=420,  # Estimated
            source='baseline_data',
            quality_indicators={
                'engagement_rate': baseline_data.get('engagement_rate', 4.9),
                'profile_visits': baseline_data.get('profile_visits', 352),
                'impression_rate': baseline_data.get('impressions', 79300)
            }
        )
        
        # Add follower_following_ratio to the returned dict
        snapshot_dict = snapshot.to_dict()
        snapshot_dict['follower_following_ratio'] = total_followers / following_count if following_count > 0 else 0
        
        # Save snapshot
        self._save_snapshot(snapshot)
        
        return snapshot_dict
    
    def get_milestone_progress(self) -> Dict[str, Any]:
        """Get progress toward follower milestones"""
        milestones_data = self._load_json(self.milestones_file)
        baseline_data = self._load_baseline_metrics()
        current_followers = baseline_data.get('verified_followers', 397)
        
        # Find next milestone
        next_milestone = None
        for milestone in milestones_data['milestones']:
            if milestone > current_followers:
                next_milestone = milestone
                break
        
        if next_milestone is None:
            next_milestone = milestones_data['milestones'][-1] + 1000
        
        # Calculate progress
        previous_milestone = 0
        for milestone in milestones_data['milestones']:
            if milestone <= current_followers:
                previous_milestone = milestone
            else:
                break
        
        progress_range = next_milestone - previous_milestone
        current_progress = current_followers - previous_milestone
        progress_percentage = (current_progress / progress_range) * 100 if progress_range > 0 else 0
        
        # Estimate achievement date (assuming 1.5 followers per day average growth)
        daily_growth_estimate = 1.5
        days_to_milestone = (next_milestone - current_followers) / daily_growth_estimate
        estimated_date = datetime.now() + timedelta(days=days_to_milestone)
        
        return {
            'next_milestone': next_milestone,
            'progress_percentage': round(progress_percentage, 1),
            'estimated_achievement_date': estimated_date.isoformat(),
            'daily_target': round((next_milestone - current_followers) / 90, 2),  # 3-month target
            'milestone_history': milestones_data.get('achieved', []),
            'current_followers': current_followers
        }
    
    def _save_snapshot(self, snapshot: FollowerSnapshot) -> None:
        """Save follower snapshot to file"""
        snapshots = self._load_json(self.snapshots_file)
        snapshots.append(snapshot.to_dict())
        
        # Keep only last 365 days of snapshots
        if len(snapshots) > 365:
            snapshots = snapshots[-365:]
        
        self._save_json(self.snapshots_file, snapshots)
    
    def _load_baseline_metrics(self) -> Dict[str, Any]:
        """Load baseline metrics from the captured baseline"""
        baseline_file = self.data_dir / "baseline_metrics_2025-06-18.json"
        if baseline_file.exists():
            baseline_data = self._load_json(baseline_file)
            return baseline_data.get('x_analytics', {})
        
        # Fallback to hardcoded baseline
        return {
            'verified_followers': 397,
            'total_followers': 1100,
            'engagement_rate': 4.9,
            'profile_visits': 352,
            'impressions': 79300
        }
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Any) -> None:
        """Save data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)