from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .models import Deal, DealListItem

class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS deals (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)')

    def _conn(self):
        return sqlite3.connect(self.path, timeout=10)

    def put(self, deal: Deal):
        with self._conn() as conn:
            conn.execute('INSERT OR REPLACE INTO deals(id, created_at, payload) VALUES(?,?,?)',
                         (deal.id, deal.created_at.isoformat(), deal.model_dump_json()))

    def get(self, id: str) -> Deal | None:
        with self._conn() as conn:
            row = conn.execute('SELECT payload FROM deals WHERE id=?', (id,)).fetchone()
        return Deal.model_validate_json(row[0]) if row else None

    def list(self) -> list[DealListItem]:
        with self._conn() as conn:
            rows = conn.execute('SELECT payload FROM deals ORDER BY created_at DESC LIMIT 50').fetchall()
        deals = [Deal.model_validate_json(r[0]) for r in rows]
        return [DealListItem(
            id=d.id, name=d.name, created_at=d.created_at, filename=d.filename, demo=d.demo,
            stage=d.facts['stage'].value, sector=d.facts['sector'].value,
            review_status=d.review.status, evidence_coverage=d.evidence_coverage
        ) for d in deals]
