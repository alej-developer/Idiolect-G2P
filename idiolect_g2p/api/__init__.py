"""
Modulo API REST FastAPI para el servicio Idiolect-G2P.
FastAPI REST API module for the Idiolect-G2P service.
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
