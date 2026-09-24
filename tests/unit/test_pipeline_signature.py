from app.extraction.signature import pipeline_manifest, pipeline_signature


def test_schema_change_changes_signature_and_correction_does_not():
    base = pipeline_signature()
    changed = pipeline_manifest()
    changed["document_types"]["logistics_invoice"]["schema_version"] = "2"
    assert pipeline_signature(changed) != base
    assert pipeline_signature(pipeline_manifest()) == base
