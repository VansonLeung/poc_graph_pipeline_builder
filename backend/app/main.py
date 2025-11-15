"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router as api_router
from backend.app.core.db import close_driver

app = FastAPI(title="Graph Pipeline Builder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"] ,
    allow_headers=["*"] ,
    allow_credentials=False,
)

app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    close_driver()
