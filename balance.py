"""
python balance.py — sweeps XP configurations and reports win rates + action usage.

For each config variant, trains a fresh agent and evaluates:
  - Win rate (did the agent defeat the boss?)
  - Action usage breakdown (which zones/actions were actually used?)

A balanced config should show all zones being used and a win rate near the target.
An unused zone signals either a redundant feature or a balance problem.
"""

import copy
from collections import defaultdict

from agent import QLearningAgent
from config import GameConfig, ZoneConfig
from environment import GymEnvironment

TRAIN_EPISODES = 3000
EVAL_EPISODES  = 300
TARGET_WIN_RATE = 0.50
MAX_TURNS = 50


def _make_config(forest_xp, cave_xp, tower_xp) -> GameConfig:
    cfg = GameConfig(max_turns=MAX_TURNS)
    cfg.zones = copy.deepcopy(cfg.zones)
    cfg.zones[0].xp_range = forest_xp
    cfg.zones[1].xp_range = cave_xp
    cfg.zones[2].xp_range = tower_xp
    return cfg


def evaluate(agent: QLearningAgent, config: GameConfig, episodes: int) -> tuple[float, dict]:
    """
    Runs the agent greedily for N episodes.
    Returns (win_rate, action_usage_pct) where action_usage_pct maps
    action index → percentage of total actions taken.
    """
    wins = 0
    action_counts: dict[int, int] = defaultdict(int)
    total_actions = 0

    for _ in range(episodes):
        env = GymEnvironment(config)
        state = env.reset()
        done = False
        while not done:
            action = agent.act_greedy(state)
            action_counts[action] += 1
            total_actions += 1
            state, _, done, info = env.step(action)
        if info.get("won"):
            wins += 1

    usage = {a: action_counts[a] / total_actions for a in range(config.max_turns and 5 or 5)}
    return wins / episodes, usage


def run_sweep():
    # (label, forest_xp, cave_xp, tower_xp)
    variants = [
        ("flat (equal XP)",    (4, 6),  (4, 6),   (4, 6)),
        ("slow progression",   (1, 2),  (3, 5),   (6, 10)),
        ("default",            (2, 4),  (5, 8),   (10, 15)),
        ("fast progression",   (4, 6),  (8, 12),  (15, 20)),
        ("forest-heavy",       (6, 10), (4, 6),   (4, 6)),
        ("tower-heavy",        (1, 2),  (2, 4),   (15, 25)),
    ]

    n_zones = 3
    zone_names = ["Forest", "Cave", "Tower"]

    # Build header
    col_w = 22
    xp_w  = 11
    wr_w  = 9
    act_w = 8

    header_parts = [f"{'Config':<{col_w}}"]
    for n in zone_names:
        header_parts.append(f"{n+' XP':<{xp_w}}")
    header_parts.append(f"{'WinRate':>{wr_w}}")
    header_parts.append(f"{'Gap':>6}")
    for n in zone_names:
        header_parts.append(f"{n:>{act_w}}")
    header_parts.append(f"{'Heal':>{act_w}}")
    header_parts.append(f"{'Boss':>{act_w}}")

    header = "  ".join(header_parts)
    sep = "=" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    results = []

    for label, forest_xp, cave_xp, tower_xp in variants:
        config = _make_config(forest_xp, cave_xp, tower_xp)

        agent = QLearningAgent()
        agent.train(episodes=TRAIN_EPISODES, env=GymEnvironment(config))
        win_rate, usage = evaluate(agent, config, EVAL_EPISODES)

        gap = win_rate - TARGET_WIN_RATE
        gap_str = f"{gap:+.0%}"

        row_parts = [f"{label:<{col_w}}"]
        for xp in (forest_xp, cave_xp, tower_xp):
            row_parts.append(f"{xp[0]}-{xp[1]:<{xp_w-3}}")
        row_parts.append(f"{win_rate:>{wr_w}.0%}")
        row_parts.append(f"{gap_str:>6}")
        # action 0=forest, 1=cave, 2=tower, 3=heal, 4=boss
        for a in range(n_zones + 2):
            pct = usage.get(a, 0.0)
            row_parts.append(f"{pct:>{act_w}.0%}")

        print("  ".join(row_parts))
        results.append((label, win_rate))

    print(sep)
    best = min(results, key=lambda x: abs(x[1] - TARGET_WIN_RATE))
    print(f"\nClosest to {TARGET_WIN_RATE:.0%} target: '{best[0]}' ({best[1]:.0%})\n")

    print("Action usage guide:")
    print("  0%  on a zone = the agent never farms there → redundant or too risky/slow")
    print("  High Boss% = agent challenges boss early → may be too easy")
    print("  High Heal% = agent heals a lot → combat too punishing")


if __name__ == "__main__":
    run_sweep()
