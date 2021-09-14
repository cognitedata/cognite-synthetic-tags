from __future__ import annotations

from typing import Dict, List, Set, Tuple, cast

import pandas as pd

from . import Tag
from ._operations import default_operations
from .types import (
    OperationT,
    TagFormulaT,
    TagResolverContextT,
    TagSpecsT,
    TagValueStoreT,
    TagValueT,
)


class TagResolver:
    """
    Usage:
    >>> from cognite_synthetic_tags import Tag
    >>> specs = {
    ...     "value_1": Tag("A1"),
    ...     "value_2": Tag("A1") + Tag("B2") * Tag("B3"),
    ... }
    >>> TagResolver(dummy_value_store).resolve(specs)
    {'value_1': 11, 'value_2': 737}
    >>> len(dummy_value_store.calls)
    3

    >>> dummy_value_store.calls = []
    >>> specs = {
    ...     "value_1": Tag("A1") * 2,
    ...     "value_2": Tag("A1") * 3 + Tag("B2") * 1000 * Tag("B3"),
    ...     "value_3": Tag("B2"),
    ... }
    >>> TagResolver(dummy_value_store).resolve(specs)
    {'value_1': 22, 'value_2': 726033, 'value_3': 22}
    >>> len(dummy_value_store.calls)
    3
    """

    def __init__(self, value_store: TagValueStoreT, additional_operations=None):
        self.context: TagResolverContextT = {}
        self.value_store = value_store
        self.operations = default_operations.copy()
        self.operations.update(additional_operations or {})
        self._real_tags: Set[str] = set()
        self._recursive_tags: List[Set[str]] = [set()]
        self._specs: TagSpecsT = {}

    def resolve(self, specs: TagSpecsT) -> Dict[str, TagValueT]:
        # extract any literal values from the specs:
        specs, literals = self._extract_literals_from_specs(specs)

        # find all the actual CDF tags from the specs, recursively:
        self._specs = specs
        self._real_tags = set()
        for key, tag in specs.items():
            if tag.formula:
                self._real_tags.update(
                    self._collect_tags_from_formula(key, tag.formula),
                )
            else:
                self._real_tags.add(tag.name)

        # fetch all the data from CDF:
        self.context.update(
            self.value_store(self._real_tags),
        )

        # perform calculations according to tag specs
        result = {}
        for key, tag in specs.items():
            if tag.name in self.context:
                result[key] = self.context[tag.name]
            else:
                assert tag.formula is not None
                result[key] = self._resolve_formula(tag.formula)

        # add the literal values back into the result:
        result.update(literals)

        return result

    def _collect_tags_from_formula(
        self, key: str, formula: TagFormulaT
    ) -> Set[str]:
        tags = set()
        for item in formula[1]:
            self._recursive_tags += [self._recursive_tags[-1].copy()]
            if hasattr(item, "formula"):
                item = self._handle_recursive_tags(key, item)
                if item.formula:
                    tags.update(
                        self._collect_tags_from_formula(key, item.formula)
                    )
                else:
                    tags.add(item.name)
            self._recursive_tags.pop()
        operator_ = formula[0]
        assert operator_ in self.operations, f"Unknown operator: {operator_}"
        return tags

    def _handle_recursive_tags(self, key: str, tag: Tag) -> Tag:
        if tag.name in self._specs:
            if tag.name in self._recursive_tags[-1]:
                raise ValueError(
                    f"Cyclic definition of tags with:"
                    f" {tag.name} in {tag.formula}"
                )
            self._recursive_tags[-1].add(tag.name)
            item = self._specs[tag.name]
            tag.formula = getattr(item, "formula", item)
        return tag

    def _resolve_formula(self, formula: TagFormulaT) -> TagValueT:
        values: List[TagValueT] = []
        for item in formula[1]:
            if hasattr(item, "formula"):
                if item.formula:
                    values.append(self._resolve_formula(item.formula))
                else:
                    values.append(self.context[item.name])
            else:
                # literal, for example when multiplying with an integer
                values.append(cast(TagValueT, item))
        operator_ = formula[0]
        assert operator_ in self.operations, f"Unknown operator: {operator_}"
        operation: OperationT = self.operations[operator_]

        # If any pd.Series instance, apply the operation element-wise
        series: List[pd.Series] = list(
            filter(lambda val: isinstance(val, pd.Series), values)
        )
        if series:
            index = series[0].index
            # check that all series have the same indexes:
            # (all are returned from the same CDF API call, so they should)
            for single_series in series:
                assert all(
                    single_series.index == index
                ), "Series need to have the same index."
            # convert any non-series items to series:
            # (repeat the item for every index)
            all_series: List[pd.Series] = [
                value
                if isinstance(value, pd.Series)
                else pd.Series([value] * len(index), index=index)
                for value in values
            ]
            # apply the operation, element-wise, and make a new pd.Series:
            result = pd.Series(
                operation(*[single_series[i] for single_series in all_series])
                for i in index
            )
        else:
            result = operation(*values)
        return result

    def _extract_literals_from_specs(
        self,
        specs: TagSpecsT,
    ) -> Tuple[TagSpecsT, TagResolverContextT]:
        literals: TagResolverContextT = {}
        for key, value in specs.items():
            if not isinstance(value, Tag):
                literals[key] = value
        self.context.update(literals)
        new_specs = {
            key: value for key, value in specs.items() if key not in literals
        }
        return new_specs, literals
