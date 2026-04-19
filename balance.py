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


def _make_config(
    forest_xp, cave_xp, tower_xp, boss_hp, boss_atk,
    xp_scale=1.0, max_turns=MAX_TURNS,
    prof_pct=0.0, prof_flat=0, prof_kpl=1,
) -> GameConfig:
    cfg = GameConfig(
        max_turns=max_turns,
        boss_hp=boss_hp,
        boss_atk=boss_atk,
        xp_scale=xp_scale,
        prof_pct=prof_pct,
        prof_flat=prof_flat,
        prof_kills_per_level=prof_kpl,
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
    # (label, f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale, max_turns, prof_pct, prof_flat, prof_kpl)
    variants = [
        # ── kpl=1: instant proficiency (1 kill per level) ───────────────
        ("kpl=1 | 0.08/1 1.3x 85/19 t=75",   3, 6, 12, 85, 19, 1.3,  75, 0.08, 1, 1),
        ("kpl=1 | 0.08/1 1.3x 95/21 t=75",   3, 6, 12, 95, 21, 1.3,  75, 0.08, 1, 1),
        ("kpl=1 | 0.08/1 1.3x 95/21 t=100",  3, 6, 12, 95, 21, 1.3, 100, 0.08, 1, 1),
        # ── kpl=3: 3 kills per proficiency level ────────────────────────
        ("kpl=3 | 0.08/1 1.3x 85/19 t=75",   3, 6, 12, 85, 19, 1.3,  75, 0.08, 1, 3),
        ("kpl=3 | 0.08/1 1.3x 95/21 t=75",   3, 6, 12, 95, 21, 1.3,  75, 0.08, 1, 3),
        ("kpl=3 | 0.08/1 1.3x 95/21 t=100",  3, 6, 12, 95, 21, 1.3, 100, 0.08, 1, 3),
        ("kpl=3 | 0.12/2 1.3x 95/21 t=100",  3, 6, 12, 95, 21, 1.3, 100, 0.12, 2, 3),
        # ── kpl=5: 5 kills per proficiency level ────────────────────────
        ("kpl=5 | 0.08/1 1.3x 85/19 t=75",   3, 6, 12, 85, 19, 1.3,  75, 0.08, 1, 5),
        ("kpl=5 | 0.08/1 1.3x 95/21 t=75",   3, 6, 12, 95, 21, 1.3,  75, 0.08, 1, 5),
        ("kpl=5 | 0.08/1 1.3x 95/21 t=100",  3, 6, 12, 95, 21, 1.3, 100, 0.08, 1, 5),
        ("kpl=5 | 0.12/2 1.3x 95/21 t=100",  3, 6, 12, 95, 21, 1.3, 100, 0.12, 2, 5),
        # ── kpl=10: slow proficiency (10 kills per level) ───────────────
        ("kpl=10 | 0.08/1 1.3x 85/19 t=75",  3, 6, 12, 85, 19, 1.3,  75, 0.08, 1, 10),
        ("kpl=10 | 0.12/2 1.3x 85/19 t=100", 3, 6, 12, 85, 19, 1.3, 100, 0.12, 2, 10),
        ("kpl=10 | 0.12/2 1.3x 95/21 t=100", 3, 6, 12, 95, 21, 1.3, 100, 0.12, 2, 10),
    ]

    zone_names = ["Forest", "Cave", "Tower"]
    col_w = 30; bs_w = 7; sc_w = 5; cv_w = 16; mt_w = 7; kl_w = 5; pf_w = 9; wr_w = 9; act_w = 8

    header = "  ".join([
        f"{'Scenario':<{col_w}}",
        f"{'BossHP':>{bs_w}}", f"{'ATK':>{bs_w}}", f"{'Scale':>{sc_w}}",
        f"{'XP/lvl 1-4':>{cv_w}}", f"{'Turns':>{mt_w}}",
        f"{'kpl':>{kl_w}}", f"{'p%/flat':>{pf_w}}",
        f"{'WinRate':>{wr_w}}",
        *[f"{n:>{act_w}}" for n in zone_names],
        f"{'Heal':>{act_w}}", f"{'Boss%':>{act_w}}",
    ])
    sep = "=" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    results = []
    prev_kpl = None

    for label, f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale, max_turns, p_pct, p_flat, p_kpl in variants:
        if prev_kpl is not None and p_kpl != prev_kpl:
            print("-" * len(header))
        prev_kpl = p_kpl

        config = _make_config(f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale, max_turns, p_pct, p_flat, p_kpl)
        agent  = QLearningAgent()
        agent.train(episodes=TRAIN_EPISODES, env=DungeonEnvironment(config))
        win_rate, usage = evaluate(agent, config, EVAL_EPISODES)

        curve = xp_curve_preview(config)
        prof_col = f"{p_pct:.2f}/{p_flat}"

        row = "  ".join([
            f"{label:<{col_w}}",
            f"{boss_hp:>{bs_w}}", f"{boss_atk:>{bs_w}}", f"{xp_scale:>{sc_w}.1f}",
            f"{curve:>{cv_w}}", f"{max_turns:>{mt_w}}",
            f"{p_kpl:>{kl_w}}", f"{prof_col:>{pf_w}}",
            f"{win_rate:>{wr_w}.0%}",
            *[f"{usage.get(a, 0):>{act_w}.0%}" for a in range(5)],
        ])
        print(row)
        results.append((label, win_rate, boss_hp, boss_atk, xp_scale, p_pct, p_flat, p_kpl))

    print(sep)
    print("\nZone usage guide:")
    print("  Forest dominates    → proficiency too fast or leveling too easy")
    print("  Tower only          → Tower XP + proficiency compounds faster than diversifying")
    print("  All zones > 5%      → agent diversifying across enemy types  ← target")


if __name__ == "__main__":
    run_sweep()
