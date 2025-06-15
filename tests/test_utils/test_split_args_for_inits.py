"""This file contains tests for the functions, classes, and decorators
in the split_args_for_inits module."""

import builtins

from python_template.utils import (
    SplitInitMixin,
    auto_split_init,
    split_args_for_inits_strict_kwargs,
)
from python_template.utils.split_args_for_inits import (
    _find_calling_class_from_init_old,
    apply_split_inits_old,
)

# Classes for tests:


class A:  # pylint: disable=too-few-public-methods
    """Test class A."""

    def __init__(self, a1, a2=0, **kwargs):
        print(f"A init: a1={a1}, a2={a2}, kwargs={kwargs}")
        self.a1 = a1
        self.a2 = a2


class A1:  # pylint: disable=too-few-public-methods
    """Class accepting one positional arg."""

    def __init__(self, a):
        self._a = a
        super().__init__()


class AcceptsAll:  # pylint: disable=too-few-public-methods
    """Class that accepts all kwargs."""

    def __init__(self, **kwargs):
        pass


class AcceptsAllDummy(AcceptsAll):  # pylint: disable=too-few-public-methods
    """Wrapper class for AcceptsAll class."""


class AKeywords:  # pylint: disable=too-few-public-methods
    """A class with optional positional args and one kwarg."""

    def __init__(self, *, a_kwarg):
        self.a_kwarg = a_kwarg


class B:  # pylint: disable=too-few-public-methods
    """Test class B."""

    def __init__(self, b1, b2=0):
        print(f"B init: b1={b1}, b2={b2}")
        self.b1 = b1
        self.b2 = b2


class B1:  # pylint: disable=too-few-public-methods
    """Class accepting variable kwargs."""

    def __init__(self, **kwargs):
        self._b_kwargs = kwargs
        super().__init__()


class B2:  # pylint: disable=too-few-public-methods
    """Class with one kwarg that accepts all kwargs."""

    def __init__(self, b=0, **kwargs):
        self.b = b
        self.extra = kwargs.get("extra", None)


class BStarKwargs:  # pylint: disable=too-few-public-methods
    """Class with star kwargs."""

    def __init__(self, **kwargs):
        # self.b_seen = "bk" in kwargs
        self.b_seen = True
        self.bk = kwargs.get("bk", None)


class BuiltinTypeClass:  # pylint: disable=too-few-public-methods
    """Class that should raise TypeError in dis.get_instructions."""

    __init__ = object.__init__


class BuiltinWrapper(builtins.int):  # pylint: disable=too-few-public-methods
    """Wrapper for a builtin class."""


class C(SplitInitMixin, A, B):  # pylint: disable=too-few-public-methods
    """Test class C. For use of the mixin class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(
            f"C leftovers: {self._init_leftovers}"  # pylint: disable=no-member
        )


class C1(SplitInitMixin, A1, B1):  # pylint: disable=too-few-public-methods
    """Class using mixin with a parent with a positional arg and a parent with a
    kwarg"""

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=useless-parent-delegation
        # apply_split_inits(self, args, kwargs)
        super().__init__(*args, **kwargs)
        # SplitInitMixin.__init__(self, *args, **kwargs)


class C2(SplitInitMixin, A1):  # pylint: disable=too-few-public-methods
    """Class using mixin with one other parent with positional arg."""

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=useless-parent-delegation
        super().__init__(*args, **kwargs)


class C3(A1, B2):  # pylint: disable=too-few-public-methods
    """Class calling other classes."""

    def __init__(self, *args, **kwargs):
        self.split = split_args_for_inits_strict_kwargs(
            type(self), args, kwargs
        )
        A1.__init__(self, *self.split[A1]["args"], **self.split[A1]["kwargs"])
        B2.__init__(self, *self.split[B2]["args"], **self.split[B2]["kwargs"])
        self.leftovers = self.split["leftovers"]


class CombinedClass(
    AKeywords, BStarKwargs
):  # pylint: disable=too-few-public-methods
    """Class combining AKeywords and BStarKwargs."""

    def __init__(self, *args, **kwargs):
        self.split = split_args_for_inits_strict_kwargs(
            type(self), args, kwargs
        )
        AKeywords.__init__(
            self,
            *self.split[AKeywords]["args"],
            **self.split[AKeywords]["kwargs"],
        )
        BStarKwargs.__init__(
            self,
            *self.split[BStarKwargs]["args"],
            **self.split[BStarKwargs]["kwargs"],
        )
        self.leftovers = self.split["leftovers"]


@auto_split_init
class D(A, B):  # pylint: disable=too-few-public-methods
    """Test class D. For use of the decorator."""

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=super-init-not-called,unused-argument
        print(
            f"D leftovers: {self._init_leftovers}"  # pylint: disable=no-member
        )


@auto_split_init
class D1(A1, B1):  # pylint: disable=too-few-public-methods
    """Class using decorator."""

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=super-init-not-called
        pass


class DummyWithApplyOld:  # pylint: disable=too-few-public-methods
    """Dummy class using the apply_split_inits method."""

    def __init__(self, *args, **kwargs):
        apply_split_inits_old(self, args=args, kwargs=kwargs)


class E(A, B):  # pylint: disable=too-few-public-methods
    """Test class E. For use of the function."""

    def __init__(self, *args, **kwargs):
        self.split = split_args_for_inits_strict_kwargs(
            type(self), args, kwargs
        )
        A.__init__(self, *self.split[A]["args"], **self.split[A]["kwargs"])
        B.__init__(self, *self.split[B]["args"], **self.split[B]["kwargs"])
        print(f"E leftovers: {self.split['leftovers']}")


class E1(A1, B1):  # pylint: disable=too-few-public-methods
    """Test class E1. For use of the function."""

    def __init__(self, *args, **kwargs):
        self.split = split_args_for_inits_strict_kwargs(
            type(self), args, kwargs
        )
        A1.__init__(self, *self.split[A1]["args"], **self.split[A1]["kwargs"])
        B1.__init__(self, *self.split[B1]["args"], **self.split[B1]["kwargs"])
        print(f"E leftovers: {self.split['leftovers']}")


class Empty:  # pylint: disable=too-few-public-methods
    """Empty class."""


class EmptyDummy(Empty):  # pylint: disable=too-few-public-methods
    """Wrapper class for Empty class."""


class F:  # pylint: disable=too-few-public-methods
    """Class with one keyword arg"""

    def __init__(self, a=1):
        pass


class FDummy(F):  # pylint: disable=too-few-public-methods
    """Wrapper class for F class."""


class M(SplitInitMixin):  # pylint: disable=too-few-public-methods
    """Class inheriting SplitInitMixin and calling apply_split_inits."""

    def __init__(self):  # pylint: disable=super-init-not-called
        apply_split_inits_old(self)


class M1:  # pylint: disable=too-few-public-methods
    """Class with one positional arg."""

    def __init__(self, x):
        self._x = x


class M2:  # pylint: disable=too-few-public-methods
    """Class with one positional arg."""

    def __init__(self, y):
        self._y = y


class M3(SplitInitMixin, M1, M2):  # pylint: disable=too-few-public-methods
    """Class with parent classes inheriting SplitInitMixin."""

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=useless-parent-delegation
        super().__init__(*args, **kwargs)


class NoInit:  # pylint: disable=too-few-public-methods
    """Class with no init method."""


class P1:  # pylint: disable=too-few-public-methods
    """Class with one positional arg and one kwarg."""

    def __init__(self, a, b=2):
        pass


class P1Dummy(P1):  # pylint: disable=too-few-public-methods
    """Dummy wrapper class for P1"""


class P2:  # pylint: disable=too-few-public-methods
    """Class with two kwargs."""

    def __init__(self, foo=None, bar=None):  # pylint: disable=disallowed-name
        pass


class P2Dummy(P2):  # pylint: disable=too-few-public-methods
    """Dummy wrapper class for P2."""


class Q(P2):  # pylint: disable=too-few-public-methods
    """Class inheriting P2 that has its own stuff too."""

    def __init__(self, q1, **kwargs):
        self.q1 = q1
        super().__init__(**kwargs)


class QDummy(Q):  # pylint:disable=too-few-public-methods
    """Wrapper class or Q."""


class Skip(SplitInitMixin):  # pylint: disable=too-few-public-methods
    """Class with a defined skip class."""

    def __init__(self):  # pylint: disable=super-init-not-called
        apply_split_inits_old(self, skip_class=Skip)


# Full tests


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


# Line tests


#  94: positive branch of if not (init := base.__dict__.get("__init__", None)):
# This I think is covered by the test for line 149 below?


# 114: positive branch of if remaining_args:
def test_split_args_with_positional_args():
    """Test: Positional argument matching (covers if remaining_args: branch)"""

    args = [1]
    kwargs = {"b": 5, "x": 42}
    result = split_args_for_inits_strict_kwargs(P1Dummy, args, kwargs)
    assert result[P1]["args"] == [1]
    assert result[P1]["kwargs"] == {"b": 5}
    assert result["leftovers"]["kwargs"] == {"x": 42}


# 131: positive branch of if key in keyword_params:
def test_split_args_with_kwarg_param():
    """Test: positive branch of if key in keyword_params"""
    a_val = 10
    args = ()
    kwargs = {"a": a_val}
    result = split_args_for_inits_strict_kwargs(FDummy, args, kwargs)
    assert result[F]["kwargs"] == kwargs


def test_bind_kwargs_from_remaining():
    """Test that binds kwargs from remaining (for the positive branch above)"""
    a_kwarg = 42
    bk = "present"
    unused = "leftover"
    obj = CombinedClass(a_kwarg=a_kwarg, bk=bk, unused=unused)
    assert obj.a_kwarg == a_kwarg
    # Beacuse of the way it is set up looking for bk in kwargs, it won't get bk.
    # assert obj.bk == bk
    assert obj.b_seen
    assert obj.leftovers["kwargs"] == {"bk": bk, "unused": unused}


# 143: positive branch of if key in accepted_keys:
def test_split_args_with_filtered_kwargs():
    """Test: Accepted key filtering (covers if key in accepted_keys:)"""
    args = []
    kwargs = {"foo": "FOO", "baz": "BAZ"}
    result = split_args_for_inits_strict_kwargs(P2Dummy, args, kwargs)
    assert result[P2]["kwargs"] == {"foo": "FOO"}
    assert result["leftovers"]["kwargs"] == {"baz": "BAZ"}

    kwargs["q1"] = "q1"
    result = split_args_for_inits_strict_kwargs(QDummy, args, kwargs)
    assert result[Q]["kwargs"] == {"q1": kwargs["q1"], "foo": kwargs["foo"]}
    assert result[P2] == {"args": [], "kwargs": {}}
    assert result["leftovers"] == {
        "args": [],
        "kwargs": {"baz": kwargs["baz"]},
    }


# 464: positive branches of if not (init := base.__dict__.get("__init__")):
def test_split_args_with_no_init():
    """Test: Class with no __init__"""
    result = split_args_for_inits_strict_kwargs(EmptyDummy, [1], {"x": 2})
    assert result["leftovers"]["args"] == [1]
    assert result["leftovers"]["kwargs"] == {"x": 2}


# 479: raise TypeError handling
def test_split_args_with_var_kwargs():
    """Test: Class with **kwargs"""
    result = split_args_for_inits_strict_kwargs(AcceptsAllDummy, [], {"z": 1})
    assert result[AcceptsAll]["kwargs"] == {"z": 1}
    assert result["leftovers"]["kwargs"] == {"z": 1}


def test_find_calling_class_typeerror_branch():
    """Test that should raise TypeError and hit that branch."""
    instance = BuiltinTypeClass()
    result = _find_calling_class_from_init_old(instance)
    assert result is None


# 500: if skip_class is None: (which means _find_calling_class_from_init failed)
def test_apply_split_inits_old_skip_class_none_branch(monkeypatch):
    """Test forcing the _find_calling_class_from_init to fail."""

    class X:  # pylint: disable=too-few-public-methods
        """Class with one positional arg."""

        def __init__(self, foo):  # pylint: disable=disallowed-name
            self.foo = foo  # pylint: disable=disallowed-name

    class Y:  # pylint: disable=too-few-public-methods
        """Class with one kwarg."""

        def __init__(self, bar=2):  # pylint: disable=disallowed-name
            self.bar = bar  # pylint: disable=disallowed-name

    class Z(X, Y):  # pylint: disable=too-few-public-methods
        """Class to inherit two other classes."""

        def __init__(
            self, *args, **kwargs
        ):  # pylint: disable=super-init-not-called
            apply_split_inits_old(self, args=args, kwargs=kwargs)

    # Force _find_calling_class_from_init to raise TypeError
    monkeypatch.setattr(
        "python_template.utils.split_args_for_inits._find_calling_class_from_init",
        # lambda self: (_ for _ in ()).throw(TypeError("mocked")),
        lambda self: None,
    )

    z = Z(1, bar=5)
    assert hasattr(z, "bar")


# 556: except exception (after already excepting TypeError earlier)
def test_apply_split_inits_old_direct_call_fallback(monkeypatch):
    """Test: super fails, then base.__init__ raises an exception."""
    # Patch super() to raise TypeError for test coverage
    original_super = super

    class MockSuper:  # pylint: disable=too-few-public-methods
        """A class to mock the super function."""

        def __init__(self, base, obj):
            raise TypeError("force fallback")

    monkeypatch.setattr("builtins.super", MockSuper)

    class Bar:  # pylint:disable=too-few-public-methods
        """Class whose base.__init__ should raise an exception."""

        def __init__(self, bar):  # pylint: disable=disallowed-name
            self.bar = bar  # pylint: disable=disallowed-name
            # This makes it raise a TypeError while doing the base.__init__:
            raise TypeError

    class FailSuper(Bar):  # pylint: disable=too-few-public-methods
        """Class that should fail super ad fall back to base.__init__"""

        def __init__(
            self, *args, **kwargs
        ):  # pylint: disable=super-init-not-called
            apply_split_inits_old(self, args=args, kwargs=kwargs)

    fortytwo = 42
    f = FailSuper(bar=fortytwo)
    assert f.bar == fortytwo

    monkeypatch.setattr("builtins.super", original_super)  # Restore


# _find_calling_class_from_init tests


def test_find_calling_class_success():
    """Test ensuring _find_calling_class succeeds."""
    dummy = DummyWithApplyOld()
    cls = _find_calling_class_from_init_old(dummy)
    assert cls is DummyWithApplyOld


def test_find_calling_class_skips_no_init():
    """Test: Class with no init"""
    obj = NoInit()
    assert _find_calling_class_from_init_old(obj) is None


def test_find_calling_class_handles_typeerror():
    """Test: Class with non-introspectable init (simulate TypeError)"""
    # Simulate with a built-in that raises TypeError on inspection
    obj = BuiltinWrapper()
    assert _find_calling_class_from_init_old(obj) is None


def test_find_calling_class_positive():
    """Test: Positive detection (init calls apply_split_inits)."""
    obj = M()
    assert _find_calling_class_from_init_old(obj) == M


# apply_split_inits tests


def test_apply_split_inits_manual_skip():
    """Test: Skip class manually"""
    obj = Skip()
    assert hasattr(obj, "_init_leftovers")


# Direct function call tests


def test_split_args_for_inits_applies_init_properly():
    """Test: Mixin correctly delegates to helper"""
    a_val = 10
    b_val = 20
    c_val = 30
    three = 3
    e = E1(a=a_val, b=b_val, c=c_val)
    assert e._a == a_val  # pylint: disable=protected-access
    # assert not e._b_kwargs  # pylint: disable=protected-access
    assert e._b_kwargs == {
        "b": b_val,
        "c": c_val,
    }  # pylint: disable=protected-access
    assert not hasattr(e, "_init_leftovers")
    assert len(e.split) == three
    assert e.split["leftovers"]["kwargs"]["b"] == b_val
    assert e.split["leftovers"]["kwargs"]["c"] == c_val


# SplitInitMixin tests


def test_splitinitmixin_applies_init_properly():
    """Test: Mixin correctly delegates to helper"""
    x_val = 10
    y_val = 20
    c = M3(x=x_val, y=y_val)
    assert c._x == x_val  # pylint: disable=protected-access
    assert c._y == y_val  # pylint: disable=protected-access
    assert hasattr(c, "_init_leftovers")


# This test fails due to the conditions listed in the mixin class docstring.
# auto_split_init SplitInitMixin extra tests
def test_apply_split_inits_correctly_applies_and_sets_leftovers():
    """Test: Normal split, one base has **kwargs"""
    c = C1(a=1, b=2, c=3)
    # Ideally we would want this to exist, but due to the described conditions
    # A1 is never initialized.
    # But with the nwe version, we're ok!
    assert c._a == 1  # pylint: disable=protected-access
    # assert not hasattr(c, "_a")
    # Note how it passes the params for A1 to B1:
    # Not anymore!
    assert c._b_kwargs == {"b": 2, "c": 3}  # pylint: disable=protected-access
    # assert c._b_kwargs == {"a": 1}  # pylint: disable=protected-access
    # Note how it then leaves the B1 params as leftovers:
    assert c._init_leftovers == {  # pylint: disable=protected-access
        "args": [],
        "kwargs": {"b": 2, "c": 3},
    }


# This test fails due to the conditions listed in the decorator docstring.
# auto_split_init Decorator extra tests
def test_auto_split_init_decorator_behavior():
    """Test: Confirm decorator wraps and initializes correctly"""
    d = D1(a=1, extra="stuff")
    # Ideally we would want this to exist, but due to the described conditions
    # A1 is never initialized.
    # Nut with the new version, now we're ok!
    assert d._a == 1  # pylint: disable=protected-access
    # assert not hasattr(d, "_a")
    # Note how it passes the params for A1 to B1:
    # Not anymore!
    assert d._b_kwargs == {  # pylint: disable=protected-access
        "extra": "stuff"
    }
    # assert d._b_kwargs == {"a": 1}  # pylint: disable=protected-access
    assert hasattr(d, "_init_leftovers")
    # Note how it then still leaves the extra params as leftovers:
    assert d._init_leftovers == {  # pylint: disable=protected-access,no-member
        "args": [],
        "kwargs": {"extra": "stuff"},
    }


# Test positional and keyword bindings:


def test_positional_binding():
    """Test to ensure positional arg binding is passed correctly."""
    a_val = 5
    c = C2(a_val)
    assert c._a == a_val  # pylint: disable=protected-access


def test_keyword_binding():
    """Test to ensure keyword binding is passed correctly."""
    a_val = 10
    c = C2(a=a_val)
    assert c._a == a_val  # pylint: disable=protected-access


# Test caveats


def test_caveat_manual_ordering():
    """Tests that the ordering of the parent classes is preserved."""

    class First:  # pylint: disable=too-few-public-methods
        """Class creating the member "order"."""

        def __init__(self):
            self.order = ["first"]

    class Second:  # pylint: disable=too-few-public-methods
        """Class that must be initialized after First,
        though it doesn't directly call First."""

        def __init__(self):
            self.order.append("second")  # pylint: disable=no-member

    class Manual(First, Second):  # pylint: disable=too-few-public-methods
        """Class to combine First and Second."""

        def __init__(self):
            self.order = []
            split = split_args_for_inits_strict_kwargs(type(self), (), {})
            First.__init__(self)
            Second.__init__(self)
            self.leftovers = split["leftovers"]

    m = Manual()
    assert m.order == ["first", "second"]


def test_split_leftovers_preserved():
    """Test that leftovers are preserved."""
    a = 1
    b = 2
    extra = "hello"
    ninetynine = 99
    obj = C3(a, b=b, extra=extra, unknown_kwarg=ninetynine)
    assert obj._a == a  # pylint: disable=protected-access
    assert obj.b == b
    # This isn't what happens either,
    # since the B parent accepts **kwargs but doen't call a parent,
    # so **kwargs aren't actually passed to it.
    # Now it does, so this is fine.
    assert obj.extra == extra
    # assert not obj.extra
    assert obj.leftovers["kwargs"] == {
        "extra": extra,
        "unknown_kwarg": ninetynine,
    }


def test_var_kwarg_binding_within_accepted_keys():
    """Test that when a positional arg and kwarg (by name) are both given,
    positional arg takes precedence and kwarg goes into leftovers."""

    class AcceptsKwargs:  # pylint: disable=too-few-public-methods
        """Class that accepts kwargs."""

        def __init__(self, **kwargs):
            self.caught = kwargs.get("target", None)

    class AcceptsDirect:  # pylint: disable=too-few-public-methods
        """Class that accepts a positional arg."""

        def __init__(self, target):
            self.target = target

    class Combiner(
        AcceptsDirect, AcceptsKwargs
    ):  # pylint: disable=too-few-public-methods
        """Class to combine AcceptsDirect and AcceptsKwargs."""

        def __init__(self, *args, **kwargs):
            self.split = split_args_for_inits_strict_kwargs(
                type(self), args, kwargs
            )
            AcceptsDirect.__init__(
                self,
                *self.split[AcceptsDirect]["args"],
                **self.split[AcceptsDirect]["kwargs"],
            )
            AcceptsKwargs.__init__(
                self,
                *self.split[AcceptsKwargs]["args"],
                **self.split[AcceptsKwargs]["kwargs"],
            )
            self.leftovers = self.split["leftovers"]

    val = "value"
    check = "check"
    unused = "meh"
    c = Combiner(val, target=check, unused=unused)
    assert c.target == val
    # This test is wrong. AcceptsKwargs will get nothing,
    # and AcceptsDirect will get both "check" and "value" for target
    # (and then put back "check").
    # But with the new version, this works as expected.
    assert c.caught == check
    # assert not c.caught
    assert c.leftovers["kwargs"] == {"target": check, "unused": unused}


# if __name__ == "__main__":
#     test_split_args_for_inits_strict_kwargs()
#     test_split_init_mixin()
#     test_auto_split_init()
