from typing import Any, Dict, List, Literal, Optional, Set

import numpy as np
import pandas as pd
from cognite.client import CogniteClient

from cognite_synthetic_tags.types import CogniteTimeT, RetrievalFuncT, TagValueT

DEFAULT_LIMIT = 10


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
    tags = external_id or id
    assert tags is not None  # otherwise c.datapoints.ret would raise
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
    start: CogniteTimeT,
    end: CogniteTimeT,
    aggregate: Optional[str] = None,
    granularity: Optional[str] = None,
    include_outside_points: bool = None,
    limit: int = DEFAULT_LIMIT,
    query_by: Literal["id", "external_id"] = "id",
    ignore_unknown_ids: bool = True,
    ffill: bool = True,
    fillna: Any = None,
) -> RetrievalFuncT:
    def _retrieve(tags: Set[str]) -> Dict[str, TagValueT]:
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
        if df.empty:
            df[start] = [np.nan] * len(df.columns)
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
        return resolved

    return _retrieve


def series(
    client: CogniteClient,
    start: CogniteTimeT,
    end: CogniteTimeT,
    aggregate: Optional[str] = None,
    granularity: Optional[str] = None,
    include_outside_points: bool = None,
    limit: int = DEFAULT_LIMIT,
    query_by: Literal["id", "external_id"] = "id",
    ignore_unknown_ids: bool = True,
    ffill: bool = False,
    fillna: Any = None,
) -> RetrievalFuncT:
    def _retrieve(tags: Set[str]) -> Dict[str, TagValueT]:
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
        if df.empty:
            df[start] = [np.nan] * len(df.columns)
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
        return resolved

    return _retrieve
