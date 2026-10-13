"""Guard for docs/design.md principle 8: PDF text never reaches HTML unescaped.

Every `st.markdown(..., unsafe_allow_html=True)` in the screen code must pass either
a constant string or the result of a component builder. A builder escapes its own
arguments (tests/unit/test_ui_components.py). An f-string or a variable there is how
the issuer-name injection got in, so it fails this test.
"""

import ast
from pathlib import Path

UI = Path(__file__).resolve().parents[2] / "app" / "ui"
BUILDERS = {"banner", "summary_card", "wordmark", "plain", "group_title", "field_label", "page_label", "stylesheet"}


def _unsafe_html_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "unsafe_allow_html" and getattr(keyword.value, "value", None) is True:
                yield node


def _is_safe_first_argument(node: ast.Call) -> bool:
    if not node.args:
        return False
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return True
    return isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id in BUILDERS


def test_unsafe_html_only_gets_constants_or_component_builders():
    offenders = []
    for path in UI.rglob("*.py"):
        if "components" in path.parts:
            continue
        tree = ast.parse(path.read_text())
        for call in _unsafe_html_calls(tree):
            if not _is_safe_first_argument(call):
                offenders.append(f"{path.relative_to(UI)}:{call.lineno}")
    assert not offenders, "unsafe_allow_html with a non-constant, non-builder argument: " + ", ".join(offenders)


def test_the_guard_catches_the_old_pattern():
    old = ast.parse('st.markdown(f"<div>{who}</div>", unsafe_allow_html=True)')
    call = next(_unsafe_html_calls(old))
    assert not _is_safe_first_argument(call)
