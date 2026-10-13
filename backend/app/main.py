from fastapi import FastAPI

app = FastAPI(
    title = "Elevate Solicitation Finder API",
    description = "Backend API for government solicitation discovery and analysis.",
    version = "0.1.0"
)

@app.get("/")
def root():
    return {
        "message": "Elevate Solicitation Finder API",
        "status" : "running",
    }