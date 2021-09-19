from __future__ import annotations

import operator
from typing import Callable, Dict

# https://docs.python.org/3/library/operator.html
default_operations: Dict[str, Callable] = {
    # binary:
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
    # boolean logic (using bitwise operators):
    "and": lambda a, b: bool(a) and bool(b),  # &
    "or": lambda a, b: bool(a) or bool(b),  # |
    "xor": lambda a, b: bool(a) != bool(b),  # ^
    "not": lambda a: not bool(a),  # ~
    "bool": lambda a: bool(a),  # no bitwise operator, only Tag.bool()
    # comparisons:
    "gt": lambda a, b: a > b,
    "ge": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "le": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    # misc:
    "r**": lambda a, b: b ** a,
    "r%": lambda a, b: b % a,
    "r//": lambda a, b: b // a,
    "recip": lambda a: 1.0 / a,
}
