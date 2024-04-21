from datetime import datetime, timedelta

import pytest
from cognite.client import CogniteClient
from pytest_regressions.data_regression import DataRegressionFixture

from cognite_synthetic_tags import CDFStore, Tag, TagResolver


@pytest.mark.cdf
def test_single_store_single_tag(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    THE_TAG = "houston.ro.REMOTE_AI[3]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {"meter_a": Tag(THE_TAG)}

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_multiple_tags(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2),
    }

    # Act
    df = TagResolver(fetch_func).df(specs)

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


def test_single_store_no_tags(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs: dict[str, Tag] = {}

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_subtraction(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2),
        "delta": Tag(TAG_1) - Tag(TAG_2),
    }

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_only_subtraction(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {
        "delta": Tag(TAG_1) - Tag(TAG_2),
    }

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_comparison(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2),
        "status": Tag(TAG_1) > Tag(TAG_2),
    }

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_only_comparison(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {"status": Tag(TAG_1) > Tag(TAG_2)}

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_comparison_w_literals(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {
        "meter_a": Tag(TAG_1),
        "meter_b": Tag(TAG_2),
        "delta_more_than_2": Tag(TAG_1) - Tag(TAG_2) > 2,
    }

    # Act
    df = TagResolver(fetch_func).df(specs)

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
def test_single_store_only_comparison_w_literals(
    approval_client: CogniteClient, data_regression: DataRegressionFixture
):
    # Arrange
    TAG_1 = "houston.ro.REMOTE_AI[3]"
    TAG_2 = "houston.ro.REMOTE_AI[4]"
    START = datetime(2021, 8, 7, 0, 0, 0)
    END = START + timedelta(minutes=60)
    fetch_func = CDFStore(
        approval_client.time_series.data.retrieve,
        start=START,
        end=END,
        aggregates=["average"],
        granularity="10m",
    )
    specs = {
        "delta_more_than_2": Tag(TAG_1) - Tag(TAG_2) > 2,
    }

    # Act
    df = TagResolver(fetch_func).df(specs)

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
