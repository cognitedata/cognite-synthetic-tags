import hashlib
import math

from cognite_synthetic_tags import Tag, TagResolver

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
        "value_3": Tag.or_(Tag("A2"), Tag("B3")),
        "value_4": Tag.or_(Tag("A0"), Tag("B3")),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 3,
        "value_2": 0,
        "value_3": 2,
        "value_4": 3,
    }
    assert value == expected


def test_bitwise_logic(value_store):
    specs = {
        "value_1": Tag("A7") & Tag("A3"),
        "value_2": Tag("A8") & Tag("A3"),
        "value_3": Tag("A8") | Tag("A1"),
        "value_4": Tag("A9") | Tag("A1"),
        "value_5": Tag("A9") ^ Tag("A1"),
        "value_6": 9 | Tag("A1"),
        "value_7": 9 ^ Tag("A1"),
        "value_8": 7 & Tag("A3"),
    }

    value = TagResolver(value_store).resolve(specs)

    expected = {
        "value_1": 3,
        "value_2": 0,
        "value_3": 9,
        "value_4": 9,
        "value_5": 8,
        "value_6": 9,
        "value_7": 8,
        "value_8": 3,
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
        "value_2": Tag("A2").calc("md5"),
    }
    additional_operations = {
        "foobar": lambda a, b: str(a + b) * 3,
        "md5": lambda a: hashlib.md5(str(a).encode()).hexdigest(),
    }

    value = TagResolver(value_store, additional_operations).resolve(specs)

    expected = {
        "value_1": "424242",
        "value_2": "c81e728d9d4c2f636f067f89cc14862c",
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
