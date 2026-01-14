import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.problem_router import router as prob_router
from app.api.submission_router import router as sub_router
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Codear Problem Service",
    description="Microservice for problem management and code submission",
    version="1.0.0"
)

@app.exception_handler(Exception)
async def runtime_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"message": str(exc)},
    )

app.include_router(prob_router)
app.include_router(sub_router)

@app.get("/api/v1/problem/health-check")
async def health_check():
    return "health is running"