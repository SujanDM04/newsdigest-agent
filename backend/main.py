from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from duckduckgo_search import DDGS
import ollama

app = FastAPI(title="NewsDigest Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class TopicRequest(BaseModel):
    topic: str


@app.get("/")
def root():
    return {"status": "NewsDigest Agent Ready"}


@app.post("/test")
def test_topic(request: TopicRequest):
    return {"message": f"Received topic: {request.topic}"}


@app.post("/news")
def fetch_news(request: TopicRequest):
    with DDGS() as ddgs:
        results = list(ddgs.news(request.topic, max_results=5))
    articles = [
        {"title": r["title"], "url": r["url"], "source": r["source"], "date": r["date"]}
        for r in results
    ]
    return {"topic": request.topic, "count": len(articles), "articles": articles}


@app.post("/digest")
def digest_news(request: TopicRequest):
    # Fetch news
    with DDGS() as ddgs:
        results = list(ddgs.news(request.topic, max_results=5))
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
    response = ollama.chat(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}],
    )
    summary = response["message"]["content"]

    return {"topic": request.topic, "summary": summary, "articles": articles}
