"""Vercel-compatible entrypoint for the Cloud FinOps FastAPI application."""

from backend.main import app

__all__ = ["app"]
