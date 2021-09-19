from typing import Any, List, Literal, Optional, Set

import numpy as np
import pandas as pd
from cognite.client import CogniteClient
from cognite.client.utils._time import granularity_to_ms, timestamp_to_ms

from cognite_synthetic_tags.types import (
    CogniteTimeT,
    RetrievalFuncT,
    TagValueStoreResultT,
)

__all__ = [
    "retrieve_datapoints_df",
    "latest_datapoint",
    "series",
]


def retrieve_datapoints_df(
    c: CogniteClient,
    id: Optional[List[int]] = None,
    external_id: Optional[List[str]] = None,
    ignore_unknown_ids: bool = True,
    fill_with=np.nan,
    **kwargs,
) -> pd.DataFrame:
    """
    Wrapper around `CogniteClient.datapoints.retrieve` which fills in any
    missing columns (i.e. values in external_ids).

    Calling, `CogniteClient.datapoints.retrieve(..., ignore_unknown_ids=True)`
    results in missing columns, while `ignore_unknown_ids="fill"` or
    `"fill,dropna"` raise exceptions.
    """
    res = c.datapoints.retrieve(
        id=id,
        external_id=external_id,
        ignore_unknown_ids=ignore_unknown_ids,
        **kwargs,
    )
    df = res.to_pandas()
    tags = external_id or id or []
    aggregates = kwargs.get("aggregates")
    columns = (
        tags
        if aggregates is None
        else [f"{tag}|{aggregate}" for tag in tags for aggregate in aggregates]
    )

    # Add any missing columns
    df.loc[:, [c for c in columns if c not in df.columns]] = fill_with

    # Reorder columns:
    df = df[columns]
    return df.copy()


def latest_datapoint(
    client: CogniteClient,
    at_time: CogniteTimeT,
    lookbehind_start_time: Optional[CogniteTimeT] = None,
    aggregate: Optional[str] = None,
    granularity: Optional[str] = None,
    lookbehind_limit: Optional[int] = None,
    include_outside_points: bool = None,
    query_by: Literal["id", "external_id"] = "id",
    ignore_unknown_ids: bool = True,
    ffill: bool = True,
    fillna: Any = None,
) -> RetrievalFuncT:

    if lookbehind_start_time is None and lookbehind_limit is None:
        raise ValueError(
            "Specify either lookbehind_start_time or lookbehind_limit."
        )
    if lookbehind_start_time is not None and lookbehind_limit is not None:
        raise ValueError(
            "Specify either lookbehind_start_time or lookbehind_limit,"
            " not both."
        )
    if lookbehind_limit is not None and aggregate is None:
        raise ValueError("Specify aggregate with lookbehind_start.")
    if lookbehind_limit is not None and granularity is None:
        raise ValueError("Specify granularity with lookbehind_start.")

    if lookbehind_start_time is not None:
        start = lookbehind_start_time
    else:
        lookbehind_ms = lookbehind_limit * granularity_to_ms(granularity)
        start = timestamp_to_ms(at_time) - lookbehind_ms

    def _retrieve(tags: Set[str]) -> TagValueStoreResultT:
        if tags:
            df = retrieve_datapoints_df(
                client,
                **{query_by: list(tags)},  # type: ignore
                start=start,
                end=at_time,
                aggregates=[aggregate] if aggregate else None,
                granularity=granularity,
                include_outside_points=include_outside_points,
                ignore_unknown_ids=ignore_unknown_ids,
                limit=None,
            )
        else:
            df = pd.DataFrame({})
        if df.empty:
            # ensure that all keys are present in the response dict:
            df.loc[start, :] = [np.nan] * len(df.columns)
        if ffill:
            df = df.ffill()
        if fillna is not None:
            df = df.fillna(fillna)
            # (BTW, Pandas doesn't support df.fillna(None) ¯\_(ツ)_/¯ )
        if aggregate:
            df.columns = [
                col.replace(f"|{aggregate}", "") for col in df.columns
            ]
        resolved = df.iloc[-1, :].to_dict()
        return resolved, None

    return _retrieve


def series(
    client: CogniteClient,
    start: CogniteTimeT,
    end: CogniteTimeT,
    aggregate: Optional[str] = None,
    granularity: Optional[str] = None,
    include_outside_points: bool = None,
    limit: Optional[int] = None,
    query_by: Literal["id", "external_id"] = "id",
    ignore_unknown_ids: bool = True,
    ffill: bool = False,
    fillna: Any = None,
) -> RetrievalFuncT:
    def _retrieve(tags: Set[str]) -> TagValueStoreResultT:
        if tags:
            df = retrieve_datapoints_df(
                client,
                **{query_by: list(tags)},  # type: ignore
                start=start,
                end=end,
                aggregates=[aggregate] if aggregate else None,
                granularity=granularity,
                include_outside_points=include_outside_points,
                ignore_unknown_ids=ignore_unknown_ids,
                limit=limit,
            )
        else:
            df = pd.DataFrame({})
        if ffill:
            df = df.ffill()
        if fillna is not None:
            df = df.fillna(fillna)
            # (BTW, Pandas doesn't support df.fillna(None) ¯\_(ツ)_/¯ )
        if aggregate:
            df.columns = [
                col.replace(f"|{aggregate}", "") for col in df.columns
            ]
        resolved = {col: df[col] for col in df.columns}
        return resolved, df.index

    return _retrieve
