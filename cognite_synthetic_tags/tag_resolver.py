from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import pandas as pd

from cognite_synthetic_tags import Tag
from cognite_synthetic_tags._operations import DEFAULT_OPERATIONS
from cognite_synthetic_tags.types import (
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
    >>> from tests.utils import dummy_value_store
    >>> specs = {
    ...     "value_1": Tag("A1"),
    ...     "value_2": Tag("A1") + Tag("B2") * Tag("B3"),
    ... }
    >>> TagResolver(dummy_value_store).resolve(specs)
    {'value_1': 1, 'value_2': 7}

    >>> specs = {
    ...     "value_1": Tag("A1") * 2,
    ...     "value_2": Tag("A1") * 3 + Tag("B2") * 1000 * Tag("B3"),
    ...     "value_3": Tag("B2"),
    ... }
    >>> TagResolver(dummy_value_store).resolve(specs)
    {'value_1': 2, 'value_2': 6003, 'value_3': 2}
    """

    def __init__(
        self,
        value_store: TagValueStoreT,
        additional_operations=None,
        **additional_stores: TagValueStoreT,
    ):
        self.context: TagResolverContextT = {}
        self._default_store_key = "value_store"
        self.data_stores: Dict[str, TagValueStoreT] = {
            self._default_store_key: value_store,
            **additional_stores,
        }
        self.operations = DEFAULT_OPERATIONS.copy()
        self.operations.update(additional_operations or {})
        self._recursive_tags: List[Set[str]] = [set()]
        self._specs: TagSpecsT = {}

    def resolve(self, specs: TagSpecsT) -> Dict[str, TagValueT]:
        """
        This is the heavy-lift method that does all the necessary steps:
         * Go through the `specs` dict and figure out all the tags that
           need to be queries from CDF.
         * Handle any literal values in the specs (values that are not
           instances of `Tag`, e.g. `2` in `Tag("foo") * 2`).
         * Perform calculations according to tag formulas (e.g. actually do
           the multiplication by 2 in the example above).
        """
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
        #    relevant when calling `resolve` more then once with a single
        #    `TagResolver` instance).
        for store_key, store_tags in real_tags.items():
            known_tags = store_tags & set(self.context.keys())
            real_tags[store_key] -= known_tags

        # fetch all the data from CDF:
        default_index = None
        for store_key, store_tags in real_tags.items():
            # actually finally call the data store:
            #   (data stores are functions form `data_stores` module, see there
            #   for details)
            values, index = self.data_stores[store_key](store_tags)

            # ensure there are no crazy duplicate names:
            #   (names for non-default store have the store name appended,
            #   so it would be really weird to hit duplicates here, so blow up)
            for key, val in values.items():
                if key in self.context:
                    raise ValueError(
                        f"Duplicate definition (multiple stores): {key}"
                    )

            # if the data store returns some series, transform all values in the
            # `values` dict are instances of `pd.Series` as well:
            values = self._make_series_in_dict(values, index)

            # add the values to context:
            #   (to be used later in `self._resolve_formula`)
            self.context.update(values)

            # remember index of the default store, to transform literals below:
            if store_key == self._default_store_key:
                default_index = index

        # transform literals according to the default data store:
        #   (if the default store returns series, transform literals to match)
        literals = self._make_series_in_dict(literals, default_index)

        # at long last, perform the actual calculations according to the tag
        # specs, and start filling up the results dict:
        results = {}
        for key, tag in specs.items():
            if tag.name in self.context:
                # this name is already in context, so just use that:
                #   (for simple tags with no formula and also for
                #   already-calculated formulas when calling `resolve` again)
                results[key] = self.context[tag.name]
            else:
                # tag must have a formula here, otherwise it wold have been
                # fetched directly by the store and already part of the context:
                assert tag.formula is not None
                # perform calculations according to the formula:
                resolved_value = self._resolve_formula(tag.formula)
                # add to context so that we have it for repeated calls to
                # `self.resolve`:
                self.context[tag.name] = resolved_value
                # and add it to the return value:
                results[key] = resolved_value

        # add the literal values back into the results:
        results.update(literals)

        return results

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
        store_key = getattr(item, "store", self._default_store_key)
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
        operands, series_index = self._make_series(operands)
        if series_index is not None:
            # some operands are instance of `pd.Series`, we need to
            # apply the operation element-wise
            values_series: List[pd.Series] = operands  # keeping mypy happy
            result = pd.Series(
                (
                    operation(*[series[i] for series in values_series])
                    for i in series_index
                ),
                index=series_index,
            )
        else:
            # all operands are just numbers, apply the operation directly
            result = operation(*operands)

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
    def _make_series(
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
        #   (all are returned from the same CDF API call, so they should)
        index = series[0].index
        for single_series in series[1:]:
            assert all(
                single_series.index.identical(index)
            ), "Series need to have the same index."
        # convert any non-series items to series:
        #   (repeat the item for every index)
        all_series: List[pd.Series] = [
            val if isinstance(val, pd.Series) else pd.Series(val, index=index)
            for val in data
        ]

        return all_series, index

    @staticmethod
    def _make_series_in_dict(
        data: TagResolverContextT,
        index: pd.Index,
    ) -> TagResolverContextT:
        """
        Make sure that all values in the dict are `pd.Series` instances if the
        index is a `pd.Index`.
        """
        if index is not None:
            data["__dummy_series__"] = pd.Series({}, index=index)
            # TODO ^^ Yeah, it's a magic string...  ¯\_(ツ)_/¯
            series_or_values, _ = TagResolver._make_series(data.values())
            data = dict(zip(data.keys(), series_or_values))
            del data["__dummy_series__"]
        return data
