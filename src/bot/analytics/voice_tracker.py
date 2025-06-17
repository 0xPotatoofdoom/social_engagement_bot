"""
Voice Metrics Tracking System

Tracks voice evolution, content performance, and engagement correlations over time
to enable data-driven voice optimization and content generation improvement.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


@dataclass
class VoiceSnapshot:
    """Snapshot of voice characteristics at a specific point in time."""
    timestamp: datetime
    posts_analyzed: int
    voice_characteristics: Dict[str, float]
    engagement_correlations: Dict[str, float]
    best_performing_themes: List[str]
    optimal_length_range: Tuple[int, int]
    primary_engagement_driver: str
    average_engagement: float
    analysis_version: str = "1.0"


@dataclass
class ContentPerformanceMetric:
    """Individual content performance tracking."""
    content_id: str
    timestamp: datetime
    content_type: str  # 'authentic', 'generated', 'optimized'
    voice_scores: Dict[str, float]
    engagement_metrics: Dict[str, int]
    engagement_score: float
    voice_alignment_score: float  # How well it matches authentic voice
    content_length: int
    themes: List[str]
    hashtags: List[str]


@dataclass
class VoiceEvolutionMetrics:
    """Track how voice characteristics evolve over time."""
    characteristic_trends: Dict[str, List[Tuple[datetime, float]]]
    engagement_correlation_trends: Dict[str, List[Tuple[datetime, float]]]
    performance_improvements: List[Dict]
    optimization_experiments: List[Dict]


class VoiceTracker:
    """
    Tracks voice evolution and content performance over time.
    
    Features:
    - Historical voice characteristic tracking
    - Content performance correlation analysis
    - A/B testing framework for voice optimization
    - Engagement prediction model refinement
    - Voice consistency monitoring
    """
    
    def __init__(self, storage_path: str = "data/voice_tracking"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.voice_history_file = self.storage_path / "voice_snapshots.json"
        self.content_performance_file = self.storage_path / "content_performance.json"
        self.evolution_metrics_file = self.storage_path / "evolution_metrics.json"
        
        # Initialize storage if needed
        self._initialize_storage()
        
        # Load existing data
        self.voice_snapshots: List[VoiceSnapshot] = self._load_voice_snapshots()
        self.content_performance: List[ContentPerformanceMetric] = self._load_content_performance()
        self.evolution_metrics: VoiceEvolutionMetrics = self._load_evolution_metrics()
        
        logger.info(
            "voice_tracker_initialized",
            storage_path=str(self.storage_path),
            existing_snapshots=len(self.voice_snapshots),
            content_records=len(self.content_performance)
        )
    
    def _initialize_storage(self):
        """Initialize storage files if they don't exist."""
        for file_path in [self.voice_history_file, self.content_performance_file, self.evolution_metrics_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
                logger.info("storage_file_initialized", file=str(file_path))
    
    def _load_voice_snapshots(self) -> List[VoiceSnapshot]:
        """Load voice snapshots from storage."""
        try:
            with open(self.voice_history_file, 'r') as f:
                data = json.load(f)
                snapshots = []
                for item in data:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    snapshots.append(VoiceSnapshot(**item))
                return snapshots
        except Exception as e:
            logger.warning("voice_snapshots_load_failed", error=str(e))
            return []
    
    def _load_content_performance(self) -> List[ContentPerformanceMetric]:
        """Load content performance data from storage."""
        try:
            with open(self.content_performance_file, 'r') as f:
                data = json.load(f)
                performance = []
                for item in data:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    performance.append(ContentPerformanceMetric(**item))
                return performance
        except Exception as e:
            logger.warning("content_performance_load_failed", error=str(e))
            return []
    
    def _load_evolution_metrics(self) -> VoiceEvolutionMetrics:
        """Load evolution metrics from storage."""
        try:
            with open(self.evolution_metrics_file, 'r') as f:
                data = json.load(f)
                if data:
                    # Convert timestamps back to datetime objects
                    for char, trends in data['characteristic_trends'].items():
                        data['characteristic_trends'][char] = [
                            (datetime.fromisoformat(ts), value) for ts, value in trends
                        ]
                    for char, trends in data['engagement_correlation_trends'].items():
                        data['engagement_correlation_trends'][char] = [
                            (datetime.fromisoformat(ts), value) for ts, value in trends
                        ]
                    return VoiceEvolutionMetrics(**data)
                else:
                    return VoiceEvolutionMetrics(
                        characteristic_trends={},
                        engagement_correlation_trends={},
                        performance_improvements=[],
                        optimization_experiments=[]
                    )
        except Exception as e:
            logger.warning("evolution_metrics_load_failed", error=str(e))
            return VoiceEvolutionMetrics(
                characteristic_trends={},
                engagement_correlation_trends={},
                performance_improvements=[],
                optimization_experiments=[]
            )
    
    def record_voice_snapshot(self, voice_profile, analysis_metadata: Dict) -> VoiceSnapshot:
        """Record a new voice analysis snapshot."""
        
        # Determine primary engagement driver
        correlations = voice_profile.engagement_correlations
        primary_driver = max(correlations.items(), key=lambda x: abs(x[1]))[0] if correlations else "unknown"
        
        snapshot = VoiceSnapshot(
            timestamp=datetime.now(),
            posts_analyzed=analysis_metadata.get('posts_analyzed', 0),
            voice_characteristics=voice_profile.tone_distribution,
            engagement_correlations=correlations,
            best_performing_themes=voice_profile.best_posting_themes[:5],
            optimal_length_range=voice_profile.optimal_length_range,
            primary_engagement_driver=primary_driver,
            average_engagement=analysis_metadata.get('average_engagement', 0.0)
        )
        
        self.voice_snapshots.append(snapshot)
        self._update_evolution_metrics(snapshot)
        self._save_voice_snapshots()
        
        logger.info(
            "voice_snapshot_recorded",
            timestamp=snapshot.timestamp.isoformat(),
            posts_analyzed=snapshot.posts_analyzed,
            primary_driver=primary_driver
        )
        
        return snapshot
    
    def record_content_performance(self, content_data: Dict) -> ContentPerformanceMetric:
        """Record performance of generated or authentic content."""
        
        metric = ContentPerformanceMetric(
            content_id=content_data['content_id'],
            timestamp=datetime.now(),
            content_type=content_data['content_type'],
            voice_scores=content_data['voice_scores'],
            engagement_metrics=content_data['engagement_metrics'],
            engagement_score=content_data['engagement_score'],
            voice_alignment_score=content_data.get('voice_alignment_score', 0.0),
            content_length=content_data['content_length'],
            themes=content_data.get('themes', []),
            hashtags=content_data.get('hashtags', [])
        )
        
        self.content_performance.append(metric)
        self._save_content_performance()
        
        logger.info(
            "content_performance_recorded",
            content_id=metric.content_id,
            content_type=metric.content_type,
            engagement_score=metric.engagement_score,
            voice_alignment=metric.voice_alignment_score
        )
        
        return metric
    
    def _update_evolution_metrics(self, snapshot: VoiceSnapshot):
        """Update evolution tracking with new snapshot."""
        
        # Update characteristic trends
        for char, value in snapshot.voice_characteristics.items():
            if char not in self.evolution_metrics.characteristic_trends:
                self.evolution_metrics.characteristic_trends[char] = []
            self.evolution_metrics.characteristic_trends[char].append((snapshot.timestamp, value))
        
        # Update engagement correlation trends
        for char, correlation in snapshot.engagement_correlations.items():
            if char not in self.evolution_metrics.engagement_correlation_trends:
                self.evolution_metrics.engagement_correlation_trends[char] = []
            self.evolution_metrics.engagement_correlation_trends[char].append((snapshot.timestamp, correlation))
        
        # Detect performance improvements
        if len(self.voice_snapshots) > 1:
            previous = self.voice_snapshots[-2]
            current = snapshot
            
            if current.average_engagement > previous.average_engagement:
                improvement = {
                    'timestamp': current.timestamp.isoformat(),
                    'type': 'engagement_increase',
                    'previous_engagement': previous.average_engagement,
                    'current_engagement': current.average_engagement,
                    'improvement_percent': ((current.average_engagement - previous.average_engagement) / previous.average_engagement) * 100,
                    'potential_drivers': self._identify_improvement_drivers(previous, current)
                }
                self.evolution_metrics.performance_improvements.append(improvement)
        
        self._save_evolution_metrics()
    
    def _identify_improvement_drivers(self, previous: VoiceSnapshot, current: VoiceSnapshot) -> List[str]:
        """Identify what characteristics changed that might have driven improvement."""
        drivers = []
        
        for char in current.voice_characteristics:
            if char in previous.voice_characteristics:
                change = current.voice_characteristics[char] - previous.voice_characteristics[char]
                if abs(change) > 0.05:  # Significant change threshold
                    direction = "increased" if change > 0 else "decreased"
                    drivers.append(f"{char} {direction} by {change:.2f}")
        
        return drivers
    
    def analyze_voice_evolution(self, days_back: int = 90) -> Dict:
        """Analyze how voice characteristics have evolved over time."""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_snapshots = [s for s in self.voice_snapshots if s.timestamp >= cutoff_date]
        
        if len(recent_snapshots) < 2:
            return {"error": "Insufficient data for evolution analysis"}
        
        analysis = {
            'time_period': f"{days_back} days",
            'snapshots_analyzed': len(recent_snapshots),
            'characteristic_trends': {},
            'engagement_trends': {},
            'key_insights': []
        }
        
        # Analyze characteristic evolution
        for char in recent_snapshots[0].voice_characteristics:
            values = [s.voice_characteristics[char] for s in recent_snapshots]
            initial_value = values[0]
            final_value = values[-1]
            change = final_value - initial_value
            
            analysis['characteristic_trends'][char] = {
                'initial_value': initial_value,
                'final_value': final_value,
                'change': change,
                'trend': 'increasing' if change > 0.02 else 'decreasing' if change < -0.02 else 'stable'
            }
        
        # Analyze engagement evolution
        engagement_values = [s.average_engagement for s in recent_snapshots]
        engagement_change = engagement_values[-1] - engagement_values[0]
        
        analysis['engagement_trends'] = {
            'initial_engagement': engagement_values[0],
            'final_engagement': engagement_values[-1],
            'change': engagement_change,
            'trend': 'improving' if engagement_change > 0.02 else 'declining' if engagement_change < -0.02 else 'stable'
        }
        
        # Generate insights
        insights = []
        
        # Find strongest positive correlations
        latest_snapshot = recent_snapshots[-1]
        strong_correlations = {k: v for k, v in latest_snapshot.engagement_correlations.items() if abs(v) > 0.3}
        
        if strong_correlations:
            best_driver = max(strong_correlations.items(), key=lambda x: x[1])
            insights.append(f"'{best_driver[0]}' is your strongest engagement driver (correlation: {best_driver[1]:.2f})")
        
        # Identify improvement opportunities
        for char, trend in analysis['characteristic_trends'].items():
            if char in strong_correlations and strong_correlations[char] > 0.3:
                if trend['final_value'] < 0.5:
                    insights.append(f"Opportunity: Increase '{char}' (currently {trend['final_value']:.2f}, correlates positively with engagement)")
        
        analysis['key_insights'] = insights
        
        logger.info("voice_evolution_analysis_completed", insights_count=len(insights), time_period=days_back)
        
        return analysis
    
    def get_content_performance_summary(self, content_type: str = None, days_back: int = 30) -> Dict:
        """Get performance summary for content, optionally filtered by type."""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_content = [
            c for c in self.content_performance 
            if c.timestamp >= cutoff_date and (content_type is None or c.content_type == content_type)
        ]
        
        if not filtered_content:
            return {"error": "No content data found for the specified criteria"}
        
        summary = {
            'time_period': f"{days_back} days",
            'content_count': len(filtered_content),
            'content_type_filter': content_type,
            'performance_metrics': {},
            'voice_alignment': {},
            'recommendations': []
        }
        
        # Calculate performance metrics
        engagement_scores = [c.engagement_score for c in filtered_content]
        voice_alignment_scores = [c.voice_alignment_score for c in filtered_content]
        
        summary['performance_metrics'] = {
            'average_engagement': sum(engagement_scores) / len(engagement_scores),
            'best_engagement': max(engagement_scores),
            'worst_engagement': min(engagement_scores),
            'engagement_variance': self._calculate_variance(engagement_scores)
        }
        
        summary['voice_alignment'] = {
            'average_alignment': sum(voice_alignment_scores) / len(voice_alignment_scores),
            'best_alignment': max(voice_alignment_scores),
            'worst_alignment': min(voice_alignment_scores)
        }
        
        # Generate recommendations
        recommendations = []
        
        if summary['voice_alignment']['average_alignment'] < 0.7:
            recommendations.append("Voice alignment below target (0.7). Consider adjusting content generation parameters.")
        
        if summary['performance_metrics']['engagement_variance'] > 0.1:
            recommendations.append("High engagement variance suggests inconsistent content quality. Review top and bottom performers.")
        
        # Find best performing characteristics
        best_content = max(filtered_content, key=lambda x: x.engagement_score)
        recommendations.append(f"Best performing content had themes: {', '.join(best_content.themes[:3])}")
        
        summary['recommendations'] = recommendations
        
        return summary
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def start_ab_experiment(self, experiment_name: str, experiment_config: Dict) -> str:
        """Start an A/B testing experiment for voice optimization."""
        
        experiment = {
            'id': f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'name': experiment_name,
            'start_time': datetime.now().isoformat(),
            'config': experiment_config,
            'status': 'active',
            'results': []
        }
        
        self.evolution_metrics.optimization_experiments.append(experiment)
        self._save_evolution_metrics()
        
        logger.info(
            "ab_experiment_started",
            experiment_id=experiment['id'],
            experiment_name=experiment_name
        )
        
        return experiment['id']
    
    def record_experiment_result(self, experiment_id: str, result_data: Dict):
        """Record a result for an ongoing A/B experiment."""
        
        for experiment in self.evolution_metrics.optimization_experiments:
            if experiment['id'] == experiment_id:
                experiment['results'].append({
                    'timestamp': datetime.now().isoformat(),
                    'data': result_data
                })
                self._save_evolution_metrics()
                
                logger.info(
                    "experiment_result_recorded",
                    experiment_id=experiment_id,
                    results_count=len(experiment['results'])
                )
                return
        
        logger.warning("experiment_not_found", experiment_id=experiment_id)
    
    def _save_voice_snapshots(self):
        """Save voice snapshots to storage."""
        try:
            data = []
            for snapshot in self.voice_snapshots:
                snapshot_dict = asdict(snapshot)
                snapshot_dict['timestamp'] = snapshot.timestamp.isoformat()
                data.append(snapshot_dict)
            
            with open(self.voice_history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("voice_snapshots_save_failed", error=str(e))
    
    def _save_content_performance(self):
        """Save content performance to storage."""
        try:
            data = []
            for performance in self.content_performance:
                performance_dict = asdict(performance)
                performance_dict['timestamp'] = performance.timestamp.isoformat()
                data.append(performance_dict)
            
            with open(self.content_performance_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("content_performance_save_failed", error=str(e))
    
    def _save_evolution_metrics(self):
        """Save evolution metrics to storage."""
        try:
            data = asdict(self.evolution_metrics)
            
            # Convert datetime objects to ISO strings
            for char, trends in data['characteristic_trends'].items():
                data['characteristic_trends'][char] = [
                    (ts.isoformat() if isinstance(ts, datetime) else ts, value) 
                    for ts, value in trends
                ]
            
            for char, trends in data['engagement_correlation_trends'].items():
                data['engagement_correlation_trends'][char] = [
                    (ts.isoformat() if isinstance(ts, datetime) else ts, value) 
                    for ts, value in trends
                ]
            
            with open(self.evolution_metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("evolution_metrics_save_failed", error=str(e))
    
    def get_tracking_summary(self) -> Dict:
        """Get a summary of all tracking data."""
        return {
            'voice_snapshots_count': len(self.voice_snapshots),
            'content_performance_records': len(self.content_performance),
            'performance_improvements_detected': len(self.evolution_metrics.performance_improvements),
            'active_experiments': len([e for e in self.evolution_metrics.optimization_experiments if e.get('status') == 'active']),
            'latest_snapshot_date': self.voice_snapshots[-1].timestamp.isoformat() if self.voice_snapshots else None,
            'tracking_duration_days': (datetime.now() - self.voice_snapshots[0].timestamp).days if self.voice_snapshots else 0
        }


# Export main classes
__all__ = ['VoiceTracker', 'VoiceSnapshot', 'ContentPerformanceMetric', 'VoiceEvolutionMetrics']