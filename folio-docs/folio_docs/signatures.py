"""Shared rendering for source signatures consumed by both products."""

from __future__ import annotations

from folio_docs.ir import FunctionIR


def render_signature(func: FunctionIR, *, show_parens: bool = True) -> str:
    """Render a Python function signature without product-specific markup."""
    prefix = "async def" if func.is_async else "def"
    params: list[str] = []
    has_var_positional = any(arg.kind == "var_positional" for arg in func.args)
    last_positional_only = max(
        (index for index, arg in enumerate(func.args) if arg.kind == "positional_only"),
        default=-1,
    )
    inserted_positional_separator = False
    inserted_keyword_separator = False

    for index, arg in enumerate(func.args):
        if arg.kind == "keyword_only" and not inserted_keyword_separator:
            inserted_keyword_separator = True
            if not has_var_positional:
                params.append("*")

        if arg.kind == "var_positional":
            part = f"*{arg.name}"
        elif arg.kind == "var_keyword":
            part = f"**{arg.name}"
        else:
            part = arg.name

        if arg.type:
            part += f": {arg.type}"
        if arg.default is not None:
            part += f" = {arg.default}"
        params.append(part)

        if (
            arg.kind == "positional_only"
            and index == last_positional_only
            and not inserted_positional_separator
            and index < len(func.args) - 1
        ):
            inserted_positional_separator = True
            params.append("/")

    if not show_parens:
        return func.name
    signature = f"{prefix} {func.name}({', '.join(params)})"
    if func.returns:
        signature += f" -> {func.returns.type}"
    return signature
