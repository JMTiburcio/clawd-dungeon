"""
RLAgent — tabular Q-Learning agent.
Clean, swappable interface: act() / train() / save() / load()
"""

import json
import random
from collections import defaultdict
from typing import Any

from environment import GymEnvironment


class QLearningAgent:
    """
    Tabular Q-Learning with epsilon-greedy exploration.

    State key: (hp_bucket, atk, level)
    HP is bucketed into 4 bands (0=critical, 3=full) to keep the state
    space compact while preserving the critical "low HP" signal.
    """

    def __init__(
        self,
        alpha: float = 0.1,          # learning rate
        gamma: float = 0.95,         # discount — values future rewards like a win after many turns
        epsilon: float = 1.0,        # initial exploration rate
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
        n_actions: int = 5,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.n_actions = n_actions

        # Q-table: state → [Q(a0)..Q(a4)] (forest, cave, tower, heal, boss)
        self.q_table: dict[tuple, list[float]] = defaultdict(lambda: [0.0] * n_actions)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def act(self, state: dict[str, Any]) -> int:
        """Chooses an action with epsilon-greedy exploration (used during training)."""
        if random.random() < self.epsilon:
            return random.randrange(self.n_actions)
        key = self._state_key(state)
        return int(max(range(self.n_actions), key=lambda a: self.q_table[key][a]))

    def act_greedy(self, state: dict[str, Any]) -> int:
        """Chooses the best known action without exploration (used for watch/eval)."""
        key = self._state_key(state)
        return int(max(range(self.n_actions), key=lambda a: self.q_table[key][a]))

    def update(
        self,
        state: dict,
        action: int,
        reward: float,
        next_state: dict,
        done: bool,
    ):
        """Q-Learning update: Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',·) − Q(s,a)]"""
        key = self._state_key(state)
        next_key = self._state_key(next_state)

        current_q = self.q_table[key][action]
        target = reward if done else reward + self.gamma * max(self.q_table[next_key])
        self.q_table[key][action] = current_q + self.alpha * (target - current_q)

    def decay_epsilon(self):
        """Reduces exploration rate after each episode."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def train(self, episodes: int = 5000, callback=None, env=None) -> list[float]:
        """
        Trains for N episodes. Returns list of total rewards per episode.
        callback(episode, total_reward, info) — optional, for external logging.
        env — optional GymEnvironment instance; creates a default one if not provided.
        """
        if env is None:
            env = GymEnvironment()
        rewards_history = []

        for ep in range(episodes):
            state = env.reset()
            total_reward = 0.0
            done = False

            while not done:
                action = self.act(state)
                next_state, reward, done, info = env.step(action)
                self.update(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

            self.decay_epsilon()
            rewards_history.append(total_reward)

            if callback:
                callback(ep, total_reward, info)

        return rewards_history

    def save(self, path: str):
        """Serializes Q-table and hyperparameters to JSON."""
        data = {
            "hyperparams": {
                "alpha": self.alpha,
                "gamma": self.gamma,
                "epsilon": self.epsilon,
                "epsilon_min": self.epsilon_min,
                "epsilon_decay": self.epsilon_decay,
                "n_actions": self.n_actions,
            },
            # Tuple keys must be stored as strings in JSON
            "q_table": {str(k): v for k, v in self.q_table.items()},
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        """Loads Q-table and hyperparameters from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        hp = data["hyperparams"]
        self.alpha = hp["alpha"]
        self.gamma = hp["gamma"]
        self.epsilon = hp["epsilon"]
        self.epsilon_min = hp["epsilon_min"]
        self.epsilon_decay = hp["epsilon_decay"]
        self.n_actions = hp["n_actions"]

        self.q_table = defaultdict(lambda: [0.0] * self.n_actions)
        for k_str, v in data["q_table"].items():
            # Rebuild tuple from string "(a, b, c)"
            key = tuple(int(x) for x in k_str.strip("()").split(","))
            self.q_table[key] = v

    # ------------------------------------------------------------------
    # State discretization
    # ------------------------------------------------------------------

    def _state_key(self, state: dict) -> tuple:
        """
        Converts the continuous state dict into a discrete Q-table key.
        HP is bucketed (0–3) to keep the state space manageable.
        """
        hp = state["player_hp"]
        max_hp = state["player_max_hp"]
        hp_bucket = min(3, int(4 * hp / max_hp))  # 0=critical, 3=full
        return (
            hp_bucket,
            state["player_atk"],
            state["player_level"],
        )
