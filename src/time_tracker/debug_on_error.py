"""This module provides a hook to open a debugging session on any terminating exception."""

import sys
from types import TracebackType


def info(
    exctype: type[BaseException],
    value: BaseException,
    tb: TracebackType | None,
):
    """This function provides the hook to open a debugging session on error.

    Args:
        exctype (type[BaseException]): Type of exception.
        value (BaseException): Exception.
        tb (TracebackType | None): Traceback.
    """
    if hasattr(sys, "ps1") or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a tty-like
        # device, so we call the default hook
        sys.__excepthook__(exctype, value, tb)
    else:
        import pdb  # pylint: disable=import-outside-toplevel
        import traceback  # pylint: disable=import-outside-toplevel

        # we are NOT in interactive mode, print the exception...
        traceback.print_exception(exctype, value, tb)
        print  # pylint: disable=pointless-statement
        # ...then start the debugger in post-mortem mode.
        # pdb.pm() # deprecated
        pdb.post_mortem(tb)  # more "modern"


sys.excepthook = info
