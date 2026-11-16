"""Unified SQLite Database Manager for AquaVision Platform.
Persists tankers, telemetry readings, reports, user profile, and activity logs.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "reports.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tankers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tankers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            province TEXT NOT NULL,
            source_type TEXT NOT NULL,
            capacity_liters REAL NOT NULL,
            current_volume_liters REAL NOT NULL,
            status TEXT NOT NULL,
            status_color TEXT NOT NULL,
            description TEXT,
            data_label TEXT DEFAULT 'DEMO SENSOR TELEMETRY',
            is_simulated INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)

    # 2. Readings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanker_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ph REAL NOT NULL,
            tds REAL NOT NULL,
            turbidity REAL NOT NULL,
            temperature REAL NOT NULL,
            ec REAL,
            chloride REAL,
            sulfate REAL,
            nitrate REAL,
            arsenic REAL,
            lead REAL,
            hardness REAL,
            coliform INTEGER DEFAULT 0,
            reading_source TEXT DEFAULT 'Simulated Sensor',
            created_at TEXT NOT NULL,
            FOREIGN KEY (tanker_id) REFERENCES tankers (id) ON DELETE CASCADE
        )
    """)

    # 3. Reports table
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

    # 4. User Profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            designation TEXT NOT NULL,
            role TEXT NOT NULL,
            organization TEXT NOT NULL,
            avatar_initials TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 5. Activity Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            tanker_id TEXT,
            report_id TEXT,
            tag TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed default user profile if empty
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO user_profile (id, full_name, designation, role, organization, avatar_initials, updated_at)
            VALUES (1, 'Dr. Ali Hassan', 'Senior Water Quality Researcher', 'Administrator', 'AquaVision National Water Lab', 'AH', ?)
        """, (datetime.now().isoformat(),))
        conn.commit()

    # Seed default tankers if empty
    cursor.execute("SELECT COUNT(*) FROM tankers")
    if cursor.fetchone()[0] == 0:
        _seed_default_tankers(cursor)
        conn.commit()

    # Seed initial activity logs if empty
    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    if cursor.fetchone()[0] == 0:
        _seed_initial_activity(cursor)
        conn.commit()

    conn.close()


def _seed_default_tankers(cursor):
    now = datetime.now()
    default_tankers = [
        ("TANK-01", "Tanker 01 - Lahore Central", "Lahore", "Punjab", "Groundwater", 5000, 4200, "Good", "emerald", "Deep aquifer extraction reservoir with multi-stage sand filtration.", now.isoformat()),
        ("TANK-02", "Tanker 02 - Rawalpindi Filtration Unit", "Rawalpindi", "Punjab", "Surface Water", 6000, 5800, "Borderline", "amber", "Municipal surface supply inflow undergoing active coagulation monitoring.", now.isoformat()),
        ("TANK-04", "Tanker 04 - Karachi Coastal Reservoir", "Karachi", "Sindh", "Desalinated / Ground Inflow", 8000, 7100, "Observation", "amber", "Coastal storage tank with membrane desalination blending.", now.isoformat()),
        ("TANK-05", "Tanker 05 - Faisalabad Industrial Inflow", "Faisalabad", "Punjab", "Industrial Groundwater", 5000, 3900, "Poor", "rose", "Mixed aquifer source near textile corridor with elevated TDS.", now.isoformat()),
    ]
    for tid, name, city, prov, st, cap, vol, status, color, desc, ts in default_tankers:
        cursor.execute("""
            INSERT INTO tankers (id, name, city, province, source_type, capacity_liters, current_volume_liters, status, status_color, description, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tid, name, city, prov, st, cap, vol, status, color, desc, ts, ts))

    # Seed default telemetry readings
    seed_readings = [
        ("TANK-01", 7.35, 420.0, 2.1, 23.8, 480.0, 95.0, 80.0, 11.5, 0.008, 0.004, 145.0, 0),
        ("TANK-02", 7.85, 540.0, 3.8, 22.4, 610.0, 180.0, 130.0, 22.0, 0.015, 0.008, 280.0, 1),
        ("TANK-04", 7.15, 465.0, 2.4, 26.5, 530.0, 210.0, 98.0, 14.0, 0.009, 0.006, 190.0, 0),
        ("TANK-05", 6.70, 780.0, 4.6, 25.1, 920.0, 320.0, 240.0, 48.0, 0.038, 0.018, 420.0, 3),
    ]
    for tid, ph, tds, turb, temp, ec, cl, so4, no3, as_, pb, hard, col in seed_readings:
        # Create 10 historical points per tanker
        for i in range(10, 0, -1):
            ts = (now - timedelta(hours=i * 2.5)).isoformat()
            cursor.execute("""
                INSERT INTO readings (tanker_id, timestamp, ph, tds, turbidity, temperature, ec, chloride, sulfate, nitrate, arsenic, lead, hardness, coliform, reading_source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Simulated Sensor', ?)
            """, (tid, ts, round(ph + (i % 3 - 1) * 0.04, 2), round(tds + (i % 3 - 1) * 15, 1), round(max(0.5, turb + (i % 2 - 0.5) * 0.2), 2), round(temp + (i % 2) * 0.4, 1), ec, cl, so4, no3, as_, pb, hard, col, ts))


def _seed_initial_activity(cursor):
    now = datetime.now()
    logs = [
        ("System Telemetry Online", "AquaVision IoT mesh initialized across 4 regional water monitoring stations.", "devices", "TANK-01", None, "SYSTEM", "ONLINE", (now - timedelta(hours=5)).isoformat()),
        ("Calibration Sequence Finalized", "Probes calibrated against Pakistan NSDWQ Table 1 tolerance windows.", "devices", "TANK-02", None, "CALIBRATE", "SUCCESS", (now - timedelta(hours=3)).isoformat()),
        ("AI Baseline Assessment", "LangGraph CatBoost and Gradient Boosting models validated against historical standards.", "ai", "TANK-01", None, "AI", "VERIFIED", (now - timedelta(hours=1)).isoformat()),
    ]
    for title, desc, cat, tid, rid, tag, status, ts in logs:
        cursor.execute("""
            INSERT INTO activity_logs (title, description, category, tanker_id, report_id, tag, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, desc, cat, tid, rid, tag, status, ts))


init_database()

