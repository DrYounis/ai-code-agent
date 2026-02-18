# 🚀 Quick Start Guide

Get your dual-agent system running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd dual-agent-system
pip install -r requirements.txt
```

## Step 2: Get Your Free Groq API Key

1. Visit **https://console.groq.com**
2. Click "Sign Up" (it's completely free)
3. Once logged in, go to "API Keys"
4. Click "Create API Key"
5. Copy your key (starts with `gsk_...`)

## Step 3: Configure Environment

```bash
cp .env.example .env
```

Open `.env` in your editor and paste your API key:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

## Step 4: Run Your First Agent Workflow

```bash
python main.py
```

You'll see:
- 👨‍💻 **Coder Agent** writing a web scraper
- 🔍 **Reviewer Agent** checking the code quality
- 📁 Generated code in the `output/` folder

## Step 5: Customize the Task

Edit `main.py` and change the `task_description` variable (around line 43):

```python
task_description = """
Build a React login page with:
- Email and password inputs
- Form validation
- Submit button with loading state
- Error message display
"""
```

Run again:
```bash
python main.py
```

## What Just Happened?

1. **Coder Agent** received your task and wrote the code
2. **Reviewer Agent** analyzed the code for quality and bugs
3. Both agents used **Groq's free Llama 3.3 70B model**
4. Code was saved to `output/` directory

## Next Steps

### Add Git Integration

Uncomment the Git tools in `agents/tools.py` to enable:
- Automatic commits
- Push to GitHub
- Trigger CI/CD pipelines

### Try Different Models

Edit `.env`:
```
GROQ_MODEL=mixtral-8x7b-32768  # Faster inference
```

### Add More Agents

Create a third agent (e.g., "Deployer") in `agents/deployer.py`:
```python
def create_deployer_agent(llm):
    return Agent(
        role="DevOps Engineer",
        goal="Deploy code to production",
        # ... rest of config
    )
```

## Troubleshooting

### "GROQ_API_KEY not found"
- Make sure you copied `.env.example` to `.env`
- Check that your API key is correctly pasted

### "Module not found"
```bash
pip install --upgrade crewai crewai-tools langchain-groq
```

### "Rate limit exceeded"
- Groq free tier: 14,400 requests/day
- Wait a minute or use a different model

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Groq API | **$0** (14,400 req/day free) |
| CrewAI | **$0** (open source) |
| GitHub | **$0** (free tier) |
| Vercel | **$0** (hobby tier) |
| **TOTAL** | **$0/month** |

## Example Tasks to Try

```python
# 1. Build a REST API
task_description = "Create a FastAPI REST API with user CRUD endpoints"

# 2. Create a Chrome Extension
task_description = "Build a Chrome extension that highlights all links on a page"

# 3. Make a CLI Tool
task_description = "Create a Python CLI tool for file organization"

# 4. Build a Discord Bot
task_description = "Create a Discord bot that responds to !hello command"
```

Happy coding! 🎉
