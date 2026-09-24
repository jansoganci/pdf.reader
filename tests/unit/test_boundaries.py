from app.extraction.group import build_evidence, group_pages


def test_two_logistics_invoices_stay_split_and_carrier_stays_together():
    pages = [
        build_evidence(1, "carrier_invoice", "7631239091", "page 1 of 2"),
        build_evidence(2, "carrier_invoice", "7631239091", "page 2 of 2"),
        build_evidence(3, "logistics_invoice", "IM26091043", None),
        build_evidence(4, "logistics_invoice", "IM26091161", None),
    ]
    groups = group_pages(pages)
    assert [len(group) for group in groups] == [2, 1, 1]
    assert groups[1][0].boundary_reason == "type_changed"
    assert groups[2][0].boundary_reason == "key_changed"


def test_weak_evidence_splits_for_review():
    pages = [
        build_evidence(1, "broker_invoice", None, None),
        build_evidence(2, "broker_invoice", None, None),
    ]
    groups = group_pages(pages)
    assert len(groups) == 2
    assert groups[1][0].boundary_status == "review"
