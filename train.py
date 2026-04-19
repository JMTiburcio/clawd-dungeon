"""
python train.py           -- train and save the agent
python train.py --watch   -- train and show progress snapshots
"""

import argparse

from agent import QLearningAgent
from cli import watch_agent

MODEL_PATH = "model.json"
DEFAULT_EPISODES = 5000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Show agent progress during training")
    parser.add_argument("--episodes", type=int, default=DEFAULT_EPISODES)
    args = parser.parse_args()

    agent = QLearningAgent()

    wins = 0
    deaths = 0
    report_every = 500

    def callback(ep: int, total_reward: float, info: dict):
        nonlocal wins, deaths
        if info.get("won"):
            wins += 1
        if info.get("died"):
            deaths += 1

        if (ep + 1) % report_every == 0:
            win_rate = wins / report_every * 100
            print(
                f"  Ep {ep + 1:>5} | eps={agent.epsilon:.3f} | "
                f"win rate last {report_every}: {win_rate:.0f}%"
            )
            wins = 0
            deaths = 0

            if args.watch:
                print("\n--- Watching agent (greedy) ---")
                watch_agent(agent, delay=0.0, episodes=1)

    print(f"Training for {args.episodes} episodes...")
    agent.train(episodes=args.episodes, callback=callback)

    agent.save(MODEL_PATH)
    print(f"\nModel saved to '{MODEL_PATH}'.")
    print("Run 'python watch.py' to watch the agent play.")


if __name__ == "__main__":
    main()
