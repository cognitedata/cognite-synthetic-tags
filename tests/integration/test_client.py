import pytest
from cognite.client import CogniteClient


@pytest.mark.cdf
def test_client_configured_correctly(cognite_client: CogniteClient):
    time_series = cognite_client.time_series.list(limit=1)
    assert (
        len(time_series) == 1
    ), """

CONFIGURATION ERROR

CogniteClient is not configured correctly.
See .env.example for required environment variables.
Also make sure that you are running pytest from the root of the project.

    """
