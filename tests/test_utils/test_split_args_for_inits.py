"""This file contains tests for the functions, classes, and decorators
in the split_args_for_inits module."""

import builtins

from python_template.utils import (
    LEFTOVERS,
    SplitInitMixin,
    apply_split_inits,
    auto_split_init,
    split_args_for_inits_strict_kwargs,
)
from python_template.utils.split_args_for_inits import (  # pylint: disable=unused-import
    _find_calling_class_from_init,
    _find_calling_class_from_init_old,
    apply_split_inits_old,
)


class Test_FullTests:  # pylint:disable=invalid-name
    """Tests of the full integration."""

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

        def __init__(
            self, *args, **kwargs
        ):  # pylint: disable=super-init-not-called
            self.split = split_args_for_inits_strict_kwargs(
                type(self), args, kwargs
            )
            # A.__init__(self, *self.split[A]["args"], **self.split[A]["kwargs"])
            # B.__init__(self, *self.split[B]["args"], **self.split[B]["kwargs"])
            apply_split_inits(self, type(self), args, kwargs)
            print(f"E leftovers: {self.split['leftovers']}")

    def test_split_args_for_inits_strict_kwargs(self):
        """Tests the split_args_for_inits_strict_kwargs function."""
        # print("\n=== Function Test ===")
        a1 = "a"
        b1 = "b"
        extra = 987
        zero = 0
        e = self.E(a1=a1, b1=b1, extra=extra)
        # === Function Test ===
        # A init: a1=a, a2=0, kwargs={}
        # B init: b1=b, b2=0
        # E leftovers: {'args': [], 'kwargs': {'extra': 987}}
        assert e.a1 == a1
        assert e.a2 == zero
        assert e.b1 == b1
        assert e.b2 == zero
        assert e.split[LEFTOVERS]["kwargs"]["extra"] == extra

    def test_split_init_mixin(self):
        """Tests the SplitInitMixin class."""
        a1 = "foo"
        b1 = "bar"
        extra = 123
        zero = 0
        # print("\n=== Mixin Test ===")
        c = self.C(a1=a1, b1=b1, extra=extra)
        # === Mixin Test ===
        # A init: a1=foo, a2=0, kwargs={}
        # B init: b1=bar, b2=0
        # C leftovers: {'args': [], 'kwargs': {'extra': 123}}
        assert c.a1 == a1
        assert c.a2 == zero
        assert c.b1 == b1
        assert c.b2 == zero
        # assert c.split[LEFTOVERS]["kwargs"]["extra"] == extra

    def test_auto_split_init(self):
        """Tests the auto_split_init decoarator."""
        a1 = "x"
        b1 = "y"
        extra = 456
        zero = 0
        # print("\n=== Decorator Test ===")
        d = self.D(a1=a1, b1=b1, extra=extra)
        # === Decorator Test ===
        # A init: a1=x, a2=0, kwargs={}
        # B init: b1=y, b2=0
        # D leftovers: {'args': [], 'kwargs': {'extra': 456}}
        assert d.a1 == a1
        assert d.a2 == zero
        assert d.b1 == b1
        assert d.b2 == zero
        # assert d.split[LEFTOVERS]["kwargs"]["extra"] == extra


class Test__find_calling_class_from_init_old:  # pylint:disable=invalid-name
    """Tests for _find_calling_class_from_init_old."""

    class BuiltinWrapper(
        builtins.int
    ):  # pylint: disable=too-few-public-methods
        """Wrapper for a builtin class."""

    class DummyWithApplyOld:  # pylint: disable=too-few-public-methods
        """Dummy class using the apply_split_inits method."""

        def __init__(self, *args, **kwargs):
            apply_split_inits_old(self, args=args, kwargs=kwargs)

    class M(SplitInitMixin):  # pylint: disable=too-few-public-methods
        """Class inheriting SplitInitMixin and calling apply_split_inits."""

        def __init__(self):  # pylint: disable=super-init-not-called
            apply_split_inits_old(self)

    class NoInit:  # pylint: disable=too-few-public-methods
        """Class with no init method."""

    def test_find_calling_class_success(self):
        """Test ensuring _find_calling_class succeeds."""
        dummy = self.DummyWithApplyOld()
        cls = _find_calling_class_from_init_old(dummy)
        assert cls is self.DummyWithApplyOld

    def test_find_calling_class_skips_no_init(self):
        """Test: Class with no init"""
        obj = self.NoInit()
        assert _find_calling_class_from_init_old(obj) is None

    def test_find_calling_class_handles_typeerror(self):
        """Test: Class with non-introspectable init (simulate TypeError)"""
        # Simulate with a built-in that raises TypeError on inspection
        obj = self.BuiltinWrapper()
        assert _find_calling_class_from_init_old(obj) is None

    def test_find_calling_class_positive(self):
        """Test: Positive detection (init calls apply_split_inits)."""
        obj = self.M()
        assert _find_calling_class_from_init_old(obj) == self.M


class Test_apply_split_inits_old:  # pylint:disable=invalid-name
    """Tests for apply_split_inits_old."""

    class AcceptsAll:  # pylint: disable=too-few-public-methods
        """Class that accepts all kwargs."""

        def __init__(self, **kwargs):
            pass

    class AcceptsAllDummy(
        AcceptsAll
    ):  # pylint: disable=too-few-public-methods
        """Wrapper class for AcceptsAll class."""

    class BuiltinTypeClass:  # pylint: disable=too-few-public-methods
        """Class that should raise TypeError in dis.get_instructions."""

        __init__ = object.__init__

    class Skip(SplitInitMixin):  # pylint: disable=too-few-public-methods
        """Class with a defined skip class."""

        def __init__(self):  # pylint: disable=super-init-not-called
            apply_split_inits_old(self, skip_class=type(self))

    def test_apply_split_inits_manual_skip(self):
        """Test: Skip class manually"""
        obj = self.Skip()
        assert hasattr(obj, "_init_leftovers")

    # Line tests: raise TypeError handling
    def test_split_args_with_var_kwargs(self):
        """Test: Class with **kwargs"""
        result = split_args_for_inits_strict_kwargs(
            self.AcceptsAllDummy, [], {"z": 1}
        )
        assert result[self.AcceptsAll]["kwargs"] == {"z": 1}
        assert result[LEFTOVERS]["kwargs"] == {"z": 1}

    def test_find_calling_class_typeerror_branch(self):
        """Test that should raise TypeError and hit that branch."""
        instance = self.BuiltinTypeClass()
        result = _find_calling_class_from_init_old(instance)
        assert result is None

    # Line test: if skip_class is None: (which means _find_calling_class_from_init failed)
    def test_apply_split_inits_old_skip_class_none_branch(self, monkeypatch):
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

    # Line test: Except exception (after already excepting TypeError earlier)
    def test_apply_split_inits_old_direct_call_fallback(self, monkeypatch):
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


class Test__find_calling_class_from_init:  # pylint:disable=invalid-name,too-few-public-methods
    """Tests for _find_calling_class_from_init."""

    class Empty:  # pylint: disable=too-few-public-methods
        """Empty class."""

    class EmptyDummy(Empty):  # pylint: disable=too-few-public-methods
        """Wrapper class for Empty class."""

    # Line test: positive branches of if not (init := base.__dict__.get("__init__")):
    def test_split_args_with_no_init(self):
        """Test: Class with no __init__"""
        result = split_args_for_inits_strict_kwargs(
            self.EmptyDummy, [1], {"x": 2}
        )
        assert result[LEFTOVERS]["args"] == [1]
        assert result[LEFTOVERS]["kwargs"] == {"x": 2}


class Test_split_args_for_inits:  # pylint:disable=invalid-name
    """Tests for split_args_for_inits"""

    class A1:  # pylint: disable=too-few-public-methods
        """Class accepting one positional arg."""

        def __init__(self, a):
            self._a = a
            super().__init__()

    class AKeywords:  # pylint: disable=too-few-public-methods
        """A class with optional positional args and one kwarg."""

        def __init__(self, *, a_kwarg):
            self.a_kwarg = a_kwarg

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

    class C3(A1, B2):  # pylint: disable=too-few-public-methods
        """Class calling other classes."""

        def __init__(
            self, *args, **kwargs
        ):  # pylint: disable=super-init-not-called
            self.split = split_args_for_inits_strict_kwargs(
                type(self), args, kwargs
            )
            # A1.__init__(self, *self.split[A1]["args"], **self.split[A1]["kwargs"])
            # B2.__init__(self, *self.split[B2]["args"], **self.split[B2]["kwargs"])
            apply_split_inits(self, type(self), args, kwargs)
            self.leftovers = self.split[LEFTOVERS]

    class CombinedClass(
        AKeywords, BStarKwargs
    ):  # pylint: disable=too-few-public-methods
        """Class combining AKeywords and BStarKwargs."""

        def __init__(self, *args, **kwargs):
            self.split = split_args_for_inits_strict_kwargs(
                type(self), args, kwargs
            )
            Test_split_args_for_inits.AKeywords.__init__(
                self,
                *self.split[Test_split_args_for_inits.AKeywords]["args"],
                **self.split[Test_split_args_for_inits.AKeywords]["kwargs"],
            )
            Test_split_args_for_inits.BStarKwargs.__init__(
                self,
                *self.split[Test_split_args_for_inits.BStarKwargs]["args"],
                **self.split[Test_split_args_for_inits.BStarKwargs]["kwargs"],
            )
            self.leftovers = self.split[LEFTOVERS]

    class E1(A1, B1):  # pylint: disable=too-few-public-methods
        """Test class E1. For use of the function."""

        def __init__(
            self, *args, **kwargs
        ):  # pylint: disable=super-init-not-called
            self.split = split_args_for_inits_strict_kwargs(
                type(self), args, kwargs
            )
            # A1.__init__(self, *self.split[A1]["args"], **self.split[A1]["kwargs"])
            # B1.__init__(self, *self.split[B1]["args"], **self.split[B1]["kwargs"])
            apply_split_inits(self, type(self), args, kwargs)
            print(f"E leftovers: {self.split['leftovers']}")

    class F:  # pylint: disable=too-few-public-methods
        """Class with one keyword arg"""

        def __init__(self, a=1):
            pass

    class FDummy(F):  # pylint: disable=too-few-public-methods
        """Wrapper class for F class."""

    class P1:  # pylint: disable=too-few-public-methods
        """Class with one positional arg and one kwarg."""

        def __init__(self, a, b=2):
            pass

    class P1Dummy(P1):  # pylint: disable=too-few-public-methods
        """Dummy wrapper class for P1"""

    class P2:  # pylint: disable=too-few-public-methods
        """Class with two kwargs."""

        def __init__(
            self, foo=None, bar=None
        ):  # pylint: disable=disallowed-name
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

    def test_split_args_for_inits_applies_init_properly(self):
        """Test: Mixin correctly delegates to helper"""
        a_val = 10
        b_val = 20
        c_val = 30
        three = 3
        e = self.E1(a=a_val, b=b_val, c=c_val)
        assert e._a == a_val  # pylint: disable=protected-access
        # assert not e._b_kwargs  # pylint: disable=protected-access
        assert e._b_kwargs == {
            "b": b_val,
            "c": c_val,
        }  # pylint: disable=protected-access
        # assert not hasattr(e, "_init_leftovers")
        assert (
            e._init_leftovers["kwargs"]  # pylint: disable=no-member
            == e._b_kwargs
        )  # pylint: disable=protected-access
        assert len(e.split) == three
        assert e.split[LEFTOVERS]["kwargs"]["b"] == b_val
        assert e.split[LEFTOVERS]["kwargs"]["c"] == c_val

    # Line test: positive branch of if remaining_args:
    def test_split_args_with_positional_args(self):
        """Test: Positional argument matching (covers if remaining_args: branch)"""

        args = [1]
        kwargs = {"b": 5, "x": 42}
        result = split_args_for_inits_strict_kwargs(self.P1Dummy, args, kwargs)
        assert result[self.P1]["args"] == [1]
        assert result[self.P1]["kwargs"] == {"b": 5}
        assert result[LEFTOVERS]["kwargs"] == {"x": 42}

    # Line test: positive branch of if key in keyword_params:
    def test_split_args_with_kwarg_param(self):
        """Test: positive branch of if key in keyword_params"""
        a_val = 10
        args = ()
        kwargs = {"a": a_val}
        result = split_args_for_inits_strict_kwargs(self.FDummy, args, kwargs)
        assert result[self.F]["kwargs"] == kwargs

    def test_bind_kwargs_from_remaining(self):
        """Test that binds kwargs from remaining (for the positive branch above)"""
        a_kwarg = 42
        bk = "present"
        unused = "leftover"
        obj = self.CombinedClass(a_kwarg=a_kwarg, bk=bk, unused=unused)
        assert obj.a_kwarg == a_kwarg
        # Beacuse of the way it is set up looking for bk in kwargs, it won't get bk.
        # assert obj.bk == bk
        assert obj.b_seen
        assert obj.leftovers["kwargs"] == {"bk": bk, "unused": unused}

    # Line test: positive branch of if not (init := base.__dict__.get("__init__", None)):
    # This I think is covered by the test below?
    # Line test: positive branch of if key in accepted_keys:
    def test_split_args_with_filtered_kwargs(self):
        """Test: Accepted key filtering (covers if key in accepted_keys:)"""
        args = []
        kwargs = {"foo": "FOO", "baz": "BAZ"}
        result = split_args_for_inits_strict_kwargs(self.P2Dummy, args, kwargs)
        assert result[self.P2]["kwargs"] == {"foo": "FOO"}
        assert result[LEFTOVERS]["kwargs"] == {"baz": "BAZ"}

        kwargs["q1"] = "q1"
        result = split_args_for_inits_strict_kwargs(self.QDummy, args, kwargs)
        assert result[self.Q]["kwargs"] == {
            "q1": kwargs["q1"],
            "foo": kwargs["foo"],
        }
        assert result[self.P2] == {
            "args": [],
            "kwargs": {},
            "args_assigned_positionally": [],
        }
        assert result[LEFTOVERS] == {
            "args": [],
            "kwargs": {"baz": kwargs["baz"]},
        }

    def test_split_leftovers_preserved(self):
        """Test that leftovers are preserved."""
        a = 1
        b = 2
        extra = "hello"
        ninetynine = 99
        obj = self.C3(a, b=b, extra=extra, unknown_kwarg=ninetynine)
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

    def test_caveat_manual_ordering(self):
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

            def __init__(self):  # pylint: disable=super-init-not-called
                self.order = []
                split = split_args_for_inits_strict_kwargs(type(self), (), {})
                # First.__init__(self)
                # Second.__init__(self)
                apply_split_inits(self, type(self), (), {})
                self.leftovers = split[LEFTOVERS]

        m = Manual()
        assert m.order == ["first", "second"]

    def test_var_kwarg_binding_within_accepted_keys(self):
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

            def __init__(
                self, *args, **kwargs
            ):  # pylint: disable=super-init-not-called
                self.split = split_args_for_inits_strict_kwargs(
                    type(self), args, kwargs
                )
                # AcceptsDirect.__init__(
                #     self,
                #     *self.split[AcceptsDirect]["args"],
                #     **self.split[AcceptsDirect]["kwargs"],
                # )
                # AcceptsKwargs.__init__(
                #     self,
                #     *self.split[AcceptsKwargs]["args"],
                #     **self.split[AcceptsKwargs]["kwargs"],
                # )
                apply_split_inits(self, type(self), args, kwargs)
                self.leftovers = self.split[LEFTOVERS]

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


class Test_SplitInitMixin:  # pylint:disable=invalid-name
    """Tests for the SplitInitMixin class"""

    class A1:  # pylint: disable=too-few-public-methods
        """Class accepting one positional arg."""

        def __init__(self, a):
            self._a = a
            super().__init__()

    class B1:  # pylint: disable=too-few-public-methods
        """Class accepting variable kwargs."""

        def __init__(self, **kwargs):
            self._b_kwargs = kwargs
            super().__init__()

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
            # pass

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
            # apply_split_inits(self, type(self), args, kwargs)

    def test_splitinitmixin_applies_init_properly(self):
        """Test: Mixin correctly delegates to helper"""
        x_val = 10
        y_val = 20
        c = self.M3(x=x_val, y=y_val)
        assert c._x == x_val  # pylint: disable=protected-access
        assert c._y == y_val  # pylint: disable=protected-access
        assert hasattr(c, "_init_leftovers")

    # This test fails due to the conditions listed in the mixin class docstring.
    # auto_split_init SplitInitMixin extra tests
    def test_apply_split_inits_correctly_applies_and_sets_leftovers(self):
        """Test: Normal split, one base has **kwargs"""
        c = self.C1(a=1, b=2, c=3)
        # Ideally we would want this to exist, but due to the described conditions
        # A1 is never initialized.
        # But with the new version, we're ok!
        assert c._a == 1  # pylint: disable=protected-access
        # assert not hasattr(c, "_a")
        # Note how it passes the params for A1 to B1:
        # Not anymore!
        assert c._b_kwargs == {  # pylint: disable=protected-access
            "b": 2,
            "c": 3,
        }
        # assert c._b_kwargs == {"a": 1}  # pylint: disable=protected-access
        # Note how it then leaves the B1 params as leftovers:
        assert c._init_leftovers == {  # pylint: disable=protected-access
            "args": [],
            "kwargs": {"b": 2, "c": 3},
        }

    # Test positional and keyword bindings:

    def test_positional_binding(self):
        """Test to ensure positional arg binding is passed correctly."""
        a_val = 5
        c = self.C2(a_val)
        assert c._a == a_val  # pylint: disable=protected-access

    def test_keyword_binding(self):
        """Test to ensure keyword binding is passed correctly."""
        a_val = 10
        c = self.C2(a=a_val)
        assert c._a == a_val  # pylint: disable=protected-access


class Test_decorator:  # pylint:disable=invalid-name,too-few-public-methods
    """Tests for the decorator."""

    class A1:  # pylint: disable=too-few-public-methods
        """Class accepting one positional arg."""

        def __init__(self, a):
            self._a = a
            super().__init__()

    class B1:  # pylint: disable=too-few-public-methods
        """Class accepting variable kwargs."""

        def __init__(self, **kwargs):
            self._b_kwargs = kwargs
            super().__init__()

    @auto_split_init
    class D1(A1, B1):  # pylint: disable=too-few-public-methods
        """Class using decorator."""

        def __init__(
            self, *args, **kwargs
        ):  # pylint: disable=super-init-not-called
            pass

    # This test fails due to the conditions listed in the decorator docstring.
    # auto_split_init Decorator extra tests
    def test_auto_split_init_decorator_behavior(self):
        """Test: Confirm decorator wraps and initializes correctly"""
        d = self.D1(a=1, extra="stuff")
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
        assert (  # pylint: disable=protected-access,no-member
            d._init_leftovers
            == {
                "args": [],
                "kwargs": {"extra": "stuff"},
            }
        )


# if __name__ == "__main__":
#     test_split_args_for_inits_strict_kwargs()
#     test_split_init_mixin()
#     test_auto_split_init()
