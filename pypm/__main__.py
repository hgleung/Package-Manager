#!/usr/bin/env python3
"""
PyPM - A fast package manager with SAT-based dependency resolution.
"""

import sys

from .cli import cli

if __name__ == "__main__":
    sys.exit(cli())
