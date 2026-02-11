import json
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from duckduckgo_search import DDGS
import ollama

app = FastAPI(title="NewsDigest Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class TopicRequest(BaseModel):
    topic: str
    model: Optional[str] = None
    max_results: Optional[int] = 5


def _get_default_model() -> str:
    """Return the first locally available model name, or 'llama3.1' as fallback."""
    try:
        models = ollama.list().get("models", [])
        if models:
            return models[0]["model"]
    except Exception:
        pass
    return "llama3.1"


@app.get("/")
def root():
    return {"status": "NewsDigest Agent Ready"}


@app.get("/models")
def list_models():
    try:
        models = ollama.list().get("models", [])
        return {"models": [m["model"] for m in models]}
    except Exception as e:
        return JSONResponse(status_code=503, content={"error": str(e), "models": []})


@app.post("/test")
def test_topic(request: TopicRequest):
    return {"message": f"Received topic: {request.topic}"}


@app.post("/news")
def fetch_news(request: TopicRequest):
    with DDGS() as ddgs:
        results = list(ddgs.news(request.topic, max_results=request.max_results))
    articles = [
        {"title": r["title"], "url": r["url"], "source": r["source"], "date": r["date"]}
        for r in results
    ]
    return {"topic": request.topic, "count": len(articles), "articles": articles}


@app.post("/digest")
def digest_news(request: TopicRequest):
    model = request.model or _get_default_model()

    # Fetch news
    with DDGS() as ddgs:
        results = list(ddgs.news(request.topic, max_results=request.max_results))
    articles = [
        {"title": r["title"], "url": r["url"], "source": r["source"], "date": r["date"]}
        for r in results
    ]

    # Build prompt
    headlines = "\n".join(f"- {a['title']} ({a['source']})" for a in articles)
    prompt = (
        f"You are a news digest assistant. Summarize the following headlines about '{request.topic}' "
        f"into a brief, informative digest (3-5 sentences):\n\n{headlines}"
    )

    # Summarize with Ollama
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response["message"]["content"]
    except ConnectionError:
        return JSONResponse(
            status_code=503,
            content={"error": "Ollama is not running. Start it with: ollama serve", "articles": articles},
        )
    except ollama.ResponseError as e:
        return JSONResponse(
            status_code=502,
            content={"error": f"Ollama error: {e.error}", "articles": articles},
        )

    return {"topic": request.topic, "summary": summary, "articles": articles}


@app.get("/digest/stream")
def digest_stream(
    topic: str = Query(...),
    model: Optional[str] = Query(None),
    max_results: int = Query(5),
):
    chosen_model = model or _get_default_model()

    def event_generator():
        # Fetch news
        with DDGS() as ddgs:
            results = list(ddgs.news(topic, max_results=max_results))
        articles = [
            {"title": r["title"], "url": r["url"], "source": r["source"], "date": r["date"]}
            for r in results
        ]

        # Send articles immediately
        yield f"event: articles\ndata: {json.dumps(articles)}\n\n"

        # Build prompt
        headlines = "\n".join(f"- {a['title']} ({a['source']})" for a in articles)
        prompt = (
            f"You are a news digest assistant. Summarize the following headlines about '{topic}' "
            f"into a brief, informative digest (3-5 sentences):\n\n{headlines}"
        )

        # Stream summary from Ollama
        try:
            stream = ollama.chat(
                model=chosen_model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                yield f"data: {json.dumps(token)}\n\n"
        except ConnectionError:
            yield f"event: error\ndata: {json.dumps('Ollama is not running. Start it with: ollama serve')}\n\n"
        except ollama.ResponseError as e:
            yield f"event: error\ndata: {json.dumps(f'Ollama error: {e.error}')}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
