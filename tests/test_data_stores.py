import numpy as np
import pandas as pd
import pytest
from cognite.client import CogniteClient
from cognite.client.testing import monkeypatch_cognite_client
from pandas.testing import assert_frame_equal

from cognite_synthetic_tags import data_stores
from tests.utils import USE_REAL_CLIENT, assert_called_once_with


@pytest.fixture
def get_c_mock():
    def _get_c_mock(option):

        if USE_REAL_CLIENT:
            return CogniteClient()

        options = {
            "single": pd.DataFrame(
                {"houston.ro.REMOTE_AI[22]": [0.003925000131130218]},
                index=pd.DatetimeIndex(["2020-01-01T00:00:53"]),
            ),
            "multi": pd.DataFrame(
                {
                    "houston.ro.REMOTE_AI[22]": [
                        0.003925000131130218,
                        0,
                        0.003925000131130218,
                    ],
                },
                index=pd.DatetimeIndex(
                    [
                        "2020-01-01T00:00:53",
                        "2020-01-01T00:00:54",
                        "2020-01-01T00:00:55",
                    ],
                ),
            ),
            "empty": pd.DataFrame(index=pd.DatetimeIndex([])),
        }

        with monkeypatch_cognite_client() as c_mock:
            data = options[option]
            p_to_pandas = c_mock.datapoints.retrieve.return_value.to_pandas
            p_to_pandas.return_value = data
            p_to_pandas = (
                c_mock.datapoints.retrieve_latest.return_value.to_pandas
            )
            p_to_pandas.return_value = np.split(data, [1])[0]  # one row df
            return c_mock

    yield _get_c_mock


def test_datapoints_retrieve(get_c_mock):
    c_mock = get_c_mock("multi")
    values = data_stores.CDFStore(
        c_mock.datapoints.retrieve,
        start=pd.to_datetime("2020-01-01T00:00:54"),
        end=pd.to_datetime("2020-01-01T00:00:59"),
        limit=3,
        include_outside_points=True,
    )(["houston.ro.REMOTE_AI[22]"])

    expected = {
        "houston.ro.REMOTE_AI[22]": pd.Series(
            [0.003925000131130218, 0, 0.003925000131130218],
            index=pd.DatetimeIndex(
                [
                    "2020-01-01T00:00:53",
                    "2020-01-01T00:00:54",
                    "2020-01-01T00:00:55",
                ],
            ),
        )
    }

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.datapoints.retrieve,
        external_id=["houston.ro.REMOTE_AI[22]"],
        start=pd.to_datetime("2020-01-01T00:00:54"),
        end=pd.to_datetime("2020-01-01T00:00:59"),
        limit=3,
        include_outside_points=True,
    )


def test_datapoints_retrieve_latest(get_c_mock):
    c_mock = get_c_mock("single")
    values = data_stores.CDFStore(
        c_mock.datapoints.retrieve_latest,
        before=pd.to_datetime("2020-01-01T00:00:54"),
    )(["houston.ro.REMOTE_AI[22]"])

    expected = {
        "houston.ro.REMOTE_AI[22]": pd.Series(
            [0.003925000131130218],
            index=pd.DatetimeIndex(["2020-01-01T00:00:53"]),
        )
    }

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.datapoints.retrieve_latest,
        external_id=["houston.ro.REMOTE_AI[22]"],
        before=pd.to_datetime("2020-01-01T00:00:54"),
    )


# def test_datapoints_retrieve_unknown_tag(mocked_client):
def test_datapoints_retrieve_unknown_tag(get_c_mock):
    c_mock = get_c_mock("empty")
    values = data_stores.CDFStore(
        c_mock.datapoints.retrieve,
        start=pd.to_datetime("2020-01-03T00:00:00"),
        end=pd.to_datetime("2020-01-03T01:00:00"),
        ignore_unknown_ids=True,
        limit=3,
    )(["FOOBAR"])

    expected = {"FOOBAR": pd.Series(index=pd.DatetimeIndex([]))}

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.datapoints.retrieve,
        external_id=["FOOBAR"],
        start=pd.to_datetime("2020-01-03T00:00:00"),
        end=pd.to_datetime("2020-01-03T01:00:00"),
        ignore_unknown_ids=True,
        limit=3,
    )
