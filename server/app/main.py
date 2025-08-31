from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from app.api.v1 import api_router  # добавить импорт

app = FastAPI(title="PrivetSuperApp")

# (CORS и прочее как есть)

# Подключаем все API-роуты под /api/v1
app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = DIST_DIR / "assets"

# ассеты Vite по корню
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# SPA: index.html на /
@app.get("/", include_in_schema=False)
async def spa_root():
    index_file = DIST_DIR / "index.html"
    return FileResponse(index_file) if index_file.exists() else Response("Frontend build not found. Run npm run build in frontend.", status_code=503)

# SPA fallback: любые пути — тоже index.html (для React Router)
@app.get("/{path:path}", include_in_schema=False)
async def spa_catch_all(path: str):
    index_file = DIST_DIR / "index.html"
    return FileResponse(index_file) if index_file.exists() else Response("Frontend build not found. Run npm run build in frontend.", status_code=503)

@app.get("/sw.js", include_in_schema=False)
async def sw():
    f = DIST_DIR / "sw.js"
    return FileResponse(f, media_type="application/javascript") if f.exists() else Response(status_code=404)

# --- Static assets from Vite ---
# app.mount("/web/assets", StaticFiles(directory=str(ASSETS_DIR)), name="web-assets")

# SPA entry points (always return index.html so client router handles routes)
# @app.get("/web", include_in_schema=False)
# async def web_root():
#    index_file = DIST_DIR / "index.html"
#    if index_file.exists():
#        return FileResponse(index_file)
#    return Response("Frontend build not found. Run npm run build in frontend.", status_code=503)

# @app.get("/web/{path:path}", include_in_schema=False)
# async def web_catch_all(path: str):
#     index_file = DIST_DIR / "index.html"
#     if index_file.exists():
#         return FileResponse(index_file)
#     return Response("Frontend build not found. Run npm run build in frontend.", status_code=503)

# Optional PWA files (return 404 if missing)
@app.get("/manifest.webmanifest", include_in_schema=False)
async def manifest():
    f = DIST_DIR / "manifest.webmanifest"
    if f.exists():
        return FileResponse(f)
    return Response(status_code=404)

@app.get("/icon.svg", include_in_schema=False)  
async def icon_svg():
    f = DIST_DIR / "icon.svg"
    if f.exists():
        return FileResponse(f)
    return Response(status_code=404)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    f = DIST_DIR / "favicon.ico"
    if f.exists():
        return FileResponse(f)
    return Response(status_code=404)