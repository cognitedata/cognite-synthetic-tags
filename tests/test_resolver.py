import math
from unittest.mock import patch

import pandas as pd

from cognite_synthetic_tags import Tag, TagResolver, latest_datapoint

from ._utils import *  # noqa


def test_regular_tag(value_store):
    specs = {
        "value_1": Tag("A1"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {"value_1": 1}
    assert value == expected
    value_store.assert_called_once_with({"A1"})


def test_regular_tags(value_store):
    specs = {
        "value_1": Tag("A1"),
        "value_2": Tag("B2"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {"value_1": 1, "value_2": 2}
    assert value == expected
    value_store.assert_called_once_with({"A1", "B2"})


def test_synthetic_tag(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2") * Tag("B3"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {"value_1": 7}
    assert value == expected
    value_store.assert_called_once_with({"A1", "B2", "B3"})


def test_synthetic_tags(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2") * Tag("B3"),
        "value_2": Tag("A10") + Tag("B2") + Tag("C300"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {"value_1": 7, "value_2": 312}
    assert value == expected
    value_store.assert_called_once_with({"A1", "B2", "B3", "A10", "C300"})


def test_arithmetic_operations(value_store):
    specs = {
        "value_1": 10 * Tag("A2"),
        "value_2": 0 + Tag("A10") + (1 + Tag("A2")) - 1 + Tag("C300") * 100,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {"value_1": 20, "value_2": 30012}
    assert value == expected
    value_store.assert_called_once_with({"A2", "A10", "C300"})


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

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 5,
        "value_2": 13,
        "value_3": -9,
        "value_4": 10,
        "value_5": 9,
        "value_6": 27,
        "value_7": 2,
        "value_8": 2,
        "value_9": 4,
    }
    assert value == expected


def test_math_functions(value_store):
    specs = {
        "value_1": Tag.sin(Tag("A2")),
        "value_2": Tag.ceil(Tag("A11") / 2),
        "value_3": Tag.floor(Tag("A11") / 2),
        "value_4": Tag.log10(Tag("X100")),
        "value_5": Tag.log(Tag("X64"), Tag("B4")),
        "value_6": Tag.cos(Tag("P0")),
        "value_7": Tag.tan(Tag("P1")),
        "value_8": Tag.log2(Tag("X16")),
        "value_9": Tag.sqrt(Tag("X9")),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": math.sin(2),
        "value_2": math.ceil(11 / 2),
        "value_3": math.floor(11 / 2),
        "value_4": math.log10(100),
        "value_5": math.log(64, 4),
        "value_6": math.cos(0),
        "value_7": math.tan(1),
        "value_8": math.log2(16),
        "value_9": math.sqrt(9),
    }
    assert value == expected


def test_boolean_logic(value_store):
    specs = {
        "value_1": Tag.bool(Tag("A2")),
        "value_2": Tag.bool(Tag("A0")),
        "value_3": Tag.not_(Tag("A3")),
        "value_4": Tag.not_(Tag("A0")),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": True,
        "value_2": False,
        "value_3": False,
        "value_4": True,
    }
    assert value == expected
    assert all([isinstance(val, bool) for val in value.values()])


def test_boolean_operators(value_store):
    specs = {
        "value_1": Tag.and_(Tag("A2"), Tag("B3")),
        "value_2": Tag.and_(Tag("A0"), Tag("B3")),
        "value_3": Tag.or_(Tag("A0"), Tag("B0")),
        "value_4": Tag.or_(Tag("A0"), Tag("B3")),
        "value_5": Tag.xor_(Tag("A0"), Tag("B3")),
        "value_6": Tag.xor_(Tag("A2"), Tag("B3")),
        "value_7": Tag.not_(Tag("A0")),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": True,
        "value_2": False,
        "value_3": False,
        "value_4": True,
        "value_5": True,
        "value_6": False,
        "value_7": True,
    }
    assert value == expected


def test_bitwise_logic(value_store):
    specs = {
        "value_1": Tag("A2") & Tag("B3"),
        "value_2": Tag("A0") & Tag("B3"),
        "value_3": Tag("A0") | Tag("B0"),
        "value_4": Tag("A0") | Tag("B3"),
        "value_5": Tag("A0") ^ Tag("B3"),
        "value_6": Tag("A2") ^ Tag("B3"),
        "value_7": ~Tag("A0"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": True,
        "value_2": False,
        "value_3": False,
        "value_4": True,
        "value_5": True,
        "value_6": False,
        "value_7": True,
    }
    assert value == expected


def test_calc(value_store):
    specs = {
        "value_1": Tag("A2").calc("+", 40),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 42,
    }
    assert value == expected


def test_calc_custom_operation(value_store):
    specs = {
        "value_1": Tag("A2").calc("foobar", 40),
        "value_2": Tag("A2").calc("is_even"),
    }
    additional_operations = {
        "foobar": lambda a, b: str(a + b) * 3,
        "is_even": lambda a: a % 2 == 0,
    }

    value = TagResolver(value_store, additional_operations).resolve(specs)

    expected = {
        "value_1": "424242",
        "value_2": True,
    }
    assert value == expected


def test_call_custom_operation(value_store):
    specs = {
        "value_1": Tag.call("max", Tag("A2"), Tag("B7")),
        "value_2": Tag.call("max", Tag("A2") * 11, Tag("B7")),
    }
    additional_operations = {"max": max}

    value = TagResolver(value_store, additional_operations).resolve(specs)

    expected = {
        "value_1": 7,
        "value_2": 22,
    }
    assert value == expected


def test_call_literal_functions(value_store):
    def foo(a, b):
        return f"{a} and {b}"

    specs = {
        "value_1": Tag.call(foo, Tag("A2"), Tag("B7")),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": "2 and 7",
    }
    assert value == expected


def test_calc_literal_functions(value_store):
    def foo(a):
        return f"foo of {a}"

    specs = {"value_1": Tag("A2").calc(foo)}

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": "foo of 2",
    }
    assert value == expected


def test_recursive_spec(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2"),
        "value_2": Tag("value_1") * 10,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 3,
        "value_2": 30,
    }
    assert value == expected


def test_recursive_spec_repeated(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2"),
        "value_2": Tag("value_1") * 10,
        "value_3": Tag("value_1") * 11,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 3,
        "value_2": 30,
        "value_3": 33,
    }
    assert value == expected


def test_recursive_spec_repeated_deep(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("B2"),
        "value_2": Tag("value_1") * 10,
        "value_3": Tag("C4") * 10,
        "value_4": Tag("value_2") + Tag("value_3"),
        "value_5": Tag("value_4") + Tag("value_1"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 3,
        "value_2": 30,
        "value_3": 40,
        "value_4": 70,
        "value_5": 73,
    }
    assert value == expected


def test_recursive_cyclic(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("value_2"),
        "value_2": Tag("value_1") * 10,
    }

    try:
        TagResolver(value_store).resolve(specs)
    except ValueError as exc:
        assert "Cyclic definition of tags with" in exc.args[0]
    else:
        assert False, "Exception not raised"


def test_recursive_cyclic_deep(value_store):
    specs = {
        "value_1": Tag("A1") + Tag("value_3"),
        "value_2": Tag("value_1") + 1,
        "value_3": Tag("value_2") * 10,
    }

    try:
        TagResolver(value_store).resolve(specs)
    except ValueError as exc:
        assert "Cyclic definition of tags with" in exc.args[0]
    else:
        assert False, "Exception not raised"


def test_recursive_same_name(value_store):
    specs = {
        "A1": Tag("A1"),
        "A2": Tag("A2"),
        "total": Tag("A1") + Tag("A2"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "A1": 1,
        "A2": 2,
        "total": 3,
    }
    assert value == expected


def test_recursive_same_name_reassigned(value_store):
    specs = {
        "A1": Tag("A1") * 10,
    }

    try:
        TagResolver(value_store).resolve(specs)
    except ValueError as exc:
        assert "Cyclic definition of tags" in exc.args[0]
    else:
        assert False, "Exception not raised"


def test_literal_value(value_store):
    specs = {
        "A2": 2,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "A2": 2,
    }
    assert value == expected


def test_literal_value_used_in_formula(value_store):
    specs = {
        "A2": 2,
        "A3": Tag("A2") * 3,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "A2": 2,
        "A3": 6,
    }
    assert value == expected


def test_literals_only(value_store):
    specs = {
        "lit1": 11,
        "lit2": 22,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "lit1": 11,
        "lit2": 22,
    }
    assert value == expected


def test_empty_specs(value_store):
    specs = {}

    value = TagResolver(value_store).resolve(specs)

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

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "A2_status1": True,
        "A2_status2": False,
        "A2_status3": True,
        "A2_status4": False,
        "A2_status5": True,
        "A2_status6": True,
        "A2_status7": True,
        "A2_status8": False,
        "A2_status9": False,
        "A2_status10": True,
        "A2_status11": False,
        "A2_status12": True,
        "A2_status13": True,
        "A2_status14": False,
    }
    assert value == expected


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

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "A2_status1": True,
        "A2_status2": False,
        "A2_status3": False,
        "A2_status4": True,
        "A2_status5": True,
        "A2_status6": True,
        "A2_status7": True,
        "A2_status8": False,
        "A2_status9": False,
        "A2_status10": True,
        "A2_status11": False,
        "A2_status12": True,
        "A2_status13": True,
        "A2_status14": False,
    }
    assert value == expected


def test_comparison_after_math(value_store):

    specs = {
        "status1": Tag("A2") * Tag("A3") < 5,
        "status2": Tag("A2") * Tag("A3") > 5,
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "status1": False,
        "status2": True,
    }
    assert value == expected


def test_series_math(series_value_store):
    specs = {
        "A3": Tag("A98") + 1,
        "A4": 2 * Tag("A10"),
    }

    value = TagResolver(series_value_store).resolve(specs)

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

    value = TagResolver(series_value_store).resolve(specs)

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

    value = TagResolver(series_value_store, additional_operations).resolve(
        specs
    )

    expected = {
        "A3_combined": pd.Series([98, 98, -2, -2, -2, -2, -2]),
        "A20_tenfold": pd.Series([200, 210, 220, 230, 240, 250, 260]),
        "A30_even": pd.Series([True, False, True, False, True, False, True]),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )


def test_series_trig(series_value_store):
    specs = {
        "sin_of_A0": Tag.sin(Tag("A0")),
    }

    value = TagResolver(series_value_store).resolve(specs)

    expected = {
        "sin_of_A0": pd.Series([math.sin(i) for i in range(7)]),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )


def test_series_index_and_literals(series_value_store):
    specs = {
        "lit": 100,
        "calc": Tag("lit") * Tag("A1"),
    }

    value = TagResolver(series_value_store).resolve(specs)

    expected = {
        "lit": pd.Series([100 for _ in range(7)]),
        "calc": pd.Series([100 * (i + 1) for i in range(7)]),
    }
    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )
    assert all(value["lit"].index == value["calc"].index)
    assert len(value["lit"].index) == 7


def test_series_only_literals(series_value_store):
    specs = {
        "lit1": 11,
        "lit2": 22,
    }

    value = TagResolver(series_value_store).resolve(specs)

    expected = {
        "lit1": pd.Series([11] * 7, index=pd.Index(range(7))),
        "lit2": pd.Series([22] * 7, index=pd.Index(range(7))),
    }

    assert expected.keys() == value.keys() and all(
        all(value[key] == expected[key]) for key in expected
    )
    assert len(value["lit1"].index) == 7


def test_series_empty_specs(series_value_store):
    specs = {}

    value = TagResolver(series_value_store).resolve(specs)

    expected = {}
    assert value == expected


def test_series_bool(series_value_store):
    specs = {
        "value_a": 4 < Tag("A3"),
        "value_b": Tag("B8") > 12,
        "a_or_b": (Tag("A3") > 4) | (Tag("B8") > 12),
    }

    value = TagResolver(series_value_store).resolve(specs)

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
        "A2": Tag("A2"),
        "A3": Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.resolve(specs)

    expected = {
        "A2": 2,
        "A3": 3333,
    }
    assert value == expected


def test_multiple_data_stores_math(value_store, another_value_store):
    specs = {
        "sumitall": Tag("A2") + Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.resolve(specs)

    expected = {
        "sumitall": 3335,
    }
    assert value == expected


def test_multiple_data_stores_tag_name_sum(value_store, another_value_store):
    specs = {
        "A2": Tag("A2"),
        "A3": Tag("A3", "alt_fetch"),
        "sumitall": Tag("A2") + Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.resolve(specs)

    expected = {
        "A2": 2,
        "A3": 3333,
        "sumitall": 3335,
    }
    assert value == expected


def test_multiple_data_stores_same_tag(value_store, another_value_store):
    specs = {
        "value_2": Tag("A2"),
        "value_3": Tag("A3"),
        "sumitall": Tag("A2") + Tag("A3", "alt_fetch"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.resolve(specs)

    expected = {
        "value_2": 2,
        "value_3": 3,
        "sumitall": 3335,
    }
    assert value == expected


def test_multiple_data_stores_same_tag2(value_store, another_value_store):
    specs = {
        "A2": Tag("A2"),
        "A3": Tag("A3", "alt_fetch"),
        "sumitall": Tag("A2") + Tag("A3"),
    }

    resolver = TagResolver(value_store, alt_fetch=another_value_store)
    value = resolver.resolve(specs)

    expected = {
        "A2": 2,
        "A3": 3333,
        "sumitall": 5,
    }
    assert value == expected


def test_reuse_known_tags():
    specs = {
        "value_2": Tag("A2"),
    }

    def retrieve(tags):
        return latest_datapoint(
            client="mock_client",
            start="mock_start",
            end="mock_end",
        )(tags)

    with patch(
        "cognite_synthetic_tags.data_stores.retrieve_datapoints_df"
    ) as p_retrieve_dp_df:
        p_retrieve_dp_df.return_value = pd.DataFrame({"A2": 2}, index=[0])
        resolver = TagResolver(retrieve)
        value = resolver.resolve(specs)

        assert value == {"value_2": 2}
        assert p_retrieve_dp_df.call_count == 1

        specs2 = {"value_22": Tag("A2") * 11}
        value2 = resolver.resolve(specs2)
        p_retrieve_dp_df.return_value = 22

        assert value2 == {"value_22": 22}
        assert p_retrieve_dp_df.call_count == 1  # no new calls!
