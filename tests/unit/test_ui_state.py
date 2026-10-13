from types import SimpleNamespace

import pytest

from app.ui import state


@pytest.fixture
def session(monkeypatch):
    store: dict = {}
    monkeypatch.setattr(state, "st", SimpleNamespace(session_state=store))
    return store


# The widget keys are the strings the screen used before state.py existed. Streamlit ties a
# typed-but-unsaved value to its key, so a changed spelling drops what a person typed.
def test_widget_keys_keep_their_original_spelling():
    assert state.file_key("order_number") == "file-order_number"
    assert state.value_key("doc1", "total_amount") == "value-doc1-total_amount"
    assert state.paper_key("doc1:vendor_code") == "paper-doc1:vendor_code"
    assert state.line_key("doc1:line:2:tax_code") == "line-doc1:line:2:tax_code"
    assert state.form_key("doc1") == "paper-doc1"
    assert state.prev_key("doc1") == "prev-doc1"
    assert state.next_key("doc1") == "next-doc1"
    assert state.join_key("doc1") == "join-doc1"
    assert state.split_after_key("doc1") == "split-after-doc1"
    assert state.split_key("doc1") == "split-doc1"
    assert state.page_key("doc1") == "page-doc1"
    assert state.override_key("doc1") == "allow-export-with-errors-doc1"


def test_init_sets_show_passed_once(session):
    state.init()
    assert session == {"show_passed": False}
    state.toggle_show_passed()
    state.init()
    assert state.show_passed() is True


def test_toggle_flips_show_passed(session):
    state.init()
    state.toggle_show_passed()
    assert state.show_passed() is True
    state.toggle_show_passed()
    assert state.show_passed() is False


def test_the_override_box_starts_from_what_is_saved_and_is_not_reset_by_later_runs(session):
    state.init_override("d1", True)
    assert session[state.override_key("d1")] is True
    session[state.override_key("d1")] = False  # the person unticked it
    state.init_override("d1", True)  # a later run must not tick it again
    assert session[state.override_key("d1")] is False
    state.init_override("d2", False)
    assert session[state.override_key("d2")] is False


def test_pending_upload_round_trip(session):
    assert state.pending() is None
    state.set_pending("a.pdf", b"%PDF")
    assert state.pending() == {"name": "a.pdf", "data": b"%PDF"}
    state.clear_pending()
    assert state.pending() is None
    state.clear_pending()  # clearing twice is fine


def test_open_and_close_a_dossier(session):
    assert state.dossier_id() is None
    state.open_dossier("d1")
    assert state.dossier_id() == "d1"
    state.close_dossier()
    assert state.dossier_id() is None


def test_current_page_uses_the_remembered_page_when_it_belongs_to_the_paper(session):
    assert state.current_page("p", 3, (2, 3)) == 3
    state.set_page("p", 2)
    assert state.current_page("p", 3, (2, 3)) == 2


def test_current_page_falls_back_when_the_remembered_page_is_gone(session):
    state.set_page("p", 9)  # e.g. the paper was split and no longer owns page 9
    assert state.current_page("p", 2, (2, 3)) == 2


def test_current_page_of_a_paper_without_pages_is_none(session):
    assert state.current_page("p", None, ()) is None
