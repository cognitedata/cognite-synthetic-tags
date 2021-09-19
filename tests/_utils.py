import re
from typing import Iterable

import pandas as pd
import pytest

from cognite_synthetic_tags.types import (
    TagResolverContextT,
    TagValueStoreResultT,
)

__all__ = [
    "value_store",
    "another_value_store",
    "series_value_store",
]


def dummy_value_store(tag_names: Iterable[str]) -> TagValueStoreResultT:
    """
    Value store for tests. Very dumb, returns int value ignoring any letters
    in the tag name, e.g:
    A1 -> 1
    C42 -> 42
    XY543--21ZZZ -> 54321
    """
    result: TagResolverContextT = {}
    for tag_name in tag_names:
        value = int(''.join(dig for dig in tag_name if dig.isdigit()))
        result[tag_name] = value
    return result, None


def dummy_another_value_store(tag_names: Iterable[str]) -> TagValueStoreResultT:
    """
    Value store for tests. Very dumb, returns int value multipllied by 1111,
    ignoring the initial digit, e.g:
    A1 -> 1111
    C42 -> 46662
    X80 -> 88880
    """
    result: TagResolverContextT = {}
    for tag_name in tag_names:
        value = int(''.join(dig for dig in tag_name if dig.isdigit()))
        result[tag_name] = value * 1111
    return result, None


def dummy_series_value_store(tag_names: Iterable[str]) -> TagValueStoreResultT:
    """
    Value store for tests. Very dumb, returns series of 7 int values,
    ignoring any letters in the tag name is (e.g. from 42 for tag "ABC42")
    and wrapping at 99:
    A1 -> Series([1, 2, 3, 4, 5, 6, 7])
    C42 -> Series([42, 43, 44, 45, 46, 47, 48])
    X96 -> Series([96, 97, 98, 99, 0, 1, 2])
    """
    result: TagResolverContextT = {}
    for tag_name in tag_names:
        start_value = int(''.join(dig for dig in tag_name if dig.isdigit()))
        values = [start_value + i for i in range(7)]
        values = [val - 100 if val >= 100 else val for val in values]
        result[tag_name] = pd.Series(values)
    return result, pd.Index(range(7))


@pytest.fixture
def value_store(mocker):
    from . import _utils

    dummy_value_store_spy = mocker.spy(_utils, "dummy_value_store")
    return dummy_value_store_spy


@pytest.fixture
def another_value_store(mocker):
    from . import _utils

    dummy_another_value_store_spy = mocker.spy(
        _utils, "dummy_another_value_store")
    return dummy_another_value_store_spy


@pytest.fixture
def series_value_store(mocker):
    from . import _utils

    dummy_value_store_spy = mocker.spy(_utils, "dummy_series_value_store")
    return dummy_value_store_spy
