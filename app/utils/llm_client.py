from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import get_settings

settings = get_settings()

def get_llm(provider="groq", model=None):
    """Get LLM client with fallback support"""
    try:
        if provider == "groq":
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=model or "llama-3.3-70b-versatile",
                temperature=0.3
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                google_api_key=settings.GOOGLE_API_KEY,
                model=model or "gemini-2.0-flash-exp",
                temperature=0.3
            )
    except Exception as e:
        # Fallback to alternative provider
        if provider == "groq":
            return get_llm("google")
        raise Exception(f"All LLM providers failed: {str(e)}")

async def call_llm(prompt: str, provider="groq"):
    """Call LLM with automatic fallback"""
    llm = get_llm(provider)
    response = await llm.ainvoke(prompt)
    return response.content
