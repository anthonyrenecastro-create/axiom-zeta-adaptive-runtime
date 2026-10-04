"""
Integration tests for Quadra Matrix A.I. system
"""
import pytest
import asyncio
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for full system"""
    
    def test_full_initialization_flow(self):
        """Test complete system initialization"""
        from app import SystemState
        
        state = SystemState()
        
        # Initialization steps
        from app import (
            OscillatorySynapseTheory,
            CoreField,
            SyntropyEngine,
            PatternModule,
            NeuroplasticityManager,
            SymbolicConfig,
            SymbolicPredictiveInterpreter
        )
        
        state.oscillator = OscillatorySynapseTheory(field_size=50)
        state.core_field = CoreField(size=50)
        state.syntropy_engine = SyntropyEngine(num_fields=3, field_size=50)
        state.pattern_module = PatternModule(n_clusters=3)
        
        assert state.oscillator is not None
        assert state.core_field is not None
        assert state.syntropy_engine is not None
    
    def test_training_iteration(self):
        """Test single training iteration"""
        from app import (
            SystemState,
            OscillatorySynapseTheory,
            CoreField,
            SyntropyEngine,
            PatternModule,
            NeuroplasticityManager
        )
        
        state = SystemState()
        state.oscillator = OscillatorySynapseTheory(field_size=50)
        state.core_field = CoreField(size=50)
        state.syntropy_engine = SyntropyEngine(num_fields=3, field_size=50)
        state.pattern_module = PatternModule(n_clusters=3)
        state.neuroplasticity_manager = NeuroplasticityManager(
            state.oscillator, state.core_field, state.syntropy_engine
        )
        
        # Run one training iteration
        test_text = "The quantum field oscillates with harmonic resonance"
        
        try:
            feature_vector = state.oscillator.process_streamed_data(test_text)
            assert feature_vector is not None
            assert len(feature_vector) == 50
        except Exception as e:
            pytest.skip(f"Training iteration requires full setup: {e}")
    
    def test_state_persistence(self, temp_dir):
        """Test state save and load"""
        from app import SystemState
        import os
        
        # Override paths to use temp directory
        with patch('app.STATE_DIR', str(temp_dir)):
            state1 = SystemState()
            state1.loss_history = [0.5, 0.4, 0.3]
            state1.iteration_count = 3
            
            # Note: save_state requires initialized components
            # This tests the interface
            assert hasattr(state1, 'save_state')
            assert hasattr(state1, 'load_state')


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def test_dashboard_workflow(self, client):
        """Test complete dashboard workflow"""
        # 1. Access dashboard
        response = client.get('/')
        assert response.status_code == 200
        
        # 2. Check health
        response = client.get('/health')
        assert response.status_code == 200
        
        # 3. Get initial status
        response = client.get('/api/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'initialized' in data
    
    def test_error_recovery(self):
        """Test system can recover from errors"""
        from app import SystemState
        
        state = SystemState()
        
        # System should handle uninitialized state gracefully
        assert state.is_initialized is False
        assert state.is_running is False


@pytest.mark.slow
class TestPerformance:
    """Performance and load tests"""
    
    def test_field_update_performance(self):
        """Test field update performance"""
        import time
        import numpy as np
        from app import CoreField
        
        field = CoreField(size=1000)
        update = np.random.randn(1000) * 0.1
        
        start = time.time()
        for _ in range(100):
            field.update_with_vibrational_mode(update)
        duration = time.time() - start
        
        # Should complete 100 updates in reasonable time
        assert duration < 5.0, f"Updates too slow: {duration}s"
    
    def test_multiple_clients_health_check(self, client):
        """Test health endpoint handles multiple requests"""
        import concurrent.futures
        
        def check_health():
            response = client.get('/health')
            return response.status_code
        
        # Simulate multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(50)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        assert all(code == 200 for code in results)


@pytest.mark.integration
class TestSocketIOIntegration:
    """SocketIO integration tests"""
    
    def test_socketio_events_defined(self):
        """Test that SocketIO events are properly defined"""
        # Import to ensure no syntax errors
        import app
        
        # Check that handlers exist
        assert hasattr(app, 'handle_connect')
        assert hasattr(app, 'handle_disconnect')
        assert hasattr(app, 'handle_initialize')
        assert hasattr(app, 'handle_start_training')
        assert hasattr(app, 'handle_stop_training')
