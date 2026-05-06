import aiohttp
import time

from fastapi import HTTPException, APIRouter, Depends

from src.core.config import settings
from src.core.dependencies import require_simple
from src.schemas.schemas import CurrencyRate

router = APIRouter(prefix="/api/currency", tags=["currency"])

_cache: dict = {}

@router.get("/usd-rate", response_model=CurrencyRate, dependencies=[Depends(require_simple)])
async def get_usd_rate(price: float = 0):

    cache_key = "usd_rate"
    now = time.time()

    # 1 hour cache
    if cache_key in _cache and now - _cache[cache_key]["ts"] < 3600:
        rate_data = _cache[cache_key]["data"]
    else:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.NB_API_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        raise HTTPException(status_code=502, detail="Ошибка получения курса валют")
                    data = await resp.json(content_type=None)
                    rate_data = {
                        "currency": data.get("Cur_Abbreviation", "USD"),
                        "rate": float(data.get("Cur_OfficialRate", 1)),
                    }
                    _cache[cache_key] = {"data": rate_data, "ts": now}
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=502, detail=f"Ошибка сети: {str(e)}")

    price_usd = round(price / rate_data["rate"], 2) if price and rate_data["rate"] else 0

    return CurrencyRate(
        currency=rate_data["currency"],
        rate=rate_data["rate"],
        price_usd=price_usd,
    )