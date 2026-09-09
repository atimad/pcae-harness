"""Shared test helper (N16-5-F-5-B2-IMPL consumer-authenticity repair).

Construct a call whose REAL, stack-inspectable caller module identity is an
arbitrary chosen name, WITHOUT using the disclosed (and, since the repair,
no-longer-authoritative) ``_caller_module`` keyword-argument seam on the
PAWA privileged factories in ``pcae.core.hpac_protected_admin_writer``.

This exercises the actual caller-provenance mechanism
(``_detect_caller_module``'s ``inspect.stack()`` walk over
``frame.f_globals["__name__"]``) rather than the removed
trust-the-caller-supplied-string shortcut. Building a throwaway module
object and executing code inside it is a materially different,
undocumented, in-process-code-execution technique from the one-line public
keyword argument the finding closed — see
docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md
§32 "Recognition predicate 6" ("the importing / calling **source
module**... a build-time / import-time fact").
"""

from __future__ import annotations

import types
from typing import Any, Callable


def call_with_real_module_identity(module_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Invoke ``fn(*args, **kwargs)`` from a call that genuinely,
    unspoofably originates from a module named ``module_name`` (from the
    perspective of ``inspect.stack()`` frame introspection). The scratch
    module is deliberately NOT registered in ``sys.modules`` — caller
    identity here is read only from the live frame's ``f_globals``, never
    from the module registry, so registration is unnecessary and would
    only risk polluting ``sys.modules`` for other tests.
    """

    scratch = types.ModuleType(module_name)
    scratch.__dict__["__name__"] = module_name
    scratch.__dict__["_fn"] = fn
    scratch.__dict__["_args"] = args
    scratch.__dict__["_kwargs"] = kwargs
    code = "_result = _fn(*_args, **_kwargs)"
    exec(compile(code, f"<{module_name}>", "exec"), scratch.__dict__)
    return scratch.__dict__["_result"]
