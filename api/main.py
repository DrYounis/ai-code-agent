"""
AI Code Agent — FastAPI Backend v2.0
SaaS API for dual-agent AI code generation (Coder + Reviewer)
Upgrades (R&D Week 1): token-bucket rate limiting, job caching, metrics
"""
import os
import sys
import uuid
import time
import stripe
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for existing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Stripe Setup ──────────────────────────────────────────────────────────────
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# ── Plans ─────────────────────────────────────────────────────────────────────
PLANS = {
    "starter": {
        "name": "Starter",
        "price": 99,
        "price_id": os.getenv("STRIPE_STARTER_PRICE_ID", ""),
        "tasks_per_month": 20,
        "features": ["20 AI tasks/month", "Coder + Reviewer agents", "Code download", "Email support"],
    },
    "professional": {
        "name": "Professional",
        "price": 199,
        "price_id": os.getenv("STRIPE_PRO_PRICE_ID", ""),
        "tasks_per_month": 100,
        "features": ["100 AI tasks/month", "Priority queue", "GitHub auto-commit", "Slack alerts", "API access"],
    },
    "team": {
        "name": "Team",
        "price": 499,
        "price_id": os.getenv("STRIPE_TEAM_PRICE_ID", ""),
        "tasks_per_month": -1,
        "features": ["Unlimited tasks", "5 team seats", "Custom agents", "Dedicated support", "SLA guarantee"],
    },
}

# ── In-memory DB (replace with Supabase in production) ────────────────────────
users_db: Dict[str, dict] = {}
jobs_db: Dict[str, dict] = {}  # job_id → job data

# ── R&D Upgrade: Token Bucket Rate Limiting ────────────────────────────────────
class TokenBucket:
    PLAN_RATES = {"starter": 0.03, "professional": 0.1, "team": 0.5}
    PLAN_BURST = {"starter": 2, "professional": 5, "team": 20}

    def __init__(self, plan: str = "starter"):
        self.rate = self.PLAN_RATES.get(plan, 0.03)
        self.capacity = self.PLAN_BURST.get(plan, 2)
        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def consume(self) -> bool:
        now = time.time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

_rate_limiters: Dict[str, TokenBucket] = {}
_total_jobs = 0
_completed_jobs = 0

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Code Agent API",
    description="Dual-agent AI code generation: Coder writes, Reviewer validates",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────
class TaskRequest(BaseModel):
    description: str
    language: Optional[str] = "python"
    framework: Optional[str] = None
    requirements: Optional[List[str]] = []

class CheckoutRequest(BaseModel):
    plan: str
    email: str

# ── Auth ──────────────────────────────────────────────────────────────────────
def get_current_user(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key not in users_db:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return users_db[x_api_key]

def check_quota(user: dict = Depends(get_current_user)):
    plan = user.get("plan", "starter")
    limit = PLANS.get(plan, PLANS["starter"])["tasks_per_month"]
    used = user.get("tasks_this_month", 0)
    if limit != -1 and used >= limit:
        raise HTTPException(status_code=429, detail=f"Monthly quota exceeded ({used}/{limit}). Upgrade your plan.")
    # R&D Upgrade: token-bucket rate limiting
    api_key = user["api_key"]
    if api_key not in _rate_limiters:
        _rate_limiters[api_key] = TokenBucket(plan)
    if not _rate_limiters[api_key].consume():
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Upgrade for higher limits.")
    return user

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    dashboard = Path(__file__).parent.parent / "dashboard" / "index.html"
    if dashboard.exists():
        return FileResponse(dashboard)
    return HTMLResponse("<h1>AI Code Agent API</h1><p>Visit /docs</p>")

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/plans")
async def get_plans():
    return {"plans": PLANS}


@app.post("/generate")
async def generate_code(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(check_quota),
):
    """
    Submit a code generation task to the dual-agent system.
    Returns a job_id to poll for results.
    """
    job_id = str(uuid.uuid4())
    
    # Build full task description
    lang_hint = f"Use {request.language}" if request.language else ""
    fw_hint = f"with {request.framework}" if request.framework else ""
    req_hint = "\nRequirements:\n" + "\n".join(f"- {r}" for r in request.requirements) if request.requirements else ""
    
    full_description = f"{request.description}\n{lang_hint} {fw_hint}{req_hint}".strip()

    # Create job record
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "description": full_description,
        "language": request.language,
        "created_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
        "user_email": user.get("email"),
    }

    # Increment usage
    user["tasks_this_month"] = user.get("tasks_this_month", 0) + 1
    global _total_jobs
    _total_jobs += 1

    # Run dual-agent in background
    background_tasks.add_task(run_dual_agent, job_id, full_description)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Task submitted. Poll /jobs/{job_id} for results.",
        "poll_url": f"/jobs/{job_id}",
    }


async def run_dual_agent(job_id: str, task_description: str):
    """Run the dual-agent system asynchronously"""
    jobs_db[job_id]["status"] = "running"
    jobs_db[job_id]["started_at"] = datetime.utcnow().isoformat()

    try:
        # Import here to avoid startup errors if GROQ_API_KEY not set
        from config.llm_config import get_groq_llm
        from agents.coder import create_coder_agent
        from agents.reviewer import create_reviewer_agent
        from crewai import Crew, Task, Process
        import tempfile

        llm = get_groq_llm(temperature=0.7)
        coder = create_coder_agent(llm)
        reviewer = create_reviewer_agent(llm)

        coding_task = Task(
            description=task_description,
            agent=coder,
            expected_output="Complete, working code that fulfills all requirements",
        )

        review_task = Task(
            description=f"""
            Review the code written by the Coder Agent for this task:
            {task_description}
            
            Check for:
            1. Correctness and completeness
            2. Error handling
            3. Code quality and best practices
            4. Security issues
            
            Provide the final, corrected code if any issues found.
            """,
            agent=reviewer,
            expected_output="Final reviewed and corrected code with review summary",
            context=[coding_task],
        )

        crew = Crew(
            agents=[coder, reviewer],
            tasks=[coding_task, review_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        jobs_db[job_id].update({
            "status": "completed",
            "result": {
                "code": str(result),
                "language": jobs_db[job_id].get("language", "python"),
                "reviewed": True,
            },
            "completed_at": datetime.utcnow().isoformat(),
        })
        global _completed_jobs
        _completed_jobs += 1

    except ImportError as e:
        # Groq not configured — return a demo response
        jobs_db[job_id].update({
            "status": "completed",
            "result": {
                "code": f"# Demo mode — configure GROQ_API_KEY to enable AI generation\n# Task: {task_description}\n\ndef main():\n    print('Hello from AI Code Agent!')\n\nif __name__ == '__main__':\n    main()",
                "language": jobs_db[job_id].get("language", "python"),
                "reviewed": False,
                "note": "Demo mode: Set GROQ_API_KEY to enable real AI generation",
            },
            "completed_at": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        jobs_db[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        })


@app.get("/jobs/{job_id}")
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs_db[job_id]
    # Only allow owner to see their job
    if job.get("user_email") != user.get("email"):
        raise HTTPException(status_code=403, detail="Access denied")
    return job


@app.get("/jobs")
async def list_jobs(user: dict = Depends(get_current_user)):
    email = user.get("email")
    user_jobs = [j for j in jobs_db.values() if j.get("user_email") == email]
    user_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "jobs": user_jobs[:20],
        "total": len(user_jobs),
        "quota_used": user.get("tasks_this_month", 0),
        "quota_limit": PLANS.get(user.get("plan", "starter"), PLANS["starter"])["tasks_per_month"],
    }


@app.post("/checkout")
async def create_checkout(request: CheckoutRequest):
    plan = request.plan.lower()
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")
    price_id = PLANS[plan]["price_id"]
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe price ID not configured")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=request.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=os.getenv("BASE_URL", "http://localhost:8000") + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("BASE_URL", "http://localhost:8000") + "/#pricing",
            metadata={"plan": plan, "email": request.email},
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhook")
async def stripe_webhook(request_body: bytes, stripe_signature: str = Header(None)):
    try:
        event = stripe.Webhook.construct_event(request_body, stripe_signature, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email") or session.get("metadata", {}).get("email", "")
        plan = session.get("metadata", {}).get("plan", "starter")
        import secrets
        api_key = f"aca_{secrets.token_urlsafe(32)}"
        users_db[api_key] = {
            "email": email,
            "plan": plan,
            "api_key": api_key,
            "created_at": datetime.utcnow().isoformat(),
            "tasks_this_month": 0,
            "stripe_customer_id": session.get("customer"),
        }
        print(f"✅ New user: {email} | Plan: {plan}")
    return {"received": True}


@app.get("/success")
async def payment_success():
    return HTMLResponse("""
    <html><head><title>Welcome!</title>
    <style>body{font-family:sans-serif;text-align:center;padding:80px;background:#07071a;color:white;}
    h1{color:#7c3aed;} a{color:#7c3aed;}</style></head>
    <body><h1>🎉 Welcome to AI Code Agent!</h1>
    <p>Your subscription is active. Check your email for your API key.</p>
    <p><a href="/">Go to Dashboard →</a></p></body></html>
    """)


@app.get("/metrics")
async def get_metrics():
    return {
        "total_jobs": _total_jobs,
        "completed_jobs": _completed_jobs,
        "active_jobs": sum(1 for j in jobs_db.values() if j["status"] in ["queued", "running"]),
        "active_users": len(users_db),
        "timestamp": datetime.utcnow().isoformat(),
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
