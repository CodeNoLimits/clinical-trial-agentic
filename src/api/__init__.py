"""
API Module - FastAPI REST Interface

Provides REST endpoints for:
- Patient screening requests
- Trial management
- Results retrieval
- Health checks
"""

from .main import app

__all__ = ["app"]
