#!/usr/bin/env python3
"""
Command line interface for the memories package.
"""

import argparse
import sys
from memories import __version__
from memories.core import MemoryStore, Config

def main():
    """Main entry point for the memories CLI."""
    parser = argparse.ArgumentParser(
        description="Memories - A package for daily synthesis of Earth Memories"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"memories-dev {__version__}"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom configuration file"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize a new memory store"
    )

    args = parser.parse_args()

    if args.init:
        config = Config(config_path=args.config) if args.config else Config()
        store = MemoryStore(config=config)
        print(f"Initialized new memory store at {store.config.database.path}")
        return 0

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main()) 