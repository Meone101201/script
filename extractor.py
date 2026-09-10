#!/usr/bin/env python3
"""
Roblox RBXLX Extractor CLI Entry Point.
Usage:
    python extractor.py save.rbxlx --output output/
"""

import sys
from src.main import main

if __name__ == "__main__":
    sys.exit(main())
