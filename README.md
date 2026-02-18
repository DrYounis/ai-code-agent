# AI Code Agent 🤖⚡

> **Dual-agent AI code generation SaaS — Coder writes, Reviewer validates**

Submit any coding task in plain English. Two AI agents collaborate to write and review production-ready code in under 60 seconds.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

**Live Demo**: [your-deployment-url.railway.app](https://your-deployment-url.railway.app)

---

## 💰 Pricing

| Plan | Price | Tasks/month |
|------|-------|-------------|
| Starter | $99/mo | 20 |
| Professional | $199/mo | 100 |
| Team | $499/mo | Unlimited |

**Target**: 50 teams = **$9,950 MRR**

---

## 🏗️ Architecture

```
dual-agent-system/
├── api/
│   ├── main.py          ← FastAPI backend + Stripe + job queue
│   └── requirements.txt
├── dashboard/
│   └── index.html       ← Premium SaaS UI with real-time polling
├── agents/
│   ├── coder.py         ← Coder AI agent (CrewAI)
│   └── reviewer.py      ← Reviewer AI agent (CrewAI)
├── config/
│   └── llm_config.py    ← Groq LLM configuration
├── main.py              ← CLI entry point
├── railway.json         ← Deploy config
├── Procfile             ← Process config
└── .env.example         ← Environment variables
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/DrYounis/ai-code-agent
cd ai-code-agent
pip install -r api/requirements.txt

# Configure
cp .env.example .env
# Add GROQ_API_KEY and STRIPE keys

# Run
cd api && uvicorn main:app --reload --port 8001
# Open http://localhost:8001
```

---

## 🔑 Setup

### 1. Groq API (Free)
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up and get a free API key
3. Add to `.env`: `GROQ_API_KEY=gsk_...`

### 2. Stripe
1. Create 3 products (Starter $99, Pro $199, Team $499)
2. Copy Price IDs to `.env`
3. Set webhook: `POST /webhook`

---

## 🌐 API Reference

### `POST /generate`
Submit a code generation task.

**Headers**: `X-API-Key: your_api_key`

**Body**:
```json
{
  "description": "Build a REST API with FastAPI for user authentication",
  "language": "python",
  "framework": "FastAPI"
}
```

**Response**:
```json
{
  "job_id": "uuid",
  "status": "queued",
  "poll_url": "/jobs/uuid"
}
```

### `GET /jobs/{job_id}`
Poll for job results.

### `GET /jobs`
List all your jobs.

---

## 🤖 How It Works

1. **You submit** a task description in plain English
2. **Coder Agent** (Groq LLaMA) writes the complete implementation
3. **Reviewer Agent** (Groq LLaMA) reviews for bugs, quality, security
4. **You receive** production-ready, reviewed code

---

## 📄 License

MIT — built by [DrYounis](https://github.com/DrYounis)
