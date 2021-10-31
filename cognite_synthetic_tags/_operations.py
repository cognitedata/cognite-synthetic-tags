from __future__ import annotations

import operator
from typing import Callable, Dict

# https://docs.python.org/3/library/operator.html
DEFAULT_OPERATIONS: Dict[str, Callable] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
    "&": lambda a, b: operator.and_(bool(a), bool(b)),
    "|": lambda a, b: operator.or_(bool(a), bool(b)),
    "^": lambda a, b: operator.xor(bool(a), bool(b)),
    "not": lambda a: operator.not_(bool(a)),  # ~
    "bool": lambda a: bool(a),  # no bitwise operator, only Tag.bool()
    "gt": operator.gt,
    "ge": operator.ge,
    "lt": operator.lt,
    "le": operator.le,
    "eq": operator.eq,
    "ne": operator.ne,
}


REVERSE_OPERATIONS = (
    "r+",
    "r-",
    "r*",
    "r/",
    "r//",
    "r**",
    "r%",
    "r&",
    "r|",
    "r^",
)


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
}
