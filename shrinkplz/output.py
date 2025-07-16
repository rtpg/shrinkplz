import sys
from typing import Any


def perr(*args: Any) -> None:
    """
    Print to stderr
    """
    print(*args, file=sys.stderr)
