import pytest

from cognite_synthetic_tags import Tag
from cognite_synthetic_tags.tag import UnsupportedOperationError


def test_tag_str():
    tag = Tag("A2")

    value = str(tag)

    expected = "A2"
    assert value == expected


def test_tag_str_with_infix_operator():
    tag = Tag("A2") * Tag("B3")

    value = str(tag)

    expected = "A2 × B3"
    assert value == expected


def test_tag_str_with_infix_operator2():
    tag = Tag("A2") & Tag("B3")

    value = str(tag)

    expected = "A2 and B3"
    assert value == expected


def test_tag_str_with_prefix_operator():
    tag = ~Tag("A2")

    value = str(tag)

    expected = "not(A2)"
    assert value == expected


def test_tag_str_apply_with_extension():
    tag = Tag.apply("foo", Tag("A2"), Tag("B3"))

    value = str(tag)

    expected = "foo(A2, B3)"
    assert value == expected


def test_tag_str_apply_with_comparison_operator():
    tag = Tag("A2") > Tag("B3")

    value = str(tag)

    expected = "A2 > B3"
    assert value == expected


def test_tag_str_apply_with_literal_function():
    def foobar(a, b): ...

    tag = Tag.apply(foobar, Tag("A2"), Tag("B3"))

    value = str(tag)

    expected = "foobar(A2, B3)"
    assert value == expected


def test_tag_str_calc_with_extension():
    tag = Tag("A2").calc("foo")

    value = str(tag)

    expected = "foo(A2)"
    assert value == expected


def test_tag_str_calc_with_literal_function():
    def foobar(a, b): ...

    tag = Tag("A2").calc(foobar)

    value = str(tag)

    expected = "foobar(A2)"
    assert value == expected


def test_tag_str_calc():
    tag = Tag("A2") * Tag("B3") + Tag("C4")

    value = str(tag)

    expected = "A2 × B3 + C4"
    assert value == expected


def test_tag_str_calc_foo():
    def foo(*a): ...

    tag = Tag.apply(foo, Tag("A2") * Tag("B3") + 2 * Tag("C4"), Tag("D5")) + 4

    value = str(tag)

    expected = "foo(A2 × B3 + 2 × C4, D5) + 4"
    assert value == expected


def test_tag_str_reverse_oper_add():
    tag = 2 + Tag("B3")

    value = str(tag)

    expected = "2 + B3"
    assert value == expected


def test_tag_str_reverse_oper_sub():
    tag = 2 - Tag("B3")

    value = str(tag)

    expected = "2 - B3"
    assert value == expected


def test_tag_str_reverse_oper_and():
    tag = 1 & Tag("B3")

    value = str(tag)

    expected = "1 and B3"
    assert value == expected


def test_tag_str_reverse_oper_or():
    tag = 2 | Tag("B3")

    value = str(tag)

    expected = "2 or B3"
    assert value == expected


def test_tag_str_reverse_oper_xor():
    tag = 2 ^ Tag("B3")

    value = str(tag)

    expected = "2 xor B3"
    assert value == expected


def test_tag_str_uft8_ne():
    tag = 2 != Tag("B3")

    value = str(tag)

    expected = "B3 ≠ 2"  # reversed, can't do much about that
    assert value == expected


def test_tag_bool_wrong_bool():
    with pytest.raises(UnsupportedOperationError):
        bool(Tag("A3"))


def test_tag_bool_wrong_and():
    with pytest.raises(UnsupportedOperationError):
        Tag("A3") and Tag("A4")


def test_tag_bool_wrong_or():
    with pytest.raises(UnsupportedOperationError):
        Tag("A3") or Tag("A4")


def test_tag_bool_wrong_chained_comparison():
    with pytest.raises(UnsupportedOperationError):
        1 < Tag("A3") < 5


def test_tag_bool_wrong_precedence():
    with pytest.raises(UnsupportedOperationError):
        Tag("A3") < 5 & Tag("B2") > 7


def test_tag_bool_allowed(env_allow_bool, caplog):
    value = bool(Tag("A3"))
    assert value is True
    assert caplog.text.startswith("WARNING")
    expected_parts = [
        (
            "Tag instances do not support boolean operators (e.g. 'and', 'or')."
            " Instead, use bitwise equivalents ('&', '|')."
        ),
        "Tag: A3",
        "There are many ways to get this error, some include:",
    ]
    for part in expected_parts:
        assert part in caplog.text


def test_tag_bool_allowed_silent(env_allow_bool_silent, caplog):
    value = bool(Tag("A3"))
    assert value is True
    assert caplog.text == ""
