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
from environment import GymEnvironment

TRAIN_EPISODES  = 3000
EVAL_EPISODES   = 300
TARGET_WIN_RATE = 0.50
MAX_TURNS       = 50


def _make_config(forest_xp, cave_xp, tower_xp, boss_hp, boss_atk, xp_scale=1.0) -> GameConfig:
    cfg = GameConfig(
        max_turns=MAX_TURNS,
        boss_hp=boss_hp,
        boss_atk=boss_atk,
        xp_scale=xp_scale,
    )
    cfg.zones = copy.deepcopy(cfg.zones)
    cfg.zones[0].xp_range = forest_xp
    cfg.zones[1].xp_range = cave_xp
    cfg.zones[2].xp_range = tower_xp
    return cfg


def evaluate(agent: QLearningAgent, config: GameConfig, episodes: int) -> tuple[float, dict]:
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


def xp_curve_preview(config: GameConfig, levels: int = 4) -> str:
    """Short XP curve string (4 levels keeps it within column width)."""
    return " ".join(f"{config.xp_required(l):>3}" for l in range(1, levels + 1))


def run_sweep():
    # (label, forest_xp, cave_xp, tower_xp, boss_hp, boss_atk, xp_scale)
    variants = [
        # ── flat XP (baseline) ─────────────────────────────────────────
        ("flat  | easy boss",     (2, 4), (5, 8), (10, 15),  50, 10, 1.0),
        ("flat  | med  boss",     (2, 4), (5, 8), (10, 15),  78, 18, 1.0),
        ("flat  | hard boss",     (2, 4), (5, 8), (10, 15), 110, 24, 1.0),
        # ── 1.3x: fine-grained boss sweep around the sweet spot ────────
        ("1.3x  | boss  78/18",   (2, 4), (5, 8), (10, 15),  78, 18, 1.3),
        ("1.3x  | boss  85/19",   (2, 4), (5, 8), (10, 15),  85, 19, 1.3),
        ("1.3x  | boss  90/20",   (2, 4), (5, 8), (10, 15),  90, 20, 1.3),
        ("1.3x  | boss  95/21",   (2, 4), (5, 8), (10, 15),  95, 21, 1.3),
        ("1.3x  | boss 100/22",   (2, 4), (5, 8), (10, 15), 100, 22, 1.3),
        ("1.3x  | boss 105/23",   (2, 4), (5, 8), (10, 15), 105, 23, 1.3),
        ("1.3x  | boss 110/24",   (2, 4), (5, 8), (10, 15), 110, 24, 1.3),
        # ── 1.3x + fast XP: does Tower help at the hard end? ───────────
        ("1.3x  | 90/20 fast XP", (4, 6), (8,12), (15, 20),  90, 20, 1.3),
        ("1.3x  | 100/22 fast XP",(4, 6), (8,12), (15, 20), 100, 22, 1.3),
        ("1.3x  | 110/24 fast XP",(4, 6), (8,12), (15, 20), 110, 24, 1.3),
        # ── 1.5x ───────────────────────────────────────────────────────
        ("1.5x  | boss  78/18",   (2, 4), (5, 8), (10, 15),  78, 18, 1.5),
        ("1.5x  | boss  78/18 fast",(4,6),(8,12), (15, 20),  78, 18, 1.5),
    ]

    zone_names = ["Forest", "Cave", "Tower"]
    col_w = 24; bs_w = 7; sc_w = 5; cv_w = 16; wr_w = 9; act_w = 8

    header = "  ".join([
        f"{'Scenario':<{col_w}}",
        f"{'BossHP':>{bs_w}}", f"{'ATK':>{bs_w}}", f"{'Scale':>{sc_w}}",
        f"{'XP/lvl 1-4':>{cv_w}}",
        f"{'WinRate':>{wr_w}}", f"{'Gap':>6}",
        *[f"{n:>{act_w}}" for n in zone_names],
        f"{'Heal':>{act_w}}", f"{'Boss%':>{act_w}}",
    ])
    sep = "=" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    results = []
    prev_scale = None

    for label, f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale in variants:
        if prev_scale is not None and xp_scale != prev_scale:
            print("-" * len(header))
        prev_scale = xp_scale

        config = _make_config(f_xp, c_xp, t_xp, boss_hp, boss_atk, xp_scale)
        agent  = QLearningAgent()
        agent.train(episodes=TRAIN_EPISODES, env=GymEnvironment(config))
        win_rate, usage = evaluate(agent, config, EVAL_EPISODES)

        gap     = win_rate - TARGET_WIN_RATE
        gap_str = f"{gap:+.0%}"
        curve   = xp_curve_preview(config)

        row = "  ".join([
            f"{label:<{col_w}}",
            f"{boss_hp:>{bs_w}}", f"{boss_atk:>{bs_w}}", f"{xp_scale:>{sc_w}.1f}",
            f"{curve:>{cv_w}}",
            f"{win_rate:>{wr_w}.0%}", f"{gap_str:>6}",
            *[f"{usage.get(a, 0):>{act_w}.0%}" for a in range(5)],
        ])
        print(row)
        results.append((label, win_rate, boss_hp, boss_atk, xp_scale))

    print(sep)
    best = min(results, key=lambda x: abs(x[1] - TARGET_WIN_RATE))
    print(
        f"\nClosest to {TARGET_WIN_RATE:.0%} target: '{best[0]}' "
        f"— boss HP={best[2]} ATK={best[3]} xp_scale={best[4]} ({best[1]:.0%} win rate)\n"
    )
    print("Zone usage guide:")
    print("  Forest dominates    → leveling too easy, raise scale or boss difficulty")
    print("  Cave/Tower at 0%    → XP reward not worth the risk at this difficulty")
    print("  All zones > 5%      → agent making real trade-off decisions  ← target")


if __name__ == "__main__":
    run_sweep()
