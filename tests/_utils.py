from typing import Iterable

import pytest

from cognite_synthetic_tags.types import TagResolverContextT

__all__ = [
    "value_store",
]


def dummy_value_store(tag_names: Iterable[str]) -> TagResolverContextT:
    """
    Value store for tests. Very dump, returns int value ignoring
    the initial digit, e.g:
    A1 -> 1
    C42 -> 42
    X54321 -> 54321
    """
    result: TagResolverContextT = {}
    for tag_name in tag_names:
        value = int(tag_name[1:])
        result[tag_name] = value
    return result


@pytest.fixture
def value_store(mocker):
    from . import _utils

    dummy_value_store_spy = mocker.spy(_utils, "dummy_value_store")
    return dummy_value_store_spy
