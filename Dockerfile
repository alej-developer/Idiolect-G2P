# Imagen de produccion multicapa de Idiolect-G2P.
# La etapa de construccion instala solo las dependencias de produccion en un
# entorno virtual. La etapa final conserva ese entorno sobre Python Alpine
# (musl) para reducir el tamano y la superficie de ataque. pydantic-core
# publica ruedas musllinux, de modo que no hace falta un compilador.

FROM python:3.12-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY idiolect_g2p ./idiolect_g2p

RUN pip install --upgrade pip \
    && pip install --no-cache-dir . \
    && python -c "from pathlib import Path; import idiolect_g2p; raiz = Path(idiolect_g2p.__file__).resolve().parent; assert (raiz / 'web' / 'index.html').is_file(), raiz" \
    && pip uninstall -y pip \
    && find /opt/venv -depth -type d -name '__pycache__' -exec rm -rf {} +

FROM python:3.12-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HOME=/tmp

LABEL org.opencontainers.image.title="Idiolect-G2P" \
      org.opencontainers.image.description="Microservicio de desambiguacion fonologica dialectal y diacronica inversa" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/alej-developer/Idiolect-G2P"

RUN apk upgrade --no-cache \
    && addgroup -S -g 1001 idiolect \
    && adduser -S -D -H -u 1001 -G idiolect -h /tmp idiolect

WORKDIR /app

COPY --from=builder --chown=idiolect:idiolect /opt/venv /opt/venv

USER idiolect

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)"]

CMD ["uvicorn", "idiolect_g2p.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
