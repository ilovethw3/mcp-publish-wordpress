from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.core.config import settings
from mcp.api.v1 import auth, articles
from mcp.db.session import create_db_and_tables

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Content Control Platform - AI文章审核与发布系统"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(articles.router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
async def root():
    return {
        "message": "MCP API is running",
        "app": settings.app_name,
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}