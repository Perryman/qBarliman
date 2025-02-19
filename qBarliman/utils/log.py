import sys

VERBOSE = 2
WARN = "❌‼️‼️"  # 0
GOOD = "✅"  # 1
INFO = "✏️"  # 2
DEBUG = "🐞"  # 3
# Avoid unnecessary coloring when redirecting to file
USE_COLORS = sys.stdout.isatty()


def warn(*args) -> None:
    if VERBOSE >= 0:
        print(f"\033[33m{WARN}\033[0m" if USE_COLORS else WARN, *args)


def good(*args) -> None:
    if VERBOSE >= 1:
        print(f"\033[32m{GOOD}\033[0m" if USE_COLORS else GOOD, *args)


def info(*args) -> None:
    if VERBOSE >= 2:
        print(f"\033[37m{INFO}\033[0m" if USE_COLORS else INFO, *args)


def debug(*args) -> None:
    if VERBOSE >= 3:
        print(f"\033[36m{DEBUG}\033[0m" if USE_COLORS else DEBUG, *args)
