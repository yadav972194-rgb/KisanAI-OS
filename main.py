"""
KisanAI OS
Main Entry Point
"""

from config.core.api.main import app  # noqa: F401  exposed as ``uvicorn main:app``
from config.settings import settings


if __name__ == "__main__":
    import uvicorn

    # Host/port are configurable via HOST/PORT (production default 0.0.0.0:8000).
    # Hot reload follows DEBUG unless RELOAD is set explicitly; production
    # deployments set DEBUG=false so reload never activates.
    reload = settings.RELOAD if settings.RELOAD is not None else settings.DEBUG

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=reload,
    )
