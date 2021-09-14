from typing import Iterable

import pandas as pd
import pytest

from cognite_synthetic_tags.types import TagResolverContextT

__all__ = [
    "value_store",
    "series_value_store",
]


def dummy_value_store(tag_names: Iterable[str]) -> TagResolverContextT:
    """
    Value store for tests. Very dumb, returns int value ignoring
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


def dummy_series_value_store(tag_names: Iterable[str]) -> TagResolverContextT:
    """
    Value store for tests. Very dumb, returns series of 7 int values,
    ignoring the first character of the tag name is (e.g. from 42 for tag "A42")
    and wrapping at 99:
    A1 -> Series([1, 2, 3, 4, 5, 6, 7])
    C42 -> Series([42, 43, 44, 45, 46, 47, 48])
    X96 -> Series([96, 97, 98, 99, 0, 1, 2])
    """
    result: TagResolverContextT = {}
    for tag_name in tag_names:
        start_value = int(tag_name[1:])
        values = [start_value + i for i in range(7)]
        values = [val - 100 if val >= 100 else val for val in values]
        result[tag_name] = pd.Series(values)
    return result


@pytest.fixture
def value_store(mocker):
    from . import _utils

    dummy_value_store_spy = mocker.spy(_utils, "dummy_value_store")
    return dummy_value_store_spy


@pytest.fixture
def series_value_store(mocker):
    from . import _utils

    dummy_value_store_spy = mocker.spy(_utils, "dummy_series_value_store")
    return dummy_value_store_spy
