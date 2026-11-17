from collections.abc import Collection

from . import auth, web  # noqa: F401


def trusted_target(value: object, allowed: Collection[str], default: str) -> str:
    """Whitelist a user-supplied redirect target.

    Returns the matching member of `allowed` (or `default`) — the trusted
    constant itself, never the request-derived copy — so no user data
    flows into a RedirectResponse (CWE-601; keeps CodeQL's url-redirection
    check quiet, unlike an ``if value not in allowed`` reassignment).
    """
    for target in allowed:
        if value == target:
            return target
    return default
