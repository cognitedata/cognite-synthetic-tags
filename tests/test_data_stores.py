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
                        0,
                        0,
                        0.003925000131130218,
                    ],
                },
                index=pd.DatetimeIndex(
                    [
                        "2020-01-01T00:00:55",
                        "2020-01-01T00:00:56",
                        "2020-01-01T00:00:57",
                        "2020-01-01T00:00:58",
                        "2020-01-01T00:00:59",
                    ],
                ),
            ),
            "empty": pd.DataFrame(index=pd.DatetimeIndex([])),
        }

        with monkeypatch_cognite_client() as c_mock:
            data = options[option]
            p_to_pandas = (
                c_mock.time_series.data.retrieve.return_value.to_pandas
            )
            p_to_pandas.return_value = data
            p_to_pandas = (
                c_mock.time_series.data.retrieve_latest.return_value.to_pandas
            )
            p_to_pandas.return_value = np.split(data, [1])[0]  # one row df
            return c_mock

    yield _get_c_mock


def test_datapoints_retrieve(get_c_mock):
    c_mock = get_c_mock("multi")
    values = data_stores.CDFStore(
        c_mock.time_series.data.retrieve,
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
    )(["houston.ro.REMOTE_AI[22]"])

    # Data changed slightly (leap second?),
    # may need to update expected data again, see get_c_mock.
    # equivalent_call = c_mock.time_series.data.retrieve(
    #     external_id="houston.ro.REMOTE_AI[22]",
    #     start=pd.to_datetime("2020-01-01T00:00:55"),
    #     end=pd.to_datetime("2020-01-01T00:01:00"),
    #     limit=5,
    # ).to_pandas()

    expected = {
        "houston.ro.REMOTE_AI[22]": pd.Series(
            [0.003925000131130218, 0, 0, 0, 0.003925000131130218],
            index=pd.DatetimeIndex(
                [
                    "2020-01-01T00:00:55",
                    "2020-01-01T00:00:56",
                    "2020-01-01T00:00:57",
                    "2020-01-01T00:00:58",
                    "2020-01-01T00:00:59",
                ],
            ),
        )
    }

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.time_series.data.retrieve,
        external_id=["houston.ro.REMOTE_AI[22]"],
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
    )


def test_datapoints_retrieve_latest(get_c_mock):
    c_mock = get_c_mock("single")
    values = data_stores.CDFStore(
        c_mock.time_series.data.retrieve_latest,
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
        c_mock.time_series.data.retrieve_latest,
        external_id=["houston.ro.REMOTE_AI[22]"],
        before=pd.to_datetime("2020-01-01T00:00:54"),
    )


def test_process(get_c_mock):
    c_mock = get_c_mock("multi")
    store = data_stores.CDFStore(
        c_mock.time_series.data.retrieve,
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
    ).process(lambda df: df + 42)

    values = store(["houston.ro.REMOTE_AI[22]"])

    expected = {
        "houston.ro.REMOTE_AI[22]": pd.Series(
            [42.003925000131130218, 42, 42, 42, 42.003925000131130218],
            index=pd.DatetimeIndex(
                [
                    "2020-01-01T00:00:55",
                    "2020-01-01T00:00:56",
                    "2020-01-01T00:00:57",
                    "2020-01-01T00:00:58",
                    "2020-01-01T00:00:59",
                ],
            ),
        )
    }

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.time_series.data.retrieve,
        external_id=["houston.ro.REMOTE_AI[22]"],
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
    )


def test_process_closure(get_c_mock):
    c_mock = get_c_mock("multi")
    stores = []
    for i in range(2):
        stores.append(
            data_stores.CDFStore(
                c_mock.time_series.data.retrieve,
                start=pd.to_datetime("2020-01-01T00:00:55"),
                end=pd.to_datetime("2020-01-01T00:01:00"),
                limit=5,
            ).process((lambda df, i_: df + 1000 * (i_ + 1)), i)
        )

    values = [
        stores[0](["houston.ro.REMOTE_AI[22]"]),
        stores[1](["houston.ro.REMOTE_AI[22]"]),
    ]

    expected = [
        {
            "houston.ro.REMOTE_AI[22]": pd.Series(
                [
                    1000.003925000131130218,
                    1000,
                    1000,
                    1000,
                    1000.003925000131130218,
                ],
                index=pd.DatetimeIndex(
                    [
                        "2020-01-01T00:00:55",
                        "2020-01-01T00:00:56",
                        "2020-01-01T00:00:57",
                        "2020-01-01T00:00:58",
                        "2020-01-01T00:00:59",
                    ],
                ),
            )
        },
        {
            "houston.ro.REMOTE_AI[22]": pd.Series(
                [
                    2000.003925000131130218,
                    2000,
                    2000,
                    2000,
                    2000.003925000131130218,
                ],
                index=pd.DatetimeIndex(
                    [
                        "2020-01-01T00:00:55",
                        "2020-01-01T00:00:56",
                        "2020-01-01T00:00:57",
                        "2020-01-01T00:00:58",
                        "2020-01-01T00:00:59",
                    ],
                ),
            )
        },
    ]
    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))


def test_preprocess(get_c_mock):
    c_mock = get_c_mock("multi")

    def fake_news(resource):
        resource.to_pandas.return_value = pd.DataFrame(
            {"houston.ro.REMOTE_AI[22]": [11, 22, 33, 44, 55]},
        )
        return resource

    store = data_stores.CDFStore(
        c_mock.time_series.data.retrieve,
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
    ).preprocess(fake_news)

    values = store(["houston.ro.REMOTE_AI[22]"])

    expected = {
        "houston.ro.REMOTE_AI[22]": pd.Series(
            [11, 22, 33, 44, 55],
        )
    }

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.time_series.data.retrieve,
        external_id=["houston.ro.REMOTE_AI[22]"],
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
    )


def test_preprocess_closure(get_c_mock):
    c_mock = get_c_mock("multi")

    def fake_news(resource, i):
        resource.to_pandas.return_value = pd.DataFrame(
            {
                "houston.ro.REMOTE_AI[22]": [
                    11 * 10**i,
                    22 * 10**i,
                    33 * 10**i,
                    44 * 10**i,
                    55 * 10**i,
                ]
            },
        )
        return resource

    stores = []
    for i in range(2):
        stores.append(
            data_stores.CDFStore(
                c_mock.time_series.data.retrieve,
                start=pd.to_datetime("2020-01-01T00:00:55"),
                end=pd.to_datetime("2020-01-01T00:01:00"),
                limit=5,
            ).preprocess(fake_news, i)
        )

    values = [
        stores[0](["houston.ro.REMOTE_AI[22]"]),
        stores[1](["houston.ro.REMOTE_AI[22]"]),
    ]

    expected = [
        {
            "houston.ro.REMOTE_AI[22]": pd.Series(
                [11, 22, 33, 44, 55],
            )
        },
        {
            "houston.ro.REMOTE_AI[22]": pd.Series(
                [110, 220, 330, 440, 550],
            )
        },
    ]
    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))


# def test_datapoints_retrieve_unknown_tag(mocked_client):
def test_datapoints_retrieve_unknown_tag(get_c_mock):
    c_mock = get_c_mock("empty")
    values = data_stores.CDFStore(
        c_mock.time_series.data.retrieve,
        start=pd.to_datetime("2020-01-03T00:00:00"),
        end=pd.to_datetime("2020-01-03T01:00:00"),
        ignore_unknown_ids=True,
        limit=3,
    )(["FOOBAR"])

    expected = {"FOOBAR": pd.Series(index=pd.DatetimeIndex([]), dtype=float)}

    assert_frame_equal(pd.DataFrame(values), pd.DataFrame(expected))
    assert_called_once_with(
        c_mock.time_series.data.retrieve,
        external_id=["FOOBAR"],
        start=pd.to_datetime("2020-01-03T00:00:00"),
        end=pd.to_datetime("2020-01-03T01:00:00"),
        ignore_unknown_ids=True,
        limit=3,
    )


def test_multiple_aggregates_not_supported(get_c_mock):
    c_mock = get_c_mock("multi")

    store = data_stores.CDFStore(
        c_mock.time_series.data.retrieve,
        start=pd.to_datetime("2020-01-01T00:00:55"),
        end=pd.to_datetime("2020-01-01T00:01:00"),
        limit=5,
        aggregates=["average", "sum"],
        granularity="3m",
    )

    with pytest.raises(ValueError) as exc:
        store(["houston.ro.REMOTE_AI[22]"])

    assert "CDFStore supports up to 1 item in `aggregates` list," in str(exc)
