"""
HumanCLI — terminal interface for playing or watching the agent.
All game I/O lives here; GymEnvironment has none.
"""

import time
from typing import Any

from environment import GymEnvironment

ACTION_LABELS = {
    0: "Forest  (easy   | low XP, low risk)",
    1: "Cave    (medium | moderate XP, medium risk)",
    2: "Tower   (hard   | high XP, high risk)",
    3: "Heal (restore HP to max)",
    4: "Challenge the Boss",
}


# ------------------------------------------------------------------
# State rendering
# ------------------------------------------------------------------

def render_state(state: dict[str, int]):
    """Displays the current state in a readable format."""
    level = state["player_level"]
    hp = state["player_hp"]
    max_hp = state["player_max_hp"]
    atk = state["player_atk"]
    boss_hp = state["boss_hp"]
    boss_atk = state["boss_atk"]

    bar_filled = int(20 * hp / max_hp)
    hp_bar = "[" + "#" * bar_filled + "." * (20 - bar_filled) + "]"

    print("\n" + "-" * 50)
    print(f"  Level {level}   HP: {hp_bar} {hp}/{max_hp}   ATK: {atk}")
    print(f"  Boss --- HP: {boss_hp}  ATK: {boss_atk}")
    print("-" * 50)


def render_actions():
    """Displays available actions."""
    print("\nWhat will you do?")
    print("  -- Farm --")
    for key in (0, 1, 2):
        print(f"  [{key}] {ACTION_LABELS[key]}")
    print("  -- Other --")
    for key in (3, 4):
        print(f"  [{key}] {ACTION_LABELS[key]}")


# ------------------------------------------------------------------
# Narration
# ------------------------------------------------------------------

def narrate(info: dict[str, Any], state: dict[str, int]):
    """Translates the step() info dict into narrative terminal output."""
    action = info["action"]

    if action in (0, 1, 2):
        zone = info.get("zone", "")
        if info.get("died"):
            print(f"\n[dead] You were defeated in the {zone}. Game over.")
        else:
            xp = info.get("xp_gained", 0)
            hp = state["player_hp"]
            max_hp = state["player_max_hp"]
            msg = f"\n[win] [{zone}] You won and gained {xp} XP! HP remaining: {hp}/{max_hp}."
            if info.get("leveled_up"):
                msg += f"\n[level up] You reached level {info['new_level']}! Stats increased!"
            print(msg)

    elif action == 3:
        healed = info.get("healed_to", state["player_max_hp"])
        print(f"\n[heal] HP restored to {healed}/{healed}.")

    elif action == 4:
        if info.get("won"):
            print("\n[victory] You defeated the Boss! Congratulations!")
        elif info.get("died"):
            hp = state["player_hp"]
            print(f"\n[dead] The Boss was too strong. You were defeated! Final HP: {hp}.")


# ------------------------------------------------------------------
# Human play loop
# ------------------------------------------------------------------

def play_human():
    """Main loop for a human player."""
    env = GymEnvironment()
    state = env.reset()
    total_reward = 0.0
    turns = 0

    print("\n" + "=" * 50)
    print("       WELCOME TO CLAWD DUNGEON GYM!")
    print("=" * 50)
    print("Defeat the Boss as fast as possible.")
    print("Each turn costs -1. Death = -50. Victory = +100.")

    done = False
    while not done:
        render_state(state)
        render_actions()

        while True:
            raw = input("\n> ").strip()
            if raw in ("0", "1", "2", "3", "4"):
                action = int(raw)
                break
            print("Invalid choice. Enter 0, 1, 2, 3 or 4.")

        next_state, reward, done, info = env.step(action)
        total_reward += reward
        turns += 1

        narrate(info, next_state)
        state = next_state

    print(f"\n{'-' * 50}")
    print(f"  Turns played: {turns}")
    print(f"  Total reward: {total_reward:.0f}")
    print(f"{'-' * 50}\n")


# ------------------------------------------------------------------
# Watch mode (observe the agent play)
# ------------------------------------------------------------------

def watch_agent(agent, delay: float = 0.8, episodes: int = 1):
    """Displays the agent playing in real time with a configurable delay."""
    env = GymEnvironment()

    for ep in range(episodes):
        state = env.reset()
        total_reward = 0.0
        turns = 0
        done = False

        print(f"\n{'=' * 50}")
        print(f"  EPISODE {ep + 1}")
        print(f"{'=' * 50}")

        while not done:
            render_state(state)

            action = agent.act_greedy(state)
            label = ACTION_LABELS[action]
            print(f"\n[agent] [{action}] {label}")
            time.sleep(delay)

            next_state, reward, done, info = env.step(action)
            total_reward += reward
            turns += 1

            narrate(info, next_state)
            state = next_state

            time.sleep(delay)

        print(f"\n  Turns: {turns}  |  Reward: {total_reward:.0f}")
