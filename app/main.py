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

