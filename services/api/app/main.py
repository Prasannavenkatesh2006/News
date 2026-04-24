"""
FastAPI application for ANIP API service.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from pathlib import Path

from app.news import router as news_router
from app.conversations import router as conversations_router
from app.auth import router as auth_router
from app.social import router as social_router
from app.notifications import router as notifications_router
from app.advanced_social import router as advanced_router
from app.disaster_alerts import router as alerts_router
from app.i18n import router as i18n_router
from app.scraper import router as scraper_router
from app.websocket_manager import manager
from anip.shared.database import Base, engine
from anip.shared.models.social import (
    User, Community, Post, Comment, Vote,
    Notification, Bookmark, DisasterAlert, UserSettings
)
from anip.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI app.
    Drops and recreates all database tables on startup.
    """
    logger.info("🚀 Starting ANIP API - Initializing database...")
    
    try:
        # Drop all tables with CASCADE to handle foreign key dependencies
        # logger.info("🗑️  Dropping all existing tables...")
        # with engine.begin() as conn:
        #     # Drop all tables with CASCADE to handle foreign key constraints // only the tables related to the news model
        #     conn.execute(text("DROP TABLE IF EXISTS newsarticle CASCADE"))
        # logger.info("✅ News article table dropped successfully")
        
        # Create extension for pgvector if it's missing
        logger.info("🔧 Ensuring pgvector extension exists...")
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("✅ pgvector extension ensured")
        except Exception as vec_err:
            logger.warning(f"⚠️  pgvector extension could not be created: {vec_err}")
            logger.warning("AI similarity search will be limited. Ensure pgvector is installed in your Postgres.")
        
        # Create all tables
        logger.info("📦 Creating database tables...")
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully")
        except Exception as create_err:
            logger.error(f"❌ Failed to create tables: {create_err}")
            if "type \"vector\" does not exist" in str(create_err):
                logger.error("CRITICAL: You are using pgvector models but the extension is missing.")
            raise
        
        # Seed default communities
        logger.info("🏘️  Seeding default communities...")
        try:
            from scripts.seed_communities import seed_communities
            seed_communities()
        except Exception as seed_err:
            logger.warning(f"⚠️ Community seeding skipped: {seed_err}")
        
    except Exception as e:
        logger.error(f"❌ Error during database initialization: {e}", exc_info=True)
        raise
    
    logger.info("✅ ANIP API startup complete")
    
    yield
    
    logger.info("🛑 Shutting down ANIP API...")


app = FastAPI(
    title="ANIP API",
    description="Automated News Intelligence Pipeline API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS - use pydantic settings for allowed origins
allowed_origins = settings.api.cors_origins.split(",")
if "*" in allowed_origins:
    logger.warning("CORS is configured to allow all origins. This should be restricted in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(news_router)
app.include_router(conversations_router)
app.include_router(auth_router)
app.include_router(social_router)
app.include_router(notifications_router)
app.include_router(advanced_router)
app.include_router(alerts_router)
app.include_router(i18n_router)
app.include_router(scraper_router)


# ========== WebSocket Endpoints ==========

@app.websocket("/ws/feed")
async def ws_feed(websocket: WebSocket):
    """Real-time feed updates."""
    await manager.connect_feed(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect_feed(websocket)


@app.websocket("/ws/notifications/{user_id}")
async def ws_notifications(websocket: WebSocket, user_id: str):
    """Real-time user notifications."""
    await manager.connect_user(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """Real-time disaster alerts."""
    await manager.connect_alerts(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_alerts(websocket)


@app.websocket("/ws/community/{slug}")
async def ws_community(websocket: WebSocket, slug: str):
    """Real-time community feed."""
    await manager.connect_community(websocket, slug)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_community(websocket, slug)

@app.websocket("/ws/live-feed")
async def ws_live_feed(websocket: WebSocket):
    """Real-time live feed — broadcasts auto-posted content to all connected clients."""
    await manager.connect_feed(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect_feed(websocket)


# Mount static files for UI
ui_static_path = Path(__file__).parent / "ui" / "static"
if ui_static_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_static_path)), name="static")
    logger.info(f"✅ Mounted static files from {ui_static_path}")
else:
    logger.warning(f"⚠️  UI static directory not found at {ui_static_path}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ANIP API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api",
        "chat": "/chat"
    }


@app.get("/chat", response_class=HTMLResponse)
async def chat_ui():
    """Serve the chat UI."""
    ui_html_path = Path(__file__).parent / "ui" / "static" / "index.html"
    
    if not ui_html_path.exists():
        return HTMLResponse(
            content="<h1>Chat UI not found</h1><p>The UI files are not available.</p>",
            status_code=404
        )
    
    with open(ui_html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from anip.shared.database import engine
    
    db_healthy = False
    db_error = None
    
    try:
        # Test database connection using SQLAlchemy text() for safety
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        db_error = str(e)
        logger.error(f"Database health check failed: {e}")
    
    overall_status = "healthy" if db_healthy else "unhealthy"
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "database": "healthy" if db_healthy else f"unhealthy: {db_error}"
        }
    )

