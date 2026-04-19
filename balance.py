"""
python balance.py — sweeps XP configurations and reports win rates.

Trains a fresh agent for each config variant and compares the converged
win rate. Use this to find the most balanced XP distribution across zones.
"""

import copy

from agent import QLearningAgent
from config import GameConfig, ZoneConfig
from environment import GymEnvironment

TRAIN_EPISODES = 3000   # enough to converge without being too slow
EVAL_EPISODES = 500     # episodes used to measure final win rate
TARGET_WIN_RATE = 0.50  # what we consider "balanced"


def _make_config(forest_xp, cave_xp, tower_xp) -> GameConfig:
    """Builds a GameConfig with custom XP ranges, keeping all other params default."""
    cfg = GameConfig()
    cfg.zones = copy.deepcopy(cfg.zones)
    cfg.zones[0].xp_range = forest_xp
    cfg.zones[1].xp_range = cave_xp
    cfg.zones[2].xp_range = tower_xp
    return cfg


def evaluate(agent: QLearningAgent, config: GameConfig, episodes: int) -> float:
    """Runs the agent greedily for N episodes and returns the win rate."""
    wins = 0
    for _ in range(episodes):
        env = GymEnvironment(config)
        state = env.reset()
        done = False
        while not done:
            action = agent.act_greedy(state)
            state, _, done, info = env.step(action)
        if info.get("won"):
            wins += 1
    return wins / episodes


def run_sweep():
    # Each entry: (label, forest_xp, cave_xp, tower_xp)
    variants = [
        ("flat (equal XP)",        (4, 6),  (4, 6),  (4, 6)),
        ("slow progression",       (1, 2),  (3, 5),  (6, 10)),
        ("default",                (2, 4),  (5, 8),  (10, 15)),
        ("fast progression",       (4, 6),  (8, 12), (15, 20)),
        ("forest-heavy",           (6, 10), (4, 6),  (4, 6)),
        ("tower-heavy",            (1, 2),  (2, 4),  (15, 25)),
    ]

    col_label = 22
    col_xp = 12
    col_rate = 10
    col_gap = 8

    header = (
        f"{'Config':<{col_label}} "
        f"{'Forest XP':<{col_xp}} "
        f"{'Cave XP':<{col_xp}} "
        f"{'Tower XP':<{col_xp}} "
        f"{'Win Rate':>{col_rate}} "
        f"{'vs target':>{col_gap}}"
    )
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    results = []

    for label, forest_xp, cave_xp, tower_xp in variants:
        config = _make_config(forest_xp, cave_xp, tower_xp)

        agent = QLearningAgent()
        env = GymEnvironment(config)
        agent.train(episodes=TRAIN_EPISODES, env=env)

        win_rate = evaluate(agent, config, EVAL_EPISODES)
        gap = win_rate - TARGET_WIN_RATE
        gap_str = f"{gap:+.0%}"

        f_xp = f"{forest_xp[0]}-{forest_xp[1]}"
        c_xp = f"{cave_xp[0]}-{cave_xp[1]}"
        t_xp = f"{tower_xp[0]}-{tower_xp[1]}"

        print(
            f"{label:<{col_label}} "
            f"{f_xp:<{col_xp}} "
            f"{c_xp:<{col_xp}} "
            f"{t_xp:<{col_xp}} "
            f"{win_rate:>{col_rate}.0%} "
            f"{gap_str:>{col_gap}}"
        )
        results.append((label, win_rate))

    print("=" * len(header))
    best = min(results, key=lambda x: abs(x[1] - TARGET_WIN_RATE))
    print(f"\nClosest to {TARGET_WIN_RATE:.0%} target: '{best[0]}' ({best[1]:.0%})")


if __name__ == "__main__":
    run_sweep()
