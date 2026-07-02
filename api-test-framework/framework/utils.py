"""
Utility helpers used across the framework:

1. resolve_env_vars   - substitutes "${ENV_VAR}" placeholders in test data
                         (e.g. API keys) with real environment variable values.
2. AttrDict / _wrap    - lets assertion expressions use dot notation
                         (response.data.id) on top of plain JSON dict/list
                         responses.
3. evaluate_assertion  - safely evaluates a single assertion expression
                         string, e.g. "response.data.id == 2", against a
                         parsed response body. An AST allow-list is used to
                         block anything beyond simple comparisons/lookups.
"""
import ast
import os
import re

_ENV_VAR_PATTERN = re.compile(r"^\$\{(\w+)\}$")


def resolve_env_vars(value):
    """Recursively replace '${VAR_NAME}' strings with os.environ values."""
    if isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_env_vars(v) for v in value]
    if isinstance(value, str):
        match = _ENV_VAR_PATTERN.match(value)
        if match:
            var_name = match.group(1)
            return os.environ.get(var_name, "")
    return value


class AttrDict(dict):
    """A dict that also supports attribute-style access: d.foo.bar.baz"""

    def __getattr__(self, item):
        try:
            value = self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc
        return _wrap(value)

    def __setattr__(self, key, value):
        self[key] = value


def _wrap(value):
    if isinstance(value, dict) and not isinstance(value, AttrDict):
        return AttrDict(value)
    if isinstance(value, list):
        return [_wrap(v) for v in value]
    return value


_ALLOWED_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "isinstance": isinstance,
    "dict": dict,
    "list": list,
    "sorted": sorted,
    "abs": abs,
    "round": round,
}

_FORBIDDEN_NODE_TYPES = (
    ast.Import,
    ast.ImportFrom,
    ast.Lambda,
    ast.FunctionDef,
    ast.ClassDef,
    ast.With,
    ast.Assign,
    ast.AugAssign,
)


class UnsafeAssertionError(ValueError):
    """Raised when an assertion expression contains disallowed constructs."""


def _validate_expression(expression: str) -> None:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, _FORBIDDEN_NODE_TYPES):
            raise UnsafeAssertionError(f"Disallowed construct in assertion: {expression!r}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise UnsafeAssertionError(f"Disallowed dunder access in assertion: {expression!r}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in _ALLOWED_BUILTINS:
                raise UnsafeAssertionError(f"Disallowed function call in assertion: {expression!r}")
            if isinstance(node.func, ast.Attribute):
                raise UnsafeAssertionError(f"Method calls are not allowed in assertions: {expression!r}")


def evaluate_assertion(expression: str, response_body, status_code: int):
    """
    Evaluate a single assertion string against a response.

    Available names inside the expression:
        response     -> parsed JSON body (dict/list), attribute-accessible
        status_code  -> the HTTP status code returned

    Example expressions:
        "response.data.id == 2"
        "len(response) == 100"
        "'first_name' in response.data"
        "status_code == 200"
    """
    _validate_expression(expression)
    context = {
        "response": _wrap(response_body) if response_body is not None else None,
        "status_code": status_code,
    }
    return eval(expression, {"__builtins__": _ALLOWED_BUILTINS}, context)  # noqa: S307 (validated above)
