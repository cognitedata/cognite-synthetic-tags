from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple, cast

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
        self._real_tags -= set(literals.keys())

        self.context.update(literals)
        # fetch all the data from CDF:
        values, index = self.value_store(self._real_tags)
        self.context.update(values)
        if index is not None:
            self.context.update(
                {"__dummy_series__": pd.Series({}, index=index)}
            )
        series_or_values, _ = self._make_series(list(self.context.values()))
        self.context = dict(zip(self.context.keys(), series_or_values))
        if index is not None:
            del self.context["__dummy_series__"]

        # perform calculations according to tag specs
        result = {}
        for key, tag in specs.items():
            if tag.name in self.context:
                result[key] = self.context[tag.name]
            else:
                assert tag.formula is not None
                result[key] = self._resolve_formula(tag.formula)

        # add the literal values back into the result:
        result.update({key: self.context[key] for key in literals})

        return result

    def _collect_tags_from_formula(
        self, key: str, formula: TagFormulaT
    ) -> Set[str]:
        """
        Given a tag formula, recursively collect all other tag names mentioned
        in the formula.
        """
        tags = set()
        for item in formula[1]:
            self._recursive_tags += [self._recursive_tags[-1].copy()]
            if hasattr(item, "formula"):
                item = self._handle_recursive_tags(item)
                if item.formula:
                    tags.update(
                        self._collect_tags_from_formula(key, item.formula)
                    )
                else:
                    tags.add(item.name)
            self._recursive_tags.pop()
        operator_ = formula[0]
        if not callable(operator_):
            assert (
                operator_ in self.operations
            ), f"Unknown operator: {operator_}"
        return tags

    def _handle_recursive_tags(self, tag: Tag) -> Tag:
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
        """Take a formula and return a value."""
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
        operation: OperationT
        if callable(operator_):
            operation = operator_
        else:
            assert (
                operator_ in self.operations
            ), f"Unknown operator: {operator_}"
            operation = self.operations[operator_]

        # If any pd.Series instance, apply the operation element-wise
        values, series_index = self._make_series(values)
        if series_index is not None:
            values_series: List[pd.Series] = values  # keeping mypy happy
            result = pd.Series(
                (
                    operation(*[series[i] for series in values_series])
                    for i in series_index
                ),
                index=series_index,
            )
        # otherwise it's just numbers, apply the operation directly:
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

    def _make_series(
        self,
        data: List[TagValueT],
    ) -> Tuple[List[TagValueT], Optional[pd.Index]]:
        """
        Take a list of values, and if any of the items is a `pd.Series`
        instance, change other values into `pd.Series` as well.

        Returns a 2-tuple:
        - list of values, either unchanged or with each item a `pd.Series`,
        - an index for the series or None. All series have the same index.
        """
        series: List[pd.Series] = [
            val for val in data if isinstance(val, pd.Series)
        ]
        if not series:
            return data, None

        # check that all series have the same indexes:
        # (all are returned from the same CDF API call, so they should)
        index = series[0].index
        for single_series in series:
            assert all(
                single_series.index == index
            ), "Series need to have the same index."
        # convert any non-series items to series:
        # (repeat the item for every index)
        all_series: List[pd.Series] = [
            val
            if isinstance(val, pd.Series)
            else pd.Series([val] * len(index), index=index)
            for val in data
        ]
        return all_series, index
