"""
A/B Testing Framework

This module provides a comprehensive A/B testing framework for feature experiments,
user segmentation, and statistical analysis of test results.

Features:
- Multiple experiment variants
- User segmentation and targeting
- Statistical significance testing
- Metrics tracking and analysis
- Gradual rollout support
- Experiment management API
"""

import hashlib
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class ExperimentStatus(Enum):
    """Experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Variant:
    """Experiment variant configuration."""
    name: str
    weight: float  # 0-1, percentage of traffic
    config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class ExperimentMetrics:
    """Metrics for an experiment variant."""
    variant_name: str
    impressions: int = 0
    conversions: int = 0
    total_value: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        return self.conversions / self.impressions if self.impressions > 0 else 0.0
    
    @property
    def average_value(self) -> float:
        """Calculate average value per impression."""
        return self.total_value / self.impressions if self.impressions > 0 else 0.0


class Experiment:
    """
    A/B test experiment with multiple variants.
    """
    
    def __init__(
        self,
        name: str,
        variants: List[Variant],
        description: str = "",
        targeting_rules: Optional[Dict[str, Any]] = None,
        status: ExperimentStatus = ExperimentStatus.DRAFT
    ):
        """
        Initialize experiment.
        
        Args:
            name: Experiment name
            variants: List of experiment variants
            description: Experiment description
            targeting_rules: Rules for user targeting
            status: Experiment status
        """
        self.name = name
        self.variants = variants
        self.description = description
        self.targeting_rules = targeting_rules or {}
        self.status = status
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        
        # Validate variant weights
        total_weight = sum(v.weight for v in variants)
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")
        
        # Metrics storage
        self.metrics: Dict[str, ExperimentMetrics] = {
            variant.name: ExperimentMetrics(variant_name=variant.name)
            for variant in variants
        }
    
    def assign_variant(
        self,
        user_id: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[Variant]:
        """
        Assign a variant to a user.
        
        Args:
            user_id: User identifier
            attributes: User attributes for targeting
        
        Returns:
            Assigned variant or None if user doesn't match targeting
        """
        # Check if experiment is running
        if self.status != ExperimentStatus.RUNNING:
            return None
        
        # Check targeting rules
        if not self._matches_targeting(attributes or {}):
            return None
        
        # Use consistent hashing for stable assignment
        hash_input = f"{self.name}:{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        bucket = (hash_value % 10000) / 10000  # 0-1 range
        
        # Assign variant based on weights
        cumulative_weight = 0.0
        for variant in self.variants:
            cumulative_weight += variant.weight
            if bucket <= cumulative_weight:
                return variant
        
        # Fallback to last variant (shouldn't happen)
        return self.variants[-1]
    
    def _matches_targeting(self, attributes: Dict[str, Any]) -> bool:
        """
        Check if user matches targeting rules.
        
        Args:
            attributes: User attributes
        
        Returns:
            True if user matches targeting
        """
        if not self.targeting_rules:
            return True
        
        for key, rule in self.targeting_rules.items():
            user_value = attributes.get(key)
            
            if isinstance(rule, dict):
                # Complex rule
                if "in" in rule:
                    if user_value not in rule["in"]:
                        return False
                if "not_in" in rule:
                    if user_value in rule["not_in"]:
                        return False
                if "gt" in rule:
                    if user_value is None or user_value <= rule["gt"]:
                        return False
                if "lt" in rule:
                    if user_value is None or user_value >= rule["lt"]:
                        return False
            else:
                # Simple equality check
                if user_value != rule:
                    return False
        
        return True
    
    def track_impression(self, variant_name: str):
        """
        Track an impression for a variant.
        
        Args:
            variant_name: Name of the variant
        """
        if variant_name in self.metrics:
            self.metrics[variant_name].impressions += 1
    
    def track_conversion(
        self,
        variant_name: str,
        value: float = 1.0,
        custom_metrics: Optional[Dict[str, float]] = None
    ):
        """
        Track a conversion for a variant.
        
        Args:
            variant_name: Name of the variant
            value: Conversion value
            custom_metrics: Additional custom metrics
        """
        if variant_name in self.metrics:
            metrics = self.metrics[variant_name]
            metrics.conversions += 1
            metrics.total_value += value
            
            if custom_metrics:
                for key, val in custom_metrics.items():
                    metrics.custom_metrics[key] = (
                        metrics.custom_metrics.get(key, 0.0) + val
                    )
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get experiment results with statistical analysis.
        
        Returns:
            Dictionary with experiment results
        """
        results = {
            "experiment_name": self.name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "variants": []
        }
        
        for variant in self.variants:
            metrics = self.metrics[variant.name]
            results["variants"].append({
                "name": variant.name,
                "weight": variant.weight,
                "impressions": metrics.impressions,
                "conversions": metrics.conversions,
                "conversion_rate": metrics.conversion_rate,
                "total_value": metrics.total_value,
                "average_value": metrics.average_value,
                "custom_metrics": metrics.custom_metrics
            })
        
        # Calculate statistical significance if we have a control
        if len(self.variants) >= 2:
            control = self.metrics[self.variants[0].name]
            
            for i, variant in enumerate(self.variants[1:], 1):
                test = self.metrics[variant.name]
                
                # Simple z-test for conversion rates
                if control.impressions > 0 and test.impressions > 0:
                    p_control = control.conversion_rate
                    p_test = test.conversion_rate
                    
                    # Calculate pooled probability
                    p_pooled = (
                        (control.conversions + test.conversions) /
                        (control.impressions + test.impressions)
                    )
                    
                    # Calculate standard error
                    se = (
                        p_pooled * (1 - p_pooled) *
                        (1/control.impressions + 1/test.impressions)
                    ) ** 0.5
                    
                    # Calculate z-score
                    if se > 0:
                        z_score = (p_test - p_control) / se
                        
                        # Approximate p-value (two-tailed)
                        from math import erf
                        p_value = 2 * (1 - 0.5 * (1 + erf(abs(z_score) / (2**0.5))))
                        
                        results["variants"][i]["statistical_significance"] = {
                            "z_score": z_score,
                            "p_value": p_value,
                            "is_significant": p_value < 0.05,
                            "lift": ((p_test - p_control) / p_control * 100) if p_control > 0 else 0
                        }
        
        return results
    
    def start(self):
        """Start the experiment."""
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now()
    
    def pause(self):
        """Pause the experiment."""
        self.status = ExperimentStatus.PAUSED
    
    def complete(self):
        """Complete the experiment."""
        self.status = ExperimentStatus.COMPLETED
        self.ended_at = datetime.now()


class ABTestingFramework:
    """Framework for managing multiple A/B tests."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize A/B testing framework.
        
        Args:
            storage_path: Path to store experiment data
        """
        self.experiments: Dict[str, Experiment] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        
        if self.storage_path and self.storage_path.exists():
            self._load_experiments()
    
    def create_experiment(
        self,
        name: str,
        variants: List[Dict[str, Any]],
        description: str = "",
        targeting_rules: Optional[Dict[str, Any]] = None
    ) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            variants: List of variant configurations
            description: Experiment description
            targeting_rules: User targeting rules
        
        Returns:
            Created experiment
        
        Example:
            >>> framework = ABTestingFramework()
            >>> experiment = framework.create_experiment(
            ...     name="new_ui_test",
            ...     variants=[
            ...         {"name": "control", "weight": 0.5, "config": {"ui": "old"}},
            ...         {"name": "treatment", "weight": 0.5, "config": {"ui": "new"}}
            ...     ],
            ...     targeting_rules={"country": {"in": ["US", "CA"]}}
            ... )
        """
        variant_objects = [Variant(**v) for v in variants]
        
        experiment = Experiment(
            name=name,
            variants=variant_objects,
            description=description,
            targeting_rules=targeting_rules
        )
        
        self.experiments[name] = experiment
        self._save_experiments()
        
        return experiment
    
    def get_variant(
        self,
        experiment_name: str,
        user_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        track_impression: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get assigned variant for a user.
        
        Args:
            experiment_name: Name of experiment
            user_id: User identifier
            attributes: User attributes
            track_impression: Whether to track impression
        
        Returns:
            Variant configuration or None
        """
        experiment = self.experiments.get(experiment_name)
        if not experiment:
            return None
        
        variant = experiment.assign_variant(user_id, attributes)
        if not variant:
            return None
        
        if track_impression:
            experiment.track_impression(variant.name)
            self._save_experiments()
        
        return {
            "variant_name": variant.name,
            "config": variant.config
        }
    
    def track_conversion(
        self,
        experiment_name: str,
        variant_name: str,
        value: float = 1.0,
        custom_metrics: Optional[Dict[str, float]] = None
    ):
        """
        Track a conversion.
        
        Args:
            experiment_name: Name of experiment
            variant_name: Name of variant
            value: Conversion value
            custom_metrics: Custom metrics
        """
        experiment = self.experiments.get(experiment_name)
        if experiment:
            experiment.track_conversion(variant_name, value, custom_metrics)
            self._save_experiments()
    
    def get_experiment_results(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """
        Get experiment results.
        
        Args:
            experiment_name: Name of experiment
        
        Returns:
            Experiment results or None
        """
        experiment = self.experiments.get(experiment_name)
        return experiment.get_results() if experiment else None
    
    def _save_experiments(self):
        """Save experiments to storage."""
        if not self.storage_path:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        for name, experiment in self.experiments.items():
            file_path = self.storage_path / f"{name}.json"
            with open(file_path, 'w') as f:
                json.dump(experiment.get_results(), f, indent=2)
    
    def _load_experiments(self):
        """Load experiments from storage."""
        # Implementation would load from storage
        # For now, experiments are created fresh each time
        pass


# Flask integration decorator
def ab_test(
    framework: ABTestingFramework,
    experiment_name: str,
    get_user_id: Callable = None
):
    """
    Decorator for A/B testing Flask routes.
    
    Args:
        framework: ABTestingFramework instance
        experiment_name: Name of experiment
        get_user_id: Function to get user ID from request
    
    Example:
        >>> @app.route('/feature')
        >>> @ab_test(framework, 'new_feature_test')
        >>> def feature_route():
        >>>     variant = g.ab_variant
        >>>     if variant['variant_name'] == 'treatment':
        >>>         return render_template('new_feature.html')
        >>>     return render_template('old_feature.html')
    """
    def decorator(func: Callable) -> Callable:
        from functools import wraps
        from flask import g, request
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user ID
            if get_user_id:
                user_id = get_user_id()
            else:
                # Default: use session or IP
                from flask import session
                user_id = session.get('user_id') or request.remote_addr
            
            # Get variant
            variant = framework.get_variant(experiment_name, user_id)
            g.ab_variant = variant
            g.ab_experiment = experiment_name
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
