"""
GameConfig — all tunable game parameters in one place.

Create a GameConfig variant to test different balance scenarios without
touching the environment logic. Pass it to DungeonEnvironment(config=...).
"""

import json
from dataclasses import dataclass, field


@dataclass
class ZoneConfig:
    name: str
    xp: int              # fixed XP awarded per victory
    enemy: dict          # single enemy: {"name": str, "hp": int, "atk": int}


@dataclass
class GameConfig:
    # Boss
    boss_hp: int = 78
    boss_atk: int = 18

    # Player starting stats
    base_hp: int = 20
    base_atk: int = 5

    # Stat gain per level-up
    level_hp_gain: int = 8
    level_atk_gain: int = 2

    # XP required for the first level-up (level 1 → 2)
    xp_base: int = 10

    # Multiplier applied per level: xp_required(n) = xp_base * xp_scale^(n-1)
    # 1.0 = flat (original behavior), 1.3 = mild curve forcing Cave/Tower at high levels
    xp_scale: float = 1.0

    # Maximum turns per episode; 0 = unlimited
    max_turns: int = 50

    # Proficiency: grows with each kill of a given enemy type
    # Applied symmetrically to both offence and defence:
    #   effective_atk        = player_atk * (1 + prof_pct * prof) + prof_flat * prof
    #   effective_enemy_atk  = max(1, enemy_atk * (1 - prof_pct * prof) - prof_flat * prof)
    prof_pct: float = 0.05   # fractional bonus/reduction per proficiency level
    prof_flat: int = 1        # flat bonus/reduction per proficiency level
    prof_max: int = 5         # proficiency cap
    prof_kills_per_level: int = 1  # kills of the same enemy needed per proficiency level

    def xp_required(self, level: int) -> int:
        """XP needed to advance from `level` to `level + 1`."""
        return max(1, int(self.xp_base * (self.xp_scale ** (level - 1))))

    # Farm zones (order defines action indices 0..N-1)
    zones: list[ZoneConfig] = field(default_factory=lambda: [
        ZoneConfig(name="Forest", xp=3,  enemy={"name": "Goblin", "hp": 15, "atk": 4}),
        ZoneConfig(name="Cave",   xp=6,  enemy={"name": "Orc",    "hp": 28, "atk": 7}),
        ZoneConfig(name="Tower",  xp=12, enemy={"name": "Troll",  "hp": 44, "atk": 11}),
    ])


DEFAULT_CONFIG = GameConfig()


def load_config(path: str) -> GameConfig:
    """
    Loads a GameConfig from a JSON file.
    Only the fields present in the file are overridden; everything else
    keeps the default value. zones, if provided, fully replace the defaults.
    """
    with open(path) as f:
        data = json.load(f)

    zones_data = data.pop("zones", None)
    cfg = GameConfig(**{k: v for k, v in data.items()})

    if zones_data:
        cfg.zones = [
            ZoneConfig(name=z["name"], xp=z["xp"], enemy=z["enemy"])
            for z in zones_data
        ]

    return cfg
