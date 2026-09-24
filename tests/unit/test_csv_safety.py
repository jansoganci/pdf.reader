from app.export.writers import safe_cell


def test_formula_prefix():
    assert safe_cell("=1+1").startswith("'")
    assert safe_cell("+cmd").startswith("'")
    assert safe_cell("-1").startswith("'")
    assert safe_cell("@sum").startswith("'")
    assert safe_cell("144.00") == "144.00"
