# clawd-dungeon

A classic turn-based dungeon RPG environment for training and balancing an RL agent.

The core idea: train a Q-Learning agent to defeat the Boss as fast as possible, learning the optimal trade-off between farming zones, healing, and challenging the Boss. The same environment doubles as a **balance testing tool** — sweeping configs exposes which features the agent actually uses.

---

## Architecture

```
┌─────────────────────────────────┐
│         DungeonEnvironment      │  ← game core, no I/O
│  reset() / step() / render()    │  ← standard environment interface
└────────────┬────────────────────┘
             │  GameConfig
     ┌───────┴────────┐
     │                │
┌────▼─────┐    ┌─────▼──────┐
│ HumanCLI │    │  RLAgent   │
│  play.py │    │  agent.py  │
└──────────┘    └────────────┘
```

All game parameters live in `GameConfig` (`config.py`). The environment has no hardcoded values — swap a config to test a different balance scenario without touching logic.

---

## Quickstart

```bash
# play as human (default config)
python3 play.py

# play with a custom config
python3 play.py --config configs/balanced.json

# train the RL agent
python3 train.py

# train and watch snapshots during training
python3 train.py --watch

# watch the trained agent play
python3 watch.py

# run the balance sweep
python3 balance.py
```

---

## Actions

| Key | Action | Notes |
|-----|--------|-------|
| `0` | Farm — Forest | Easy enemy, low XP, low risk |
| `1` | Farm — Cave | Medium enemy, moderate XP, medium risk |
| `2` | Farm — Tower | Hard enemy, high XP, high risk |
| `3` | Heal | Restores HP to max, costs 1 turn |
| `4` | Challenge Boss | Final battle |

---

## State

```python
state = {
    "player_hp":          int,  # current HP
    "player_max_hp":      int,  # grows on level-up
    "player_atk":         int,  # grows on level-up
    "player_level":       int,
    "player_xp":          int,  # XP toward next level
    "player_xp_required": int,  # XP needed for next level-up
    "boss_hp":            int,  # fixed
    "boss_atk":           int,  # fixed
}
```

## Rewards

| Event | Reward |
|-------|--------|
| Defeat the Boss | +100 |
| Die (any battle) | -50 |
| Each turn spent | -1 |
| Level up | +5 |

---

## Configuration

All parameters are in `GameConfig` and can be overridden via a JSON file:

```json
{
  "boss_hp": 95,
  "boss_atk": 21,
  "xp_scale": 1.3,
  "max_turns": 0
}
```

Pass only the fields you want to change — everything else uses the default. `max_turns: 0` means unlimited.

**Key parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `boss_hp` | 78 | Boss health points |
| `boss_atk` | 18 | Boss attack damage |
| `xp_base` | 10 | XP required for level 1→2 |
| `xp_scale` | 1.0 | XP multiplier per level (`1.3` = mild curve forcing Cave/Tower at high levels) |
| `max_turns` | 50 | Turn limit per episode; `0` = unlimited |

Preset configs live in `configs/`.

---

## Balance Testing

`balance.py` trains a fresh agent for each config variant and reports win rate + action usage breakdown. An unused zone signals either a redundant feature or a balance problem.

```
Zone usage guide:
  Forest dominates    → leveling too easy, raise xp_scale or boss difficulty
  Cave/Tower at 0%    → not worth the risk at this difficulty
  All zones > 5%      → agent making real trade-off decisions  ← target
```

Key finding: `xp_scale=1.3` with a scaled boss makes all three zones viable — early levels favor Forest, late levels require Cave/Tower to progress within the turn limit.

---

## Files

```
environment.py   game core (no I/O)
config.py        GameConfig dataclass + load_config()
agent.py         Q-Learning agent (act / train / save / load)
cli.py           terminal UI and watch mode
play.py          human play entry point
train.py         agent training entry point
watch.py         watch trained agent entry point
balance.py       balance sweep tool
configs/         JSON config presets
```
