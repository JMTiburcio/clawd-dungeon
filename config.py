"""
GameConfig — all tunable game parameters in one place.

Create a GameConfig variant to test different balance scenarios without
touching the environment logic. Pass it to GymEnvironment(config=...).
"""

import json
from dataclasses import dataclass, field


@dataclass
class ZoneConfig:
    name: str
    xp_range: tuple[int, int]   # (min, max) XP awarded per victory
    enemies: list[dict]         # each dict: {"hp": int, "atk": int}


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
    # 1.0 = flat (original behavior), 1.5 = steep curve forcing Tower at high levels
    xp_scale: float = 1.0

    # Maximum turns per episode; 0 = unlimited
    max_turns: int = 50

    def xp_required(self, level: int) -> int:
        """XP needed to advance from `level` to `level + 1`."""
        return max(1, int(self.xp_base * (self.xp_scale ** (level - 1))))

    # Farm zones (order defines action indices 0..N-1)
    zones: list[ZoneConfig] = field(default_factory=lambda: [
        ZoneConfig(
            name="Forest",
            xp_range=(2, 4),
            enemies=[
                {"hp": 10, "atk": 3},
                {"hp": 12, "atk": 3},
                {"hp": 15, "atk": 4},
                {"hp": 18, "atk": 4},
            ],
        ),
        ZoneConfig(
            name="Cave",
            xp_range=(5, 8),
            enemies=[
                {"hp": 22, "atk": 6},
                {"hp": 28, "atk": 7},
                {"hp": 32, "atk": 8},
                {"hp": 36, "atk": 9},
            ],
        ),
        ZoneConfig(
            name="Tower",
            xp_range=(10, 15),
            enemies=[
                {"hp": 38, "atk": 10},
                {"hp": 44, "atk": 11},
                {"hp": 48, "atk": 12},
                {"hp": 52, "atk": 13},
            ],
        ),
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
    cfg = GameConfig(**{k: v for k, v in data.items() if k != "zones"})

    if zones_data:
        cfg.zones = [
            ZoneConfig(
                name=z["name"],
                xp_range=tuple(z["xp_range"]),
                enemies=z["enemies"],
            )
            for z in zones_data
        ]

    return cfg
