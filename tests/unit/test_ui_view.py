import pytest

from app.models import DocumentRecord, ValidationResult
from app.ui import view
from tests.ui_fixtures import SUPPLIER, field, maroc_dossier, paper


def _paper(screen, document_id):
    return next(item for item in screen.papers if item.id == document_id)


# -- tiers and the banner ------------------------------------------------------------

def test_a_dossier_with_a_blocking_error_is_crit():
    dossier = maroc_dossier(maersk_last_line="1500.00")
    screen = view.build(dossier)
    assert screen.tier == "crit"
    assert screen.blocking_count == 1
    assert screen.banner_text == "1 item(s) block the download until you check them."


def test_a_dossier_with_only_a_warning_is_warn():
    dossier = maroc_dossier()
    dossier.validation = [
        ValidationResult(rule_id="supported_currency", severity="warning", status="failed", message="x")
    ]
    screen = view.build(dossier)
    assert (screen.tier, screen.blocking_count) == ("warn", 0)
    assert screen.banner_text == "1 item(s) might need a second look before you download."


def test_a_clean_dossier_is_good():
    dossier = maroc_dossier(flag_review=False)
    assert [item for item in dossier.validation if item.status == "failed"] == []
    screen = view.build(dossier)
    assert screen.tier == "good"
    assert screen.banner_text == "Ready to download."


def test_values_in_review_make_the_dossier_warn_even_when_every_check_passes():
    # The sample file flags three totals; its checks all pass. The header must not say "ready".
    dossier = maroc_dossier()
    assert [item for item in dossier.validation if item.status == "failed"] == []
    screen = view.build(dossier)
    assert view.review_count(dossier) == 3
    assert screen.tier == "warn"
    assert screen.blocking_count == 0
    assert screen.banner_text == "3 value(s) might need a second look before you download."


def test_one_flagged_value_is_enough_to_warn():
    dossier = maroc_dossier(flag_review=False)
    dossier.documents[0].fields["total_amount"].status = "review"
    assert view.build(dossier).tier == "warn"


def test_a_failed_warning_check_is_counted_before_flagged_values():
    dossier = maroc_dossier()
    dossier.validation = [
        ValidationResult(rule_id="supported_currency", severity="warning", status="failed", message="x")
    ]
    assert view.build(dossier).banner_text == "1 item(s) might need a second look before you download."


def test_a_blocking_error_is_still_crit_when_values_are_flagged_too():
    screen = view.build(maroc_dossier(maersk_last_line="1500.00"))
    assert screen.tier == "crit" and screen.blocking_count == 1


def test_severity_decides_the_tier_of_one_check():
    error = ValidationResult(rule_id="a", severity="error", status="failed", message="m")
    warning = ValidationResult(rule_id="b", severity="warning", status="failed", message="m")
    assert view.check_tier(error) == "crit"
    assert view.check_tier(warning) == "warn"


# -- numbers and words ---------------------------------------------------------------

def test_money_is_shown_with_separators_and_the_currency_after():
    dossier = maroc_dossier()
    assert view.display(dossier.documents[0], "total_amount") == "6,830.00 MAD"
    assert view.display(dossier.documents[6], "total_amount") == "18,921.09 EUR"


def test_customs_value_is_always_in_dirhams():
    dossier = maroc_dossier()
    declaration = next(doc for doc in dossier.documents if doc.id == "dum")
    assert view.display(declaration, "customs_value") == "210,800.00 MAD"


def test_a_missing_field_is_an_empty_string_never_zero():
    document = DocumentRecord(id="x", document_type="supplier_invoice", page_numbers=[1], fields={})
    assert view.display(document, "total_amount") == ""
    assert view.headline_amount(document) == ""


def test_a_corrected_value_replaces_the_read_one():
    dossier = maroc_dossier()
    broker = dossier.documents[0]
    broker.fields["total_amount"].user_value = "7000.00"
    assert view.display(broker, "total_amount") == "7,000.00 MAD"


def test_headline_falls_back_from_total_to_customs_value():
    dossier = maroc_dossier()
    declaration = next(doc for doc in dossier.documents if doc.id == "dum")
    assert view.headline_amount(declaration) == "210,800.00 MAD"


# -- tabs and pages ------------------------------------------------------------------

def test_a_paper_that_needs_a_check_gets_a_bullet_in_its_tab():
    screen = view.build(maroc_dossier())
    assert _paper(screen, "broker").tab_label == "• Broker invoice"
    assert _paper(screen, "oncf1").tab_label == "Logistics invoice"


def test_a_paper_opens_on_the_page_its_flagged_field_was_read_from():
    screen = view.build(maroc_dossier())
    assert _paper(screen, "liquidation").default_page == 3  # pages 2-3, total flagged on 3
    assert _paper(screen, "maersk").default_page == 6
    assert _paper(screen, "supplier").default_page == 9


def test_a_paper_without_pages_has_no_default_page():
    document = DocumentRecord(id="x", document_type="unknown", page_numbers=[], fields={})
    assert view.default_page(document) is None


# -- what a person types -------------------------------------------------------------

def test_broker_invoices_type_codes_per_line_not_per_paper():
    keys = [key for key, _ in view.paper_manual_fields("broker_invoice")]
    assert "tax_code" not in keys and "reason_code" not in keys
    assert _paper(view.build(maroc_dossier()), "broker").line_codes is True


def test_customs_papers_add_a_sap_reference():
    for kind in ("customs_declaration", "customs_liquidation"):
        assert ("sap_reference", "SAP reference") in view.paper_manual_fields(kind)
    assert "sap_reference" not in [key for key, _ in view.paper_manual_fields("supplier_invoice")]


def test_other_papers_type_the_five_standard_fields():
    keys = [key for key, _ in view.paper_manual_fields("supplier_invoice")]
    assert keys == ["vendor_code", "posting_date", "tax_code", "reason_code", "gl_account"]


def test_the_notes_under_you_type_depend_on_the_paper():
    screen = view.build(maroc_dossier())
    assert any("liquidation number" in note for note in _paper(screen, "liquidation").typed_notes)
    assert any("service line" in note for note in _paper(screen, "broker").typed_notes)
    assert _paper(screen, "supplier").typed_notes == ()


def test_store_keys_tie_typed_values_to_a_paper():
    assert view.paper_store_key("broker", "vendor_code") == "broker:vendor_code"
    assert view.line_store_key("broker", 3, "tax_code") == "broker:line:3:tax_code"


# -- rows and lines ------------------------------------------------------------------

def test_rows_carry_label_value_printed_text_and_the_check_flag():
    rows = {row.key: row for row in _paper(view.build(maroc_dossier()), "liquidation").rows}
    total = rows["total_amount"]
    assert (total.label, total.value_text, total.printed_text, total.needs_check) == (
        "Total", "44,004.00 MAD", "44004.00", True,
    )
    assert rows["document_number"].label == "Payment number"
    assert rows["document_number"].needs_check is False


def test_lines_are_numbered_text():
    lines = _paper(view.build(maroc_dossier()), "broker").lines
    assert [line.index for line in lines] == [1, 2, 3, 4, 5, 6, 7]
    assert lines[0].text == "1. Honoraire 2000.00"


def test_a_line_with_nothing_read_is_just_its_number():
    document = paper("x", "supplier_invoice", [1], {})
    document.lines = [view_line_without_fields()]
    assert view._lines(document)[0].text == "1."


def view_line_without_fields():
    from app.models import LineRecord

    return LineRecord(fields={})


# -- missing and edited values ---------------------------------------------------------

def _row(screen, paper_id, key):
    return next(row for row in _paper(screen, paper_id).rows if row.key == key)


def test_a_field_that_was_not_read_is_marked_missing_and_stays_empty():
    row = _row(view.build(maroc_dossier()), "licence", "hs_code")
    assert row.missing is True
    assert row.value_text == "" and row.printed_text is None  # nothing invented
    assert row.edited is False and row.needs_check is False


def test_a_field_that_was_read_is_not_missing():
    screen = view.build(maroc_dossier())
    assert _row(screen, "supplier", "total_amount").missing is False
    assert _row(screen, "licence", "total_amount").missing is False


def test_a_missing_field_is_not_missing_once_a_person_typed_a_value():
    dossier = maroc_dossier()
    licence = next(doc for doc in dossier.documents if doc.id == "licence")
    licence.fields["hs_code"].user_value = "3004.90"
    row = _row(view.build(dossier), "licence", "hs_code")
    assert (row.missing, row.edited, row.value_text) == (False, True, "3004.90")


def test_a_value_a_person_changed_is_marked_edited_and_the_original_stays_in_the_data():
    dossier = maroc_dossier()
    broker = dossier.documents[0]
    broker.fields["total_amount"].user_value = "7000.00"
    row = _row(view.build(dossier), "broker", "total_amount")
    assert row.edited is True and row.value_text == "7,000.00 MAD"
    assert broker.fields["total_amount"].value == "6830.00"  # the screen never touches the original


def test_clearing_a_value_counts_as_an_edit_and_is_not_called_missing():
    dossier = maroc_dossier()
    dossier.documents[0].fields["tax_amount"].user_value = ""
    row = _row(view.build(dossier), "broker", "tax_amount")
    assert (row.edited, row.missing, row.value_text) == (True, False, "")


def test_nothing_is_marked_edited_until_a_person_edits():
    screen = view.build(maroc_dossier())
    assert not any(row.edited for paper in screen.papers for row in paper.rows)


def test_the_not_on_the_page_words_never_reach_an_export():
    from app.export.writers import dossier_json, fields_csv
    from app.ui import lang

    dossier = maroc_dossier()
    for code in lang.LANGUAGES:
        words = lang.CATALOGS[code]["form.not_on_page"]
        assert words not in fields_csv(dossier)
        assert words not in dossier_json(dossier)


# -- totals strip --------------------------------------------------------------------

def test_totals_show_only_the_kinds_that_exist_and_say_when_a_figure_was_not_read():
    screen = view.build(maroc_dossier())
    assert [cell.label for cell in screen.totals] == [
        "Supplier invoice", "Customs value", "Customs payment", "Shipping invoice",
    ]
    by_label = {cell.label: cell for cell in screen.totals}
    assert by_label["Supplier invoice"].amount == "18,921.09 EUR"
    assert by_label["Supplier invoice"].sub == f"Issued by {SUPPLIER}"
    assert by_label["Customs value"].sub == "Copied from the customs papers"
    assert by_label["Customs payment"].needs_check is True
    assert by_label["Supplier invoice"].needs_check is False

    dossier = maroc_dossier()
    dossier.documents = [paper("s", "supplier_invoice", [1], {"currency": field("EUR")})]
    assert view.totals(dossier)[0].amount == "Not read"


# -- checks --------------------------------------------------------------------------

def test_a_failed_check_is_attached_to_the_paper_it_names():
    screen = view.build(maroc_dossier(maersk_last_line="1500.00"))
    maersk = _paper(screen, "maersk")
    assert [(check.tier, check.text) for check in maersk.failed_checks] == [
        ("crit", "Shipping invoice: The lines on the page do not add up to the amount before tax."),
    ]
    assert _paper(screen, "supplier").failed_checks == ()


def test_passed_checks_are_listed_with_their_paper_name():
    screen = view.build(maroc_dossier())
    assert any(text.startswith("Shipping invoice:") for text in _paper(screen, "maersk").passed_checks)


# -- the whole screen ----------------------------------------------------------------

def test_the_screen_has_one_view_per_paper_in_order():
    screen = view.build(maroc_dossier())
    assert screen.paper_count == 8
    assert [paper.id for paper in screen.papers] == [
        "broker", "liquidation", "oncf1", "oncf2", "maersk", "dum", "supplier", "licence",
    ]
    assert [paper.position for paper in screen.papers] == list(range(8))
    assert screen.filename == "maroc-import-document.pdf"


def test_the_view_objects_are_frozen():
    screen = view.build(maroc_dossier())
    with pytest.raises(Exception):
        screen.tier = "good"  # type: ignore[misc]


def test_view_imports_neither_streamlit_nor_the_service():
    import re
    from pathlib import Path

    source = Path(view.__file__).read_text()
    assert not re.search(r"^\s*(import|from)\s+(streamlit|app\.service)\b", source, re.MULTILINE)
