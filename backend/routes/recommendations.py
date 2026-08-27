"""Unified recommendation routes are exposed through backend.routes.aws."""

from backend.routes.aws import explain_recommendation, recommendations

__all__ = ["recommendations", "explain_recommendation"]
