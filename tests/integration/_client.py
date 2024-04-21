import hashlib
import inspect
import itertools
import json
import os

from collections.abc import Collection
from contextlib import suppress
from typing import Any, Callable, Sequence, Union, Optional
from unittest.mock import MagicMock

import arrow
import pandas as pd
import yaml
from cognite.client import CogniteClient, ClientConfig

from cognite.client._api_client import APIClient
from cognite.client.credentials import OAuthClientCredentials
from cognite.client.data_classes import FileMetadata, FileMetadataList
from cognite.client.data_classes._base import CogniteResource, CogniteResourceList, CogniteUpdate
from cognite.client.data_classes.data_modeling import (
    EdgeApply,
    EdgeApplyList,
    EdgeApplyResult,
    EdgeApplyResultList,
    EdgeList,
    InstancesApplyResult,
    InstancesResult,
    NodeApply,
    NodeApplyList,
    NodeApplyResult,
    NodeApplyResultList,
    NodeList,
)
from dotenv import load_dotenv
from yaml.parser import ParserError


load_dotenv()

client = CogniteClient(
    ClientConfig(
        client_name=os.environ["CDF_CLIENT_NAME"],
        project=os.environ["CDF_PROJECT"],
        credentials=OAuthClientCredentials(
            token_url=os.environ["CDF_TOKEN_URL"],
            client_id=os.environ["CDF_CLIENT_ID"],
            client_secret=os.environ["CDF_CLIENT_SECRET"],
            scopes=os.environ["CDF_SCOPES"].split("|"),
        ),
    ),
)


def _dump(obj: CogniteResource) -> dict:
    """Duplicate cognite object to break references with the original."""
    return obj.dump()


def create_mock_api(
    api: APIClient,
    read_list_cls: type[CogniteResourceList],
    inputs: dict[str, Union[CogniteResourceList, list[Any]]],
    outputs: dict[str, Union[CogniteResourceList, list[Any]]],
    write_list_cls: Optional[type[CogniteResourceList]] = None,
) -> APIClient:
    api_cls = type(api)
    mock_api = MagicMock(spec=api_cls)

    resource_cls = read_list_cls._RESOURCE
    write_list_cls = write_list_cls or read_list_cls
    write_resource_cls = write_list_cls._RESOURCE

    outputs[resource_cls.__name__] = write_list_cls([])
    inputs[resource_cls.__name__] = []
    # FDM Instances and Files need some additional lists:
    if write_list_cls == NodeApplyList:
        outputs["EdgeApply"] = EdgeApplyList([])
        inputs["EdgeApply"] = []
        outputs["Node"] = NodeList([])
        inputs["Node"] = []
        outputs["Edge"] = EdgeList([])
        inputs["Edge"] = []
    if write_list_cls == FileMetadataList:
        outputs["FileContent"] = []
        inputs["FileContent"] = []

    def create(*args, **kwargs) -> Any:
        created = []
        is_single = True
        for value in itertools.chain(args, kwargs.values()):
            if isinstance(value, write_resource_cls):
                created.append(value)
            elif isinstance(value, Sequence) and all(isinstance(v, write_resource_cls) for v in value):
                is_single = False
                created.extend(value)
            elif isinstance(value, CogniteUpdate):
                dumped = value.dump(camel_case=True)
                called = api.retrieve(external_id=dumped["externalId"])
                # Note that we do not apply the update, that should not be necessary as it was done
                # the first time this function was run on the historical data.
                created.append(called)

        for item in created:
            outputs[resource_cls.__name__].append(_dump(item))
        return created[0] if created and is_single else write_list_cls(created)

    def apply(
        nodes: Union[NodeApply, Sequence[NodeApply], None] = None,
        edges: Union[EdgeApply, Sequence[EdgeApply], None] = None,
        **kwargs,
    ) -> InstancesApplyResult:
        if nodes is not None:
            nodes = nodes if isinstance(nodes, Sequence) else [nodes]
            outputs[NodeApply.__name__].extend([_dump(node) for node in nodes])
        if edges is not None:
            if EdgeApply.__name__ not in outputs:
                outputs[EdgeApply.__name__] = EdgeApplyList([])
            edges = edges if isinstance(edges, Sequence) else [edges]
            outputs[EdgeApply.__name__].extend([_dump(edge) for edge in edges])
        now_epoch = int(arrow.utcnow().timestamp())
        return InstancesApplyResult(
            nodes=NodeApplyResultList(
                [
                    NodeApplyResult(
                        space=node.space,
                        external_id=node.external_id,
                        # totally fake:
                        version=1,
                        was_modified=True,
                        last_updated_time=now_epoch,
                        created_time=now_epoch,
                    )
                    for node in nodes
                ],
            ),
            edges=EdgeApplyResultList(
                [
                    EdgeApplyResult(
                        space=edge.space,
                        external_id=edge.external_id,
                        # totally fake:
                        version=1,
                        was_modified=True,
                        last_updated_time=now_epoch,
                        created_time=now_epoch,
                    )
                    for edge in edges
                ],
            ),
        )

    def upload_bytes(**kwargs) -> Any:
        with suppress(KeyError, ValueError, ParserError):
            kwargs["content"] = kwargs["content"].decode()
            kwargs["content"] = yaml.safe_load(kwargs["content"])
        outputs["FileContent"].append(kwargs)
        file_metadata = FileMetadata(id=42, **{k: v for k, v in kwargs.items() if k != "content"})
        outputs[FileMetadata.__name__].append(file_metadata)

        return file_metadata

    def insert(*args, **kwargs) -> Any:
        if args:
            raise NotImplementedError()
        if kwargs:
            dump = {}
            for k, v in kwargs.items():
                # The json dump + load is to ensure that the object is serializable, typically, replacing np.float64 with float and so on
                dump[k] = json.loads(v.to_json()) if isinstance(v, pd.DataFrame) else json.loads(json.dumps(v))
            outputs[resource_cls.__name__].append(dump)

    def log_input_data(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            output = fn(*args, **kwargs)
            if isinstance(output, bytes):
                if args:
                    kwargs.update(zip(inspect.signature(fn).parameters, args))
                inputs[resource_cls.__name__].append({"content_hash": hashlib.md5(output).hexdigest(), **kwargs})
            elif isinstance(output, pd.DataFrame):
                if args:
                    kwargs.update(zip(inspect.signature(fn).parameters, args))
                dataframe_hash = int(
                    hashlib.sha256(pd.util.hash_pandas_object(output, index=True).values).hexdigest(), 16
                )
                inputs[resource_cls.__name__].append({"dataframe_hash": dataframe_hash, **kwargs})
            elif isinstance(output, InstancesResult):
                inputs["Node"].extend(_dump(node) for node in output.nodes)
                inputs["Edge"].extend(_dump(edge) for edge in output.edges)
            elif isinstance(output, NodeList):
                inputs["Node"].extend(_dump(edge) for edge in output)
            elif isinstance(output, EdgeList):
                inputs["Edge"].extend(_dump(edge) for edge in output)
            elif isinstance(output, Collection):
                inputs[resource_cls.__name__].extend([_dump(obj) for obj in output])
            else:
                inputs[resource_cls.__name__].append(_dump(output))

            return output

        return wrapper

    for method in [
        "list",
        "retrieve",
        "retrieve_dataframe",
        "retrieve_multiple",
        "download_bytes",
        "retrieve_latest",
        "retrieve_subtree",
    ]:
        if hasattr(api, method):
            setattr(mock_api, method, log_input_data(getattr(api, method)))

    if hasattr(api_cls, "create"):
        mock_api.create = create
    if hasattr(api_cls, "apply"):
        mock_api.apply = apply

    if hasattr(api_cls, "upsert"):
        mock_api.upsert = create
    if hasattr(api_cls, "update"):
        mock_api.update = create

    if hasattr(api_cls, "insert"):
        mock_api.insert = insert
    if hasattr(api_cls, "insert_dataframe"):
        mock_api.insert_dataframe = insert

    if hasattr(api_cls, "upload_bytes"):
        mock_api.upload_bytes = upload_bytes

    return mock_api
