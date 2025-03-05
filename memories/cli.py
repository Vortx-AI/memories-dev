#!/usr/bin/env python3
"""
Command line interface for the memories package.
"""

import argparse
import sys
from memories import __version__
from memories.core import MemoryManager
from memories.config import Config

def cli():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Memories CLI")
    parser.add_argument("--version", action="version", version=f"memories {__version__}")
    
    args = parser.parse_args()
    return 0

if __name__ == "__main__":
    sys.exit(cli()) 