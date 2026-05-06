from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.v1 import auth, users, categories, products, currency, logs, pages
from src.core.config import settings
from src.db.database import cleanup
from src.db.seed import seed

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await seed()
    except Exception as e:
        print(f"Failed to seed database: {e}")
        raise

    yield

    await cleanup()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(currency.router)
app.include_router(logs.router)
app.include_router(pages.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}