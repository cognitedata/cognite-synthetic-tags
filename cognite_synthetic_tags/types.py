from __future__ import annotations

from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Tuple,
    Union,
)

from mypy_extensions import VarArg

if TYPE_CHECKING:
    from .tag import Tag  # noqa  # pragma: no cover


TagFormulaT = Tuple[str, Tuple["Tag", ...]]

# value from CDF
TagValueT = Any

# internal:
TagSpecsT = Dict[str, "Tag"]  # unresolved specs
TagResolverContextT = Dict[str, TagValueT]  # resolved values
TagValueStoreT = Callable[[Iterable[str]], TagResolverContextT]  # API call

OperationT = Callable[[VarArg(TagValueT)], TagValueT]


#

CogniteTimeT = Union[int, str, datetime]

CogniteIdT = Union[
    int,
    List[int],
    Dict[str, Union[int, List[str]]],
    List[Dict[str, Union[int, List[str]]]],
]
CogniteExternalIdT = Union[
    str,
    List[str],
    Dict[str, Union[int, List[str]]],
    List[Dict[str, Union[int, List[str]]]],
]
