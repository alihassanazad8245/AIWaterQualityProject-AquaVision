"""FastAPI entry point for AquaVision AI Water Quality Platform.
Provides full Tanker CRUD, Manual Reading Influx, Persistent Reports, Dynamic Insights,
User Profile, Activity Logs, and Static UI hosting.
"""

import io
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.ai_service import ai_service
from services.pdf_generator import generate_report_pdf
from services.profile_activity_service import profile_activity_service
from services.report_store import report_store
from services.tanker_service import tanker_service

app = FastAPI(
    title="AquaVision AI Platform API",
    version="2.0.0",
    description="Integrated AI-Based Water Quality Analysis and Monitoring Dashboard API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== PYDANTIC SCHEMAS ====================

class TankerCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=2)
    city: str = Field(..., min_length=2)
    province: str = "Punjab"
    source_type: str = "Groundwater"
    capacity_liters: float = Field(5000.0, gt=0)
    current_volume_liters: Optional[float] = None
    description: Optional[str] = None
    pH: Optional[float] = Field(7.2, ge=0.0, le=14.0)
    TDS: Optional[float] = Field(450.0, ge=0.0, le=5000.0)
    Turbidity: Optional[float] = Field(2.0, ge=0.0, le=100.0)
    Temperature: Optional[float] = Field(24.0, ge=-10.0, le=70.0)


class TankerUpdateRequest(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    source_type: Optional[str] = None
    capacity_liters: Optional[float] = None
    current_volume_liters: Optional[float] = None
    description: Optional[str] = None


class ReadingEntryRequest(BaseModel):
    pH: float = Field(..., ge=0.0, le=14.0, description="pH must be between 0 and 14")
    TDS: float = Field(..., ge=0.0, le=5000.0, description="TDS in mg/L (0-5000)")
    Turbidity: float = Field(..., ge=0.0, le=100.0, description="Turbidity in NTU (0-100)")
    Temperature: float = Field(..., ge=-10.0, le=70.0, description="Temperature in °C (-10 to 70)")
    EC: Optional[float] = Field(None, ge=0.0)
    Chloride: Optional[float] = Field(None, ge=0.0)
    Sulfate: Optional[float] = Field(None, ge=0.0)
    Nitrate: Optional[float] = Field(None, ge=0.0)
    Hardness: Optional[float] = Field(None, ge=0.0)
    reading_source: Optional[str] = "Manual Entry"


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    designation: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    avatar_url: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"
    tanker_id: Optional[str] = None
    context_mode: Optional[str] = "overall"


class GenerateReportRequest(BaseModel):
    tanker_id: str
    measurements: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    session_id: Optional[str] = "default-session"


# ==================== SYSTEM & HEALTH ====================

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "AquaVision AI Platform",
        "version": "2.0.0",
        "model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        "timestamp": os.getenv("TIMESTAMP", "LIVE"),
    }


# ==================== TANKER MANAGEMENT ROUTES ====================

@app.get("/api/tankers")
def list_tankers():
    return tanker_service.get_all_tankers()


@app.post("/api/tankers")
def create_tanker(payload: TankerCreateRequest):
    try:
        new_tanker = tanker_service.create_tanker(payload.dict())
        return new_tanker
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/tankers/{tanker_id}")
def get_tanker(tanker_id: str):
    tanker = tanker_service.get_tanker_by_id(tanker_id)
    if not tanker:
        raise HTTPException(status_code=404, detail=f"Tanker '{tanker_id}' not found.")
    return tanker


@app.put("/api/tankers/{tanker_id}")
def update_tanker(tanker_id: str, payload: TankerUpdateRequest):
    updated = tanker_service.update_tanker(tanker_id, {k: v for k, v in payload.dict().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=404, detail=f"Tanker '{tanker_id}' not found.")
    return updated


@app.delete("/api/tankers/{tanker_id}")
def delete_tanker(tanker_id: str):
    success = tanker_service.delete_tanker(tanker_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tanker '{tanker_id}' not found.")
    return {"status": "deleted", "tanker_id": tanker_id}


@app.post("/api/tankers/{tanker_id}/reading")
def add_tanker_reading(tanker_id: str, payload: ReadingEntryRequest):
    try:
        updated = tanker_service.add_reading(
            tanker_id=tanker_id,
            measurements=payload.dict(),
            reading_source=payload.reading_source or "Manual Entry",
        )
        if not updated:
            raise HTTPException(status_code=404, detail=f"Tanker '{tanker_id}' not found.")
        return updated
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ==================== DYNAMIC ANALYTICS & INSIGHTS ====================

@app.get("/api/analytics")
def get_analytics():
    return tanker_service.get_analytics_summary()


@app.get("/api/insights")
def get_dynamic_insights():
    return tanker_service.get_dynamic_insights()


# ==================== USER PROFILE & ACTIVITY LOGS ====================

@app.get("/api/profile")
def get_user_profile():
    return profile_activity_service.get_profile()


@app.put("/api/profile")
def update_user_profile(payload: ProfileUpdateRequest):
    return profile_activity_service.update_profile(payload.dict())


@app.get("/api/activity")
def get_activity_logs(category: Optional[str] = None, limit: int = 50):
    return profile_activity_service.get_activity_logs(limit=limit, category=category)


# ==================== CHAT & AI COPILOT ROUTES ====================

@app.post("/api/chat")
def chat_with_copilot(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be blank.")
    result = ai_service.process_chat(
        session_id=req.session_id or "default-session",
        message=req.message,
        active_tanker_id=req.tanker_id,
        context_mode=req.context_mode or "overall",
    )
    return result


# ==================== REPORT ROUTES ====================

@app.post("/api/reports/generate")
def generate_report(req: GenerateReportRequest):
    try:
        report = ai_service.generate_report(
            tanker_id=req.tanker_id,
            custom_measurements=req.measurements,
            user_query=req.query,
            session_id=req.session_id or "default-session",
        )
        return report
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation error: {exc}")


@app.get("/api/reports")
def list_reports(limit: int = 50):
    return report_store.list_reports(limit=limit)


@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    report = report_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return report


@app.get("/api/reports/{report_id}/pdf")
def download_report_pdf(report_id: str):
    report = report_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    try:
        pdf_bytes = generate_report_pdf(report)
        clean_tanker = (report.get("tanker_id") or "SAMPLE").replace(" ", "_").replace("/", "-")
        filename = f"Water_Quality_Report_{clean_tanker}_{report_id}.pdf"

        # Log download activity
        profile_activity_service.log_activity(
            title=f"PDF Downloaded: {report_id}",
            description=f"Exported official audit certificate for {report.get('tanker_id')}.",
            category="reports",
            report_id=report_id,
            tag="PDF",
            status="DOWNLOADED"
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {exc}")


# ==================== STATIC FRONTEND SERVING ====================

FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found.")
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
