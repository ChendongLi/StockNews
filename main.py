"""Thin entry point for StockNews."""

from __future__ import annotations

import sys

from src.app import run


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))

