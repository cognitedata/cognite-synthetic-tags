from __future__ import annotations

import logging
import os
from typing import Any, Optional

from ._operations import INFIX_OPERATORS, REVERSE_OPERATIONS
from .types import OperatorT, TagFormulaT

logger = logging.getLogger(__name__)


class Tag:
    def __init__(self, name: str, store: Optional[str] = None):
        self.name = f"{name}__{store}" if store else name
        self.store = store
        self._value = None
        self.formula: Optional[TagFormulaT] = None

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()

    def calc(self, operator_: OperatorT, *args: Any) -> Tag:
        return Tag.apply(operator_, self, *args)

    @classmethod
    def apply(cls, operator_: OperatorT, *args: Any) -> Tag:
        if callable(operator_):
            oper_str = operator_.__name__
        else:
            assert isinstance(operator_, str), f"Invalid operator: {operator_}"
            if operator_ in REVERSE_OPERATIONS:
                operator_ = operator_[1:]
                args = args[::-1]
            oper_str = operator_
        if oper_str in INFIX_OPERATORS:
            oper_str = INFIX_OPERATORS[oper_str]
            new_tag = Tag(f" {oper_str} ".join(map(str, args)))
        else:
            new_tag = Tag(f"{oper_str}({', '.join(map(str, args))})")
        new_tag.formula = (operator_, args)
        return new_tag

    # forward binary operations, e.g: Tag + 3

    def __add__(self, other: Any) -> Tag:
        return self.calc("+", other)

    def __sub__(self, other: Any) -> Tag:
        return self.calc("-", other)

    def __mul__(self, other: Any) -> Tag:
        return self.calc("*", other)

    def __truediv__(self, other: Any) -> Tag:
        return self.calc("/", other)

    def __floordiv__(self, other: Any) -> Tag:
        return self.calc("//", other)

    def __mod__(self, other: Any) -> Tag:
        return self.calc("%", other)

    def __pow__(self, other: Any) -> Tag:
        return self.calc("**", other)

    def __or__(self, other: Any) -> Tag:
        return self.calc("|", other)

    def __and__(self, other: Any) -> Tag:
        return self.calc("&", other)

    def __xor__(self, other: Any) -> Tag:
        return self.calc("^", other)

    def __invert__(self) -> Tag:
        return self.calc("not")

    def __gt__(self, other: Any) -> Tag:
        return self.calc("gt", other)

    def __ge__(self, other: Any) -> Tag:
        return self.calc("ge", other)

    def __lt__(self, other: Any) -> Tag:
        return self.calc("lt", other)

    def __le__(self, other: Any) -> Tag:
        return self.calc("le", other)

    def __eq__(self, other: Any) -> Tag:  # type: ignore
        return self.calc("eq", other)

    def __ne__(self, other: Any) -> Tag:  # type: ignore
        return self.calc("ne", other)

    # reverse binary operations (e.g: 42 + Tag)

    def __radd__(self, other: Any) -> Tag:
        return self.calc("r+", other)

    def __rsub__(self, other: Any) -> Tag:
        return self.calc("r-", other)

    def __rmul__(self, other: Any) -> Tag:
        return self.calc("r*", other)

    def __rtruediv__(self, other: Any) -> Tag:
        return self.calc("r/", other)

    def __rfloordiv__(self, other: Any) -> Tag:
        return self.calc("r//", other)

    def __rmod__(self, other: Any) -> Tag:
        return self.calc("r%", other)

    def __rpow__(self, other: Any) -> Tag:
        return self.calc("r**", other)

    def __ror__(self, other: Any) -> Tag:
        return self.calc("r|", other)

    def __rand__(self, other: Any) -> Tag:
        return self.calc("r&", other)

    def __rxor__(self, other: Any) -> Tag:
        return self.calc("r^", other)

    def __bool__(self):
        """
        To prevent Python from short-circuiting logic operations, Tag does not
        support casting to boolean.

        For example:
          specs = {"status": Tag("A") or Tag("B")}
        Here the value of specs["status"] will always be Tag("A"). This happens
        be there is a chance to resolve the specs (i.e. the short-circuiting
        happens on the line of code in the example).
        """
        if os.environ.get("COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL", False):
            logger.warning(UnsupportedOperationError.MESSAGE.format(tag=self))
            return True
        else:
            raise UnsupportedOperationError(self)

    def bool(self) -> Tag:
        return self.calc("bool")

    def bool_not(self) -> Tag:
        return self.calc("not")


class UnsupportedOperationError(ValueError):
    MESSAGE = (
        "Tag instances do not support boolean operators (e.g. 'and', 'or')."
        " Instead, use bitwise equivalents ('&', '|')."
        "\nTag: {tag}"
        "\nThere are many ways to get this error, some include:"
        "\n  error: Tag(A) or Tag(B)"
        "\n    fix: Tag(A) | Tag(B)"
        "\n  error: Tag(A) and Tag(B)"
        "\n    fix: Tag(A) & Tag(B)"
        "\n  error: 1 < Tag(A) < 2"
        "\n    fix: (1 < Tag(A)) & (Tag(A) < 2)"
        "\n  error: 1 < Tag(A) | 2 < Tag(B)"
        "\n    fix: (1 < Tag(A)) | (2 < Tag(B))"
        "\n  error: bool(Tag(A))"
        "\n    fix: Tag(A).bool()"
        "\n  error: not Tag(A)"
        "\n    fix: Tag(A).bool_not()"
        "\n    fix: ~Tag(A)  # same as .bool_not()"
    )

    def __init__(self, tag):
        super().__init__(self.MESSAGE.format(tag=tag))
