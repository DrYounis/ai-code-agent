"""
Alternative LLM Configuration for Local Ollama
Use this if you want to run 100% locally without any API calls
"""
from langchain_community.llms import Ollama


def get_ollama_llm(model_name="llama3.2", temperature=0.7):
    """
    Initialize and return a local Ollama LLM instance.
    
    Prerequisites:
    1. Install Ollama: brew install ollama (Mac) or visit ollama.ai
    2. Pull a model: ollama pull llama3.2
    3. Start Ollama: ollama serve (runs on http://localhost:11434)
    
    Args:
        model_name: Model to use (default: llama3.2)
        temperature: Creativity level (0.0-1.0)
    
    Returns:
        Ollama instance configured for local inference
    """
    return Ollama(
        model=model_name,
        temperature=temperature,
        base_url="http://localhost:11434",
    )


# Available Ollama models (download with: ollama pull <model>)
RECOMMENDED_MODELS = {
    "llama3.2": "Latest Llama, great all-around performance",
    "qwen2.5-coder": "Specialized for coding tasks",
    "codellama": "Meta's code-focused model",
    "mistral": "Fast and efficient",
    "mixtral": "Mixture of experts, very capable",
}


def setup_instructions():
    """Print setup instructions for Ollama"""
    print("\n🏠 Local Ollama Setup Instructions:\n")
    print("1. Install Ollama:")
    print("   Mac:     brew install ollama")
    print("   Linux:   curl -fsSL https://ollama.ai/install.sh | sh")
    print("   Windows: Download from https://ollama.ai\n")
    
    print("2. Pull a model:")
    print("   ollama pull llama3.2\n")
    
    print("3. Start Ollama (in a separate terminal):")
    print("   ollama serve\n")
    
    print("4. Update main.py to use Ollama:")
    print("   from config.ollama_config import get_ollama_llm")
    print("   llm = get_ollama_llm()\n")
    
    print("✅ Benefits of Local Ollama:")
    print("   • 100% free forever")
    print("   • No API keys needed")
    print("   • Complete privacy (no data leaves your machine)")
    print("   • No rate limits")
    print("   • Works offline\n")


if __name__ == "__main__":
    setup_instructions()
