from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Callable, Dict, List, Set, Tuple, Union

import pandas as pd
from mypy_extensions import VarArg

if TYPE_CHECKING:
    from .tag import Tag  # noqa  # pragma: no cover


TagFormulaT = Tuple["OperatorT", Tuple["Tag", ...]]

# value from CDF
TagValueT = Union[str, float, pd.Series]  # note: np.nan is subtype of float

# internal:
TagSpecsT = Dict[str, "Tag"]  # unresolved specs
TagResolverContextT = Dict[str, TagValueT]  # resolved values
TagValueStoreResultT = TagResolverContextT

OperationT = Callable[[VarArg(TagValueT)], TagValueT]
OperatorT = Union[OperationT, str]

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


RetrievalFuncT = Callable[[Set[str]], TagValueStoreResultT]
