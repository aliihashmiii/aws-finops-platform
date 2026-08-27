"""FastAPI entry point for the Cloud FinOps Control Plane."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import ai, aws, dashboard, kubernetes

app = FastAPI(title="Cloud FinOps Control Plane", version="2.0.0", description="AWS, Kubernetes, and AI FinOps visibility and optimization API.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(dashboard.router)
app.include_router(aws.router)
app.include_router(kubernetes.router)
app.include_router(ai.router)

frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
