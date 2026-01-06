import os
import httpx
from app.config import get_settings

settings = get_settings()

async def call_llm(prompt: str, provider="groq"):
    """Call LLM with automatic fallback"""
    
    if provider == "groq":
        try:
            return await call_groq(prompt)
        except:
            return await call_google(prompt)
    else:
        return await call_google(prompt)

async def call_groq(prompt: str):
    """Direct Groq API call"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=30.0)
        result = response.json()
        return result["choices"][0]["message"]["content"]

async def call_google(prompt: str):
    """Direct Google Gemini API call"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=30.0)
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
