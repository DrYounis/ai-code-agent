"""
Dual-Agent Developer System
Main orchestration script using CrewAI and Groq
"""
import os
from crewai import Crew, Task, Process
from config.llm_config import get_groq_llm, print_available_models
from agents.coder import create_coder_agent
from agents.reviewer import create_reviewer_agent


def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("🤖 Dual-Agent Developer System")
    print("="*60 + "\n")
    
    # Initialize LLM
    print("🔧 Initializing Groq LLM...")
    try:
        llm = get_groq_llm(temperature=0.7)
        print("✅ LLM initialized successfully\n")
    except ValueError as e:
        print(f"❌ {e}")
        print("\n💡 Quick setup:")
        print("   1. Visit https://console.groq.com")
        print("   2. Sign up and get your free API key")
        print("   3. Copy .env.example to .env")
        print("   4. Add your API key to .env\n")
        return
    
    # Create agents
    print("👨‍💻 Creating Coder Agent...")
    coder = create_coder_agent(llm)
    
    print("🔍 Creating Reviewer Agent...")
    reviewer = create_reviewer_agent(llm)
    print()
    
    # Define the task
    task_description = """
    Create a simple Python web scraper that:
    1. Takes a URL as input
    2. Fetches the HTML content
    3. Extracts all links from the page
    4. Saves the links to a JSON file
    5. Includes proper error handling
    6. Has a main() function for easy execution
    
    Use the requests and beautifulsoup4 libraries.
    Save the code to 'web_scraper.py' in the output directory.
    """
    
    # Create tasks
    coding_task = Task(
        description=task_description,
        agent=coder,
        expected_output="A complete Python script saved to web_scraper.py with all required functionality"
    )
    
    review_task = Task(
        description="""
        Review the code written by the Coder Agent:
        1. Read the web_scraper.py file
        2. Check for code quality, error handling, and best practices
        3. Verify the implementation meets all requirements
        4. List any issues or improvements needed
        5. If the code is good, provide a summary of what it does
        
        Provide a detailed review with specific feedback.
        """,
        agent=reviewer,
        expected_output="A comprehensive code review with feedback on quality, correctness, and suggestions",
        context=[coding_task]  # Reviewer waits for coder to finish
    )
    
    # Create crew
    crew = Crew(
        agents=[coder, reviewer],
        tasks=[coding_task, review_task],
        process=Process.sequential,  # Tasks run in order
        verbose=True
    )
    
    # Execute
    print("🚀 Starting dual-agent workflow...\n")
    print("="*60 + "\n")
    
    result = crew.kickoff()
    
    print("\n" + "="*60)
    print("✅ Workflow Complete!")
    print("="*60 + "\n")
    print("📊 Final Result:\n")
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Check output
    output_dir = "output"
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        if files:
            print(f"📁 Generated files in '{output_dir}/':")
            for file in files:
                print(f"   • {file}")
        else:
            print(f"⚠️  No files generated in '{output_dir}/'")
    
    print("\n💡 Next steps:")
    print("   • Review the generated code in the output/ directory")
    print("   • Modify the task_description in main.py to try different tasks")
    print("   • Add Git integration to auto-commit approved code")
    print("   • Set up GitHub Actions for automated deployment\n")


if __name__ == "__main__":
    main()
