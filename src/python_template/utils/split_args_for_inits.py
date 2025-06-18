"""This file contains utilities to split args for inits."""

import ast
import dis
import inspect
import textwrap
from collections import defaultdict
from typing import Any, get_type_hints

from python_template import config

DEBUG_PRINTS = config.debug_prints
LEFTOVERS = "leftovers"


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


def split_args_for_inits_strict_kwargs(  # pylint: disable=too-many-locals,too-complex,too-many-branches,too-many-arguments
    cls: type,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    stop_at: type = object,
    enable_type_heuristics: bool = False,
    enable_dis_bytecode_scan: bool = False,
) -> dict[type, dict[str, Any]]:
    """Split args/kwargs across MRO classes, and only pass **kwargs
    to a class if it (or its parents) will actually use them.

    Notes: The following caveats should be respected:
     - The desired initialization order must be manually respected, since this
       bypasses the MRO. So if one parent depends on another being initialized
       first, ensure that the correct parent is initialized first in the order
       of parent __init__ calls.
     - Any parent class that uses super().__init__() may still try to call its
       own parent (though I think this is the intended behavior). Since we're
       calling its __init__ directly, it may
        - Skip expected initialization (since we short-circuit the super chain)
        - Double-call something if one of the manual __init__ calls followed by
          super() ends up calling the same thing again.

    Usage example:
    class Child(Parent1, Parent2):
        def __init__(self, *args, **kwargs):
            self.split = split_args_for_inits_strict_kwargs(
                type(self), args, kwargs
            )
            Parent1.__init__(
                self, *self.split[Parent1]["args"], **self.split[Parent1]["kwargs"]
            )
            Parent2.__init__(
                self, *self.split[Parent2]["args"], **self.split[Parent2]["kwargs"]
            )
            self._init_leftovers = self.split[LEFTOVERS]

    Args:
        cls (type): The class type (e.g., "type(self)").
        args (tuple): Any args passed to the instance being instantiated.
        kwargs (dict[str, Any]): Any kwargs passed to the instance being instantiated.
        stop_at (type): At which class to stop the hierarchy search. Defaults to object.
        enable_type_heuristics (bool): whether to use type hint resolution. Defaults
            to False.
        enable_dis_bytecode_scan (bool): whether to inspect bytecode for kwargs.get.
            Defaults to False.

    Returns:
        defaultDict[Any, dict[str, list[Any] | dict[Any, Any]]]: The dict (by class type)
            used to indicate to which direct parent class to pass which args and kwargs.
    """
    remaining_args = list(args)
    remaining_kwargs = dict(kwargs)
    if DEBUG_PRINTS:
        print("[split_args_for_inits_strict_kwargs] Splitting with:")
        print(f"    args: {remaining_args}")
        print(f"    kwargs: {remaining_kwargs}")
    result: defaultdict[Any, dict[str, list[Any] | dict[Any, Any]]] = (
        defaultdict(
            lambda: {
                "args": [],
                "kwargs": {},
                "args_assigned_positionally": [],
            }
        )
    )
    param_cache = {}

    # params_assigned_positionally = {}

    # for base in cls.__mro__[1:]:  # Skip the class itself
    for base in cls.__bases__:  # Only look at the bases of this class.
        # params_assigned_positionally[base] = []
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
        bound_kwargs = {}
        # 1. Route positional args:
        param_iter = (
            p
            for p in params
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        )
        for p in param_iter:
            if remaining_args:
                bound_args.append(remaining_args.pop(0))
                # params_assigned_positionally[base].append(p.name)
                result[base]["args_assigned_positionally"].append(  # type: ignore[union-attr]
                    p.name
                )
            elif p.name in remaining_kwargs:
                # There's an arg necessary, but it's not in args, so check kwargs:
                bound_kwargs[p.name] = remaining_kwargs.pop(p.name)
                # bound_args.append(remaining_kwargs.pop(p.name))
            else:
                break
        # 2. Route kwargs:
        # Bind kwargs explicitly listed in this __init__:
        keyword_params = {
            p.name
            for p in params
            if p.kind in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD)
        }
        for key in list(remaining_kwargs):
            if (
                key in keyword_params
                # and key not in params_assigned_positionally[base]
                and key not in result[base]["args_assigned_positionally"]
            ):
                bound_kwargs[key] = remaining_kwargs.pop(key)

        # If accepts **kwargs, only pass keys that base class (or its ancestors) can use:
        if accepts_var_keyword:
            if base not in param_cache:
                param_cache[base] = collect_init_param_names(base)
            accepted_keys = param_cache[base]
            for key in list(remaining_kwargs):
                if (
                    key in accepted_keys
                    # and key not in params_assigned_positionally[base]
                    and key not in result[base]["args_assigned_positionally"]
                ):
                    bound_kwargs[key] = remaining_kwargs.pop(key)

        result[base]["args"].extend(bound_args)  # type: ignore[union-attr]
        result[base]["kwargs"].update(bound_kwargs)  # type: ignore[union-attr]

    # 3. Use heuristics to route ambiguous leftovers:
    if enable_type_heuristics:
        apply_type_heuristic_routing(cls, remaining_kwargs, result, stop_at)

    if enable_dis_bytecode_scan:
        apply_dis_bytecode_routing(cls, remaining_kwargs, result, stop_at)

    # 4. Use per-branch safe `**kwargs` inference:
    safe_receivers = find_safe_kwargs_targets(cls)
    for base in safe_receivers:
        # for k in list(remaining_kwargs):
        for k, v in remaining_kwargs.items():
            # if k not in params_assigned_positionally[base]:
            if k not in result[base]["args_assigned_positionally"]:
                # Pass leftovers to first safe_reciever:
                # result[base][k] = remaining_kwargs.pop(k)
                # Pass leftovers to all safe_recievers:
                result[base]["kwargs"][k] = v  # type: ignore[call-overload]

    # if remaining_args or remaining_kwargs:
    result[LEFTOVERS] = {"args": remaining_args, "kwargs": remaining_kwargs}

    return result


def get_mro_kwarg_info(cls):
    """Get kwarg ifno from the MRO."""
    mro = cls.mro()
    paraminfo = {}
    for base in mro:
        sig = inspect.signature(base.__init__)
        accepted = {
            name
            for name, param in sig.parameters.items()
            if name != "self"  # pylint: disable=magic-value-comparison
            and param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD)
        }
        accepts_var_kw = any(
            p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
        )
        paraminfo[base] = (accepted, accepts_var_kw)
    return paraminfo


def apply_type_heuristic_routing(
    cls, remaining_kwargs, routing, stop_at=object
):
    """Route kwargs based on parameter types."""
    paraminfo = get_mro_kwarg_info(cls)
    for base in cls.__bases__:
        current = base
        # for base, (accepted, _) in paraminfo.items():
        while current != stop_at:  # pylint: disable=while-used
            (accepted, _) = paraminfo.get(current, (set(), False))
            type_hints = get_type_hints(base.__init__)
            for name, val in list(remaining_kwargs.items()):
                if name in accepted and name in type_hints:
                    hint = type_hints[name]
                    if isinstance(val, hint):
                        routing[base]["kwargs"][name] = remaining_kwargs.pop(
                            name
                        )
            current = current.__base__


def apply_dis_bytecode_routing(  # pylint: disable=too-many-nested-blocks
    cls, remaining_kwargs, routing, stop_at=object
):
    """Route kwargs if init function internally uses them."""
    # paraminfo = get_mro_kwarg_info(cls)
    # for base in paraminfo:
    for base in cls.__bases__:
        current = base
        while current != stop_at:  # pylint: disable=while-used
            try:  # pylint: disable=too-many-try-statements
                func = base.__init__
                # code = func.__code__
                for instr in dis.get_instructions(func):
                    if (
                        instr.opname  # pylint: disable=magic-value-comparison
                        == "LOAD_CONST"
                        and isinstance(instr.argval, str)
                    ):
                        if (key := instr.argval) in remaining_kwargs:
                            routing[base]["kwargs"][key] = (
                                remaining_kwargs.pop(key)
                            )
            except Exception:  # pylint: disable=broad-exception-caught
                # continue
                pass
            current = current.__base__


def find_safe_kwargs_targets(cls):
    """For each direct base class of `cls`, follow its MRO path down and ensure all accept **kwargs.
    Return those safe to receive leftover kwargs.
    """
    paraminfo = get_mro_kwarg_info(cls)
    safe_bases = set()
    for base in cls.__bases__:
        current = base
        path_safe = True
        while current != object:  # pylint: disable=while-used
            _, accepts_var_kw = paraminfo.get(current, (set(), False))
            if DEBUG_PRINTS:
                print(f"Current: {current.__name__}")
            if not accepts_var_kw:
                if DEBUG_PRINTS:
                    print("  --> Not safe!")
                path_safe = False
                break
            current = current.__base__
        if path_safe:
            if DEBUG_PRINTS:
                print("  --> Safe!")
            safe_bases.add(base)
    return safe_bases


def share_missing_params_across_parents(
    split: dict[type, dict[str, Any]], stop_at=object
) -> None:
    """For each parent class in the split, check if it is missing any required parameters
    (positional or keyword) and try to fill them in by copying from other parent's args/kwargs.
    """
    # # This is not necessary. We can just use split directly.
    # # Build param sources from other parents
    # param_sources = defaultdict(list)
    # for parent, data in split.items():
    #     for k, v in zip(data.get("sig_params", []), data["args"]):
    #         param_sources[k.name].append((parent, v))
    #     for k, v in data["kwargs"].items():
    #         param_sources[k].append((parent, v))

    # Now check for missing parameters in each parent:
    for parent, data in split.items():
        if parent == LEFTOVERS:
            continue
        required_params = []
        # if hasattr(parent, "__init__"):
        #     sig = inspect.signature(parent.__init__)
        #     required_params.extend(
        #         [
        #             p.name for p in sig.parameters.values()
        #             if p.name != 'self'
        #             and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
        #             # We don't need this restriction; do it even if there is a default value:
        #             # and p.default is p.empty
        #         ]
        #     )
        current = parent
        while current != stop_at:  # pylint: disable=while-used
            if hasattr(current, "__init__"):
                sig = inspect.signature(current.__init__)  # type: ignore[misc]
                required_params.extend(
                    [
                        p.name
                        for p in sig.parameters.values()
                        if p.name  # pylint: disable=magic-value-comparison
                        != "self"
                        # and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
                        # We don't need this restriction; do it even if there is a default value:
                        # and p.default is p.empty
                    ]
                )
                print(f"{current.__name__}: {required_params}")
            current = current.__base__  # type: ignore
        for pname in required_params:
            if pname in data["kwargs"]:
                continue
            # found = param_sources.get(pname, [])
            # for source_cls, val in found:
            for source_cls, args_dicts in split.items():
                if (
                    source_cls != parent
                    and pname in split[source_cls]["kwargs"]
                    and pname
                    not in split[parent]["args_assigned_positionally"]
                ):
                    data["kwargs"][pname] = args_dicts["kwargs"][pname]
                    break


def call_init_chain_respecting_super(  # pylint: disable=too-many-locals,too-complex
    self,
    cls: type,
    split: dict[type, dict[str, Any]],
    stop_at=object,
    skip_class=None,
) -> None:
    """Call init methods of super-respecting classes via `super()` chain, and manually call
    those that don't use `super()`.
    """

    # Step 1: Identify super-respecting classes:
    # (crude guess: look at if "super" is in source)
    super_respecting = set()
    # for base in cls.__mro__:
    for base in cls.__bases__:
        if base in (object, stop_at, skip_class):
            continue
        # try:
        # if hasattr(base, "__init__"):
        #     src = inspect.getsource(base.__init__)
        #     if "super(" in src:
        #         super_respecting.add(base)
        if uses_super(base):
            super_respecting.add(base)
        # except Exception:
        #     pass

    # Maybe skip this next step, since the classes will be called again
    # as part of the super-respecting chains (as individual single-link
    # chains)?
    # # Step 2: Call init for non-super-respecting classes:
    # for base in cls.__mro__:
    #     if base in (object, stop_at, skip_class) or base in called:
    #         continue
    #     if base not in super_respecting and base in split:
    #         args = split[base].get("args", [])
    #         kwargs = split[base].get("kwargs", {})
    #         if DEBUG_PRINTS:
    #             print(
    #                 "[call_init_chain_respecting_super] Calling init of "
    #                 f"non-super-respecting class {base.__name__}"
    #             )
    #         base.__init__(self, *args, **kwargs)  # type: ignore[misc] # pylint: disable=unnecessary-dunder-call
    #         called.add(base)

    # Step 3: Collect args and kwargs for super-respecting chain:
    # first_bases = []
    chains = find_super_chains(cls)
    first_bases = [chain[0] for chain in chains]
    super_args: dict[type, list] = {}
    super_kwargs: dict[type, dict] = {}
    # super_args = []
    # super_kwargs = {}
    # for base in cls.__mro__:
    #     if base in super_respecting:
    #         # if not first_base:
    #         #     first_base = base
    #         # What is the correct criteria to start a new "first_base"?
    #         if ___________:
    #             first_bases.append(base)
    #         super_args.extend(split[base].get("args", []))
    #         super_kwargs.update(split[base].get("kwargs", {}))
    #         # super(base, self).__init__(*args, **kwargs)
    #         break
    for chain in chains:
        base = chain[0]
        super_args[base] = []
        super_kwargs[base] = {}
        for link in chain:
            if link in split:
                super_args[base].extend(split[link]["args"])
                super_kwargs[base].update(split[link]["kwargs"])

    # Step 4: Begin super-respecting chain from first super-respecting class in MRO:
    for base in first_bases:
        if base in (skip_class,):
            continue
        if DEBUG_PRINTS:
            print(
                "[call_init_chain_respecting_super] Calling init of "
                f"super-respecting class {base.__name__}"
            )
        # super(base, self).__init__(*super_args[base], **super_kwargs[base])
        base.__init__(  # type: ignore[misc] # pylint: disable=unnecessary-dunder-call
            self, *super_args[base], **super_kwargs[base]
        )


def accepts_kwargs(cls) -> bool:
    """Determine whether a class accepts kwargs."""
    sig = inspect.signature(cls.__init__)
    return any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())


def get_qualified_path(node, parents):
    """Construct fully qualified class name from parents and the node itself."""
    return ".".join(parents + [node.name])


def find_class_with_path(module, target_path):
    """Recursively search for a class by its qualified path (e.g., TestFoo.C).
    Returns the AST node if found, else None.
    """

    def recurse(node, parents):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                if (get_qualified_path(child, parents)) == target_path:
                    return child
                if result := recurse(child, parents + [child.name]):
                    return result
        return None

    return recurse(module, [])


def get_class_qualname(cls):
    """Return fully qualified class name including enclosing classes.
    Handles nested classes by parsing __qualname__.
    """
    parts = cls.__qualname__.split(".")
    return ".".join(parts)


def uses_super(cls) -> bool:
    """Determine whether a clss uses super."""
    # if hasattr(cls, "__init__"):
    #     src = inspect.getsource(cls.__init__)
    #     if "super(" in src:  # pylint: disable=magic-value-comparison
    #         return True
    # return False
    try:  # pylint: disable=too-many-try-statements,too-many-nested-blocks
        if (sourcefile := inspect.getsourcefile(cls)) is None:
            return False

        with open(sourcefile, "r", encoding="utf8") as f:
            sourcecode = f.read()

        sourcecode = textwrap.dedent(sourcecode)
        module = ast.parse(sourcecode)

        fq_path = get_class_qualname(cls)
        if not (class_node := find_class_with_path(module, fq_path)):
            return False  # Class not found

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Call):
                        func = stmt.func
                        if (  # pylint: disable=too-many-boolean-expressions
                            isinstance(func, ast.Name) and func.id == "super"
                        ) or (
                            isinstance(func, ast.Attribute)
                            and isinstance(func.value, ast.Call)
                            and isinstance(func.value.func, ast.Name)
                            and func.value.func.id == "super"
                        ):
                            return True
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[uses_super] Error: {e}")
        return False


def find_super_chains(cls, stop_at=object):
    """Find chains of super-respecting classes."""
    mro = cls.mro()[1:]  # exclude cls itself
    chains = []
    current_chain = []

    for c in mro:
        # if accepts_kwargs(c) and uses_super(c):
        #     current_chain.append(c)
        # else:
        #     if current_chain:
        if c in (object, stop_at):
            break
        current_chain.append(c)
        if not (accepts_kwargs(c) and uses_super(c)):
            chains.append(list(current_chain))
            current_chain = []
    if current_chain:
        chains.append(current_chain)
    return chains


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


# def _find_calling_class_from_init_old(instance):  # pylint: disable=too-complex
#     """Examine classes in MRO of `instance` to find whose `__init__` contains
#     a direct call to `apply_split_inits_old`.
#     """
#     apply_split_inits_name = "apply_split_inits_old"
#     cls = type(instance)
#     for base in cls.__mro__:
#         if DEBUG_PRINTS:
#             print(
#                 f"\n[_find_calling_class_from_init] Inspecting parent class: {base.__name__}"
#             )
#         if base is object:
#             if DEBUG_PRINTS:
#                 print(
#                     f"\n[_find_calling_class_from_init] Found hierarchy pinnacle: {base.__name__}"
#                 )
#             continue
#         if not (init := base.__dict__.get("__init__")):
#             if DEBUG_PRINTS:
#                 print(
#                     f"\n[_find_calling_class_from_init] {base.__name__} has no __init__ method."
#                 )
#             continue

#         try:  # pylint: disable=too-many-try-statements
#             instructions = list(dis.get_instructions(init))
#             for instr in instructions:
#                 if (
#                     instr.opname in set(["LOAD_GLOBAL", "LOAD_METHOD"])
#                     and instr.argval == apply_split_inits_name
#                 ):
#                     return base
#         except TypeError as e:
#             if DEBUG_PRINTS:
#                 print(
#                     f"\n[_find_calling_class_from_init] Encountered TypeError: {e}"
#                 )
#             continue  # Skip builtins or non-Python functions
#     return None


# def apply_split_inits_old(  # pylint: disable=too-complex,too-many-branches
#     self, cls=None, args=(), kwargs=None, skip_class=None
# ):
#     """Call __init__ of all base classes using split argument mapping."""
#     cls = cls or type(self)
#     kwargs = kwargs or {}
#     if DEBUG_PRINTS:
#         # print(
#         #     f"\n[apply_split_inits] Called from class: {_find_calling_class_from_init(self)}"
#         # )
#         print(f"\n[apply_split_inits] Running for class: {cls.__name__}")
#     # Automatically detect skip class as the defining class of apply_split_inits:
#     if skip_class is None:
#         if (skip_class := _find_calling_class_from_init_old(self)) is None:
#             if DEBUG_PRINTS:
#                 print(
#                     "[apply_split_inits] Warning: Failed to auto-detect skip_class."
#                 )
#         else:  # pylint: disable=else-if-used,confusing-consecutive-elif
#             if DEBUG_PRINTS:  # pylint: disable=confusing-consecutive-elif
#                 print(
#                     f"[apply_split_inits] Auto-detected skip_class as: {skip_class.__name__}"
#                 )
#     split = split_args_for_inits_strict_kwargs(cls, args, kwargs)
#     seen = set()
#     for base in cls.__mro__[1:]:
#         if base in (object,) or base in seen:
#             continue
#         if base is skip_class:
#             if DEBUG_PRINTS:
#                 print(f"[apply_split_inits] Skipping class {base.__name__}")
#             continue
#         seen.add(base)
#         if base in split:
#             base_args = split[base]["args"]
#             base_kwargs = split[base]["kwargs"]
#             if DEBUG_PRINTS:
#                 print(
#                     f"[apply_split_inits] Calling __init__ of {base.__name__} with:"
#                 )
#                 print(f"    args: {base_args}")
#                 print(f"    kwargs: {base_kwargs}")
#             if hasattr(base, "__init__"):
#                 try:  # pylint: disable=too-many-try-statements
#                     # base.__init__(self, *base_args, **base_kwargs)
#                     # if DEBUG_PRINTS:
#                     #     print(
#                     #         f"[apply_split_inits] __init__ call succeeded for {base.__name__}."
#                     #     )
#                     # super(base, self).__init__(self, *base_args, **base_kwargs)
#                     super(base, self).__init__(*base_args, **base_kwargs)
#                     if DEBUG_PRINTS:
#                         print(
#                             f"[apply_split_inits] super() call succeeded for {base.__name__}."
#                         )
#                 except TypeError as e:
#                     # print(f"[Warning] Skipped {base.__name__} due to: {e}")
#                     # continue
#                     if DEBUG_PRINTS:
#                         print(
#                             f"[apply_split_inits] TypeError using super() for {base.__name__}:"
#                             f" {e}"
#                         )
#                         print(
#                             f"[apply_split_inits] Falling back to direct call for {base.__name__}"
#                         )
#                     try:
#                         # Fall back to direct init in edge cases:
#                         base.__init__(  # pylint: disable=unnecessary-dunder-call
#                             self, *base_args, **base_kwargs
#                         )
#                     except (  # pylint: disable=broad-exception-caught
#                         Exception
#                     ) as e1:
#                         if DEBUG_PRINTS:
#                             print(
#                                 f"[apply_split_inits] Direct call failed for {base.__name__}:"
#                                 f" {e1}"
#                             )
#     #         args_for_super.extend(base_args)
#     #         kwargs_for_super.update(base_kwargs)
#     # # One and only call to super()
#     # try:
#     #     super(cls, self).__init__(*args_for_super, **kwargs_for_super)
#     #     if DEBUG_PRINTS:
#     #         print(f"[apply_split_inits] super() call succeeded for {cls.__name__}.")
#     # except TypeError as e:
#     #     if DEBUG_PRINTS:
#     #         print(f"[apply_split_inits] TypeError in super call: {e}")
#     #     raise
#     self._init_leftovers = split.get(  # pylint: disable=protected-access
#         LEFTOVERS, {"args": [], "kwargs": {}}
#     )
#     if DEBUG_PRINTS:
#         print(
#             "[apply_split_inits] Leftovers set to:"
#             f" {self._init_leftovers}"  # pylint: disable=protected-access
#         )
#     return self._init_leftovers  # pylint: disable=protected-access


def apply_split_inits(self, cls=None, args=(), kwargs=None, skip_class=None):
    """Apply the split to the parent classes, first those who don't respect super
    and then those who do based on the MRO chainsextracted from the parent classes.
    """
    cls = cls or type(self)
    kwargs = kwargs or {}
    if DEBUG_PRINTS:
        # print(
        #     f"\n[apply_split_inits] Called from class: {_find_calling_class_from_init(self)}"
        # )
        print(f"\n[apply_split_inits] Running for class: {cls.__name__}")
    # Automatically detect skip class as the defining class of apply_split_inits:
    if skip_class is None:
        if (skip_class := _find_calling_class_from_init(self)) is None:
            if DEBUG_PRINTS:
                print(
                    "[apply_split_inits] Warning: Failed to auto-detect skip_class."
                )
        else:  # pylint: disable=else-if-used,confusing-consecutive-elif
            if DEBUG_PRINTS:  # pylint: disable=confusing-consecutive-elif
                print(
                    f"[apply_split_inits] Auto-detected skip_class as: {skip_class.__name__}"
                )
    split = split_args_for_inits_strict_kwargs(cls, args, kwargs)
    share_missing_params_across_parents(split, stop_at=object)
    call_init_chain_respecting_super(
        self, type(self), split, stop_at=object, skip_class=skip_class
    )
    self._init_leftovers = split.get(  # pylint: disable=protected-access
        LEFTOVERS, {"args": [], "kwargs": {}}
    )
    if DEBUG_PRINTS:
        print(
            f"[apply_split_inits] Leftovers set to: {self._init_leftovers}"  # pylint: disable=protected-access
        )
    return self._init_leftovers  # pylint: disable=protected-access


class SplitInitMixin:  # pylint: disable=too-few-public-methods
    """A mixin class to be used for automatically splitting args across inits.

    Note: this mixin class is not perfect, and will fail under certain circumstances:
     - If some parent class has only positional arguments and comes before another
       parent class with kwargs, the first parent may fail to initialize (whether or not it
       calls super).
    [The following parts ay not apply anymore, using the new apply_split_inits:
     - Calling super().__init__() in apply_split_inits can skip the init methods
       for the direct parent classes, so they won't get ininialized.
     - Changing the calls in apply_split_inits from super().__init__() to
       calling the init of each parent directly results in recursion.
     - Changing the calls in apply_split_inits from super().__init__() to
       calling the super().__init__() once also results in recursion.
    The big dilema is we want
     - To automate splitting and routing *args and **kwargs to multiple __init__ methods.
     - To work cooperatively with super(), without requiring all third-party classes to cooperate.
     - To avoid recursion and ensure each __init__ is called exactly once.
     - To not manually walk the MRO, because that breaks super() semantics and third-party
       expectations.
    So we can't really have all three of the following at the same time, only two:
     - Automatic argument splitting
     - Compatibility with arbitrary third-party __init__ methods
     - Full preservation of Python's super()]

    Usage example:
    class Child(SplitInitMixin, Parent1, Parent2):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Use self._init_leftovers if needed
    """

    def __init__(self, *args, **kwargs):
        """New init for the class."""
        self._init_leftovers = apply_split_inits(
            self, cls=type(self), args=args, kwargs=kwargs
        )  # , skip_class=SplitInitMixin)


def auto_split_init(cls):
    """A decorator to be used for automatically splitting args across inits.

    Note: this decorator is not perfect, and will fail under certain circumstances:
     - If some parent class has only positional arguments and comes before another
       parent class with kwargs, the first parent may fail to initialize (whether or not it
       calls super).
     - Calling super().__init__() in apply_split_inits can skip the init methods
       for the direct parent classes, so they won't get ininialized.
     - Changing the calls in apply_split_inits from super().__init__() to
       calling the init of each parent directly results in recursion.
     - Changing the calls in apply_split_inits from super().__init__() to
       calling the super().__init__() once also results in recursion.
    The big dilema is we want
     - To automate splitting and routing *args and **kwargs to multiple __init__ methods.
     - To work cooperatively with super(), without requiring all third-party classes to cooperate.
     - To avoid recursion and ensure each __init__ is called exactly once.
     - To not manually walk the MRO, because that breaks super() semantics and third-party
       expectations.
    So we can't really have all three of the following at the same time, only two:
     - Automatic argument splitting
     - Compatibility with arbitrary third-party __init__ methods
     - Full preservation of Python's super()

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
