"""This file contains utilities to split args for inits."""

import dis
import inspect
from collections import defaultdict
from typing import Any

DEBUG_PRINTS = False


def collect_init_param_names(cls: type) -> set:
    """Collect all __init__ param names (excluding 'self') from cls and ancestors."""
    names: set[str] = set()
    for base in cls.__mro__:
        if base is object:
            break
        if (init := base.__dict__.get("__init__", None)) is not None:
            sig = inspect.signature(init)
            params = list(sig.parameters.values())[1:]  # skip 'self'
            names.update(
                p.name
                for p in params
                if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
            )
    return names


def split_args_for_inits_strict_kwargs(  # pylint: disable=too-many-locals,too-complex
    cls: type,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    stop_at: type = object,
) -> dict[type, dict[str, Any]]:
    """Split args/kwargs across MRO classes, and only pass **kwargs
    to a class if it (or its parents) will actually use them.
    """
    remaining_args = list(args)
    remaining_kwargs = dict(kwargs)
    result: defaultdict[Any, dict[str, list[Any] | dict[Any, Any]]] = (
        defaultdict(lambda: {"args": [], "kwargs": {}})
    )
    param_cache = {}

    for base in cls.__mro__[1:]:  # Skip the class itself
        if base is stop_at:
            break
        if not (init := base.__dict__.get("__init__", None)):
            continue

        sig = inspect.signature(init)
        params = list(sig.parameters.values())[1:]

        # accepts_var_positional = any(p.kind == p.VAR_POSITIONAL for p in params)
        accepts_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params)

        # Bind args
        bound_args = []
        param_iter = (
            p
            for p in params
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        )
        for p in param_iter:
            if remaining_args:
                bound_args.append(remaining_args.pop(0))
            else:
                break

        # Bind kwargs explicitly listed in this __init__:
        keyword_params = {
            p.name
            for p in params
            if p.kind in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD)
        }
        bound_kwargs = {}
        for key in list(remaining_kwargs):
            if key in keyword_params:
                bound_kwargs[key] = remaining_kwargs.pop(key)

        # If accepts **kwargs, only pass keys that base class (or its ancestors) can use:
        if accepts_var_keyword:
            if base not in param_cache:
                param_cache[base] = collect_init_param_names(base)
            accepted_keys = param_cache[base]
            for key in list(remaining_kwargs):
                if key in accepted_keys:
                    bound_kwargs[key] = remaining_kwargs.pop(key)

        result[base]["args"].extend(bound_args)  # type: ignore[union-attr]
        result[base]["kwargs"].update(bound_kwargs)  # type: ignore[union-attr]

    # if remaining_args or remaining_kwargs:
    result["leftovers"] = {"args": remaining_args, "kwargs": remaining_kwargs}

    return result


def _find_calling_class_from_init(instance):  # pylint: disable=too-complex
    """Examine classes in MRO of `instance` to find whose `__init__` contains
    a direct call to `apply_split_inits`.
    """
    apply_split_inits_name = "apply_split_inits"
    cls = type(instance)
    for base in cls.__mro__:
        if DEBUG_PRINTS:
            print(
                f"\n[_find_calling_class_from_init] Inspecting parent class: {base.__name__}"
            )
        if base is object:
            if DEBUG_PRINTS:
                print(
                    f"\n[_find_calling_class_from_init] Found hierarchy pinnacle: {base.__name__}"
                )
            continue
        if not (init := base.__dict__.get("__init__")):
            if DEBUG_PRINTS:
                print(
                    f"\n[_find_calling_class_from_init] {base.__name__} has no __init__ method."
                )
            continue

        try:  # pylint: disable=too-many-try-statements
            instructions = list(dis.get_instructions(init))
            for instr in instructions:
                if (
                    instr.opname in set(["LOAD_GLOBAL", "LOAD_METHOD"])
                    and instr.argval == apply_split_inits_name
                ):
                    return base
        except TypeError as e:
            if DEBUG_PRINTS:
                print(
                    f"\n[_find_calling_class_from_init] Encountered TypeError: {e}"
                )
            continue  # Skip builtins or non-Python functions
    return None


def apply_split_inits(  # pylint: disable=too-complex,too-many-branches
    self, cls=None, args=(), kwargs=None, skip_class=None
):
    """Call __init__ of all base classes using split argument mapping."""
    cls = cls or type(self)
    kwargs = kwargs or {}
    if DEBUG_PRINTS:
        print(
            f"\n[apply_split_inits] Called from class: {_find_calling_class_from_init(self)}"
        )
        print(f"\n[apply_split_inits] Running for class: {cls.__name__}")
    # Automatically detect skip class as the defining class of apply_split_inits:
    if skip_class is None:
        skip_class = _find_calling_class_from_init(self)
        if DEBUG_PRINTS:
            if skip_class is None:
                print(
                    "[apply_split_inits] Warning: Failed to auto-detect skip_class."
                )
            else:
                print(
                    f"[apply_split_inits] Auto-detected skip_class as: {skip_class.__name__}"
                )
    split = split_args_for_inits_strict_kwargs(cls, args, kwargs)
    seen = set()
    for base in cls.__mro__[1:]:
        if base in (object,) or base in seen:
            continue
        if base is skip_class:
            if DEBUG_PRINTS:
                print(f"[apply_split_inits] Skipping class {base.__name__}")
            continue
        seen.add(base)
        if base in split:
            base_args = split[base]["args"]
            base_kwargs = split[base]["kwargs"]
            if DEBUG_PRINTS:
                print(
                    f"[apply_split_inits] Calling __init__ of {base.__name__} with:"
                )
                print(f"    args: {base_args}")
                print(f"    kwargs: {base_kwargs}")
            if hasattr(base, "__init__"):
                try:
                    # base.__init__(self, *base_args, **base_kwargs)
                    # super(base, self).__init__(self, *base_args, **base_kwargs)
                    super(base, self).__init__(*base_args, **base_kwargs)
                except TypeError as e:
                    # print(f"[Warning] Skipped {base.__name__} due to: {e}")
                    # continue
                    if DEBUG_PRINTS:
                        print(
                            f"[apply_split_inits] TypeError using super() for {base.__name__}: {e}"
                        )
                        print(
                            f"[apply_split_inits] Falling back to direct call for {base.__name__}"
                        )
                    # Fall back to direct init in edge cases:
                    base.__init__(  # pylint: disable=unnecessary-dunder-call
                        self, *base_args, **base_kwargs
                    )
    self._init_leftovers = split.get(  # pylint: disable=protected-access
        "leftovers", {"args": [], "kwargs": {}}
    )
    if DEBUG_PRINTS:
        print(
            f"[apply_split_inits] Leftovers set to: {self._init_leftovers}"  # pylint: disable=protected-access
        )
    return self._init_leftovers  # pylint: disable=protected-access


class SplitInitMixin:  # pylint: disable=too-few-public-methods
    """A mixin class to be used for automatically splitting args across inits.

    Usage example:
    class Child(SplitInitMixin, Parent1, Parent2):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Use self._init_leftovers if needed
    """

    def __init__(self, *args, **kwargs):
        """New init for the class."""
        apply_split_inits(
            self, cls=type(self), args=args, kwargs=kwargs
        )  # , skip_class=SplitInitMixin)


def auto_split_init(cls):
    """A decorator to be used for automatically splitting args across inits.

    Usage example:
    @auto_split_init
    class Child(Parent1, Parent2):
        def __init__(self, *args, **kwargs):
            # self._init_leftovers is available if needed
            print("Child custom init logic")
    """
    original_init = cls.__init__

    def wrapped_init(self, *args, **kwargs):
        """New init for the wrapped class."""
        leftovers = apply_split_inits(self, type(self), args, kwargs)
        original_init(
            self, *leftovers.get("args", []), **leftovers.get("kwargs", {})
        )

    cls.__init__ = wrapped_init
    return cls
