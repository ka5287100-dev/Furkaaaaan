# app.py

from fastapi import FastAPI, Query
from typing import Optional
import httpx
import asyncio
from api import stripe_auth

app = FastAPI()

@app.get("/check")
async def check(
    card: str = Query(...), 
    site: str = Query(...)
):
    try:
        async with httpx.AsyncClient(timeout=90) as session:
            result = await stripe_auth(card, site, session)
        return result

    except Exception as e:
        return {"status": False, 'response': f'{str(e)}', 'gate': 'AutoStripe Auth', 'card': card}
      
