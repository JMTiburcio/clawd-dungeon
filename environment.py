"""
GymEnvironment — game core, no I/O.
Standard gymnasium interface: reset() / step() / render()
"""

import random
from typing import Any

# Boss stats (fixed — the final objective)
BOSS_HP = 78
BOSS_ATK = 18

# Player stat progression per level
def _stats_for_level(level: int) -> tuple[int, int]:
    """Returns (max_hp, atk) for a given level."""
    max_hp = 20 + (level - 1) * 8
    atk = 5 + (level - 1) * 2
    return max_hp, atk

# Three farm zones with increasing difficulty and XP rewards.
# Each zone has a pool of possible enemies and an XP range per victory.
FARM_ZONES: dict[int, dict] = {
    0: {
        "name": "Forest",
        "xp_range": (2, 4),
        "enemies": [
            {"hp": 10, "atk": 3},
            {"hp": 12, "atk": 3},
            {"hp": 15, "atk": 4},
            {"hp": 18, "atk": 4},
        ],
    },
    1: {
        "name": "Cave",
        "xp_range": (5, 8),
        "enemies": [
            {"hp": 22, "atk": 6},
            {"hp": 28, "atk": 7},
            {"hp": 32, "atk": 8},
            {"hp": 36, "atk": 9},
        ],
    },
    2: {
        "name": "Tower",
        "xp_range": (10, 15),
        "enemies": [
            {"hp": 38, "atk": 10},
            {"hp": 44, "atk": 11},
            {"hp": 48, "atk": 12},
            {"hp": 52, "atk": 13},
        ],
    },
}

XP_TO_LEVEL = 10  # XP required per level-up


class GymEnvironment:
    """
    RL environment inspired by the first Pokémon gym.

    Actions:
        0 — Farm in the Forest  (easy:   low XP, low risk)
        1 — Farm in the Cave    (medium: moderate XP, medium risk)
        2 — Farm in the Tower   (hard:   high XP, high risk)
        3 — Heal (restore HP to max, costs 1 turn)
        4 — Challenge the Boss (final battle)

    Rewards:
        +100  defeat the boss
        -50   die in any battle
        -1    each turn spent
        +5    level up
    """

    REWARD_WIN = 100
    REWARD_DEATH = -50
    REWARD_TURN = -1
    REWARD_LEVEL_UP = 5

    N_ACTIONS = 5

    def __init__(self):
        self._state: dict[str, int] = {}
        self._xp: int = 0
        self.reset()

    # ------------------------------------------------------------------
    # Gymnasium interface
    # ------------------------------------------------------------------

    def reset(self) -> dict[str, int]:
        """Resets the episode. Returns the initial state."""
        max_hp, atk = _stats_for_level(1)
        self._state = {
            "player_hp": max_hp,
            "player_max_hp": max_hp,
            "player_atk": atk,
            "player_level": 1,
            "boss_hp": BOSS_HP,
            "boss_atk": BOSS_ATK,
        }
        self._xp = 0
        return dict(self._state)

    def step(self, action: int) -> tuple[dict[str, int], float, bool, dict[str, Any]]:
        """
        Executes an action and returns (next_state, reward, done, info).
        info holds narrative details used by the CLI layer.
        """
        assert action in range(self.N_ACTIONS), f"Invalid action: {action}"

        reward = self.REWARD_TURN  # base cost per turn
        done = False
        info: dict[str, Any] = {"action": action, "leveled_up": False, "won": False, "died": False}

        if action in FARM_ZONES:
            reward += self._farm(action, info)
        elif action == 3:
            self._heal(info)
        elif action == 4:
            reward += self._challenge_boss(info)
            done = info["won"] or info["died"]

        if info["leveled_up"]:
            reward += self.REWARD_LEVEL_UP

        if info["died"] and not info.get("boss_battle"):
            # Death in a farm zone also ends the episode
            done = True

        return dict(self._state), reward, done, info

    def render(self) -> dict[str, int]:
        """Returns a copy of the current state (no I/O)."""
        return dict(self._state)

    # ------------------------------------------------------------------
    # Internal actions
    # ------------------------------------------------------------------

    def _farm(self, zone_id: int, info: dict) -> float:
        """Battles a random enemy in the given zone. Returns extra reward."""
        zone = FARM_ZONES[zone_id]
        enemy = random.choice(zone["enemies"]).copy()
        player_atk = self._state["player_atk"]
        enemy_hp = enemy["hp"]
        enemy_atk = enemy["atk"]
        player_hp = self._state["player_hp"]

        info["zone"] = zone["name"]
        info["enemy"] = enemy

        # Simulate turn-by-turn battle
        while player_hp > 0 and enemy_hp > 0:
            enemy_hp -= player_atk
            if enemy_hp <= 0:
                break
            player_hp -= enemy_atk

        self._state["player_hp"] = max(0, player_hp)

        if player_hp <= 0:
            info["died"] = True
            info["boss_battle"] = False
            return self.REWARD_DEATH

        xp_gained = random.randint(*zone["xp_range"])
        self._xp += xp_gained
        info["xp_gained"] = xp_gained

        if self._xp >= XP_TO_LEVEL:
            self._xp -= XP_TO_LEVEL
            self._level_up(info)

        return 0.0

    def _heal(self, info: dict):
        """Restores HP to max."""
        self._state["player_hp"] = self._state["player_max_hp"]
        info["healed_to"] = self._state["player_max_hp"]

    def _challenge_boss(self, info: dict) -> float:
        """Battles the boss. Returns extra reward."""
        info["boss_battle"] = True
        player_atk = self._state["player_atk"]
        boss_atk = self._state["boss_atk"]
        boss_hp = self._state["boss_hp"]
        player_hp = self._state["player_hp"]

        while player_hp > 0 and boss_hp > 0:
            boss_hp -= player_atk
            if boss_hp <= 0:
                break
            player_hp -= boss_atk

        self._state["player_hp"] = max(0, player_hp)

        if player_hp <= 0:
            info["died"] = True
            return self.REWARD_DEATH
        else:
            info["won"] = True
            return self.REWARD_WIN

    def _level_up(self, info: dict):
        """Increases player level and updates stats."""
        self._state["player_level"] += 1
        new_max_hp, new_atk = _stats_for_level(self._state["player_level"])
        hp_gained = new_max_hp - self._state["player_max_hp"]
        self._state["player_max_hp"] = new_max_hp
        self._state["player_atk"] = new_atk
        # HP scales up proportionally on level-up
        self._state["player_hp"] = min(
            self._state["player_hp"] + hp_gained,
            new_max_hp
        )
        info["leveled_up"] = True
        info["new_level"] = self._state["player_level"]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def state_as_tuple(self) -> tuple:
        """Converts state to a hashable tuple — useful for the Q-table."""
        s = self._state
        return (
            s["player_hp"],
            s["player_max_hp"],
            s["player_atk"],
            s["player_level"],
        )
