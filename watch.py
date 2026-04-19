"""
python watch.py                      -- watch 3 episodes with default delay
python watch.py --episodes 5 --delay 1.2
"""

import argparse
import os
import sys

from agent import QLearningAgent
from cli import watch_agent

MODEL_PATH = "model.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.8, help="Seconds between turns")
    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at '{MODEL_PATH}'. Run 'python train.py' first.")
        sys.exit(1)

    agent = QLearningAgent()
    agent.load(MODEL_PATH)
    agent.epsilon = 0.0  # no exploration when watching

    print(f"Loading model from '{MODEL_PATH}'...")
    watch_agent(agent, delay=args.delay, episodes=args.episodes)


if __name__ == "__main__":
    main()
