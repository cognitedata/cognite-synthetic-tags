import abc
from typing import Callable, List

import numpy as np
import pandas as pd

__all__ = [
    "CDFStore",
]


class Store(abc.ABC):
    def __init__(self, retrieve_func, *args, **kwargs):
        self.retrieve_func = retrieve_func
        self.retrieve_args = args
        self.retrieve_kwargs = kwargs
        self._process_funcs: List[Callable[[pd.DataFrame], pd.DataFrame]] = []

    def __call__(self, external_ids):
        res = self._fetch(external_ids)
        df = self._process(res, external_ids)
        for process_func in self._process_funcs:
            df = process_func(df)
        return {col: df[col] for col in df.columns}

    @abc.abstractmethod
    def _fetch(self, external_ids):
        ...

    @abc.abstractmethod
    def _process(self, raw, external_ids):
        ...

    def process(self, func):
        self._process_funcs.append(func)
        return self


class CDFStore(Store):
    fill_with = np.nan

    def _fetch(self, external_ids):
        return self.retrieve_func(
            external_id=list(external_ids),
            *self.retrieve_args,
            **self.retrieve_kwargs,
        )

    def _process(self, raw, external_ids):
        df = raw.to_pandas()
        if df.empty:
            df.index = pd.DatetimeIndex([])
        # Compile a list of expected columns:
        tags = external_ids
        aggregates = self.retrieve_kwargs.get("aggregates", [])
        if len(aggregates) > 1:
            raise ValueError(
                f"CDFStore supports up to 1 item in `aggregates` list,"
                f" got: {aggregates}"
            )
        aggregate = aggregates[0] if aggregates else None
        columns = (
            tags
            if aggregate is None
            else [f"{tag}|{aggregate}" for tag in tags]
        )

        # Add any missing columns:
        df.loc[:, [c for c in columns if c not in df.columns]] = self.fill_with

        # Reorder columns:
        df = df[columns]

        # Drop aggreated from column names:
        if aggregate:
            df.columns = [
                col.replace(f"|{aggregate}", "") for col in df.columns
            ]

        return df
