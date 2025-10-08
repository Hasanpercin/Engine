import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.routers import electional, health
from app.utils.rate_limit import init_rate_limiter
from contextlib import asynccontextmanager

load_dotenv()

app = FastAPI(title="AstroCalc Calculation Engine", version="0.1.0")

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_rate_limiter()
    yield

app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
async def on_startup():
    await init_rate_limiter(app)

app.include_router(health.router)
app.include_router(electional.router)

@app.get("/")
async def root():
    return {"name": "AstroCalc Calculation Engine", "status": "ready"}
