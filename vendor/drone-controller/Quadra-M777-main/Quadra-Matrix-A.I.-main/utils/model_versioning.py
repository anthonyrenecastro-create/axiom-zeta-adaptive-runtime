"""
Model versioning and management system
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import torch
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for model versions"""
    version: str
    created_at: str
    model_hash: str
    metrics: Dict[str, float]
    config: Dict[str, Any]
    training_info: Dict[str, Any]
    file_path: str
    file_size: int
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ModelVersionManager:
    """Manages model versions and metadata"""
    
    def __init__(self, models_dir: Path, metadata_file: str = "model_registry.json"):
        """
        Initialize model version manager
        
        Args:
            models_dir: Directory for model storage
            metadata_file: JSON file for version metadata
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.models_dir / metadata_file
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, ModelMetadata]:
        """Load model registry from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                return {
                    version: ModelMetadata(**meta)
                    for version, meta in data.items()
                }
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                return {}
        return {}
    
    def _save_registry(self):
        """Save model registry to disk"""
        try:
            data = {
                version: asdict(meta)
                for version, meta in self.registry.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Registry saved with {len(self.registry)} versions")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of model file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def save_model(
        self,
        model: torch.nn.Module,
        version: str,
        metrics: Dict[str, float],
        config: Dict[str, Any],
        training_info: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ModelMetadata:
        """
        Save model with version metadata
        
        Args:
            model: PyTorch model to save
            version: Version identifier (e.g., "1.0.0", "2024-12-21-001")
            metrics: Training metrics (loss, accuracy, etc.)
            config: Model configuration
            training_info: Training run information
            description: Human-readable description
            tags: Optional tags for categorization
            
        Returns:
            ModelMetadata object
        """
        # Create version-specific filename
        model_filename = f"model_v{version}.pth"
        model_path = self.models_dir / model_filename
        
        # Save model state
        try:
            torch.save(model.state_dict(), model_path)
            logger.info(f"Model saved: {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
        
        # Compute hash and size
        model_hash = self._compute_hash(model_path)
        file_size = model_path.stat().st_size
        
        # Create metadata
        metadata = ModelMetadata(
            version=version,
            created_at=datetime.now().isoformat(),
            model_hash=model_hash,
            metrics=metrics,
            config=config,
            training_info=training_info,
            file_path=str(model_path),
            file_size=file_size,
            description=description,
            tags=tags or []
        )
        
        # Update registry
        self.registry[version] = metadata
        self._save_registry()
        
        logger.info(f"Model version {version} registered")
        return metadata
    
    def load_model(
        self,
        model: torch.nn.Module,
        version: str,
        verify_integrity: bool = True
    ) -> ModelMetadata:
        """
        Load model by version
        
        Args:
            model: Model instance to load state into
            version: Version to load
            verify_integrity: Whether to verify hash
            
        Returns:
            ModelMetadata for loaded version
            
        Raises:
            ValueError: If version not found or integrity check fails
        """
        if version not in self.registry:
            raise ValueError(f"Model version {version} not found")
        
        metadata = self.registry[version]
        model_path = Path(metadata.file_path)
        
        if not model_path.exists():
            raise ValueError(f"Model file not found: {model_path}")
        
        # Verify integrity
        if verify_integrity:
            current_hash = self._compute_hash(model_path)
            if current_hash != metadata.model_hash:
                raise ValueError(
                    f"Model integrity check failed for version {version}. "
                    f"Expected hash: {metadata.model_hash}, "
                    f"Got: {current_hash}"
                )
            logger.info(f"Model integrity verified for version {version}")
        
        # Load model state
        try:
            state_dict = torch.load(model_path, map_location='cpu')
            model.load_state_dict(state_dict)
            logger.info(f"Model version {version} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        return metadata
    
    def get_latest_version(self) -> Optional[str]:
        """Get latest model version"""
        if not self.registry:
            return None
        
        # Sort by created timestamp
        sorted_versions = sorted(
            self.registry.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )
        return sorted_versions[0][0]
    
    def list_versions(self, tags: Optional[List[str]] = None) -> List[ModelMetadata]:
        """
        List all model versions, optionally filtered by tags
        
        Args:
            tags: Filter by tags
            
        Returns:
            List of ModelMetadata objects
        """
        versions = list(self.registry.values())
        
        if tags:
            versions = [
                v for v in versions
                if v.tags and any(tag in v.tags for tag in tags)
            ]
        
        return sorted(versions, key=lambda x: x.created_at, reverse=True)
    
    def get_version_info(self, version: str) -> Optional[ModelMetadata]:
        """Get metadata for specific version"""
        return self.registry.get(version)
    
    def delete_version(self, version: str, delete_file: bool = False):
        """
        Delete model version from registry
        
        Args:
            version: Version to delete
            delete_file: Whether to delete the model file
        """
        if version not in self.registry:
            raise ValueError(f"Version {version} not found")
        
        metadata = self.registry[version]
        
        # Delete file if requested
        if delete_file:
            model_path = Path(metadata.file_path)
            if model_path.exists():
                model_path.unlink()
                logger.info(f"Deleted model file: {model_path}")
        
        # Remove from registry
        del self.registry[version]
        self._save_registry()
        logger.info(f"Version {version} removed from registry")
    
    def promote_to_production(self, version: str):
        """Mark a version as production-ready"""
        if version not in self.registry:
            raise ValueError(f"Version {version} not found")
        
        metadata = self.registry[version]
        if metadata.tags is None:
            metadata.tags = []
        
        # Remove production tag from other versions
        for v, meta in self.registry.items():
            if meta.tags and 'production' in meta.tags:
                meta.tags.remove('production')
        
        # Add production tag to this version
        if 'production' not in metadata.tags:
            metadata.tags.append('production')
        
        self._save_registry()
        logger.info(f"Version {version} promoted to production")
    
    def get_production_version(self) -> Optional[str]:
        """Get current production version"""
        for version, metadata in self.registry.items():
            if metadata.tags and 'production' in metadata.tags:
                return version
        return None


def generate_version_string(prefix: str = "") -> str:
    """
    Generate version string with timestamp
    
    Args:
        prefix: Optional prefix (e.g., "train", "exp")
        
    Returns:
        Version string like "train-2024-12-21-001"
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if prefix:
        return f"{prefix}-{timestamp}"
    return timestamp


def compare_model_versions(
    manager: ModelVersionManager,
    version1: str,
    version2: str
) -> Dict[str, Any]:
    """
    Compare two model versions
    
    Args:
        manager: ModelVersionManager instance
        version1: First version
        version2: Second version
        
    Returns:
        Comparison results
    """
    meta1 = manager.get_version_info(version1)
    meta2 = manager.get_version_info(version2)
    
    if not meta1 or not meta2:
        raise ValueError("One or both versions not found")
    
    return {
        'version1': version1,
        'version2': version2,
        'created_at_diff': meta2.created_at,
        'metrics_comparison': {
            metric: {
                'v1': meta1.metrics.get(metric),
                'v2': meta2.metrics.get(metric),
                'improvement': (
                    meta2.metrics.get(metric, 0) - meta1.metrics.get(metric, 0)
                    if metric in meta1.metrics and metric in meta2.metrics
                    else None
                )
            }
            for metric in set(meta1.metrics.keys()) | set(meta2.metrics.keys())
        },
        'size_comparison': {
            'v1': meta1.file_size,
            'v2': meta2.file_size,
            'diff': meta2.file_size - meta1.file_size
        }
    }
