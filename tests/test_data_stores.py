from datetime import datetime, timezone
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from cognite.client.exceptions import CogniteAPIError

from cognite_synthetic_tags import data_stores


@pytest.fixture
def mocked_client():
    p_client = MagicMock()
    p_retrieve = p_client.datapoints.retrieve.return_value
    p_retrieve.to_pandas.return_value = pd.DataFrame(
        {"houston.ro.REMOTE_AI[22]": [0.003925000131130218, np.nan, np.nan]},
        index=pd.DatetimeIndex([
            "2020-01-01T00:00:53",
            "2020-01-01T00:00:54",
            "2020-01-01T00:00:55",
        ]),
    )
    return p_client


@pytest.fixture
def patch_retrieve_datapoints_df(mocker):
    p_retrieve_datapoints_df = mocker.patch(
        "cognite_synthetic_tags.data_stores.retrieve_datapoints_df",
    )
    p_retrieve_datapoints_df.return_value = pd.DataFrame(
        {"houston.ro.REMOTE_AI[22]": [0.003925000131130218, np.nan, np.nan]},
        index=pd.DatetimeIndex([
            "2020-01-01T00:00:53",
            "2020-01-01T00:00:54",
            "2020-01-01T00:00:55",
        ]),
    )
    return p_retrieve_datapoints_df


def test_point_at_time_argument_translation(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-03T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"
        ),
        aggregate="average",
        granularity="1d",
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    mocked_client.datapoints.retrieve.assert_called_once_with(
        id=None,
        external_id=["houston.ro.REMOTE_AI[22]"],
        ignore_unknown_ids=True,
        include_outside_points=None,
        limit=None,
        end=datetime.strptime("2020-01-03T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        start=datetime.strptime("2020-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        aggregates=["average"],
        granularity="1d",
    )
    assert index is None


def test_point_at_time_w_lookbehind_limit_argument_translation(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-03T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        aggregate="average",
        granularity="1d",
        lookbehind_limit=1,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    expected_start_epoch_ms = int(
        datetime.strptime(
            "2020-01-02T00:00:00",
            "%Y-%m-%dT%H:%M:%S",
        )
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * 1000
    )
    mocked_client.datapoints.retrieve.assert_called_once_with(
        id=None,
        external_id=["houston.ro.REMOTE_AI[22]"],
        ignore_unknown_ids=True,
        include_outside_points=None,
        limit=None,
        end=datetime.strptime("2020-01-03T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        start=expected_start_epoch_ms,
        aggregates=["average"],
        granularity="1d",
    )
    assert index is None


def test_point_at_time_ffill(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:02:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
        ffill=True,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    expected = 0.003925000131130218
    assert value["houston.ro.REMOTE_AI[22]"] == expected
    assert index is None


def test_point_at_time_no_ffill(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:02:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    assert np.isnan(value["houston.ro.REMOTE_AI[22]"])
    assert index is None


def test_missing_tags_filled(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
    )

    value, index = store({"houston.ro.REMOTE_AI[22]", "FOO.bar"})

    assert np.isnan(value["FOO.bar"])
    assert index is None


def test_missing_tags_fill_with(mocked_client):
    special_value = object()
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
        fillna=special_value,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]", "FOO.bar"})

    assert value["FOO.bar"] is special_value
    assert index is None


def test_no_ffill(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
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
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time="whatever, using patched client",
        lookbehind_start_time="whatever, using patched client",
        ffill=False,
        fillna=special_value,
    )

    value, index = store({"houston.ro.REMOTE_AI[22]"})

    assert value["houston.ro.REMOTE_AI[22]"] is special_value
    assert index is None


def test_unknown_tag_tolerate(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
    )

    value, index = store({"FOO.bar"})

    assert np.isnan(value["FOO.bar"])
    assert index is None


def test_unknown_tag_tolerate_with_fillna_value(mocked_client):
    special_value = object()
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
        fillna=special_value,
    )

    value, index = store({"FOO.bar"})

    assert value["FOO.bar"] is special_value
    assert index is None


def test_unknown_tag_dont_tolerate(mocked_client):
    mocked_client.datapoints.retrieve.side_effect = CogniteAPIError("booo")
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
        ignore_unknown_ids=False,
    )

    with pytest.raises(CogniteAPIError):
        store({"FOO.bar"})


def test_empty(mocked_client):
    store = data_stores.point_at_time(
        mocked_client,
        query_by="external_id",
        at_time=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        lookbehind_start_time=datetime.strptime(
            "2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"
        ),
        ignore_unknown_ids=False,
    )

    values, index = store(set())
    assert isinstance(values, dict), "Value should be a dict"
    assert not values, "Expecting empty values"
    assert index is None, "Expecting None for index"


def test_series(mocked_client):
    store = data_stores.series(
        mocked_client,
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


def test_series_empty(mocked_client):
    store = data_stores.series(
        mocked_client,
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


def test_series_all_unknown_tags(mocked_client):
    mocked_client.datapoints.retrieve.return_value.to_pandas.return_value = (
        pd.DataFrame()
    )
    store = data_stores.series(
        mocked_client,
        query_by="external_id",
        start=datetime.strptime("2020-01-01T00:00:50", "%Y-%m-%dT%H:%M:%S"),
        end=datetime.strptime("2020-01-01T00:01:00", "%Y-%m-%dT%H:%M:%S"),
        ignore_unknown_ids=False,
    )

    values, index = store({"FOO", "BAR"})
    assert isinstance(values, dict), "Value should be a dict"
    assert isinstance(index, pd.Index), "series store must return an index"
    assert len(index) == 0, "Expecting empty index"
