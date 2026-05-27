"""FastAPI application for SalesPatriot FSC Classifier."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from salespatriot_shared.db import get_engine, dispose_engine
from salespatriot_shared.mq import connect

from .routes import submissions, events


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.db = get_engine()
    mq_ctx = connect()
    app.state.mq = await mq_ctx.__aenter__()
    app.state.mq_channel = await app.state.mq.channel()
    try:
        yield
    finally:
        await app.state.mq_channel.close()
        await mq_ctx.__aexit__(None, None, None)
        await dispose_engine()


app = FastAPI(title="SalesPatriot FSC Classifier", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions.router)
app.include_router(events.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
