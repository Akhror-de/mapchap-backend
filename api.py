from fastapi import FastAPI, HTTPException
import aiosqlite
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import threading
import asyncio
import os

# Импортируем главную функцию бота из bot.py
from bot import main as bot_main

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Place(BaseModel):
    name: str
    description: str
    discount: str
    category: str
    lat: float
    lng: float

@app.on_event("startup")
async def startup_event():
    """Запускаем бота в отдельном потоке при старте сервера"""
    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_main())
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Бот запущен в фоне")

@app.get("/api/places")
async def get_places():
    async with aiosqlite.connect("data.db") as db:
        cursor = await db.execute("SELECT name, description, discount, category, lat, lng FROM places")
        rows = await cursor.fetchall()
        places = []
        for row in rows:
            places.append({
                "name": row[0],
                "description": row[1],
                "discount": row[2],
                "category": row[3],
                "lat": row[4],
                "lng": row[5]
            })
        return places

@app.post("/api/add_place")
async def add_place(place: Place):
    async with aiosqlite.connect("data.db") as db:
        await db.execute(
            "INSERT INTO places (name, description, discount, category, lat, lng) VALUES (?, ?, ?, ?, ?, ?)",
            (place.name, place.description, place.discount, place.category, place.lat, place.lng)
        )
        await db.commit()
    return {"status": "ok"}
