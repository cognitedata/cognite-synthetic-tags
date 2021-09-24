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
    "series",
    "point",
    "series_at_time",
    "point_at_time",
]


def retrieve_datapoints_df(
    client: CogniteClient,
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
    res = client.datapoints.retrieve(
        id=id,
        external_id=external_id,
        ignore_unknown_ids=ignore_unknown_ids,
        **kwargs,
    )
    df = res.to_pandas()

    # Compile a list of expected columns:
    tags = external_id or id or []
    aggregates = kwargs.get("aggregates")
    columns = (
        tags
        if aggregates is None
        else [f"{tag}|{aggregate}" for tag in tags for aggregate in aggregates]
    )

    # Add any missing columns:
    df.loc[:, [c for c in columns if c not in df.columns]] = fill_with

    # Reorder columns:
    df = df[columns]

    return df


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
    """
    Returns a dict with series of data points.

    This is a very thin wrapper around `CogniteClient.datapoints.retrieve`, with
    a few tweaks:
     * if `ignore_unknown_ids=True` is used, the response will always contain
       all tags that have been requested, even if these tags don't exists in CDF
     * this function takes `aggregate` (singular) instead of `aggregates`
       (plural), and expects a string (no support for a list, use multiple `Tag`
       instances for that).
     * additional argument: `ffill` will forward-fill the data if set to `True`
     * additional argument: `fillna` will replace `np.nan` with specified value
       unless set to `None` (which is the default)
    """

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
            df = pd.DataFrame()
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


def _last_point_from_series(
    data: TagValueStoreResultT,
    fillna: Any = None,
) -> TagValueStoreResultT:
    """
    Return a dict with only the last value from every series. For empty series,
    the value will be set to `np.nan` by default or whatever `fillna` is set to.
    """
    for key, value in data[0].items():
        if isinstance(value, pd.Series):
            if len(value.index) == 0:
                data[0][key] = np.nan if fillna is None else fillna
            else:
                last_index = value.index[-1]
                data[0][key] = value[last_index]
    return data[0], None


def point(
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
    """
    Exactly the same as `series`, except that the result dict will
    contain only the last value of the fetched series.
    """
    _series = series(
        client,
        start,
        end,
        aggregate,
        granularity,
        include_outside_points,
        limit,
        query_by,
        ignore_unknown_ids,
        ffill,
        fillna,
    )

    def _retrieve(tags: Set[str]) -> TagValueStoreResultT:
        return _last_point_from_series(_series(tags))

    return _retrieve


def series_at_time(
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
    """
    Allows simpler retrieval of data before a set point in time (the `at_time`
    argument).

    Instead of the usual `start` and `end`, this function takes `at_time` and
    `lookbehind_start_time`. These are translated to `start` and `end` before
    querying the CDF.

    As an alternative to `lookbehind_start_time`, `lookbehind_limit` can be used
    together with `aggregate` and `granularity`.
    Using these arguments will automatically calculate `lookbehind_start_time`
    such that only `lookbehind_limit` (int) number of intervals are included in
    the query. For example, to look at last 10 minutes 24 hours ago in
    increments of 2 minute:
        series_at_time(
            ...,
            at_time="24h-ago",
            aggregate="average",
            granularity="2m",
            lookbehind_limit=5,
        )
    """

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
        assert lookbehind_limit is not None
        lookbehind_ms = lookbehind_limit * granularity_to_ms(granularity)
        start = timestamp_to_ms(at_time) - lookbehind_ms

    end = at_time
    limit = None

    return series(
        client,
        start,
        end,
        aggregate,
        granularity,
        include_outside_points,
        limit,
        query_by,
        ignore_unknown_ids,
        ffill,
        fillna,
    )


def point_at_time(
    client: CogniteClient,
    at_time: CogniteTimeT,
    lookbehind_start_time: Optional[CogniteTimeT] = None,
    aggregate: Optional[str] = None,
    granularity: Optional[str] = None,
    lookbehind_limit: Optional[int] = None,
    include_outside_points: bool = None,
    query_by: Literal["id", "external_id"] = "id",
    ignore_unknown_ids: bool = True,
    ffill: bool = False,
    fillna: Any = None,
) -> RetrievalFuncT:
    """
    Exactly the same as `series_at_time`, except that the result dict will
    contain only the last value of the fetched series.
    """
    _series_at_time = series_at_time(
        client,
        at_time,
        lookbehind_start_time,
        aggregate,
        granularity,
        lookbehind_limit,
        include_outside_points,
        query_by,
        ignore_unknown_ids,
        ffill,
        fillna,
    )

    def _retrieve(tags: Set[str]) -> TagValueStoreResultT:
        return _last_point_from_series(_series_at_time(tags), fillna)

    return _retrieve
