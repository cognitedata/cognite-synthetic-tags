from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from cognite.client import CogniteClient
from cognite.client.exceptions import CogniteAPIError

from cognite_synthetic_tags import data_stores


@pytest.fixture
def client():
    return CogniteClient()


@pytest.fixture
def mocked_client(mocker):
    p_retrieve_datapoints_df = mocker.patch(
        "cognite_synthetic_tags.data_stores.retrieve_datapoints_df",
    )
    p_retrieve_datapoints_df.return_value = pd.DataFrame(
        columns=["houston.ro.REMOTE_AI[22]"],
        data=[
            [0.003925000131130218],
            [np.nan],
            [np.nan],
        ],
        index=map(
            lambda val: datetime.strptime(val, "%Y-%m-%dT%H:%M:%S"),
            [
                "2020-01-01T00:00:53",
                "2020-01-01T00:00:54",
                "2020-01-01T00:00:55",
            ],
        ),
    )
    return p_retrieve_datapoints_df


def test_latest_aggregate(client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-03T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        aggregate="average",
        granularity="1d",
        fillna=0,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    expected = 5.371694281525284
    assert value["houston.ro.REMOTE_AI[22]"] == expected
    assert index is None


def test_latest_value(client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    expected = 0.003925000131130218
    assert value["houston.ro.REMOTE_AI[22]"] == expected
    assert index is None


def test_missing_tags_filled(client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
    )

    value, index = store({"houston.ro.REMOTE_AI[22]", "FOO.bar"})

    assert np.isnan(value["FOO.bar"])
    assert index is None


def test_missing_tags_fill_with(client):
    special_value = object()
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        fillna=special_value,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]", "FOO.bar"})

    assert value["FOO.bar"] is special_value
    assert index is None


def test_no_ffill(mocked_client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time="whatever, using patched client",
        lookbehind_start_time="whatever, using patched client",
        ffill=False,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    assert np.isnan(value["houston.ro.REMOTE_AI[22]"])
    assert index is None


def test_no_ffill_filna_value(mocked_client):
    special_value = object()
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time="whatever, using patched client",
        lookbehind_start_time="whatever, using patched client",
        ffill=False,
        fillna=special_value,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    assert value["houston.ro.REMOTE_AI[22]"] is special_value
    assert index is None


def test_unknown_tag_tollerate(client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
    )

    value, index = store({"FOO.bar"})

    assert np.isnan(value["FOO.bar"])
    assert index is None


def test_unknown_tag_tollerate_with_fillna_value(client):
    special_value = object()
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        fillna=special_value,
    )

    value, index = store({"FOO.bar"})

    assert value["FOO.bar"] is special_value
    assert index is None


def test_unknown_tag_dont_tollerate(client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        ignore_unknown_ids=False,
    )

    try:
        store({"FOO.bar"})
    except CogniteAPIError:
        pass
    else:
        assert False, "Didn't raise the expected exception."


def test_empty(client):
    store = data_stores.latest_datapoint(
        client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        ignore_unknown_ids=False,
    )

    values, index = store(set())
    assert isinstance(values, dict), "Value should be a dict"
    assert not values, "Expecting empty values"
    assert index is None, "Expecting None for index"


def test_series(client):
    store = data_stores.series(
        client,
        query_by="external_id",
        start=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        end=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        ignore_unknown_ids=False,
    )

    values, index = store({"houston.ro.REMOTE_AI[22]"})
    assert isinstance(values, dict), "Value should be a dict"
    assert "houston.ro.REMOTE_AI[22]" in values, "Tag missing from result"
    assert isinstance(
        values["houston.ro.REMOTE_AI[22]"], pd.Series
    ), "Values should be Series instances."
    assert (
        len(values["houston.ro.REMOTE_AI[22]"]) > 1
    ), "Multiple values expected."
    assert isinstance(index, pd.Index), "series store must return an index"


def test_series_empty(client):
    store = data_stores.series(
        client,
        query_by="external_id",
        start=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        end=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        ignore_unknown_ids=False,
    )

    values, index = store(set())
    assert isinstance(values, dict), "Value should be a dict"
    assert not values, "Expecting empty values"
    assert isinstance(index, pd.Index), "series store must return an index"
    assert len(index) == 0, "Expecting empty index"
