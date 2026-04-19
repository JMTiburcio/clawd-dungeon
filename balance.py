"""
python balance.py — sweeps XP config + XP scaling + boss difficulty.

xp_scale controls how much harder each level-up becomes:
  1.0 = flat (original)        level 4→5 costs same as 1→2
  1.3 = mild curve             level 4→5 costs ~2x level 1→2
  1.5 = steep curve            level 4→5 costs ~3x level 1→2

Goal: find configs where win rate ≈ 50% AND all zones are used.
"""

import copy
from collections import defaultdict

from agent import QLearningAgent
from config import GameConfig
from environment import DungeonEnvironment

TRAIN_EPISODES  = 3000
EVAL_EPISODES   = 300
TARGET_WIN_RATE = 0.50
MAX_TURNS       = 50


def _make_config(forest_xp, cave_xp, tower_xp, boss_hp, boss_atk, xp_scale=1.0, max_turns=MAX_TURNS) -> GameConfig:
    cfg = GameConfig(
        max_turns=max_turns,
        boss_hp=boss_hp,
        boss_atk=boss_atk,
        xp_scale=xp_scale,
    )
    cfg.zones = copy.deepcopy(cfg.zones)
    cfg.zones[0].xp = forest_xp
    cfg.zones[1].xp = cave_xp
    cfg.zones[2].xp = tower_xp
    return cfg


def evaluate(agent: QLearningAgent, config: GameConfig, episodes: int) -> tuple[float, dict]:
    wins = 0
    action_counts: dict[int, int] = defaultdict(int)
    total_actions = 0

    for _ in range(episodes):
        env = DungeonEnvironment(config)
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


def xp_curve_preview(config: GameConfig, levels: int = 4) -> str:
    """Short XP curve string (4 levels keeps it within column width)."""
    return " ".join(f"{config.xp_required(l):>3}" for l in range(1, levels + 1))


def run_sweep():
    # (label, forest_xp, cave_xp, tower_xp, boss_hp, boss_atk, xp_scale)
    # (label, forest_xp, cave_xp, tower_xp, boss_hp, boss_atk, xp_scale, max_turns)
    variants = [
        # ── 1.3x cliff: does more turns smooth it out? ─────────────────
        ("1.3x  | 78/18  t=50",   3, 6, 12,  78, 18, 1.3,  50),
        ("1.3x  | 85/19  t=50",   3, 6, 12,  85, 19, 1.3,  50),
        ("1.3x  | 78/18  t=75",   3, 6, 12,  78, 18, 1.3,  75),
        ("1.3x  | 85/19  t=75",   3, 6, 12,  85, 19, 1.3,  75),
        ("1.3x  | 95/21  t=75",   3, 6, 12,  95, 21, 1.3,  75),
        ("1.3x  | 78/18  t=100",  3, 6, 12,  78, 18, 1.3, 100),
        ("1.3x  | 85/19  t=100",  3, 6, 12,  85, 19, 1.3, 100),
        ("1.3x  | 95/21  t=100",  3, 6, 12,  95, 21, 1.3, 100),
        ("1.3x  | 110/24 t=100",  3, 6, 12, 110, 24, 1.3, 100),
        # ── 1.5x + fast XP: more turns to reach target ─────────────────
        ("1.5x  | 78/18  t=50  fast",  5, 10, 18,  78, 18, 1.5,  50),
        ("1.5x  | 85/19  t=50  fast",  5, 10, 18,  85, 19, 1.5,  50),
        ("1.5x  | 78/18  t=75  fast",  5, 10, 18,  78, 18, 1.5,  75),
        ("1.5x  | 85/19  t=75  fast",  5, 10, 18,  85, 19, 1.5,  75),
        ("1.5x  | 95/21  t=75  fast",  5, 10, 18,  95, 21, 1.5,  75),
        ("1.5x  | 110/24 t=75  fast",  5, 10, 18, 110, 24, 1.5,  75),
        ("1.5x  | 110/24 t=100 fast",  5, 10, 18, 110, 24, 1.5, 100),
    ]

    zone_names = ["Forest", "Cave", "Tower"]
    col_w = 24; bs_w = 7; sc_w = 5; cv_w = 16; mt_w = 7; wr_w = 9; act_w = 8

    header = "  ".join([
        f"{'Scenario':<{col_w}}",
        f"{'BossHP':>{bs_w}}", f"{'ATK':>{bs_w}}", f"{'Scale':>{sc_w}}",
        f"{'XP/lvl 1-4':>{cv_w}}", f"{'Turns':>{mt_w}}",
        f"{'WinRate':>{wr_w}}",
        *[f"{n:>{act_w}}" for n in zone_names],
        f"{'Heal':>{act_w}}", f"{'Boss%':>{act_w}}",
    ])
    sep = "=" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    results = []
    prev_scale = None

    for label, f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale, max_turns in variants:
        if prev_scale is not None and xp_scale != prev_scale:
            print("-" * len(header))
        prev_scale = xp_scale

        config = _make_config(f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale, max_turns)
        agent  = QLearningAgent()
        agent.train(episodes=TRAIN_EPISODES, env=DungeonEnvironment(config))
        win_rate, usage = evaluate(agent, config, EVAL_EPISODES)

        curve = xp_curve_preview(config)

        row = "  ".join([
            f"{label:<{col_w}}",
            f"{boss_hp:>{bs_w}}", f"{boss_atk:>{bs_w}}", f"{xp_scale:>{sc_w}.1f}",
            f"{curve:>{cv_w}}", f"{max_turns:>{mt_w}}",
            f"{win_rate:>{wr_w}.0%}",
            *[f"{usage.get(a, 0):>{act_w}.0%}" for a in range(5)],
        ])
        print(row)
        results.append((label, win_rate, boss_hp, boss_atk, xp_scale))

    print(sep)
    best = min(results, key=lambda x: abs(x[1] - TARGET_WIN_RATE))
    print(
        f"\nClosest to {TARGET_WIN_RATE:.0%} target: '{best[0]}' "
        f"— boss HP={best[2]} ATK={best[3]} xp_scale={best[4]} ({best[1]:.0%})\n"
    )
    print("Zone usage guide:")
    print("  Forest dominates    → leveling too easy, raise scale or boss difficulty")
    print("  Cave/Tower at 0%    → XP reward not worth the risk at this difficulty")
    print("  All zones > 5%      → agent making real trade-off decisions  ← target")


if __name__ == "__main__":
    run_sweep()
