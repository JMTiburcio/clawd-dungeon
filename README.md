# clawd-dungeon

A classic turn-based dungeon RPG — playable on Android and scriptable for RL training and balance testing.

The core idea: train a Q-Learning agent to build the strongest character possible within a turn limit, learning the optimal trade-off between farming zones, healing, and proficiency. The same environment doubles as a **balance testing tool** — sweeping configs exposes which features the agent actually uses.

---

## Architecture

```
┌─────────────────────────────────┐
│         DungeonEnvironment      │  ← game core, no I/O
│  reset() / step()               │  ← standard environment interface
└──────────────┬──────────────────┘
               │  GameConfig
     ┌─────────┼──────────┐
     │         │          │
┌────▼───┐ ┌───▼────┐ ┌───▼──────┐
│  app/  │ │  cli/  │ │  core/   │
│Android │ │ train  │ │  shared  │
│   UI   │ │ watch  │ │  logic   │
│        │ │balance │ │          │
└────────┘ └────────┘ └──────────┘
```

All game parameters live in `GameConfig` (`core/`). The environment has no hardcoded values — change a config field to test a different balance scenario without touching logic.

---

## Modules

```
core/   game logic — GameConfig, DungeonEnvironment, QLearningAgent
app/    Android UI for human play
cli/    CLI tools: train, watch, balance sweep
```

---

## Quickstart

### Android app
Open the project in Android Studio and run the `app` module on a device or emulator.

### CLI tools
```bash
# train the RL agent (saves model.bin)
./gradlew :cli:run --args="train"

# watch the trained agent play
./gradlew :cli:run --args="watch"

# run the balance sweep
./gradlew :cli:run --args="balance"
```

---

## Actions

| Action | Description | Notes |
|--------|-------------|-------|
| Farm — Forest | Fight a Goblin | Easy, low XP, low risk |
| Farm — Cave | Fight an Orc | Medium XP, medium risk |
| Farm — Tower | Fight a Troll | High XP, high risk |
| Heal | Restore HP to max | Costs 1 turn |
| Challenge Boss | Final battle | |

---

## State

```kotlin
data class GameState(
    val playerHp: Int,          // current HP
    val playerMaxHp: Int,       // grows on level-up
    val playerAtk: Int,         // grows on level-up
    val playerLevel: Int,
    val playerXp: Int,          // XP toward next level
    val playerXpRequired: Int,  // XP needed for next level-up
    val bossHp: Int,
    val bossAtk: Int,
    val proficiency: Map<String, Int>,  // enemyName → proficiency level (0..profMax)
)
```

---

## Rewards

| Event | Reward |
|-------|--------|
| Survive the turn limit | `+playerAtk × 2` |
| Level up | +15 |
| Each turn spent | -1 |
| Die (hardcore — no respawn) | -75 |

---

## Proficiency

Each enemy type (Goblin, Orc, Troll) has an independent proficiency level that grows with kills, capped at `profMax`. Every `profKillsPerLevel` kills advances proficiency by 1.

Combat bonuses per proficiency level:
```
effectiveAtk       = playerAtk × (1 + profPct × prof) + profFlat × prof
effectiveEnemyAtk  = max(1, enemyAtk × (1 − profPct × prof) − profFlat × prof)
```

**Balanced config** (`kpl=3, profPct=0.08, profFlat=1, xp_scale=1.3, boss=85/19, t=75`):
```
Forest 27%  Cave 25%  Tower 25%  Heal 20%  — all zones viable
```

---

## Key Config Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bossHp` | 85 | Boss health points |
| `bossAtk` | 19 | Boss attack damage |
| `xpBase` | 10 | XP required for level 1→2 |
| `xpScale` | 1.3 | XP multiplier per level |
| `maxTurns` | 0 | Turn limit per episode; `0` = unlimited |
| `profPct` | 0.08 | Fractional ATK/DEF bonus per proficiency level |
| `profFlat` | 1 | Flat ATK/DEF bonus per proficiency level |
| `profMax` | 5 | Proficiency cap |
| `profKillsPerLevel` | 3 | Kills needed to advance one proficiency level |

---

## Balance Testing

`./gradlew :cli:run --args="balance"` trains a fresh agent for each config variant and reports win rate + action usage breakdown. An unused zone signals either a redundant feature or a balance problem.

```
Zone usage guide:
  Forest dominates → proficiency too fast or leveling too easy
  Tower only       → Tower XP + proficiency compounds faster than diversifying
  All zones > 5%   → agent diversifying across enemy types  ← target
```
