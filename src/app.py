from fastapi import FastAPI

from src.api.routes import router as api_router

app = FastAPI(title="MSTeams Vertex Connector", version="1.0.0")
app.include_router(api_router)
