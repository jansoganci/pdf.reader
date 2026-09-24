import hashlib
import json
import sqlite3
import uuid
from pathlib import Path

from app.config import settings
from app.models import Dossier


def connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.data_dir / "app.sqlite")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS dossiers (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            pipeline_signature TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            current_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS extraction_runs (
            id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            pipeline_signature TEXT NOT NULL,
            normalized_json TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cache_creation_input_tokens INTEGER NOT NULL,
            cache_read_input_tokens INTEGER NOT NULL,
            estimated_cost_usd REAL NOT NULL,
            duration_ms INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            corrected_json TEXT NOT NULL,
            export_with_errors INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS exports (
            id TEXT PRIMARY KEY,
            dossier_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            kind TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            path TEXT NOT NULL
        );
        """
    )
    return connection


def find_cached(sha256: str, signature: str) -> Dossier | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT current_json FROM dossiers WHERE sha256 = ? AND pipeline_signature = ?",
            (sha256, signature),
        ).fetchone()
    if row is None:
        return None
    return Dossier.model_validate_json(row["current_json"])


def save_dossier(dossier: Dossier) -> None:
    payload = dossier.model_dump_json()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO dossiers (id, filename, sha256, pipeline_signature, status, current_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (dossier.id, dossier.filename, dossier.sha256, dossier.pipeline_signature, dossier.status, payload),
        )
        connection.execute(
            """
            INSERT INTO extraction_runs (
                id, dossier_id, pipeline_signature, normalized_json,
                input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens,
                estimated_cost_usd, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                dossier.id,
                dossier.pipeline_signature,
                payload,
                dossier.usage.input_tokens,
                dossier.usage.output_tokens,
                dossier.usage.cache_creation_input_tokens,
                dossier.usage.cache_read_input_tokens,
                dossier.estimated_cost_usd,
                dossier.usage.duration_ms,
            ),
        )


def update_current(dossier: Dossier, export_with_errors: bool) -> None:
    payload = dossier.model_dump_json()
    with connect() as connection:
        connection.execute(
            "UPDATE dossiers SET current_json = ?, status = ? WHERE id = ?",
            (payload, dossier.status, dossier.id),
        )
        connection.execute(
            "INSERT INTO reviews (id, dossier_id, corrected_json, export_with_errors) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), dossier.id, payload, int(export_with_errors)),
        )


def get_dossier(dossier_id: str) -> Dossier | None:
    with connect() as connection:
        row = connection.execute("SELECT current_json FROM dossiers WHERE id = ?", (dossier_id,)).fetchone()
    if row is None:
        return None
    return Dossier.model_validate_json(row["current_json"])


def list_dossiers() -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT id, filename, status, created_at FROM dossiers ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def original_path(dossier_id: str) -> Path:
    folder = settings.data_dir / "originals" / dossier_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "source.pdf"


def record_export(dossier_id: str, kind: str, path: Path, content: bytes) -> None:
    with connect() as connection:
        connection.execute(
            "INSERT INTO exports (id, dossier_id, kind, sha256, path) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), dossier_id, kind, hashlib.sha256(content).hexdigest(), str(path)),
        )
