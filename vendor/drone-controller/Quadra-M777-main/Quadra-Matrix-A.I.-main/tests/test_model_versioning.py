"""
Tests for model versioning
"""
import pytest
import torch
import torch.nn as nn
from pathlib import Path
from utils.model_versioning import (
    ModelVersionManager,
    generate_version_string,
    compare_model_versions
)


class SimpleModel(nn.Module):
    """Simple model for testing"""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 5)
    
    def forward(self, x):
        return self.linear(x)


@pytest.fixture
def tmp_models_dir(tmp_path):
    """Create temporary models directory"""
    return tmp_path / "models"


@pytest.fixture
def version_manager(tmp_models_dir):
    """Create version manager"""
    return ModelVersionManager(tmp_models_dir)


@pytest.fixture
def sample_model():
    """Create sample model"""
    return SimpleModel()


def test_version_manager_init(version_manager, tmp_models_dir):
    """Test version manager initialization"""
    assert version_manager.models_dir == tmp_models_dir
    assert tmp_models_dir.exists()
    assert version_manager.registry == {}


def test_save_model(version_manager, sample_model):
    """Test model saving"""
    metadata = version_manager.save_model(
        model=sample_model,
        version="1.0.0",
        metrics={'loss': 0.5, 'accuracy': 0.9},
        config={'hidden_size': 10},
        training_info={'epochs': 10},
        description="Test model"
    )
    
    assert metadata.version == "1.0.0"
    assert metadata.metrics['loss'] == 0.5
    assert 'test model' in metadata.description.lower()
    assert Path(metadata.file_path).exists()


def test_load_model(version_manager, sample_model):
    """Test model loading"""
    # Save first
    version_manager.save_model(
        model=sample_model,
        version="1.0.0",
        metrics={'loss': 0.5},
        config={},
        training_info={}
    )
    
    # Create new model and load
    new_model = SimpleModel()
    metadata = version_manager.load_model(new_model, "1.0.0")
    
    assert metadata.version == "1.0.0"
    
    # Check weights match
    for p1, p2 in zip(sample_model.parameters(), new_model.parameters()):
        assert torch.allclose(p1, p2)


def test_integrity_check(version_manager, sample_model, tmp_models_dir):
    """Test integrity checking"""
    # Save model
    metadata = version_manager.save_model(
        model=sample_model,
        version="1.0.0",
        metrics={},
        config={},
        training_info={}
    )
    
    # Corrupt the file
    model_path = Path(metadata.file_path)
    with open(model_path, 'ab') as f:
        f.write(b'corrupt data')
    
    # Try to load with integrity check
    new_model = SimpleModel()
    with pytest.raises(ValueError, match="integrity check failed"):
        version_manager.load_model(new_model, "1.0.0", verify_integrity=True)


def test_get_latest_version(version_manager, sample_model):
    """Test getting latest version"""
    assert version_manager.get_latest_version() is None
    
    # Save multiple versions
    for i in range(3):
        version_manager.save_model(
            model=sample_model,
            version=f"1.0.{i}",
            metrics={},
            config={},
            training_info={}
        )
    
    latest = version_manager.get_latest_version()
    assert latest is not None


def test_list_versions(version_manager, sample_model):
    """Test listing versions"""
    # Save with tags
    version_manager.save_model(
        model=sample_model,
        version="1.0.0",
        metrics={},
        config={},
        training_info={},
        tags=['production']
    )
    
    version_manager.save_model(
        model=sample_model,
        version="1.0.1",
        metrics={},
        config={},
        training_info={},
        tags=['experimental']
    )
    
    # List all
    all_versions = version_manager.list_versions()
    assert len(all_versions) == 2
    
    # Filter by tag
    prod_versions = version_manager.list_versions(tags=['production'])
    assert len(prod_versions) == 1
    assert prod_versions[0].version == "1.0.0"


def test_promote_to_production(version_manager, sample_model):
    """Test promoting to production"""
    # Save versions
    version_manager.save_model(
        model=sample_model,
        version="1.0.0",
        metrics={},
        config={},
        training_info={}
    )
    
    version_manager.save_model(
        model=sample_model,
        version="1.0.1",
        metrics={},
        config={},
        training_info={}
    )
    
    # Promote
    version_manager.promote_to_production("1.0.1")
    
    prod_version = version_manager.get_production_version()
    assert prod_version == "1.0.1"


def test_generate_version_string():
    """Test version string generation"""
    version = generate_version_string()
    assert len(version) > 0
    
    version_with_prefix = generate_version_string("train")
    assert version_with_prefix.startswith("train-")


def test_compare_versions(version_manager, sample_model):
    """Test version comparison"""
    # Save two versions
    version_manager.save_model(
        model=sample_model,
        version="1.0.0",
        metrics={'loss': 1.0, 'accuracy': 0.7},
        config={},
        training_info={}
    )
    
    version_manager.save_model(
        model=sample_model,
        version="1.0.1",
        metrics={'loss': 0.5, 'accuracy': 0.9},
        config={},
        training_info={}
    )
    
    # Compare
    comparison = compare_model_versions(version_manager, "1.0.0", "1.0.1")
    
    assert comparison['version1'] == "1.0.0"
    assert comparison['version2'] == "1.0.1"
    assert comparison['metrics_comparison']['loss']['improvement'] == -0.5
    assert comparison['metrics_comparison']['accuracy']['improvement'] == 0.2
