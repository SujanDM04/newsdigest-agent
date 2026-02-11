# NewsDigest Agent — Build Report

## Overview

We built a local AI-powered news digest tool that fetches real-time news articles and summarizes them using a local LLM. No external API keys required.

## What Was Built

### 1. FastAPI Backend (`backend/main.py`)

Four endpoints:

| Method | Endpoint  | What it does |
|--------|-----------|--------------|
| GET    | `/`       | Health check — returns `{"status": "NewsDigest Agent Ready"}` |
| POST   | `/test`   | Echo endpoint — accepts a topic, returns it back |
| POST   | `/news`   | Fetches 5 recent news articles from DuckDuckGo |
| POST   | `/digest` | Fetches news + summarizes them via Ollama (llama3.1) |

### 2. Frontend (`frontend/index.html`)

A single HTML page that:
- Takes a topic as input
- Calls the `/digest` endpoint
- Displays the AI-generated summary
- Lists source articles with title, link, source, and date
- Shows errors in red if Ollama is down, still shows articles

### 3. Error Handling

- **503** if Ollama is not running (with message: "Start it with: ollama serve")
- **502** if Ollama returns a model error
- In both cases, fetched articles are still returned so the user isn't left empty-handed

## Tech Stack

- **FastAPI** — backend framework
- **DuckDuckGo Search** — real-time news (no API key)
- **Ollama (llama3.1)** — local LLM summarization
- **Vanilla HTML/CSS/JS** — frontend

## Project Structure

```
newsdigest-agent/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   └── index.html
├── .gitignore
└── README.md
```

## Git History

```
e28002f Add error handling for when Ollama is unavailable
57c269d Initial project scaffold with FastAPI backend and frontend
```

## How to Run

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open `frontend/index.html` in a browser.
