from __future__ import annotations

from typing import Any, Optional

from .types import OperatorT, TagFormulaT


class Tag:
    def __init__(self, name: str):
        self.name = name
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
        return self.calc("|", other)  # bitwise

    def __and__(self, other: Any) -> Tag:
        return self.calc("&", other)  # bitwise

    def __xor__(self, other: Any) -> Tag:
        return self.calc("^", other)  # bitwise

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
    def not_(cls, tag: Tag) -> Tag:
        return tag.calc("not")

    @classmethod
    def bool(cls, tag: Tag) -> Tag:
        return tag.calc("bool")

    @classmethod
    def sin(cls, tag: Tag) -> Tag:
        return tag.calc("sin")

    @classmethod
    def cos(cls, tag: Tag) -> Tag:
        return tag.calc("cos")

    @classmethod
    def tan(cls, tag: Tag) -> Tag:
        return tag.calc("tan")

    @classmethod
    def log2(cls, tag: Tag) -> Tag:
        return tag.calc("log2")

    @classmethod
    def sqrt(cls, tag: Tag) -> Tag:
        return tag.calc("sqrt")

    @classmethod
    def log10(cls, tag: Tag) -> Tag:
        return tag.calc("log10")

    @classmethod
    def log(cls, tag: Tag, *args) -> Tag:
        return tag.calc("log", *args)

    @classmethod
    def ceil(cls, tag: Tag) -> Tag:
        return tag.calc("ceil")

    @classmethod
    def floor(cls, tag: Tag) -> Tag:
        return tag.calc("floor")
