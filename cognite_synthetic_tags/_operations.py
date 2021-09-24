from __future__ import annotations

import operator
from typing import Callable, Dict

# https://docs.python.org/3/library/operator.html
DEFAULT_OPERATIONS: Dict[str, Callable] = {
    # binary:
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
    # boolean logic (using bitwise operators):
    "&": lambda a, b: bool(a) and bool(b),
    "|": lambda a, b: bool(a) or bool(b),
    "^": lambda a, b: bool(a) != bool(b),
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
    "r+": lambda a, b: a + b,
    "r-": lambda a, b: a - b,
    "r*": lambda a, b: b * a,
    "r/": lambda a, b: a / b,
    "r//": lambda a, b: a // b,
    "r**": lambda a, b: a ** b,
    "r%": lambda a, b: a % b,
    "r&": lambda a, b: bool(a) and bool(b),
    "r|": lambda a, b: bool(a) or bool(b),
    "r^": lambda a, b: bool(a) != bool(b),
}


# This is for cosmetics only.
# By default, Tag.__str__ uses "prefix" notation (a.k.a. Polish notation):
# oper(val1, val2)
# Any operators in this dict will use "infix" notation:
# val1 oper val2
# Additionally, operators (keys) will be replaced with their values, e.g:
# 2^3 is more commonly understood to be 2 "to the power of" then 2**3 would be.
INFIX_OPERATORS = {
    "+": "+",
    "-": "-",
    "*": "×",
    "/": "∕",
    "//": "∕↓",
    "%": "modulo",
    "**": "^",
    "&": "and",
    "|": "or",
    "^": "xor",
    "gt": ">",
    "ge": "≥",
    "lt": "<",
    "le": "≤",
    "eq": "=",
    "ne": "≠",
    # reverse operations:
    "r*": "×",
    "r/": "∕",
    "r//": "∕↓",
    "r+": "+",
    "r-": "-",
}
