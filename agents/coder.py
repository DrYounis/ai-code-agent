"""
Coder Agent Definition
"""
from crewai import Agent
from agents.tools import get_coder_tools


def create_coder_agent(llm):
    """
    Create the Coder Agent - a senior Python developer
    
    Args:
        llm: Language model instance (Groq)
    
    Returns:
        CrewAI Agent configured as a senior developer
    """
    return Agent(
        role="Senior Software Developer",
        goal="Write clean, efficient, and production-ready code based on requirements",
        backstory="""You are a highly experienced software developer with 10+ years of experience.
        You specialize in writing clean, maintainable code that follows best practices.
        You always consider edge cases, error handling, and code readability.
        You write code that is well-documented and easy to understand.
        You prefer simple, elegant solutions over complex ones.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=get_coder_tools(),
        max_iter=15,
    )
