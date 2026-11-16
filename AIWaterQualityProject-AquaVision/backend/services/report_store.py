"""Persistent SQLite store for AquaVision AI-generated water quality reports."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "reports.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tanker_id TEXT,
            city TEXT,
            province TEXT,
            resource_type TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            wqi_score REAL,
            quality_class TEXT,
            narrative TEXT,
            markdown_content TEXT NOT NULL,
            structured_data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


class ReportStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def save_report(
        self,
        report_id: str,
        title: str,
        tanker_id: Optional[str],
        city: str,
        province: str,
        resource_type: str,
        status: str,
        wqi_score: Optional[float],
        quality_class: str,
        narrative: str,
        markdown_content: str,
        structured_data: Dict[str, Any],
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        ts = created_at or datetime.now().isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO reports (
                id, title, tanker_id, city, province, resource_type,
                created_at, status, wqi_score, quality_class,
                narrative, markdown_content, structured_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                title,
                tanker_id or "N/A",
                city or "N/A",
                province or "N/A",
                resource_type or "N/A",
                ts,
                status,
                wqi_score,
                quality_class,
                narrative,
                markdown_content,
                json.dumps(structured_data),
            ),
        )
        conn.commit()
        conn.close()
        return self.get_report(report_id)

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, tanker_id, city, province, resource_type,
                   created_at, status, wqi_score, quality_class,
                   narrative, markdown_content, structured_data
            FROM reports WHERE id = ?
            """,
            (report_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "tanker_id": row[2],
            "city": row[3],
            "province": row[4],
            "resource_type": row[5],
            "created_at": row[6],
            "status": row[7],
            "wqi_score": row[8],
            "quality_class": row[9],
            "narrative": row[10],
            "markdown_content": row[11],
            "structured_data": json.loads(row[12]),
        }

    def list_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, tanker_id, city, province, resource_type,
                   created_at, status, wqi_score, quality_class,
                   narrative, markdown_content, structured_data
            FROM reports
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "title": r[1],
                "tanker_id": r[2],
                "city": r[3],
                "province": r[4],
                "resource_type": r[5],
                "created_at": r[6],
                "status": r[7],
                "wqi_score": r[8],
                "quality_class": r[9],
                "narrative": r[10],
                "markdown_content": r[11],
                "structured_data": json.loads(r[12]),
            }
            for r in rows
        ]

    def delete_report(self, report_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0


report_store = ReportStore()

