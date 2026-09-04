"""
Punto de entrada principal de la aplicacion FastAPI Idiolect-G2P.
Main entry point for Idiolect-G2P FastAPI application with security hardening.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .routes import router


def create_app() -> FastAPI:
    """Fabrica de inicializacion de la aplicacion FastAPI con politicas de seguridad estrictas."""
    app = FastAPI(
        title="Idiolect-G2P Scientific API",
        description=(
            "Microservicio de desambiguacion fonologica dialectal y diacronica inversa, "
            "sintesis acustica formántica AFI y generacion de informes periciales."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. Configuracion de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Middleware de Seguridad (Cabeceras HTTP estrictas y mitigacion de ataques)
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
        # Validacion preventiva de tamano de payload (Maximo 2 MB)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 2 * 1024 * 1024:
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={"detail": "La carga util supera el limite de seguridad permitido (2 MB)."}
            )

        response: Response = await call_next(request)

        # Inyeccion de cabeceras de ciberseguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "media-src 'self' data: blob:; "
            "connect-src 'self';"
        )
        return response

    # 3. Registro de Rutas API
    app.include_router(router)

    # 4. Servir Interfaz Web Estatica si existe el directorio
    web_dir = Path(__file__).resolve().parent.parent / "web"
    if web_dir.exists() and web_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

        @app.get("/", include_in_schema=False)
        def serve_index() -> FileResponse:
            index_file = web_dir / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            return JSONResponse({"message": "Idiolect-G2P Web UI en construccion."})

    return app


app = create_app()
