"""
python play.py                        -- play with default config
python play.py --config configs/balanced.json
"""

import argparse

from cli import play_human
from config import load_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default=None, help="Path to a JSON config file")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else None
    play_human(config)
