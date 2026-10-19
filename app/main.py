import os
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.csv_parser import parse_points_table_csv
from app.image_generator import generate_points_table_image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Max CSV upload size: 2 MB — prevents abuse on free-tier Render
MAX_CSV_BYTES = 2 * 1024 * 1024

app = FastAPI(
    title="BattleX Free Fire Points Table Studio",
    description="Esports Points Table Generator & High-Res Image Exporter for Free Fire tournaments",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class ExportImageRequest(BaseModel):
    standings: List[Dict[str, Any]]
    tournament_title: Optional[str] = "FREE FIRE BATTLEGROUNDS CHAMPIONSHIP"
    match_info: Optional[str] = "GRAND FINALS • MATCH 01 • BERMUDA"
    theme: Optional[str] = "inferno"
    width: Optional[int] = 1920
    height: Optional[int] = 1080


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Parse an uploaded CSV entirely in memory — nothing is saved to disk."""
    try:
        content_bytes = await file.read()

        if len(content_bytes) > MAX_CSV_BYTES:
            return JSONResponse(
                status_code=413,
                content={"success": False, "error": "CSV file exceeds 2 MB limit."}
            )

        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = content_bytes.decode("latin-1")

        result = parse_points_table_csv(content)
        result["filename"] = file.filename
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.get("/api/sample-csv")
async def get_sample_csv():
    """Return pre-bundled sample data (read-only file shipped with the repo)."""
    sample_path = os.path.join(BASE_DIR, "free_fire_points_table.csv")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample CSV not found")
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            content = f.read()
        result = parse_points_table_csv(content)
        result["filename"] = "free_fire_points_table.csv"
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/export-image")
async def export_image(payload: ExportImageRequest):
    """Generate a PNG poster entirely in memory and stream it back — no disk writes."""
    try:
        buf = generate_points_table_image(
            standings=payload.standings,
            tournament_title=payload.tournament_title or "FREE FIRE CHAMPIONSHIP",
            match_info=payload.match_info or "MATCH STANDINGS",
            theme_name=payload.theme or "inferno",
            width=payload.width or 1920,
            height=payload.height or 1080
        )
        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=free_fire_points_table.png"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "BattleX Free Fire Points Table"}
