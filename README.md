# 🦥 LazyMorning — Your Overnight Life Assistant

> **"Slow plans, brighter days."**  
> *Built for the "Slow and Steady" Open-Source AI Challenge.*

LazyMorning is a privacy-first, 100% local personal morning assistant. While you sleep, LazyMorning reviews your active tasks, notes, deadlines, and approved files to prepare a serene, focused morning briefing—eliminating morning decision fatigue and friction.

---

## 📸 Design & Experience

Crafted to match modern, calming aesthetics with an adorable mascot and clean cards:

1. **Dashboard**: Daily greeting, Today's Focus hero banner, 4 vital metrics (Top Priorities, Upcoming Deadlines, Pending Tasks, Total Notes), latest briefing summary, and quick actions.
2. **Morning Briefing**: Today's Focus, Top 3 Priorities (with reasoning and deadlines), Upcoming Deadlines list, Unfinished Items, and a gentle Suggested First Step.
3. **Notes**: Create, organize, tag, and search thoughts and ideas.
4. **Tasks**: Track priorities (High, Medium, Low), due dates, and instant checkbox completion.
5. **Imported Files**: Scan and import local `.txt` and `.md` files with a **Privacy Approval Gate** (AI only reads files you explicitly approve).
6. **Briefing History**: Review, expand, and export past briefings as `.txt` files.
7. **Settings**: Configure automated daily briefing schedule time, timezone, and AI model settings.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Frontend**: Streamlit with custom CSS and base64 asset rendering
- **Database**: SQLite with SQLAlchemy ORM
- **AI & Fallback**: Ollama with open-weight models (e.g. `qwen2.5:7b`), backed by a resilient, deterministic local offline engine
- **Scheduler**: APScheduler for automatic overnight/early morning briefing generation
- **Testing**: Pytest & Pytest-Asyncio (100% passing tests)

---

## 🚀 Quick Start (Windows Setup)

### 1. Install Dependencies
Open PowerShell or Command Prompt in the project folder and run:
```bash
pip install -r requirements.txt
```

### 2. Launch LazyMorning
You can launch both the backend API and frontend dashboard with one click:
```cmd
run_all.bat
```
Or start them individually in separate terminals:
- **Backend**: `run_backend.bat` (or `python -m uvicorn backend.app.main:app --port 8000 --reload`)
- **Frontend**: `run_frontend.bat` (or `python -m streamlit run frontend/app.py --server.port 8501`)

### 3. Open in Browser
- **Streamlit Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI OpenAPI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ☁️ Cloudflare & AI Integration

LazyMorning provides first-class support for running Ollama through **Cloudflare**:

### 1. Ollama via Cloudflare Tunnel
- If you run Ollama on a remote GPU machine or behind a Cloudflare Tunnel (e.g. `https://xxxx.trycloudflare.com` or custom domain `https://ollama.yourdomain.com`), simply paste your Tunnel URL in **Settings -> ☁️ Cloudflare & AI Configuration**.
- **Cloudflare Zero Trust / Access Support**: If your tunnel is protected by Cloudflare Access, configure `CF-Access-Client-Id` and `CF-Access-Client-Secret` (or `Bearer Token`) directly in the UI.

### 2. Cloudflare Workers AI (Serverless Qwen 2.5)
- If you don't have local GPU power or want serverless execution, select **Cloudflare Workers AI** in Settings.
- Enter your **Cloudflare Account ID** and **API Token**.
- LazyMorning runs `@cf/qwen/qwen2.5-7b-instruct` on Cloudflare's serverless GPUs with zero local hardware load.

### 3. Zero-Dependency Local Fallback Engine
- If your Cloudflare Tunnel or Ollama instance is ever offline or unreachable, LazyMorning automatically and seamlessly generates the morning briefing using its deterministic local rule-based offline engine.
- **Hallucination Prevention**: Output validator cross-references generated tasks and deadlines against database records to eliminate false dates or ghost tasks.

---

## 🔒 Privacy & File Approval Gate

In LazyMorning, privacy is non-negotiable:
- All processing is local.
- Files dropped into the `imports/` folder are scanned in a pending state (`⏳ Needs Approval`).
- You must click **"✅ Approve for AI"** before an imported file's content can be included in the AI context.

---

## 🧪 Running Automated Tests

Run the test suite with verbose output:
```bash
python -m pytest tests/ -v
```
All 10 test suites cover CRUD APIs, file approval security, briefing generation, hallucination filtering, and offline fallback.

---

## 📂 Project Architecture

```
LazyMorning/
├── backend/
│   └── app/
│       ├── config.py              # Environment and app configuration
│       ├── database.py            # SQLite engine & session management
│       ├── main.py                # FastAPI app with seed data & scheduler
│       ├── models/                # SQLAlchemy ORM models (Note, Task, Briefing, File)
│       ├── schemas/               # Pydantic request & response validation
│       ├── routers/               # REST API endpoints (notes, tasks, files, briefings, settings)
│       ├── services/              # AI service, briefing generator, file sync, scheduler
│       └── utils/                 # Hallucination filter and parser
├── frontend/
│   ├── app.py                     # Streamlit multi-view application
│   ├── styles.css                 # Custom modern styling
│   └── assets/                    # Sloth mascot and cozy banner illustrations
├── tests/                         # Pytest test suite (10/10 passing)
├── data/                          # SQLite database location
├── imports/                       # Directory for local .txt & .md files
├── requirements.txt               # Python package dependencies
├── run_backend.bat                # Windows backend launch script
├── run_frontend.bat               # Windows frontend launch script
├── run_all.bat                    # Windows unified launch script
└── README.md
```

---
*Created with care for the Slow and Steady Challenge.*
