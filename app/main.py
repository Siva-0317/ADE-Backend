from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
# Remove auth import temporarily
from app.routes import automations, workflows  # No auth for MVP!

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (NO AUTH for MVP)
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])  # Disabled for MVP
app.include_router(automations.router, prefix="/api/automations", tags=["Automations"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.API_VERSION,
        "status": "online"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
