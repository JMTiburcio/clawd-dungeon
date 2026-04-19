"""
GymEnvironment — game core, no I/O.
Standard gymnasium interface: reset() / step() / render()
"""

import random
from typing import Any

from config import GameConfig, DEFAULT_CONFIG


class GymEnvironment:
    """
    RL environment inspired by the first Pokémon gym.

    Actions are derived from the config:
        0..N-1  — farm in each zone (defined by config.zones)
        N       — heal (restore HP to max, costs 1 turn)
        N+1     — challenge the boss (final battle)

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

    def __init__(self, config: GameConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.N_ACTIONS = len(self.config.zones) + 2  # zones + heal + boss
        self._heal_action = len(self.config.zones)
        self._boss_action = len(self.config.zones) + 1
        self._state: dict[str, int] = {}
        self._xp: int = 0
        self._turn: int = 0
        self.reset()

    # ------------------------------------------------------------------
    # Gymnasium interface
    # ------------------------------------------------------------------

    def reset(self) -> dict[str, int]:
        """Resets the episode. Returns the initial state."""
        cfg = self.config
        self._state = {
            "player_hp": cfg.base_hp,
            "player_max_hp": cfg.base_hp,
            "player_atk": cfg.base_atk,
            "player_level": 1,
            "boss_hp": cfg.boss_hp,
            "boss_atk": cfg.boss_atk,
        }
        self._xp = 0
        self._turn = 0
        return dict(self._state)

    def step(self, action: int) -> tuple[dict[str, int], float, bool, dict[str, Any]]:
        """
        Executes an action and returns (next_state, reward, done, info).
        info holds narrative details used by the CLI layer.
        """
        assert 0 <= action < self.N_ACTIONS, f"Invalid action: {action}"

        self._turn += 1
        reward = self.REWARD_TURN
        done = False
        info: dict[str, Any] = {"action": action, "leveled_up": False, "won": False, "died": False, "timeout": False}

        if action < self._heal_action:
            reward += self._farm(action, info)
        elif action == self._heal_action:
            self._heal(info)
        elif action == self._boss_action:
            reward += self._challenge_boss(info)
            done = info["won"] or info["died"]

        if info["leveled_up"]:
            reward += self.REWARD_LEVEL_UP

        if info["died"] and not info.get("boss_battle"):
            done = True

        max_turns = self.config.max_turns
        if max_turns > 0 and self._turn >= max_turns and not done:
            done = True
            info["timeout"] = True

        return dict(self._state), reward, done, info

    def render(self) -> dict[str, int]:
        """Returns a copy of the current state (no I/O)."""
        return dict(self._state)

    # ------------------------------------------------------------------
    # Internal actions
    # ------------------------------------------------------------------

    def _farm(self, zone_idx: int, info: dict) -> float:
        """Battles a random enemy in the given zone. Returns extra reward."""
        zone = self.config.zones[zone_idx]
        enemy = random.choice(zone.enemies).copy()
        player_atk = self._state["player_atk"]
        enemy_hp = enemy["hp"]
        enemy_atk = enemy["atk"]
        player_hp = self._state["player_hp"]

        info["zone"] = zone.name
        info["enemy"] = enemy

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

        xp_gained = random.randint(*zone.xp_range)
        self._xp += xp_gained
        info["xp_gained"] = xp_gained

        if self._xp >= self.config.xp_to_level:
            self._xp -= self.config.xp_to_level
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
        cfg = self.config
        self._state["player_level"] += 1
        level = self._state["player_level"]
        new_max_hp = cfg.base_hp + (level - 1) * cfg.level_hp_gain
        new_atk = cfg.base_atk + (level - 1) * cfg.level_atk_gain
        hp_gained = new_max_hp - self._state["player_max_hp"]
        self._state["player_max_hp"] = new_max_hp
        self._state["player_atk"] = new_atk
        self._state["player_hp"] = min(self._state["player_hp"] + hp_gained, new_max_hp)
        info["leveled_up"] = True
        info["new_level"] = level

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def state_as_tuple(self) -> tuple:
        """Converts state to a hashable tuple — useful for the Q-table."""
        s = self._state
        return (s["player_hp"], s["player_max_hp"], s["player_atk"], s["player_level"])
