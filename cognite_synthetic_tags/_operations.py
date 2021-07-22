from __future__ import annotations

import math
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
    "|": operator.or_,
    "&": operator.and_,
    "^": operator.xor,
    # boolean logic:
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
    "bool": lambda a: bool(a),
    "not": lambda a: not bool(a),
    # math module:
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log10": math.log10,
    "log2": math.log2,
    "log": math.log,
    "ceil": math.ceil,
    "floor": math.floor,
    # misc:
    "r**": lambda a, b: b ** a,
    "r^": lambda a, b: b ^ a,
    "r%": lambda a, b: b % a,
    "r//": lambda a, b: b // a,
    "recip": lambda a: 1.0 / a,
}
