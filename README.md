# NewsDigest Agent

An AI-powered news digest agent that fetches and summarizes news on any topic.

## Project Structure

- `backend/main.py` - FastAPI server
- `backend/requirements.txt` - Python dependencies
- `backend/.env` - Environment variables

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Server runs at http://127.0.0.1:8000
