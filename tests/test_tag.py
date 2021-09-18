from cognite_synthetic_tags import Tag


def test_tag_str():
    tag = Tag("A2")

    value = str(tag)

    expected = "A2"
    assert value == expected


def test_tag_str_with_operator():
    tag = Tag("A2") * Tag("B3")

    value = str(tag)

    expected = "*([A2], [B3])"
    assert value == expected


def test_tag_str_call_with_extension():
    tag = Tag.call("foo", Tag("A2"), Tag("B3"))

    value = str(tag)

    expected = "foo([A2], [B3])"
    assert value == expected


def test_tag_str_call_with_comparison_operator():
    tag = Tag("A2") > Tag("B3")

    value = str(tag)

    expected = "gt([A2], [B3])"
    assert value == expected


def test_tag_str_call_with_literal_function():
    def foobar(a, b):
        ...

    tag = Tag.call(foobar, Tag("A2"), Tag("B3"))

    value = str(tag)

    expected = "foobar([A2], [B3])"
    assert value == expected


def test_tag_str_calc_with_extension():
    tag = Tag("A2").calc("foo")

    value = str(tag)

    expected = "foo([A2])"
    assert value == expected


def test_tag_str_calc_with_literal_function():
    def foobar(a, b):
        ...

    tag = Tag("A2").calc(foobar)

    value = str(tag)

    expected = "foobar([A2])"
    assert value == expected
