"""Persistent SQLite Tanker & Telemetry Management Service."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.db import get_connection


class TankerService:
    def get_all_tankers(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tankers ORDER BY id ASC")
        rows = cursor.fetchall()

        result = []
        for r in rows:
            tanker = dict(r)
            tanker["is_simulated"] = bool(tanker["is_simulated"])
            # Fetch latest reading
            cursor.execute(
                "SELECT * FROM readings WHERE tanker_id = ? ORDER BY id DESC LIMIT 1",
                (tanker["id"],),
            )
            latest = cursor.fetchone()
            if latest:
                tanker["measurements"] = {
                    "pH": latest["ph"],
                    "TDS": latest["tds"],
                    "Turbidity": latest["turbidity"],
                    "Temperature": latest["temperature"],
                    "EC": latest["ec"] or 500.0,
                    "Chloride": latest["chloride"] or 150.0,
                    "Sulfate": latest["sulfate"] or 100.0,
                    "Nitrate": latest["nitrate"] or 15.0,
                    "Arsenic": latest["arsenic"] or 0.01,
                    "Lead": latest["lead"] or 0.005,
                    "Hardness": latest["hardness"] or 180.0,
                    "Total_Coliform": latest["coliform"] or 0,
                    "E_Coli": 0,
                }
            else:
                tanker["measurements"] = {
                    "pH": 7.2, "TDS": 450.0, "Turbidity": 2.0, "Temperature": 24.0,
                    "EC": 500.0, "Chloride": 120.0, "Sulfate": 90.0, "Nitrate": 12.0,
                    "Arsenic": 0.008, "Lead": 0.005, "Hardness": 160.0, "Total_Coliform": 0, "E_Coli": 0,
                }
            result.append(tanker)

        conn.close()
        return result

    def get_tanker_by_id(self, tanker_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        norm_id = tanker_id.strip().upper()

        cursor.execute("SELECT * FROM tankers WHERE UPPER(id) = ?", (norm_id,))
        row = cursor.fetchone()
        if not row:
            # Fallback loose search by name or number
            cursor.execute("SELECT * FROM tankers WHERE UPPER(name) LIKE ?", (f"%{norm_id}%",))
            row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        tanker = dict(row)
        tanker["is_simulated"] = bool(tanker["is_simulated"])

        # Fetch history (last 20 readings chronological)
        cursor.execute(
            "SELECT * FROM readings WHERE tanker_id = ? ORDER BY id DESC LIMIT 20",
            (tanker["id"],),
        )
        readings = [dict(rd) for rd in cursor.fetchall()][::-1]

        history = []
        for rd in readings:
            ts_str = rd["timestamp"]
            display_time = ts_str[11:16] if len(ts_str) >= 16 else ts_str
            history.append({
                "id": rd["id"],
                "timestamp": display_time,
                "full_time": ts_str,
                "pH": rd["ph"],
                "TDS": rd["tds"],
                "Turbidity": rd["turbidity"],
                "Temperature": rd["temperature"],
                "EC": rd["ec"] or 500.0,
                "reading_source": rd["reading_source"],
            })
        tanker["history"] = history

        # Latest measurements
        if history:
            latest = readings[-1]
            tanker["measurements"] = {
                "pH": latest["ph"],
                "TDS": latest["tds"],
                "Turbidity": latest["turbidity"],
                "Temperature": latest["temperature"],
                "EC": latest["ec"] or 500.0,
                "Chloride": latest["chloride"] or 150.0,
                "Sulfate": latest["sulfate"] or 100.0,
                "Nitrate": latest["nitrate"] or 15.0,
                "Arsenic": latest["arsenic"] or 0.01,
                "Lead": latest["lead"] or 0.005,
                "Hardness": latest["hardness"] or 180.0,
                "Total_Coliform": latest["coliform"] or 0,
                "E_Coli": 0,
            }
        else:
            tanker["measurements"] = {
                "pH": 7.2, "TDS": 450.0, "Turbidity": 2.0, "Temperature": 24.0,
                "EC": 500.0, "Chloride": 120.0, "Sulfate": 90.0, "Nitrate": 12.0,
                "Arsenic": 0.008, "Lead": 0.005, "Hardness": 160.0, "Total_Coliform": 0, "E_Coli": 0,
            }

        conn.close()
        return tanker

    def create_tanker(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        raw_id = (data.get("id") or f"TANK-{datetime.now().strftime('%M%S')}").strip().upper()
        name = data.get("name") or f"Tanker {raw_id}"
        city = data.get("city") or "Lahore"
        province = data.get("province") or "Punjab"
        source_type = data.get("source_type") or "Groundwater"
        capacity = float(data.get("capacity_liters") or 5000)
        volume = float(data.get("current_volume_liters") or capacity * 0.8)
        description = data.get("description") or f"New dynamic water tanker monitoring point in {city}."
        status = "Good"
        color = "emerald"

        cursor.execute("""
            INSERT INTO tankers (id, name, city, province, source_type, capacity_liters, current_volume_liters, status, status_color, description, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (raw_id, name, city, province, source_type, capacity, volume, status, color, description, now, now))

        # Seed initial reading
        ph = float(data.get("pH") or 7.3)
        tds = float(data.get("TDS") or 430.0)
        turb = float(data.get("Turbidity") or 2.1)
        temp = float(data.get("Temperature") or 24.0)

        cursor.execute("""
            INSERT INTO readings (tanker_id, timestamp, ph, tds, turbidity, temperature, ec, chloride, sulfate, nitrate, arsenic, lead, hardness, coliform, reading_source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Initial Setup', ?)
        """, (raw_id, now, ph, tds, turb, temp, 500.0, 120.0, 90.0, 12.0, 0.008, 0.005, 160.0, 0, now))

        # Log activity
        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tanker_id, tag, status, created_at)
            VALUES (?, ?, 'devices', ?, 'NEW_TANKER', 'SUCCESS', ?)
        """, (f"Tanker Created: {raw_id}", f"Registered {name} ({source_type}) in {city}.", raw_id, now))

        conn.commit()
        conn.close()
        return self.get_tanker_by_id(raw_id)

    def update_tanker(self, tanker_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        tanker = self.get_tanker_by_id(tanker_id)
        if not tanker:
            conn.close()
            return None

        name = data.get("name") or tanker["name"]
        city = data.get("city") or tanker["city"]
        province = data.get("province") or tanker["province"]
        source_type = data.get("source_type") or tanker["source_type"]
        capacity = float(data.get("capacity_liters") or tanker["capacity_liters"])
        volume = float(data.get("current_volume_liters") or tanker["current_volume_liters"])
        description = data.get("description") if "description" in data else tanker.get("description")

        cursor.execute("""
            UPDATE tankers
            SET name = ?, city = ?, province = ?, source_type = ?, capacity_liters = ?, current_volume_liters = ?, description = ?, last_updated = ?
            WHERE id = ?
        """, (name, city, province, source_type, capacity, volume, description, now, tanker["id"]))

        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tanker_id, tag, status, created_at)
            VALUES (?, ?, 'devices', ?, 'UPDATE', 'SUCCESS', ?)
        """, (f"Tanker Updated: {tanker['id']}", f"Modified specifications for {name}.", tanker["id"], now))

        conn.commit()
        conn.close()
        return self.get_tanker_by_id(tanker["id"])

    def delete_tanker(self, tanker_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("SELECT name FROM tankers WHERE id = ?", (tanker_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        tanker_name = row[0]
        cursor.execute("DELETE FROM readings WHERE tanker_id = ?", (tanker_id,))
        cursor.execute("DELETE FROM tankers WHERE id = ?", (tanker_id,))

        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tanker_id, tag, status, created_at)
            VALUES (?, ?, 'devices', ?, 'DELETE', 'REMOVED', ?)
        """, (f"Tanker Deleted: {tanker_id}", f"Decommissioned {tanker_name}.", tanker_id, now))

        conn.commit()
        conn.close()
        return True

    def add_reading(
        self,
        tanker_id: str,
        measurements: Dict[str, Any],
        reading_source: str = "Manual Entry",
    ) -> Optional[Dict[str, Any]]:
        tanker = self.get_tanker_by_id(tanker_id)
        if not tanker:
            return None

        # Validation
        ph = float(measurements.get("pH", tanker["measurements"]["pH"]))
        tds = float(measurements.get("TDS", tanker["measurements"]["TDS"]))
        turb = float(measurements.get("Turbidity", tanker["measurements"]["Turbidity"]))
        temp = float(measurements.get("Temperature", tanker["measurements"]["Temperature"]))

        if ph < 0 or ph > 14:
            raise ValueError(f"pH must be between 0 and 14. Got {ph}")
        if tds < 0 or tds > 5000:
            raise ValueError(f"TDS must be non-negative and realistic (0-5000 mg/L). Got {tds}")
        if turb < 0 or turb > 100:
            raise ValueError(f"Turbidity must be non-negative (0-100 NTU). Got {turb}")
        if temp < -10 or temp > 70:
            raise ValueError(f"Temperature must be realistic (-10 to 70 °C). Got {temp}")

        now = datetime.now().isoformat()
        conn = get_connection()
        cursor = conn.cursor()

        # Determine status by Pakistan NSDWQ limits
        if ph < 6.5 or ph > 8.5 or tds > 1000 or turb > 5.0:
            status = "Poor"
            color = "rose"
        elif tds > 500 or turb > 3.0:
            status = "Borderline"
            color = "amber"
        else:
            status = "Good"
            color = "emerald"

        def _get_val(m_dict, key, default):
            v = m_dict.get(key)
            if v is not None:
                return float(v)
            v_tanker = tanker["measurements"].get(key)
            return float(v_tanker) if v_tanker is not None else float(default)

        cursor.execute("""
            INSERT INTO readings (tanker_id, timestamp, ph, tds, turbidity, temperature, ec, chloride, sulfate, nitrate, arsenic, lead, hardness, coliform, reading_source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tanker["id"],
            now,
            round(ph, 2),
            round(tds, 1),
            round(turb, 2),
            round(temp, 1),
            _get_val(measurements, "EC", 500.0),
            _get_val(measurements, "Chloride", 120.0),
            _get_val(measurements, "Sulfate", 90.0),
            _get_val(measurements, "Nitrate", 12.0),
            _get_val(measurements, "Arsenic", 0.008),
            _get_val(measurements, "Lead", 0.005),
            _get_val(measurements, "Hardness", 160.0),
            int(measurements.get("Total_Coliform") or tanker["measurements"].get("Total_Coliform") or 0),
            reading_source,
            now,
        ))

        cursor.execute("""
            UPDATE tankers
            SET status = ?, status_color = ?, last_updated = ?
            WHERE id = ?
        """, (status, color, now, tanker["id"]))

        # Log activity
        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tanker_id, tag, status, created_at)
            VALUES (?, ?, 'devices', ?, 'READING', 'LOGGED', ?)
        """, (f"Reading Logged: {tanker['id']}", f"Recorded pH {ph:.2f}, TDS {tds:.1f} ppm ({reading_source}).", tanker["id"], now))

        conn.commit()
        conn.close()
        return self.get_tanker_by_id(tanker["id"])

    def get_analytics_summary(self) -> Dict[str, Any]:
        tankers = self.get_all_tankers()
        if not tankers:
            return {
                "total_tankers": 0, "active_nodes": 0,
                "ph_stats": {"min": 0, "avg": 0, "max": 0},
                "tds_stats": {"min": 0, "avg": 0, "max": 0},
                "turbidity_stats": {"min": 0, "avg": 0, "max": 0},
                "temperature_stats": {"min": 0, "avg": 0, "max": 0},
                "node_comparison": [],
            }

        all_ph = [t["measurements"]["pH"] for t in tankers]
        all_tds = [t["measurements"]["TDS"] for t in tankers]
        all_turb = [t["measurements"]["Turbidity"] for t in tankers]
        all_temp = [t["measurements"]["Temperature"] for t in tankers]

        conn = get_connection()
        cursor = conn.cursor()
        comparison = []
        for t in tankers:
            cursor.execute(
                "SELECT ph, tds, turbidity, timestamp FROM readings WHERE tanker_id = ? ORDER BY id DESC LIMIT 8",
                (t["id"],),
            )
            pts = [dict(r) for r in cursor.fetchall()][::-1]
            comparison.append({
                "id": t["id"],
                "name": t["name"],
                "status": t["status"],
                "history": pts,
            })
        conn.close()

        return {
            "total_tankers": len(tankers),
            "active_nodes": len([t for t in tankers if t["status"] in ["Good", "Borderline"]]),
            "ph_stats": {
                "min": round(min(all_ph), 2),
                "avg": round(sum(all_ph) / len(all_ph), 2),
                "max": round(max(all_ph), 2),
            },
            "tds_stats": {
                "min": round(min(all_tds), 1),
                "avg": round(sum(all_tds) / len(all_tds), 1),
                "max": round(max(all_tds), 1),
            },
            "turbidity_stats": {
                "min": round(min(all_turb), 2),
                "avg": round(sum(all_turb) / len(all_turb), 2),
                "max": round(max(all_turb), 2),
            },
            "temperature_stats": {
                "min": round(min(all_temp), 1),
                "avg": round(sum(all_temp) / len(all_temp), 1),
                "max": round(max(all_temp), 1),
            },
            "node_comparison": comparison,
        }

    def get_dynamic_insights(self) -> List[Dict[str, Any]]:
        """Evaluate real tankers in the system to produce data-driven observations."""
        tankers = self.get_all_tankers()
        insights = []

        if not tankers:
            return [{
                "tag": "SYSTEM NOTICE",
                "tag_color": "bg-brand-warning border-amber-300",
                "title": "No Water Sources Configured",
                "description": "Please register water tankers or reservoirs to initiate automated AI surveillance.",
                "tanker_id": None,
                "action_text": "Add New Tanker",
            }]

        for t in tankers:
            m = t["measurements"]
            ph = m.get("pH", 7.0)
            tds = m.get("TDS", 400.0)
            turb = m.get("Turbidity", 2.0)

            if tds > 700:
                insights.append({
                    "tag": "ELEVATED SOLIDS",
                    "tag_color": "bg-rose-100 text-rose-800 border-rose-300",
                    "title": f"High Dissolved Minerals in {t['name']}",
                    "description": f"TDS measured at {tds:.1f} mg/L exceeds the 500 mg/L potable comfort baseline. Desalination or reverse osmosis blending is recommended.",
                    "tanker_id": t["id"],
                    "action_text": f"Audit {t['id']} Chemical Profile",
                })
            elif turb > 3.0:
                insights.append({
                    "tag": "OPTICAL VARIANCE",
                    "tag_color": "bg-brand-warning text-brand-dark border-amber-300",
                    "title": f"Elevated Turbidity in {t['name']}",
                    "description": f"Turbidity reading {turb:.2f} NTU indicates suspended particulate matter. Inspect pre-filter membranes.",
                    "tanker_id": t["id"],
                    "action_text": f"Check {t['id']} Filtration",
                })
            elif ph < 6.8 or ph > 8.2:
                insights.append({
                    "tag": "pH DEVIATION",
                    "tag_color": "bg-brand-warning text-brand-dark border-amber-300",
                    "title": f"pH Equilibrium Shift in {t['name']}",
                    "description": f"pH of {ph:.2f} is nearing regulatory boundaries (6.5 - 8.5). Monitor buffer capacity.",
                    "tanker_id": t["id"],
                    "action_text": f"Inspect {t['id']} Neutralization",
                })
            else:
                insights.append({
                    "tag": "COMPLIANCE VERIFIED",
                    "tag_color": "bg-emerald-100 text-emerald-900 border-emerald-300",
                    "title": f"NSDWQ Alignment: {t['name']}",
                    "description": f"All measured parameters (pH {ph:.2f}, TDS {tds:.0f} mg/L, Turbidity {turb:.1f} NTU) satisfy Pakistan potable standards.",
                    "tanker_id": t["id"],
                    "action_text": f"Generate {t['id']} Certification",
                })

        return insights[:6]


tanker_service = TankerService()
