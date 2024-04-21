from collections import Counter
from typing import Any, Callable, Union

import pytest

from cognite.client import CogniteClient
from cognite.client.data_classes import (
    AssetList,
    DatapointsList,
    DataSetList,
    EventList,
    FileMetadataList,
    FunctionList,
    LabelDefinitionList,
    RelationshipList,
    SequenceList,
    SequenceRowsList,
    TimeSeriesList,
)
from cognite.client.data_classes._base import CogniteResourceList
from cognite.client.data_classes.data_modeling import DataModelList, NodeApplyList
from cognite.client.testing import monkeypatch_cognite_client

from tests.integration._client import create_mock_api


@pytest.fixture(scope="function")
def cognite_client() -> CogniteClient:
    from ._client import client
    return client


@pytest.fixture
def approval_client(cognite_client: CogniteClient) -> CogniteClient:
    inputs: dict[str, Union[CogniteResourceList, dict[str, Any], list[Any]]] = {}
    outputs: dict[str, Union[CogniteResourceList, dict[str, Any]]] = {}

    def create_dump(dct: dict[str, Union[CogniteResourceList, dict[str, Any]]]) -> Callable[[], dict[str, Any]]:
        def dump() -> dict[str, Any]:
            # prepare a dump dict, nodes and edges need some special consideration:
            dumped = {key: [] for key in {*dct.keys()}}
            # dump:
            for key in sorted(dct):
                values = dct[key] or []
                for value in values:
                    dumped[key].append(value.dump(camel_case=True) if hasattr(value, "dump") else value)
            # sort values and remove empty keys:
            for key, values in list(dumped.items()):
                if not values:
                    del dumped[key]
                else:
                    dumped[key] = sorted(
                        values,
                        key=lambda x: next(x[k] for k in ["externalId", "external_id", "name", "id"] if k in x),
                    )
            return dumped

        return dump

    with monkeypatch_cognite_client() as client:
        for api_instance, name, read_list_cls, write_list_cls in [
            (cognite_client.events, "events", EventList, None),
            (cognite_client.data_sets, "data_sets", DataSetList, None),
            (cognite_client.relationships, "relationships", RelationshipList, None),
            (cognite_client.sequences, "sequences", SequenceList, None),
            (cognite_client.sequences.rows, "sequences.data", SequenceRowsList, None),
            (cognite_client.time_series, "time_series", TimeSeriesList, None),
            (cognite_client.time_series.data, "time_series.data", DatapointsList, None),
            (cognite_client.assets, "assets", AssetList, None),
            (cognite_client.files, "files", FileMetadataList, None),
            (cognite_client.data_modeling.instances, "data_modeling.instances", NodeApplyList, None),
            (cognite_client.labels, "labels", LabelDefinitionList, None),
            (cognite_client.data_modeling.data_models, "data_modeling.data_models", DataModelList, None),
            (cognite_client.functions, "functions", FunctionList, None),
        ]:
            mock_api = create_mock_api(api_instance, read_list_cls, inputs, outputs, write_list_cls)

            dot_count = Counter(name)["."]
            if dot_count == 1:
                parent, child = name.split(".")
                setattr(getattr(client, parent), child, mock_api)
            elif dot_count == 0:
                setattr(client, name, mock_api)
            else:
                raise ValueError(f"Invalid name: {name}")

            client.dump_inputs = create_dump(inputs)
            client.dump_outputs = create_dump(outputs)
        # Set post to real post as that is used for the GraphQL Query
        client.post = cognite_client.post
        client.iam.token = cognite_client.iam.token
        yield client

    inputs.clear()
    outputs.clear()
