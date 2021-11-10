from unittest import mock
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from cognite_synthetic_tags import Tag, TagResolver

from .utils import *  # noqa
from .utils import now


def test_regular_tag(value_store):
    specs = {
        "value_1": Tag("A1"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {"value_1": pd.Series([1], index=pd.DatetimeIndex([now]))}
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))
    value_store.get.assert_called_once_with({"A1"})


def test_regular_tags(value_store):
    specs = {
        "value_1": Tag("A1"),
        "value_2": Tag("B2"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([1], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([2], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))
    value_store.get.assert_called_once_with({"A1", "B2"})


def test_synthetic_tag(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2") * Tag("B3"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {"value_1": pd.Series([7], index=pd.DatetimeIndex([now]))}
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))
    value_store.get.assert_called_once_with({"A1", "B2", "B3"})


def test_synthetic_tags(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2") * Tag("B3"),
        "value_2": Tag("A10") + Tag("B2") + Tag("C300"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([7], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([312], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))
    value_store.get.assert_called_once_with({"A1", "B2", "B3", "A10", "C300"})


def test_arithmetic_operations(value_store):
    specs = {
        "value_1": 10 * Tag("A2"),
        "value_2": 0 + Tag("A10") + (1 + Tag("A2")) - 1 + Tag("C300") * 100,
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([20], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([30012], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))
    value_store.get.assert_called_once_with({"A2", "A10", "C300"})


def test_more_arithmetic_operations(value_store):
    specs = {
        "value_1": Tag("A11") // 2,
        "value_2": 2 + Tag("A11"),
        "value_3": 2 - Tag("A11"),
        "value_4": 110 / Tag("A11"),
        "value_5": Tag("A3") ** 2,
        "value_6": 3 ** Tag("A3"),
        "value_7": Tag("A14") % 4,
        "value_8": 14 % Tag("A4"),
        "value_9": 19 // Tag("A4"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([5], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([13], index=pd.DatetimeIndex([now])),
        "value_3": pd.Series([-9], index=pd.DatetimeIndex([now])),
        "value_4": pd.Series([10.0], index=pd.DatetimeIndex([now])),
        "value_5": pd.Series([9], index=pd.DatetimeIndex([now])),
        "value_6": pd.Series([27], index=pd.DatetimeIndex([now])),
        "value_7": pd.Series([2], index=pd.DatetimeIndex([now])),
        "value_8": pd.Series([2], index=pd.DatetimeIndex([now])),
        "value_9": pd.Series([4], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_bool(value_store):
    specs = {
        "value_1": Tag("A2").bool(),
        "value_2": Tag("A0").bool(),
        "value_3": Tag("A2").bool_not(),
        "value_4": Tag("A0").bool_not(),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([True], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([False], index=pd.DatetimeIndex([now])),
        "value_3": pd.Series([False], index=pd.DatetimeIndex([now])),
        "value_4": pd.Series([True], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_boolean_operators(value_store):
    specs = {
        "value_1": Tag("A2") & Tag("B3"),
        "value_2": Tag("A0") & Tag("B3"),
        "value_3": Tag("A0") | Tag("B0"),
        "value_4": Tag("A0") | Tag("B3"),
        "value_5": Tag("A0") ^ Tag("B3"),
        "value_6": Tag("A2") ^ Tag("B3"),
        "value_7": ~Tag("A0"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([True], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([False], index=pd.DatetimeIndex([now])),
        "value_3": pd.Series([False], index=pd.DatetimeIndex([now])),
        "value_4": pd.Series([True], index=pd.DatetimeIndex([now])),
        "value_5": pd.Series([True], index=pd.DatetimeIndex([now])),
        "value_6": pd.Series([False], index=pd.DatetimeIndex([now])),
        "value_7": pd.Series([True], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_calc(value_store):
    specs = {
        "value_1": Tag("A2").calc("+", 40),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([42], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_calc_custom_operation(value_store):
    specs = {
        "value_1": Tag("A2").calc("foobar", 40),
        "value_2": Tag("A2").calc("is_even"),
    }
    additional_operations = {
        "foobar": lambda a, b: str(a + b) * 3,
        "is_even": lambda a: a % 2 == 0,
    }

    value = TagResolver(value_store, additional_operations).series(specs)

    expected = {
        "value_1": pd.Series(["424242"], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([True], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_apply_custom_operation(value_store):
    specs = {
        "value_1": Tag.apply("max", Tag("A2"), Tag("B7")),
        "value_2": Tag.apply("max", Tag("A2") * 11, Tag("B7")),
    }
    additional_operations = {"max": max}

    value = TagResolver(value_store, additional_operations).series(specs)

    expected = {
        "value_1": pd.Series([7], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([22], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_apply_literal_functions(value_store):
    def foo(a, b):
        return f"{a} and {b}"

    specs = {
        "value_1": Tag.apply(foo, Tag("A2"), Tag("B7")),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series(["2 and 7"], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_calc_literal_functions(value_store):
    def foo(a):
        return f"foo of {a}"

    specs = {"value_1": Tag("A2").calc(foo)}

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series(["foo of 2"], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_recursive_spec(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2"),
        "value_2": Tag("value_1") * 10,
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([3], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([30], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_recursive_spec_repeated(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2"),
        "value_2": Tag("value_1") * 10,
        "value_3": Tag("value_1") * 11,
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([3], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([30], index=pd.DatetimeIndex([now])),
        "value_3": pd.Series([33], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_recursive_spec_repeated_deep(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2"),
        "value_2": Tag("value_1") * 10,
        "value_3": Tag("C4") * 10,
        "value_4": Tag("value_2") + Tag("value_3"),
        "value_5": Tag("value_4") + Tag("value_1"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "value_1": pd.Series([3], index=pd.DatetimeIndex([now])),
        "value_2": pd.Series([30], index=pd.DatetimeIndex([now])),
        "value_3": pd.Series([40], index=pd.DatetimeIndex([now])),
        "value_4": pd.Series([70], index=pd.DatetimeIndex([now])),
        "value_5": pd.Series([73], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_recursive_cyclic(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("value_2"),
        "value_2": Tag("value_1") * 10,
    }

    with pytest.raises(ValueError):
        TagResolver(value_store).series(specs)


def test_recursive_cyclic_deep(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("value_3"),
        "value_2": Tag("value_1") + 1,
        "value_3": Tag("value_2") * 10,
    }

    with pytest.raises(ValueError):
        TagResolver(value_store).series(specs)


def test_recursive_same_name(value_store):
    specs = {
        "A1": Tag("A1"),
        "A2": Tag("A2"),
        "total": Tag("A1") + Tag("A2"),
    }

    with pytest.raises(ValueError):
        TagResolver(value_store).series(specs)


def test_recursive_same_name_reassigned(value_store):
    specs = {
        "A1": Tag("A1") * 10,
    }

    with pytest.raises(ValueError):
        TagResolver(value_store).series(specs)


def test_literal_value(value_store):
    specs = {
        "A2": 2,
    }

    with mock.patch("cognite_synthetic_tags.tag_resolver.datetime") as m_dt:
        m_dt.utcnow.return_value = now
        value = TagResolver(value_store).series(specs)

    expected = {
        "A2": pd.Series([2], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_literal_value_used_in_formula(value_store):
    specs = {
        "A2": 2,
        "A3": Tag("A2") * 3,
    }

    with mock.patch("cognite_synthetic_tags.tag_resolver.datetime") as m_dt:
        m_dt.utcnow.return_value = now
        value = TagResolver(value_store).series(specs)

    expected = {
        "A2": pd.Series([2], index=pd.DatetimeIndex([now])),
        "A3": pd.Series([6], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_literals_only(value_store):
    specs = {
        "lit1": 11,
        "lit2": 22,
    }

    with mock.patch("cognite_synthetic_tags.tag_resolver.datetime") as m_dt:
        m_dt.utcnow.return_value = now
        value = TagResolver(value_store).series(specs)

    expected = {
        "lit1": pd.Series([11], index=pd.DatetimeIndex([now])),
        "lit2": pd.Series([22], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_empty_specs(value_store):
    specs = {}

    value = TagResolver(value_store).series(specs)

    expected = {}
    assert value == expected


def test_comparators(value_store):
    specs = {
        "A2_status1": Tag("A2") > 1,
        "A2_status2": Tag("A2") > 4,
        "A2_status3": Tag("A2") > 1,
        "A2_status4": Tag("A2") > 4,
        "A2_status5": Tag("A2") >= 2,
        "A2_status6": Tag("A2") <= 2,
        "A2_status7": Tag("A2") >= 1,
        "A2_status8": Tag("A2") >= 4,
        "A2_status9": Tag("A2") <= 1,
        "A2_status10": Tag("A2") <= 4,
        "A2_status11": Tag("A2") == 4,
        "A2_status12": Tag("A2") != 4,
        "A2_status13": Tag("A2") == 2,
        "A2_status14": Tag("A2") != 2,
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "A2_status1": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status2": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status3": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status4": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status5": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status6": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status7": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status8": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status9": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status10": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status11": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status12": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status13": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status14": pd.Series([False], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_reversed_comparators(value_store):
    specs = {
        "A2_status1": 1 < Tag("A2"),
        "A2_status2": 4 < Tag("A2"),
        "A2_status3": 1 > Tag("A2"),
        "A2_status4": 4 > Tag("A2"),
        "A2_status5": 2 <= Tag("A2"),
        "A2_status6": 2 >= Tag("A2"),
        "A2_status7": 1 <= Tag("A2"),
        "A2_status8": 4 <= Tag("A2"),
        "A2_status9": 1 >= Tag("A2"),
        "A2_status10": 4 >= Tag("A2"),
        "A2_status11": 4 == Tag("A2"),
        "A2_status12": 4 != Tag("A2"),
        "A2_status13": 2 == Tag("A2"),
        "A2_status14": 2 != Tag("A2"),
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "A2_status1": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status2": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status3": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status4": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status5": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status6": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status7": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status8": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status9": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status10": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status11": pd.Series([False], index=pd.DatetimeIndex([now])),
        "A2_status12": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status13": pd.Series([True], index=pd.DatetimeIndex([now])),
        "A2_status14": pd.Series([False], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_comparison_after_math(value_store):

    specs = {
        "status1": Tag("A2") * Tag("A3") < 5,
        "status2": Tag("A2") * Tag("A3") > 5,
    }

    value = TagResolver(value_store).series(specs)

    expected = {
        "status1": pd.Series([False], index=pd.DatetimeIndex([now])),
        "status2": pd.Series([True], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_series_math(series_value_store):
    specs = {
        "A3": Tag("A98") + 1,
        "A4": 2 * Tag("A10"),
    }

    value = TagResolver(series_value_store).series(specs)

    expected = {
        "A3": pd.Series([99, 100, 1, 2, 3, 4, 5]),
        "A4": pd.Series([20, 22, 24, 26, 28, 30, 32]),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )


def test_series_math_two_series(series_value_store):
    specs = {
        "A3": Tag("A98") + Tag("A0"),
    }

    value = TagResolver(series_value_store).series(specs)

    expected = {
        "A3": pd.Series([98, 100, 2, 4, 6, 8, 10]),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )


def test_series_math_stuff(series_value_store):
    specs = {
        "A3_combined": Tag("A98") - Tag("A0"),
        "A20_tenfold": 10 * Tag("A20"),
        "A30_even": Tag("A30").calc("is_even"),
    }
    additional_operations = {
        "is_even": lambda a: a % 2 == 0,
    }

    value = TagResolver(series_value_store, additional_operations).series(specs)

    expected = {
        "A3_combined": pd.Series([98, 98, -2, -2, -2, -2, -2]),
        "A20_tenfold": pd.Series([200, 210, 220, 230, 240, 250, 260]),
        "A30_even": pd.Series([True, False, True, False, True, False, True]),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )


def test_series_index_and_literals(series_value_store):
    specs = {
        "lit": 100,
        "calc": Tag("lit") * Tag("A1"),
    }

    value = TagResolver(series_value_store).series(specs)

    expected = {
        "lit": pd.Series([100] * 7),
        "calc": pd.Series([100 * (i + 1) for i in range(7)]),
    }
    assert all(value["calc"] == expected["calc"])
    assert all(value["lit"] == expected["lit"])


def test_series_empty_specs(series_value_store):
    specs = {}

    value = TagResolver(series_value_store).series(specs)

    expected = {}
    assert value == expected


def test_series_bool(series_value_store):
    specs = {
        "value_a": 4 < Tag("A3"),
        "value_b": Tag("B8") > 12,
        "a_or_b": (Tag("A3") > 4) | (Tag("B8") > 12),
    }

    value = TagResolver(series_value_store).series(specs)

    index = pd.Index(range(7))
    expected = {
        "value_a": pd.Series(
            [False, False, True, True, True, True, True],
            index=index,
        ),
        "value_b": pd.Series(
            [False, False, False, False, False, True, True],
            index=index,
        ),
        "a_or_b": pd.Series(
            [False, False, True, True, True, True, True],
            index=index,
        ),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )


def test_multiple_data_stores(value_store, another_value_store):
    specs = {
        "val2": Tag("A2"),
        "val3": Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.series(specs)

    expected = {
        "val2": pd.Series([2], index=pd.DatetimeIndex([now])),
        "val3": pd.Series([3333], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_multiple_data_stores_math(value_store, another_value_store):
    specs = {
        "sumitall": Tag("A2") + Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.series(specs)

    expected = {
        "sumitall": pd.Series([3335], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_multiple_data_stores_tag_name_sum(value_store, another_value_store):
    specs = {
        "val2": Tag("A2"),
        "val3": Tag("A3", "alt_fetch"),
        "sumitall": Tag("A2") + Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.series(specs)

    expected = {
        "val2": pd.Series([2], index=pd.DatetimeIndex([now])),
        "val3": pd.Series([3333], index=pd.DatetimeIndex([now])),
        "sumitall": pd.Series([3335], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_multiple_data_stores_same_tag(value_store, another_value_store):
    specs = {
        "value_2": Tag("A2"),
        "value_3": Tag("A3"),
        "sumitall": Tag("A2") + Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.series(specs)

    expected = {
        "value_2": pd.Series([2], index=pd.DatetimeIndex([now])),
        "value_3": pd.Series([3], index=pd.DatetimeIndex([now])),
        "sumitall": pd.Series([3335], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_multiple_data_stores_same_tag2(value_store, another_value_store):
    specs = {
        "val2": Tag("A2"),
        "val3": Tag("A3", "alt_fetch"),
        "sumitall": Tag("A2") + Tag("A3"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.series(specs)

    expected = {
        "val2": pd.Series([2], index=pd.DatetimeIndex([now])),
        "val3": pd.Series([3333], index=pd.DatetimeIndex([now])),
        "sumitall": pd.Series([5], index=pd.DatetimeIndex([now])),
    }
    assert_frame_equal(pd.DataFrame(value), pd.DataFrame(expected))


def test_reuse_known_tags():
    specs = {
        "value_2": Tag("A2"),
    }

    from cognite_synthetic_tags import CDFStore

    with patch("cognite_synthetic_tags.data_stores.CDFStore.get") as p_get:
        p_get.return_value = {"A2": pd.Series([2], index=[0])}
        resolver = TagResolver(CDFStore(None))
        value = resolver.series(specs)

        assert_frame_equal(
            pd.DataFrame(value),
            pd.DataFrame({"value_2": 2}, index=[0]),
        )
        assert p_get.call_count == 1

        specs2 = {"value_22": Tag("A2") * 11}
        value2 = resolver.series(specs2)

        assert_frame_equal(
            pd.DataFrame(value2),
            pd.DataFrame({"value_22": 22}, index=[0]),
        )
        assert p_get.call_count == 1  # no new calls!


def test_latest_single_value(value_store):
    specs = {
        "value_1": Tag("A1"),
    }

    value = TagResolver(value_store).latest(specs)

    expected = {"value_1": 1}
    assert value == expected


def test_latest_empty(value_store):
    specs = {}

    value = TagResolver(value_store).latest(specs)

    expected = {}
    assert value == expected


def test_latest_multiple(series_value_store):
    specs = {
        "value_1": Tag("A1"),
    }

    value = TagResolver(series_value_store).latest(specs)

    expected = {"value_1": 7}
    assert value == expected
