from fastapi import FastAPI
from src.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# launch without docker
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )