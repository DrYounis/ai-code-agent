"""
LLM Configuration for Groq API
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

def get_groq_llm(model_name=None, temperature=0.7):
    """
    Initialize and return a Groq LLM instance.
    
    Args:
        model_name: Model to use (default: llama-3.3-70b-versatile)
        temperature: Creativity level (0.0-1.0)
    
    Returns:
        ChatGroq instance configured with API key
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in environment variables. "
            "Please copy .env.example to .env and add your API key."
        )
    
    # Default to llama-3.3-70b-versatile if no model specified
    if model_name is None:
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    return ChatGroq(
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=8000,
    )


# Available Groq models (all free tier)
AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": "Best overall performance, great for coding",
    "llama-3.1-70b-versatile": "Excellent reasoning, good for complex tasks",
    "mixtral-8x7b-32768": "Fast inference, large context window",
    "llama-3.2-90b-text-preview": "Latest Llama model, experimental",
}


def print_available_models():
    """Print all available Groq models"""
    print("\n🤖 Available Groq Models (Free Tier):\n")
    for model, description in AVAILABLE_MODELS.items():
        print(f"  • {model}")
        print(f"    {description}\n")
