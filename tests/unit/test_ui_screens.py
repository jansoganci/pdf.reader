"""Smoke and behaviour tests that run the real screens with Streamlit's AppTest.

The fake provider is on (tests/conftest.py), so nothing calls a model.
"""

from pathlib import Path

import fitz
import pytest
from streamlit.testing.v1 import AppTest

from app.service import get_dossier
from app.storage import db
from tests.ui_fixtures import maroc_dossier

MAIN = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "main.py")


def _run(**session) -> AppTest:
    at = AppTest.from_file(MAIN, default_timeout=30)
    for key, value in session.items():
        at.session_state[key.replace("__", "-")] = value
    return at.run()


def _seed(dossier_id: str, **kwargs):
    dossier = maroc_dossier(dossier_id, **kwargs)
    db.save_dossier(dossier)
    pdf = fitz.open()
    for number in range(1, 11):
        page = pdf.new_page()
        page.insert_text((72, 90), f"Sample page {number}", fontsize=20)
    db.original_path(dossier_id).write_bytes(pdf.tobytes())
    return dossier


def _tiny_pdf() -> bytes:
    pdf = fitz.open()
    pdf.new_page().insert_text((72, 90), "hello", fontsize=20)
    return pdf.tobytes()


def _text(at: AppTest) -> str:
    return "\n".join(item.value for item in at.markdown)


def _save_button(at: AppTest, paper_id: str):
    return next(b for b in at.button if b.label == "Save" and b.proto.form_id == f"paper-{paper_id}")


# -- start and reading ---------------------------------------------------------------

def test_the_start_screen_asks_for_a_pdf():
    at = _run()
    assert not at.exception
    assert at.header[0].value == "Would you like to read a new import file?"
    assert [b.label for b in at.button] == ["Read this PDF"]


def test_pressing_read_without_a_file_warns():
    at = _run()
    at.button[0].click().run()
    assert "Choose a PDF first." in _text(at)


def test_a_waiting_pdf_is_read_and_its_dossier_opens():
    at = _run(pending={"name": "tiny.pdf", "data": _tiny_pdf()})
    assert not at.exception
    assert at.session_state["dossier_id"]
    assert "pending" not in at.session_state


def test_a_bad_file_shows_the_reason_and_a_way_back():
    at = _run(pending={"name": "x.pdf", "data": b"not a pdf"})
    assert not at.exception
    assert "File was not accepted. Upload one PDF." in _text(at)
    assert "pending" not in at.session_state  # the bad file is forgotten
    at.button[0].click().run()
    assert at.header[0].value == "Would you like to read a new import file?"


# -- the review screen ---------------------------------------------------------------

def test_the_review_screen_shows_eight_tabs_and_the_dossier_state():
    _seed("screen-a", maersk_last_line="1500.00")
    at = _run(dossier_id="screen-a")
    assert not at.exception
    assert [tab.label for tab in at.tabs] == [
        "• Broker invoice", "• Customs payment", "Logistics invoice", "Logistics invoice",
        "• Shipping invoice", "Customs declaration", "Supplier invoice", "Import licence",
    ]
    text = _text(at)
    assert "Import file" in text and "8 papers read" in text and "Blocks download" in text
    assert "1 item(s) block the download until you check them." in text


def test_values_and_typed_boxes_are_filled_from_the_dossier():
    _seed("screen-b")
    at = _run(dossier_id="screen-b")
    assert at.text_input(key="value-liquidation-total_amount").value == "44,004.00 MAD"
    assert at.text_input(key="paper-liquidation:sap_reference").value == ""
    assert not any(box.key == "paper-broker:tax_code" for box in at.text_input)  # per line instead
    assert at.text_input(key="line-broker:line:1:tax_code").value == ""


def test_a_clean_dossier_is_ready_to_download():
    _seed("screen-c", flag_review=False)
    at = _run(dossier_id="screen-c")
    assert "Ready to download." in _text(at)
    assert not at.checkbox  # nothing blocks, so no override box


def test_flagged_values_keep_the_dossier_from_saying_ready():
    _seed("screen-c2")  # three totals flagged, every check passes
    at = _run(dossier_id="screen-c2")
    text = _text(at)
    assert "Ready to download" not in text
    assert "3 value(s) might need a second look before you download." in text
    assert "Needs a check" in text


def test_a_blocked_dossier_offers_the_override_and_remembers_it():
    _seed("screen-d", maersk_last_line="1500.00")
    at = _run(dossier_id="screen-d")
    assert at.checkbox(key="allow-export-with-errors").label.startswith("Download anyway")
    at.checkbox(key="allow-export-with-errors").check().run()
    assert get_dossier("screen-d").export_with_errors is True
    assert not at.checkbox  # the override box is gone once it is on


def test_show_passed_checks_toggles():
    _seed("screen-e", flag_review=False)
    at = _run(dossier_id="screen-e")
    assert any(b.label == "Show passed checks" for b in at.button)
    next(b for b in at.button if b.label == "Show passed checks").click().run()
    assert any(b.label == "Hide passed checks" for b in at.button)
    assert at.session_state["show_passed"] is True


def test_a_two_page_paper_opens_on_the_flagged_page_and_steps_back():
    _seed("screen-f")
    at = _run(dossier_id="screen-f")
    assert "Page 3 · 2 of 2 for this paper" in _text(at)
    at.button(key="prev-liquidation").click().run()
    assert "Page 2 · 1 of 2 for this paper" in _text(at)
    assert at.session_state["page-liquidation"] == 2
    assert at.button(key="prev-liquidation").disabled


def test_saving_a_correction_updates_the_dossier_and_keeps_the_original():
    _seed("screen-g")
    at = _run(dossier_id="screen-g")
    at.text_input(key="value-liquidation-total_amount").set_value("50000.00")
    at.text_input(key="paper-liquidation:vendor_code").set_value("V-123")
    at.text_input(key="file-order_number").set_value("4500")
    _save_button(at, "liquidation").click().run()
    assert not at.exception
    saved = get_dossier("screen-g")
    total = next(doc for doc in saved.documents if doc.id == "liquidation").fields["total_amount"]
    assert total.user_value == "50000.00" and total.value == "44004.00"  # the original is kept
    assert saved.manual["liquidation:vendor_code"] == "V-123"
    assert saved.manual["order_number"] == "4500"
    assert at.text_input(key="value-liquidation-total_amount").value == "50,000.00 MAD"


def test_saving_without_a_change_makes_no_correction():
    _seed("screen-h")
    at = _run(dossier_id="screen-h")
    _save_button(at, "supplier").click().run()
    saved = get_dossier("screen-h")
    assert all(f.user_value is None for doc in saved.documents for f in doc.fields.values())


def test_joining_a_paper_with_the_one_above_merges_them():
    _seed("screen-i")
    before = len(get_dossier("screen-i").documents)
    at = _run(dossier_id="screen-i")
    at.button(key="join-liquidation").click().run()
    assert not at.exception
    assert len(get_dossier("screen-i").documents) == before - 1


def test_splitting_a_two_page_paper_makes_two_papers():
    _seed("screen-j")
    before = len(get_dossier("screen-j").documents)
    at = _run(dossier_id="screen-j")
    at.button(key="split-liquidation").click().run()
    assert not at.exception
    assert len(get_dossier("screen-j").documents) == before + 1


def test_the_first_paper_has_no_join_button():
    _seed("screen-k")
    at = _run(dossier_id="screen-k")
    assert not any(b.key == "join-broker" for b in at.button)


def test_a_missing_dossier_says_so():
    at = _run(dossier_id="does-not-exist")
    assert not at.exception
    assert "This file could not be opened." in _text(at)


def test_read_another_file_returns_to_the_start_screen():
    _seed("screen-l")
    at = _run(dossier_id="screen-l")
    next(b for b in at.button if b.label == "Read another file").click().run()
    assert at.header[0].value == "Would you like to read a new import file?"


def test_a_hostile_issuer_name_is_shown_as_text_not_markup():
    hostile = '<img src=x id="pwn"> **BOLD** [l](http://evil.example/)'
    _seed("screen-m", supplier_name=hostile)
    at = _run(dossier_id="screen-m")
    assert not at.exception
    html = _text(at)
    assert "<img" not in html and "&lt;img" in html
