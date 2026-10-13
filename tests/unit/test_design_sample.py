import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _builder():
    spec = importlib.util.spec_from_file_location("build_sample", ROOT / "design" / "build_sample.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_committed_sample_is_current():
    html = _builder().render()
    committed = (ROOT / "design" / "sample.html").read_text()
    assert committed == html, "design/sample.html is out of date: run `python3 design/build_sample.py`"


def test_the_sample_is_drawn_with_the_real_components_and_none_of_the_old_look():
    html = (ROOT / "design" / "sample.html").read_text()
    for marker in ('class="banner warn"', 'class="totals"', 'class="chip warn"', 'class="pdf-printed"', 'class="wordmark"'):
        assert marker in html, marker
    assert not re.search(r"\bInter\b|Iowan|Palatino|Georgia", html)
    assert not re.search(r"border-(left|right)\s*:\s*[2-9]\d*px", html)  # no bar on the side of a box (a 2px tab underline is by design)
    assert not re.search(r"box-shadow\s*:(?!\s*none)", html)
    assert "#f4f1ea" not in html  # the old cream ground
