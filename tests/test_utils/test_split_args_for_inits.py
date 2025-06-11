"""This file contains tests for the functions, classes, and decorators
in the split_args_for_inits module."""

from python_template.utils import (
    SplitInitMixin,
    auto_split_init,
    split_args_for_inits_strict_kwargs,
)


class A:  # pylint: disable=too-few-public-methods
    """Test class A."""

    def __init__(self, a1, a2=0, **kwargs):
        print(f"A init: a1={a1}, a2={a2}, kwargs={kwargs}")
        self.a1 = a1
        self.a2 = a2


class B:  # pylint: disable=too-few-public-methods
    """Test class B."""

    def __init__(self, b1, b2=0):
        print(f"B init: b1={b1}, b2={b2}")
        self.b1 = b1
        self.b2 = b2


class C(SplitInitMixin, A, B):  # pylint: disable=too-few-public-methods
    """Test class C. For use of the mixin class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(
            f"C leftovers: {self._init_leftovers}"  # pylint: disable=no-member
        )


@auto_split_init
class D(A, B):  # pylint: disable=too-few-public-methods
    """Test class D. For use of the decorator."""

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=super-init-not-called,unused-argument
        print(
            f"D leftovers: {self._init_leftovers}"  # pylint: disable=no-member
        )


class E(A, B):  # pylint: disable=too-few-public-methods
    """Test class E. For use of the function."""

    def __init__(self, *args, **kwargs):
        self.split = split_args_for_inits_strict_kwargs(
            type(self), args, kwargs
        )
        A.__init__(self, *self.split[A]["args"], **self.split[A]["kwargs"])
        B.__init__(self, *self.split[B]["args"], **self.split[B]["kwargs"])
        print(f"E leftovers: {self.split['leftovers']}")


def test_split_args_for_inits_strict_kwargs():
    """Tests the split_args_for_inits_strict_kwargs function."""
    # print("\n=== Function Test ===")
    a1 = "a"
    b1 = "b"
    extra = 987
    zero = 0
    e = E(a1=a1, b1=b1, extra=extra)
    # === Function Test ===
    # A init: a1=a, a2=0, kwargs={}
    # B init: b1=b, b2=0
    # E leftovers: {'args': [], 'kwargs': {'extra': 987}}
    assert e.a1 == a1
    assert e.a2 == zero
    assert e.b1 == b1
    assert e.b2 == zero
    assert e.split["leftovers"]["kwargs"]["extra"] == extra


def test_split_init_mixin():
    """Tests the SplitInitMixin class."""
    a1 = "foo"
    b1 = "bar"
    extra = 123
    zero = 0
    # print("\n=== Mixin Test ===")
    c = C(a1=a1, b1=b1, extra=extra)
    # === Mixin Test ===
    # A init: a1=foo, a2=0, kwargs={}
    # B init: b1=bar, b2=0
    # C leftovers: {'args': [], 'kwargs': {'extra': 123}}
    assert c.a1 == a1
    assert c.a2 == zero
    assert c.b1 == b1
    assert c.b2 == zero
    # assert c.split["leftovers"]["kwargs"]["extra"] == extra


def test_auto_split_init():
    """Tests the auto_split_init decoarator."""
    a1 = "x"
    b1 = "y"
    extra = 456
    zero = 0
    # print("\n=== Decorator Test ===")
    d = D(a1=a1, b1=b1, extra=extra)
    # === Decorator Test ===
    # A init: a1=x, a2=0, kwargs={}
    # B init: b1=y, b2=0
    # D leftovers: {'args': [], 'kwargs': {'extra': 456}}
    assert d.a1 == a1
    assert d.a2 == zero
    assert d.b1 == b1
    assert d.b2 == zero
    # assert d.split["leftovers"]["kwargs"]["extra"] == extra


# if __name__ == "__main__":
#     test_split_args_for_inits_strict_kwargs()
#     test_split_init_mixin()
#     test_auto_split_init()
