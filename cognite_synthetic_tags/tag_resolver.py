from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Set, Tuple, cast

import pandas as pd

from cognite_synthetic_tags import Tag
from cognite_synthetic_tags._operations import DEFAULT_OPERATIONS
from cognite_synthetic_tags.data_stores import Store
from cognite_synthetic_tags.types import (
    OperationT,
    TagFormulaT,
    TagResolverContextT,
    TagSpecsT,
    TagValueT,
)


class TagResolver:
    """
    Usage:
    >>> from cognite_synthetic_tags import Tag
    >>> from tests.utils import DummyValueStore
    >>> specs = {
    ...     "value_1": Tag("A1"),
    ...     "value_2": Tag("A1") + Tag("B2") * Tag("B3"),
    ... }
    >>> TagResolver(DummyValueStore()).latest(specs)
    {'value_1': 1, 'value_2': 7}

    >>> specs = {
    ...     "value_1": Tag("A1") * 2,
    ...     "value_2": Tag("A1") * 3 + Tag("B2") * 1000 * Tag("B3"),
    ...     "value_3": Tag("B2"),
    ... }
    >>> TagResolver(DummyValueStore()).latest(specs)
    {'value_1': 2, 'value_2': 6003, 'value_3': 2}
    """

    def __init__(
        self,
        value_store: Store,
        additional_operations=None,
        **additional_stores: Store,
    ):
        self.context: TagResolverContextT = {}
        self._default_store_key = "value_store"
        self.data_stores: Dict[str, Store] = {
            self._default_store_key: value_store,
            **additional_stores,
        }
        self.operations = DEFAULT_OPERATIONS.copy()
        self.operations.update(additional_operations or {})
        self._recursive_tags: List[Set[str]] = [set()]
        self._specs: TagSpecsT = {}

    def series(self, specs: TagSpecsT) -> Dict[str, TagValueT]:
        """
        This is the heavy-lift method that does all the necessary steps:
         * Go through the `specs` dict and figure out all the tags that
           need to be queries from CDF.
         * Handle any literal values in the specs (values that are not
           instances of `Tag`, e.g. `2` in `Tag("foo") * 2`).
         * Perform calculations according to tag formulas (e.g. actually do
           the multiplication by 2 in the example above).
        """
        spec_keys = list(specs.keys())
        # extract any literal values from the specs:
        specs, literals = self._extract_literals_from_specs(specs)

        # add literals to context so that they can be used when resolving:
        self.context.update(literals)

        # recursively find all the actual CDF tags from the specs:
        self._specs = specs
        real_tags = defaultdict(set)
        for key, tag in specs.items():
            if tag.formula:
                # dig into the formula recursively
                tags = self._collect_tags_from_formula(key, tag.formula)
                for store_key, store_tags in tags.items():
                    real_tags[store_key].update(store_tags)
            else:
                # no formula, it's just a tag name
                store_key = self._get_item_value_store(tag)
                real_tags[store_key].add(tag.name)
                # TODO this branch is present in _collect_tags_from_formula too.
                #  Should refactor it so that both branches are handled there.

        # remove known values from query these can be:
        #  - literals, they are already in context,
        #  - previously fetch or calculated tags (basically caching, only
        #    relevant when calling `series` more then once with a single
        #    `TagResolver` instance).
        for store_key, store_tags in real_tags.items():
            known_tags = store_tags & set(self.context.keys())
            real_tags[store_key] -= known_tags

        # fetch all the data from CDF:
        for store_key, store_tags in real_tags.items():

            if not store_tags:
                continue

            # actually finally call the data store:
            #   (data stores are functions form `data_stores` module, see there
            #   for details)
            values = self.data_stores[store_key](store_tags)

            # add the values to context:
            #   (to be used later in `self._resolve_formula`)
            self.context.update(values)

        # add literals back:
        self.context.update(literals)

        # if the data store returns some series, transform all values in the
        # `values` dict are instances of `pd.Series` as well:
        self.context = self._make_series_in_dict(self.context)

        # at long last, perform the actual calculations according to the tag
        # specs, and start filling up the results dict:
        results = {}
        for key in spec_keys:
            if key in self.context:
                # this name is already in context, so just use that:
                #   (for simple tags with no formula and also for
                #   already-calculated formulas when calling `series` again)
                results[key] = self.context[key]
            else:
                # key must be a real tag in specs:
                assert key in specs
                tag = specs[key]
                if tag.name in self.context:
                    results[key] = self.context[tag.name]
                else:
                    # tag must have a formula here, otherwise it wold have been
                    # fetched directly by the store and already in the context:
                    assert tag.formula is not None
                    # perform calculations according to the formula:
                    resolved_value = self._resolve_formula(tag.formula)
                    # add to context so that we have it for repeated calls to
                    # `self.resolve`:
                    self.context[tag.name] = resolved_value
                    # and add it to the return value:
                    results[key] = resolved_value

        return results

    def df(self, specs):
        res = self.series(specs)
        return pd.DataFrame(res)

    def latest(self, specs):
        df = self.df(specs)
        if len(df) == 0:
            return {}
        last = df.iloc[-1:]
        return last.to_dict("records")[0]

    def _collect_tags_from_formula(
        self, key: str, formula: TagFormulaT
    ) -> Dict[str, Set[str]]:
        """
        Given a tag formula, recursively collect all other tag names mentioned
        in the formula.
        """
        tags = defaultdict(set)
        for item in formula[1]:
            self._recursive_tags += [self._recursive_tags[-1].copy()]
            if hasattr(item, "formula"):
                item = self._handle_recursive_tags(item)
                if item.formula:
                    new_tags = self._collect_tags_from_formula(
                        key,
                        item.formula,
                    )
                    for store_key, store_tags in new_tags.items():
                        tags[store_key].update(store_tags)
                else:
                    tags[self._get_item_value_store(item)].add(item.name)
            self._recursive_tags.pop()
        operator_ = formula[0]
        if not callable(operator_):
            assert (
                operator_ in self.operations
            ), f"Unknown operator: {operator_}"
        return tags

    def _get_item_value_store(self, item: Any) -> str:
        store_key = getattr(item, "store", None) or self._default_store_key
        if store_key not in self.data_stores:
            raise ValueError(
                f"Unknown value store '{store_key}' for tag '{item}'."
            )
        return store_key

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
        """
        Take a formula and return a value.
        Uses `self.context` dict to fetch individual values (leaves in the
        tree of math operations in the formula).
        """
        operands: List[TagValueT] = []

        # resolve subformulas and collect all operands:
        operator_, subformulas = formula  # e.g: ("*", (2, Tag("FOO")))
        undefined = object()
        for item in subformulas:
            subformula = getattr(item, "formula", undefined)
            if subformula is undefined:
                # literal, for example when adding an integer to a `Tag`
                operands.append(cast(TagValueT, item))
            elif subformula is None:
                # no formula, just a tag name - must be present in context
                operands.append(self.context[item.name])
            else:
                # got some formula, recursion!
                operands.append(self._resolve_formula(subformula))

        # find which operation should be applied:
        operation: OperationT
        if callable(operator_):
            operation = operator_
        else:
            assert (
                operator_ in self.operations
            ), f"Unknown operator: {operator_}"
            operation = self.operations[operator_]

        # apply the operator to the operands:
        uniform_operands = self._make_series(operands)
        # ...do it manually so that we support all possible operations
        # ...(this is slower, but supports things like string manipulation)
        # ... TODO consider making a FastTagResolver ?
        values_series: List[pd.Series] = uniform_operands
        result = pd.Series(
            (
                operation(*[series[i] for series in values_series])
                for i in values_series[0].index
            ),
            index=values_series[0].index,
        )

        return result

    @staticmethod
    def _extract_literals_from_specs(
        specs: TagSpecsT,
    ) -> Tuple[TagSpecsT, TagResolverContextT]:
        """
        Split specs dict in two: one with the actual specs and another with
        only literal values.
        """
        new_specs: TagSpecsT = {}
        literals: TagResolverContextT = {}
        for key, value in specs.items():
            if isinstance(value, Tag):
                new_specs[key] = value
            else:
                literals[key] = value
        return new_specs, literals

    @staticmethod
    def _make_series(data: Iterable[TagValueT]) -> List[TagValueT]:
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
            series = [pd.Series(index=pd.DatetimeIndex([datetime.utcnow()]))]

        # check that all series have the same indexes:
        #   (all are returned from the same CDF API call, so they should)
        index = series[0].index
        assert all(
            single_series.index.identical(index) for single_series in series[1:]
        ), "Series need to have the same index."
        # convert any non-series items to series:
        #   (repeat the item for every index)
        all_series: List[pd.Series] = [
            val if isinstance(val, pd.Series) else pd.Series(val, index=index)
            for val in data
        ]

        return all_series

    @staticmethod
    def _make_series_in_dict(data: TagResolverContextT) -> TagResolverContextT:
        """
        Make sure that all values in the dict are `pd.Series` instances if the
        index is a `pd.Index`.
        """
        series = TagResolver._make_series(data.values())
        data = dict(zip(data.keys(), series))
        return data
