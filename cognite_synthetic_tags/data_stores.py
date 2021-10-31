import abc

import numpy as np

__all__ = [
    "CDFStore",
]

import pandas as pd


class Store(abc.ABC):
    def __init__(self, retrieve_func, *args, **kwargs):
        self.retrieve_func = retrieve_func
        self.retrieve_args = args
        self.retrieve_kwargs = kwargs

    def get(self, external_ids):
        res = self._fetch(external_ids)
        results = self._process(res, external_ids)
        return results

    @abc.abstractmethod
    def _fetch(self, external_ids):
        ...

    @abc.abstractmethod
    def _process(self, raw, external_ids):
        ...


class CDFStore(Store):
    fill_with = np.nan

    def _fetch(self, external_ids):
        return self.retrieve_func(
            external_id=external_ids,
            *self.retrieve_args,
            **self.retrieve_kwargs,
        )

    def _process(self, raw, external_ids):
        df = raw.to_pandas()
        if df.empty:
            df.index = pd.DatetimeIndex([])
        # Compile a list of expected columns:
        tags = external_ids
        aggregates = self.retrieve_kwargs.get("aggregates")
        columns = (
            tags
            if aggregates is None
            else [
                f"{tag}|{aggregate}" for tag in tags for aggregate in aggregates
            ]
        )

        # Add any missing columns:
        df.loc[:, [c for c in columns if c not in df.columns]] = self.fill_with

        # Reorder columns:
        df = df[columns]

        resolved = {col: df[col] for col in df.columns}
        return resolved
