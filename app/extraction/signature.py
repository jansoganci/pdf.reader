import hashlib
import json

from app.config import settings
from app.documents.registry import DOCUMENT_TYPES, PROMPT_VERSION, SCHEMA_VERSION


def pipeline_manifest() -> dict:
    return {
        "provider": settings.extraction_provider,
        "model": settings.anthropic_model,
        "effort": settings.anthropic_effort,
        "system_prompt_version": settings.system_prompt_version,
        "classification_prompt_version": PROMPT_VERSION,
        "classification_schema_version": SCHEMA_VERSION,
        "boundary_prompt_version": PROMPT_VERSION,
        "boundary_schema_version": SCHEMA_VERSION,
        "document_types": {
            name: {"prompt_version": PROMPT_VERSION, "schema_version": SCHEMA_VERSION}
            for name in DOCUMENT_TYPES
        },
        "preprocessing_version": settings.preprocessing_version,
        "grouping_rules_version": settings.grouping_rules_version,
        "normalization_version": settings.normalization_version,
    }


def pipeline_signature(manifest: dict | None = None) -> str:
    body = json.dumps(manifest or pipeline_manifest(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()
