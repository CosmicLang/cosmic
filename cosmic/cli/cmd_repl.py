"""Cosmic CLI — repl command."""
from __future__ import annotations
import sys


def run(args) -> int:
    from cosmic.REPL import main
    main()
    return 0
