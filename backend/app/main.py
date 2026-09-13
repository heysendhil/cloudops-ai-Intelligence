from fastapi import FastAPI

from app.api import incidents_router

app = FastAPI(title="Cloud Ops AI Intelligence")
app.include_router(incidents_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
