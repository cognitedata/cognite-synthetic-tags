from __future__ import annotations

from typing import Any, Optional

from .types import OperatorT, TagFormulaT


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
        return Tag.call(operator_, self, *args)

    @classmethod
    def call(cls, operator_: OperatorT, *args: Any) -> Tag:
        if callable(operator_):
            oper_str = operator_.__name__
        else:
            oper_str = str(operator_)
        new_tag = Tag(f"{oper_str}([{'], ['.join(map(str, args))}])")
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
        return self.calc("or", other)  # bitwise |

    def __and__(self, other: Any) -> Tag:
        return self.calc("and", other)  # bitwise &

    def __xor__(self, other: Any) -> Tag:
        return self.calc("xor", other)  # bitwise ^

    def __invert__(self) -> Tag:
        return self.calc("not")  # bitwise ~

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
        return self.__add__(other)

    def __rsub__(self, other: Any) -> Tag:
        return (self * -1) + other

    def __rmul__(self, other: Any) -> Tag:
        return self.__mul__(other)

    def __rtruediv__(self, other: Any) -> Tag:
        return self.reciprocal().calc("*", other)

    def __rfloordiv__(self, other: Any) -> Tag:
        return self.calc("r//", other)

    def __rmod__(self, other):
        return self.calc("r%", other)

    def __rpow__(self, other):
        return self.calc("r**", other)

    def __ror__(self, other: Any) -> Tag:
        return self.__or__(other)  # bitwise

    def __rand__(self, other: Any) -> Tag:
        return self.__and__(other)  # bitwise

    def __rxor__(self, other: Any) -> Tag:
        return self.calc("r^", other)  # bitwise

    def __bool__(self):
        """
        To prevent Python fro short-circuiting logic operations, Tag does not
        support casting to boolean.

        For example:
          specs = {"status": Tag("A") or Tag("B")}
        Here the value of specs["status"] will always be Tag("A"). This happens
        be there is a chance to resolve the specs (i.e. the short-circuiting
        happens on the line of code in the example).
        """
        raise ValueError(
            "Tag instances do not support boolean operators ('and', 'or')."
            " Instead, use '&' and '|'."
            "\nThere are many ways to get this error, some include:"
            "\n  wrong: Tag(A) or Tag(B)"
            "\n    fix: Tag(A) | Tag(B)"
            "\n  wrong: Tag(A) and Tag(B)"
            "\n    fix: Tag(A) & Tag(B)"
            "\n  wrong: 1 < Tag(A) < 2"
            "\n    fix: (1 <Tag(A)) & (Tag(A) < 2)"
            "\n  wrong: 1 < Tag(A) | 2 < Tag(B)"
            "\n    fix: (1 <Tag(A)) | (2 < Tag(B))"
            "\n  wrong: bool(Tag(A))"
            "\n    fix: Tag(A).bool()"
        )

    # misc

    def reciprocal(self) -> Tag:
        return self.calc("recip")

    @classmethod
    def and_(cls, tag: Tag, other: Tag) -> Tag:
        return tag.calc("and", other)

    @classmethod
    def or_(cls, tag: Tag, other: Tag) -> Tag:
        return tag.calc("or", other)

    @classmethod
    def xor_(cls, tag: Tag, other: Tag) -> Tag:
        return tag.calc("xor", other)

    @classmethod
    def not_(cls, tag: Tag) -> Tag:
        return tag.calc("not")

    @classmethod
    def bool(cls, tag: Tag) -> Tag:
        return tag.calc("bool")

