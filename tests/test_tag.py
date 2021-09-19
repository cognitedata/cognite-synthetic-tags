from cognite_synthetic_tags import Tag


def test_tag_str():
    tag = Tag("A2")

    value = str(tag)

    expected = "A2"
    assert value == expected


def test_tag_str_with_infix_operator():
    tag = Tag("A2") * Tag("B3")

    value = str(tag)

    expected = "([A2] * [B3])"
    assert value == expected


def test_tag_str_with_infix_operator2():
    tag = Tag("A2") & Tag("B3")

    value = str(tag)

    expected = "([A2] and [B3])"
    assert value == expected


def test_tag_str_with_prefix_operator():
    tag = ~Tag("A2")

    value = str(tag)

    expected = "not([A2])"
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


def test_tag_bool_wrong_bool():
    try:
        bool(Tag("A3"))
    except ValueError as exc:
        exc.args[0].startswith("Tag instances do not support boolean operators")
    else:
        assert False, "Expected ValueError not raised!"


def test_tag_bool_wrong_and():
    try:
        Tag("A3") and Tag("A4")
    except ValueError as exc:
        exc.args[0].startswith("Tag instances do not support boolean operators")
    else:
        assert False, "Expected ValueError not raised!"


def test_tag_bool_wrong_or():
    try:
        Tag("A3") or Tag("A4")
    except ValueError as exc:
        exc.args[0].startswith("Tag instances do not support boolean operators")
    else:
        assert False, "Expected ValueError not raised!"


def test_tag_bool_wrong_chained_comparison():
    try:
        1 < Tag("A3") < 5
    except ValueError as exc:
        exc.args[0].startswith("Tag instances do not support boolean operators")
    else:
        assert False, "Expected ValueError not raised!"


def test_tag_bool_wrong_precedence():
    try:
        Tag("A3") < 5 & Tag("B2") > 7
    except ValueError as exc:
        exc.args[0].startswith("Tag instances do not support boolean operators")
    else:
        assert False, "Expected ValueError not raised!"
