from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import automations, workflows, hosted_automations
from app.scheduler.automation_scheduler import start_scheduler, shutdown_scheduler
from app.database import engine, Base

# Create tables
print("📊 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables ready")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()

app = FastAPI(
    title="Agentic Automation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(automations.router, prefix="/api/automations", tags=["automations"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(hosted_automations.router, prefix="/api/hosted-automations", tags=["hosted"])

@app.get("/")
def read_root():
    return {
        "message": "Agentic Automation Platform API",
        "version": "1.0.0",
        "status": "online"
    }
