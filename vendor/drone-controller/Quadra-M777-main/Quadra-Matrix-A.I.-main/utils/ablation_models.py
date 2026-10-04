"""
Ablation Study Models
Baseline models for comparing against the full Quadra-Matrix system.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Tuple


class SimpleMLPBaseline(nn.Module):
    """Simple MLP baseline without quantum fields or SNN."""
    
    def __init__(self, input_dim: int = 16, hidden_dim: int = 128, output_dim: int = 4):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through MLP."""
        return self.network(x)


class SimpleQLearner:
    """Simple Q-Learning baseline without neural networks."""
    
    def __init__(self, state_dim: int = 16, action_dim: int = 4, 
                 learning_rate: float = 0.1, gamma: float = 0.99, epsilon: float = 0.1):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        
        # Q-table (discretized states)
        self.q_table = {}
        
    def _discretize_state(self, state: np.ndarray) -> str:
        """Discretize continuous state into bins."""
        # Bin states into discrete values
        discretized = np.digitize(state, bins=np.linspace(-2, 2, 5))
        return str(discretized.tolist())
    
    def get_action(self, state: np.ndarray, training: bool = True) -> int:
        """Epsilon-greedy action selection."""
        state_key = self._discretize_state(state)
        
        # Initialize Q-values if not seen
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_dim)
        
        # Epsilon-greedy
        if training and np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        else:
            return np.argmax(self.q_table[state_key])
    
    def update(self, state: np.ndarray, action: int, reward: float, 
               next_state: np.ndarray, done: bool) -> float:
        """Q-learning update."""
        state_key = self._discretize_state(state)
        next_state_key = self._discretize_state(next_state)
        
        # Initialize if needed
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_dim)
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = np.zeros(self.action_dim)
        
        # Q-learning update
        current_q = self.q_table[state_key][action]
        max_next_q = np.max(self.q_table[next_state_key]) if not done else 0
        target_q = reward + self.gamma * max_next_q
        
        self.q_table[state_key][action] += self.lr * (target_q - current_q)
        
        return abs(target_q - current_q)  # TD error


class MLPQLearner(nn.Module):
    """MLP-based Q-learner (middle ground between tabular and full system)."""
    
    def __init__(self, state_dim: int = 16, action_dim: int = 4, hidden_dim: int = 64):
        super().__init__()
        self.action_dim = action_dim
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        self.optimizer = torch.optim.Adam(self.parameters(), lr=0.001)
        self.loss_fn = nn.MSELoss()
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Get Q-values for all actions."""
        return self.network(state)
    
    def get_action(self, state: torch.Tensor, epsilon: float = 0.1) -> int:
        """Epsilon-greedy action selection."""
        if np.random.random() < epsilon:
            return np.random.randint(self.action_dim)
        
        with torch.no_grad():
            q_values = self.forward(state)
            return q_values.argmax().item()
    
    def update(self, state: torch.Tensor, action: int, reward: float,
               next_state: torch.Tensor, gamma: float = 0.99) -> float:
        """DQN-style update."""
        # Current Q-value
        q_values = self.forward(state)
        current_q = q_values[action]
        
        # Target Q-value
        with torch.no_grad():
            next_q_values = self.forward(next_state)
            target_q = reward + gamma * next_q_values.max()
        
        # Update
        loss = self.loss_fn(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()


class AblationConfig:
    """Configuration for ablation studies."""
    
    def __init__(self):
        self.noise_enabled = False
        self.plasticity_enabled = True  # True = plastic weights, False = frozen
        self.field_feedback_enabled = True
        self.model_type = "full"  # "full", "mlp", "q_learner", "mlp_q"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "noise_enabled": self.noise_enabled,
            "plasticity_enabled": self.plasticity_enabled,
            "field_feedback_enabled": self.field_feedback_enabled,
            "model_type": self.model_type
        }
    
    def from_dict(self, config: Dict[str, Any]):
        """Load from dictionary."""
        self.noise_enabled = config.get("noise_enabled", False)
        self.plasticity_enabled = config.get("plasticity_enabled", True)
        self.field_feedback_enabled = config.get("field_feedback_enabled", True)
        self.model_type = config.get("model_type", "full")
        return self
    
    def get_description(self) -> str:
        """Get human-readable description."""
        parts = []
        parts.append(f"Model: {self.model_type}")
        parts.append(f"Noise: {'ON' if self.noise_enabled else 'OFF'}")
        parts.append(f"Plasticity: {'ON' if self.plasticity_enabled else 'FROZEN'}")
        parts.append(f"Field Feedback: {'ON' if self.field_feedback_enabled else 'OFF'}")
        return " | ".join(parts)
