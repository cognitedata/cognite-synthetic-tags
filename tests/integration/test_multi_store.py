from datetime import datetime, timedelta, timezone

import pytest
from cognite.client import CogniteClient
from pytest_regressions.data_regression import DataRegressionFixture

from cognite_synthetic_tags import CDFStore, Tag, TagResolver


@pytest.mark.cdf
def test_multi_store_single_tag(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    THE_TAG = "houston.ro.REMOTE_AI[3]"
    START = datetime(2021, 8, 7, 0, 0, 0, tzinfo=timezone.utc)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(  # not used
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    additional_store = CDFStore(  # used
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="20m",
    )
    specs = {"meter_a": Tag(THE_TAG, store="additional_store")}

    # Act
    df = TagResolver(fetch_func, additional_store=additional_store).df(specs)

    # Assert
    inputs = approval_client.dump_inputs()  # ignore: type[no-any-return]
    outputs = approval_client.dump_outputs()  # ignore: type[no-any-return]
    data_regression.check(
        {
            "inputs": inputs,
            "outputs": outputs,
            "results": df.to_dict("records"),
        }
    )


@pytest.mark.cdf
def test_multi_store_multiple_tags(
    approval_client: CogniteClient,
    data_regression: DataRegressionFixture,
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0, tzinfo=timezone.utc)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    additional_store = CDFStore(  # used
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="20m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2, store="additional_store"),
    }

    # Act
    df = TagResolver(fetch_func, additional_store=additional_store).df(specs)

    # Assert
    inputs = approval_client.dump_inputs()  # ignore: type[no-any-return]
    outputs = approval_client.dump_outputs()  # ignore: type[no-any-return]
    data_regression.check(
        {
            "inputs": inputs,
            "outputs": outputs,
            "results": df.to_dict("records"),
        }
    )


@pytest.mark.cdf
def test_multi_store_multiple_tags_and_literals(
    approval_client: CogniteClient,
    data_regression: DataRegressionFixture,
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0, tzinfo=timezone.utc)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    additional_store = CDFStore(  # used
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="20m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2, store="additional_store"),
        "literal": 42,
    }

    # Act
    df = TagResolver(fetch_func, additional_store=additional_store).df(specs)

    # Assert
    inputs = approval_client.dump_inputs()  # ignore: type[no-any-return]
    outputs = approval_client.dump_outputs()  # ignore: type[no-any-return]
    data_regression.check(
        {
            "inputs": inputs,
            "outputs": outputs,
            "results": df.to_dict("records"),
        }
    )


@pytest.mark.cdf
def test_multi_store_multiple_tags_and_literals_subraction(
    approval_client: CogniteClient,
    data_regression: DataRegressionFixture,
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0, tzinfo=timezone.utc)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    additional_store = CDFStore(  # used
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="20m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2, store="additional_store"),
        "delta": Tag(TAG_1) - Tag(TAG_2, store="additional_store"),
    }

    # Act
    df = TagResolver(fetch_func, additional_store=additional_store).df(specs)

    # Assert
    inputs = approval_client.dump_inputs()  # ignore: type[no-any-return]
    outputs = approval_client.dump_outputs()  # ignore: type[no-any-return]
    data_regression.check(
        {
            "inputs": inputs,
            "outputs": outputs,
            "results": df.to_dict("records"),
        }
    )


@pytest.mark.cdf
def test_multi_store_multiple_tags_same_tag_in_multiple_stores(
    approval_client: CogniteClient,
    data_regression: DataRegressionFixture,
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0, tzinfo=timezone.utc)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    additional_store = CDFStore(  # used
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="20m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2, store="additional_store"),
        "delta1": Tag(TAG_1) - Tag(TAG_2),
        "delta2": Tag(TAG_1) - Tag(TAG_2, store="additional_store"),
    }

    # Act
    df = TagResolver(fetch_func, additional_store=additional_store).df(specs)

    # Assert
    inputs = approval_client.dump_inputs()  # ignore: type[no-any-return]
    outputs = approval_client.dump_outputs()  # ignore: type[no-any-return]
    data_regression.check(
        {
            "inputs": inputs,
            "outputs": outputs,
            "results": df.to_dict("records"),
        }
    )
