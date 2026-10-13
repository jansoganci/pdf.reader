"""Layer rules from docs/UI_PLAN.md section 3, checked on the import lines."""

import re
from pathlib import Path

UI = Path(__file__).resolve().parents[2] / "app" / "ui"


def _imports(path: Path) -> list[str]:
    return re.findall(r"^\s*(?:from|import)\s+([\w.]+)", path.read_text(), re.MULTILINE)


def _files(folder: str) -> list[Path]:
    return sorted((UI / folder).glob("*.py"))


def test_only_screens_call_the_service():
    for path in UI.rglob("*.py"):
        if "screens" in path.parts:
            continue
        assert not any(name.startswith("app.service") for name in _imports(path)), path.relative_to(UI)


def test_pure_layers_never_import_streamlit():
    pure = [UI / "view.py", UI / "words.py", *_files("components")]
    for path in pure:
        assert "streamlit" not in _imports(path), path.relative_to(UI)


def test_lower_layers_never_import_higher_ones():
    rules = {
        "components": ("app.ui.widgets", "app.ui.screens", "app.ui.view", "app.ui.state"),
        "widgets": ("app.ui.screens",),
        "theme": ("app.ui.widgets", "app.ui.screens", "app.ui.view", "app.ui.components"),
    }
    for folder, forbidden in rules.items():
        for path in _files(folder):
            bad = [name for name in _imports(path) if name.startswith(forbidden)]
            assert not bad, f"{path.relative_to(UI)} imports {bad}"
    for path in (UI / "view.py", UI / "state.py"):
        bad = [name for name in _imports(path) if name.startswith(("app.ui.widgets", "app.ui.screens"))]
        assert not bad, f"{path.name} imports {bad}"


def test_main_is_only_a_router():
    assert len((UI / "main.py").read_text().splitlines()) <= 60


def test_no_ui_file_becomes_a_monolith_again():
    # main.py held everything at 690 lines. The ceiling leaves room for view.py, the largest file.
    for path in UI.rglob("*.py"):
        assert len(path.read_text().splitlines()) <= 350, path.relative_to(UI)
