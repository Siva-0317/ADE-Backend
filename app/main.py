from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import automations, workflows, hosted_automations
from app.scheduler.automation_scheduler import start_scheduler, shutdown_scheduler
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from fastapi.responses import HTMLResponse
import random
from datetime import datetime

# Add this route for demos
@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Demo page that changes every request"""
    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7"]
    quotes = [
        "Innovation distinguishes between a leader and a follower.",
        "The best way to predict the future is to invent it.",
        "Stay hungry. Stay foolish.",
        "Think different.",
        "Move fast and break things."
    ]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Demo Page</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, {random.choice(colors)} 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.95);
                padding: 50px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                text-align: center;
            }}
            .number {{
                font-size: 72px;
                font-weight: bold;
                color: {random.choice(colors)};
                margin: 20px 0;
            }}
            .quote {{
                font-style: italic;
                color: #555;
                margin: 20px 0;
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Live Automation Demo</h1>
            <div class="number">{random.randint(1, 100)}</div>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
            <p><strong>Request ID:</strong> #{random.randint(1000, 9999)}</p>
            <div class="quote">"{random.choice(quotes)}"</div>
            <hr>
            <p style="color: #888;">This page changes with EVERY request!</p>
            <p style="color: #888;">Perfect for testing real-time monitoring.</p>
        </div>
    </body>
    </html>
    """

