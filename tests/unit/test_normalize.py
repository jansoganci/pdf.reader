from app.extraction.normalize import parse_currency, parse_date, parse_decimal


def test_decimal_formats():
    assert parse_decimal("18 921,09")[0] == parse_decimal("18,921.09")[0]
    assert str(parse_decimal("18921.09")[0]) == "18921.09"
    assert parse_decimal("1.234")[0] is None
    assert parse_decimal("1.234")[1] is True


def test_dates_and_currency():
    assert parse_date("21.07.2026")[0] == "2026-07-21"
    assert parse_date("21/07/2026")[0] == "2026-07-21"
    assert parse_date("Aug 24, 2026")[0] == "2026-08-24"
    assert parse_currency("EUR")[0] == "EUR"
    assert parse_currency("DH")[0] == "MAD"
