"""The French / English switch: the two catalogs agree, no key is used or left unused by
mistake, the screen follows the switch, and French leaves no English behind."""

import ast
import re
import threading
from pathlib import Path

import fitz
import pytest
from streamlit.testing.v1 import AppTest

from app.config import settings
from app.pdf.render import PdfRejected, render_pdf
from app.ui import lang, state, view
from app.ui.words import rejection_text
from tests.ui_fixtures import maroc_dossier

UI = Path(__file__).resolve().parents[2] / "app" / "ui"
MAIN = str(UI / "main.py")
EN, FR = lang.en.MESSAGES, lang.fr.MESSAGES

# Keys built from data at run time (a paper type, a field key, a rule id), so no literal names them.
DYNAMIC_PREFIXES = (
    "paper.", "number.", "field.", "manual.", "check.failed.", "check.passed.", "tier.", "reject.",
    "wordmark.papers.", "pages.",
)


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.use("en")


def _slots(message: str) -> set[str]:
    return set(re.findall(r"{(\w+)}", message))


def _literal_keys() -> set[str]:
    """Every `t("...")` / `tn("...")` key written out in app/ui."""
    found = set()
    for path in UI.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)  # t(...) or lang.t(...)
            first = node.args[0]
            if name in ("t", "tn") and isinstance(first, ast.Constant) and isinstance(first.value, str):
                if name == "tn":
                    found.update({first.value + ".one", first.value + ".other"})
                else:
                    found.add(first.value)
    return found


# -- the catalogs --------------------------------------------------------------------

def test_both_languages_have_the_same_keys():
    assert set(EN) == set(FR)


def test_a_key_has_the_same_slots_in_both_languages():
    for key in EN:
        assert _slots(EN[key]) == _slots(FR[key]), key


def test_no_sentence_is_empty():
    for catalog in (EN, FR):
        assert all(text.strip() for text in catalog.values())


def test_every_key_written_in_code_exists():
    assert _literal_keys() <= set(EN)


def test_every_key_is_used_by_code_or_built_from_data():
    used = _literal_keys()
    unused = [k for k in EN if k not in used and not k.startswith(DYNAMIC_PREFIXES)]
    assert unused == []


def test_the_default_language_is_the_first_one_on_the_switch():
    # The switch is given no `index`, so its first option is what a new person sees.
    assert lang.LANGUAGES[0] == lang.DEFAULT_LANGUAGE
    assert set(lang.LANGUAGES) == set(lang.CATALOGS) == set(lang.SWITCH_LABELS)


def test_the_language_key_is_pinned():
    assert state.LANGUAGE_KEY == "lang"


# -- looking words up ----------------------------------------------------------------

def test_english_is_what_code_outside_a_run_speaks():
    assert lang.current() == "en"
    assert lang.t("start.read") == "Read this PDF"


def test_a_missing_key_is_a_bug_not_a_blank():
    with pytest.raises(KeyError):
        lang.t("no.such.key")


def test_an_unknown_language_is_refused():
    with pytest.raises(ValueError):
        lang.use("de")


def test_slots_are_filled_without_reading_inside_the_value():
    lang.use("fr")
    # Text from a PDF is a value, never a template: braces in it come through as typed.
    assert lang.t("reading.name", name="{n} <b>x</b>.pdf") == "{n} <b>x</b>.pdf est en cours de lecture."


def test_plural_follows_the_count():
    assert lang.tn("wordmark.papers", 1) == "1 paper read"
    assert lang.tn("wordmark.papers", 8) == "8 papers read"
    lang.use("fr")
    assert lang.tn("wordmark.papers", 1) == "1 pièce lue"
    assert lang.tn("wordmark.papers", 8) == "8 pièces lues"


def test_one_thread_cannot_change_the_language_of_another():
    lang.use("fr")
    seen = []
    worker = threading.Thread(target=lambda: seen.append(lang.current()))
    worker.start()
    worker.join()
    assert seen == ["en"] and lang.current() == "fr"


# -- the view in French --------------------------------------------------------------

def _strings(value):
    """Every string inside a view object."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _strings(item)
    elif hasattr(value, "__dataclass_fields__"):
        for name in value.__dataclass_fields__:
            yield from _strings(getattr(value, name))


def test_the_french_view_holds_no_english_sentence():
    dossier = maroc_dossier()
    lang.use("en")
    english = set(_strings(view.build(dossier)))
    lang.use("fr")
    french = set(_strings(view.build(dossier)))
    shared_words = {EN[k] for k in EN if EN[k] == FR[k]}  # "Date", "FOB", "Total": the same in both
    english_sentences = {EN[k] for k in EN if "{" not in EN[k]} - shared_words
    assert not (french & english_sentences)
    assert french != english


def test_passed_checks_say_what_validation_said_in_english():
    # The English catalog repeats the sentences in app/validation/rules.py; if one changes there,
    # this fails and the catalog (and its French) must follow.
    dossier = maroc_dossier()
    for item in dossier.validation:
        if item.status == "passed" and lang.has(f"check.passed.{item.rule_id}"):
            assert EN[f"check.passed.{item.rule_id}"] == item.message


# -- refused PDFs --------------------------------------------------------------------

def _refusal(data: bytes, tmp_path) -> str:
    with pytest.raises(PdfRejected) as caught:
        render_pdf(data, tmp_path)
    return caught.value.message


def _pdf(pages: int = 1, encrypt: bool = False) -> bytes:
    pdf = fitz.open()
    for _ in range(pages):
        pdf.new_page().insert_text((72, 90), "x")
    if encrypt:
        return pdf.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="a", owner_pw="b")
    return pdf.tobytes()


def test_every_refusal_render_pdf_can_give_has_a_french_sentence(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "max_pages", 2)
    messages = {
        _refusal(b"x" * (settings.max_upload_bytes + 1), tmp_path),
        _refusal(b"not a pdf", tmp_path),
        _refusal(b"%PDF-1.4 broken", tmp_path),
        _refusal(_pdf(encrypt=True), tmp_path),
        _refusal(_pdf(pages=3), tmp_path),
    }
    assert len(messages) == 5
    lang.use("fr")
    for message in messages:
        assert rejection_text(message) != message, message
    assert "2 pages" in rejection_text("File was not accepted. The limit is 2 pages.")


def test_a_refusal_it_does_not_know_is_shown_as_it_came():
    lang.use("fr")
    assert rejection_text("Something new.") == "Something new."


# -- the screen ----------------------------------------------------------------------

def test_the_app_opens_in_french_and_the_switch_changes_every_word():
    at = AppTest.from_file(MAIN, default_timeout=30).run()
    assert not at.exception
    assert at.header[0].value == FR["start.heading"]
    assert [b.label for b in at.button] == [FR["start.read"]]
    assert at.radio(key=state.LANGUAGE_KEY).value == "fr"

    at.radio(key=state.LANGUAGE_KEY).set_value("en").run()
    assert at.header[0].value == EN["start.heading"]
    assert [b.label for b in at.button] == [EN["start.read"]]
    # The switch must still say English after the switch itself was redrawn in English: its label and
    # options may not depend on the language, or Streamlit resets it to French.
    assert at.radio(key=state.LANGUAGE_KEY).value == "en"
    at.run()
    assert at.radio(key=state.LANGUAGE_KEY).value == "en"
    assert at.header[0].value == EN["start.heading"]

    at.radio(key=state.LANGUAGE_KEY).set_value("fr").run()
    assert at.radio(key=state.LANGUAGE_KEY).value == "fr"
    assert at.header[0].value == FR["start.heading"]


def test_the_choice_follows_the_person_to_the_review_screen():
    from app.storage import db

    dossier = maroc_dossier("lang-1")
    db.save_dossier(dossier)
    at = AppTest.from_file(MAIN, default_timeout=30)
    at.session_state["dossier_id"] = "lang-1"
    at.run()
    assert not at.exception
    labels = [b.label for b in at.button]
    assert FR["header.read_another"] in labels and FR["review.show_passed"] in labels
    assert any(FR["paper.customs_declaration"] in tab.label for tab in at.tabs)

    at.radio(key=state.LANGUAGE_KEY).set_value("en").run()
    labels = [b.label for b in at.button]
    assert EN["header.read_another"] in labels and EN["review.show_passed"] in labels
