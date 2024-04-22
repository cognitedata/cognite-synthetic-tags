import logging
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--skipcdf",
        action="store_true",
        default=False,
        help="Skip tests that use CDF API.",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "cdf: mark test as needing CDF to run")


def pytest_collection_modifyitems(config, items):
    # --skipcdf
    skip_cdf = pytest.mark.skip(reason="skipped using --skipcdf option")
    if config.getoption("--skipcdf"):
        # --skipcdf given in cli: mark tests with cdf to be skipped
        for item in items:
            if "cdf" in item.keywords:
                item.add_marker(skip_cdf)


@pytest.fixture
def env_allow_bool():
    val = os.environ.get("COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL")
    os.environ["COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL"] = "yes"
    yield
    if val is None:
        del os.environ["COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL"]
    else:
        os.environ["COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL"] = val


@pytest.fixture
def env_allow_bool_silent():
    val = os.environ.get("COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL")
    os.environ["COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL"] = "silent"
    yield
    if val is None:
        del os.environ["COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL"]
    else:
        os.environ["COGNITE_SYNTHETIC_TAGS_ALLOW_BOOL"] = val
