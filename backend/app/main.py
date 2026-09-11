from fastapi import FastAPI

app = FastAPI(title="Cloud Ops AI Intelligence")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
