from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.routes.alarm_definitions import router as definitions_router
from src.api.routes.alarms import router as alarms_router
from src.api.routes.machines import router as machines_router
from src.api.routes.status import router as status_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="FactorIA API",
        version="1.1.0",
        description="Máquinas, PLC, sensores lógicos y alarmas de catálogo",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(status_router)
    app.include_router(machines_router)
    app.include_router(alarms_router)
    app.include_router(definitions_router)
    return app


app = create_app()
