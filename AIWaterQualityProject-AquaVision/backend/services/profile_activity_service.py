"""User Profile and Persistent Activity Audit Trail Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from services.db import get_connection


class ProfileActivityService:
    def get_profile(self) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profile WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if not row:
            res = {
                "full_name": "Dr. Ali Hassan",
                "designation": "Senior Water Quality Researcher",
                "role": "Administrator",
                "organization": "AquaVision National Water Lab",
                "avatar_initials": "AH",
            }
        else:
            res = dict(row)
        res["name"] = res.get("full_name") or "Dr. Ali Hassan"
        return res

    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        full_name = data.get("name") or data.get("full_name") or "Dr. Ali Hassan"
        designation = data.get("designation") or "Senior Water Quality Researcher"
        role = data.get("role") or "Administrator"
        organization = data.get("organization") or "AquaVision National Water Lab"

        # Auto compute avatar initials
        parts = [p for p in full_name.replace("Dr.", "").strip().split(" ") if p]
        initials = "".join(p[0].upper() for p in parts[:2]) or "AH"

        cursor.execute("""
            UPDATE user_profile
            SET full_name = ?, designation = ?, role = ?, organization = ?, avatar_initials = ?, updated_at = ?
            WHERE id = 1
        """, (full_name, designation, role, organization, initials, now))

        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tag, status, created_at)
            VALUES (?, ?, 'settings', 'PROFILE', 'UPDATED', ?)
        """, ("User Profile Updated", f"Profile details updated for {full_name} ({designation}).", now))

        conn.commit()
        conn.close()
        return self.get_profile()

    def get_activity_logs(self, limit: int = 50, category: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()

        if category and category.lower() != "all":
            cursor.execute(
                "SELECT * FROM activity_logs WHERE category = ? ORDER BY id DESC LIMIT ?",
                (category.lower(), limit),
            )
        else:
            cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def log_activity(
        self,
        title: str,
        description: str,
        category: str = "general",
        tanker_id: Optional[str] = None,
        report_id: Optional[str] = None,
        tag: str = "SYSTEM",
        status: str = "LOGGED",
    ):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tanker_id, report_id, tag, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, category, tanker_id, report_id, tag, status, datetime.now().isoformat()))
        conn.commit()
        conn.close()


profile_activity_service = ProfileActivityService()

