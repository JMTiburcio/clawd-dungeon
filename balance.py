"""
python balance.py — sweeps XP + boss configurations and reports win rates + action usage.

Each scenario varies XP progression across zones AND boss difficulty.
Goal: find configs where win rate ≈ 50% and all zones are actually used.
"""

import copy
from collections import defaultdict

from agent import QLearningAgent
from config import GameConfig
from environment import GymEnvironment

TRAIN_EPISODES  = 3000
EVAL_EPISODES   = 300
TARGET_WIN_RATE = 0.50
MAX_TURNS       = 50


def _make_config(forest_xp, cave_xp, tower_xp, boss_hp, boss_atk) -> GameConfig:
    cfg = GameConfig(max_turns=MAX_TURNS, boss_hp=boss_hp, boss_atk=boss_atk)
    cfg.zones = copy.deepcopy(cfg.zones)
    cfg.zones[0].xp_range = forest_xp
    cfg.zones[1].xp_range = cave_xp
    cfg.zones[2].xp_range = tower_xp
    return cfg


def evaluate(agent: QLearningAgent, config: GameConfig, episodes: int) -> tuple[float, dict]:
    """
    Runs the agent greedily for N episodes.
    Returns (win_rate, action_usage_pct).
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

    usage = {a: action_counts[a] / total_actions for a in range(5)}
    return wins / episodes, usage


def run_sweep():
    # (label, forest_xp, cave_xp, tower_xp, boss_hp, boss_atk)
    variants = [
        # ── easy boss ──────────────────────────────────────────────────
        ("easy  | slow XP",      (1, 2),  (3, 5),  (6, 10),  50, 10),
        ("easy  | default XP",   (2, 4),  (5, 8),  (10, 15), 50, 10),
        ("easy  | fast XP",      (4, 6),  (8, 12), (15, 20), 50, 10),
        # ── medium boss (current) ──────────────────────────────────────
        ("med   | slow XP",      (1, 2),  (3, 5),  (6, 10),  78, 18),
        ("med   | default XP",   (2, 4),  (5, 8),  (10, 15), 78, 18),
        ("med   | fast XP",      (4, 6),  (8, 12), (15, 20), 78, 18),
        # ── hard boss ──────────────────────────────────────────────────
        ("hard  | slow XP",      (1, 2),  (3, 5),  (6, 10),  110, 24),
        ("hard  | default XP",   (2, 4),  (5, 8),  (10, 15), 110, 24),
        ("hard  | fast XP",      (4, 6),  (8, 12), (15, 20), 110, 24),
        ("hard  | tower-heavy",  (1, 2),  (3, 5),  (15, 25), 110, 24),
        # ── brutal boss ────────────────────────────────────────────────
        ("brut  | default XP",   (2, 4),  (5, 8),  (10, 15), 140, 30),
        ("brut  | fast XP",      (4, 6),  (8, 12), (15, 20), 140, 30),
        ("brut  | tower-heavy",  (1, 2),  (3, 5),  (15, 25), 140, 30),
    ]

    zone_names = ["Forest", "Cave", "Tower"]

    col_w  = 22
    xp_w   = 10
    bs_w   = 8
    wr_w   = 9
    act_w  = 8

    header_parts = (
        [f"{'Scenario':<{col_w}}"]
        + [f"{'BossHP':>{bs_w}}", f"{'BossATK':>{bs_w}}"]
        + [f"{n+' XP':<{xp_w}}" for n in zone_names]
        + [f"{'WinRate':>{wr_w}}", f"{'Gap':>6}"]
        + [f"{n:>{act_w}}" for n in zone_names]
        + [f"{'Heal':>{act_w}}", f"{'Boss%':>{act_w}}"]
    )
    header = "  ".join(header_parts)
    sep    = "=" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    results = []
    prev_boss = None

    for label, f_xp, c_xp, t_xp, boss_hp, boss_atk in variants:
        # Visual separator between boss tiers
        if prev_boss is not None and boss_hp != prev_boss:
            print("-" * len(header))
        prev_boss = boss_hp

        config = _make_config(f_xp, c_xp, t_xp, boss_hp, boss_atk)
        agent  = QLearningAgent()
        agent.train(episodes=TRAIN_EPISODES, env=GymEnvironment(config))
        win_rate, usage = evaluate(agent, config, EVAL_EPISODES)

        gap     = win_rate - TARGET_WIN_RATE
        gap_str = f"{gap:+.0%}"

        row = (
            [f"{label:<{col_w}}"]
            + [f"{boss_hp:>{bs_w}}", f"{boss_atk:>{bs_w}}"]
            + [f"{xp[0]}-{xp[1]:<{xp_w-3}}" for xp in (f_xp, c_xp, t_xp)]
            + [f"{win_rate:>{wr_w}.0%}", f"{gap_str:>6}"]
            + [f"{usage.get(a, 0):>{act_w}.0%}" for a in range(5)]
        )
        print("  ".join(row))
        results.append((label, win_rate, boss_hp, boss_atk))

    print(sep)
    best = min(results, key=lambda x: abs(x[1] - TARGET_WIN_RATE))
    print(f"\nClosest to {TARGET_WIN_RATE:.0%} target: '{best[0]}' — boss HP={best[2]} ATK={best[3]} ({best[1]:.0%} win rate)\n")

    print("Action usage guide:")
    print("  0% on a zone   → redundant or too risky/slow for the current boss")
    print("  High Boss%     → agent rushes boss early → may be too easy")
    print("  High Heal%     → combat too punishing")


if __name__ == "__main__":
    run_sweep()
