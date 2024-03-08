from datetime import datetime

import pandas as pd
import pytest

from cognite_synthetic_tags.types import TagResolverContextT

__all__ = [
    "value_store",
    "another_value_store",
    "series_value_store",
    "USE_REAL_CLIENT",
    "assert_called_once_with",
]


USE_REAL_CLIENT = False
# USE_REAL_CLIENT = True

now = datetime.now()


def assert_called_once_with(func_mock, *args, **kwargs):
    if USE_REAL_CLIENT:
        return
    func_mock.assert_called_once_with(*args, **kwargs)


class DummyValueStore:
    """
    Value store for tests. Very dumb, returns int value ignoring any letters
    in the tag name, e.g:
    A1 -> Series([1])
    C42 -> Series([42])
    XY543--21ZZZ -> Series([54321])
    """

    def get(self, tag_names):
        result: TagResolverContextT = {}
        for tag_name in tag_names:
            value = int("".join(filter(str.isdigit, tag_name)))
            result[tag_name] = pd.Series(value, index=pd.DatetimeIndex([now]))
        return result

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)


class DummyAnotherValueStore:
    """
    Value store for tests. Very dumb, returns int value multipllied by 1111,
    ignoring the initial digit, e.g:
    A1 -> Series([1111])
    C42 -> Series([46662])
    X80 -> Series([88880])
    """

    def get(self, tag_names):
        result: TagResolverContextT = {}
        for tag_name in tag_names:
            value = (
                int("".join(dig for dig in tag_name if dig.isdigit())) * 1111
            )
            result[tag_name] = pd.Series(value, index=pd.DatetimeIndex([now]))
        return result

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)


class DummySeriesValueStore:
    """
    Value store for tests. Very dumb, returns series of 7 int values,
    ignoring any letters in the tag name is (e.g. from 42 for tag "ABC42")
    and wrapping at 99:
    A1 -> Series([1, 2, 3, 4, 5, 6, 7])
    C42 -> Series([42, 43, 44, 45, 46, 47, 48])
    X96 -> Series([96, 97, 98, 99, 0, 1, 2])
    """

    def get(self, tag_names):
        result: TagResolverContextT = {}
        for tag_name in tag_names:
            start_value = int("".join(dig for dig in tag_name if dig.isdigit()))
            values = [start_value + i for i in range(7)]
            values = [val - 100 if val >= 100 else val for val in values]
            result[tag_name] = pd.Series(values, index=range(7))
        return result

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)


@pytest.fixture
def value_store(mocker):
    store = DummyValueStore()
    spy = mocker.spy(store, "get")
    store.get = spy
    return store


@pytest.fixture
def another_value_store(mocker):
    store = DummyAnotherValueStore()
    spy = mocker.spy(store, "get")
    store.get = spy
    return store


@pytest.fixture
def series_value_store(mocker):
    store = DummySeriesValueStore()
    spy = mocker.spy(store, "get")
    store.get = spy
    return store
