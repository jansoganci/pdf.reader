import csv
import io
import json

from app.models import Dossier, FieldValue

_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value) -> str:
    text = "" if value is None else str(value)
    if text.startswith(_DANGEROUS):
        return "'" + text
    return text


def displayed(field: FieldValue):
    return field.user_value if field.user_value is not None else field.value


def dossier_json(dossier: Dossier) -> str:
    body = json.loads(dossier.model_dump_json())
    body["exported_fields_use_user_value_when_present"] = True
    return json.dumps(body, indent=2)


def fields_csv(dossier: Dossier) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["document_id", "document_type", "field", "value", "extracted_value", "user_value", "raw_text", "source_page", "status", "method"]
    )
    for document in dossier.documents:
        for name, field in document.fields.items():
            writer.writerow(
                [
                    document.id,
                    document.document_type,
                    safe_cell(name),
                    safe_cell(displayed(field)),
                    safe_cell(field.value),
                    safe_cell(field.user_value),
                    safe_cell(field.raw_text),
                    field.source_page if field.source_page is not None else "",
                    field.status,
                    field.method,
                ]
            )
    for key, value in dossier.manual.items():
        document_id, _, name = key.partition(":")
        if not name:
            document_id, name = "", key
        writer.writerow(
            [
                document_id,
                "",
                safe_cell(name),
                safe_cell(value),
                "",
                safe_cell(value),
                "",
                "",
                "missing",
                "user",
            ]
        )
    return buffer.getvalue()


def lines_csv(dossier: Dossier) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["document_id", "line", "field", "value", "extracted_value", "user_value", "raw_text", "source_page", "status"])
    for document in dossier.documents:
        for index, line in enumerate(document.lines, start=1):
            for name, field in line.fields.items():
                writer.writerow(
                    [
                        document.id,
                        index,
                        name,
                        safe_cell(displayed(field)),
                        safe_cell(field.value),
                        safe_cell(field.user_value),
                        safe_cell(field.raw_text),
                        field.source_page if field.source_page is not None else "",
                        field.status,
                    ]
                )
    return buffer.getvalue()
