from fastapi import FastAPI, HTTPException
import aiosqlite
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

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
    contact: str = None   # новое поле: контакт предпринимателя
    expiry: str = None
    category: str
    lat: float
    lng: float

async def init_db():
    async with aiosqlite.connect("data.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                discount TEXT,
                category TEXT,
                lat REAL,
                lng REAL
            )
        """)
        # Добавляем contact и expiry, если их ещё нет
        try:
            await db.execute("ALTER TABLE places ADD COLUMN expiry TEXT")
        except:
            pass
        try:
            await db.execute("ALTER TABLE places ADD COLUMN contact TEXT")
        except:
            pass
        await db.commit()

@app.on_event("startup")
async def startup_event():
    await init_db()
    try:
        from bot import start_bot
        asyncio.create_task(start_bot())
        print("Бот запущен как asyncio задача")
    except Exception as e:
        print(f"Не удалось запустить бота: {e}")

@app.get("/api/places")
async def get_places():
    async with aiosqlite.connect("data.db") as db:
        cursor = await db.execute(
            "SELECT name, description, discount, contact, expiry, category, lat, lng FROM places "
            "WHERE expiry IS NULL OR datetime(expiry) > datetime('now')"
        )
        rows = await cursor.fetchall()
        places = []
        for row in rows:
            places.append({
                "name": row[0],
                "description": row[1],
                "discount": row[2],
                "contact": row[3],
                "expiry": row[4],
                "category": row[5],
                "lat": row[6],
                "lng": row[7]
            })
        return places

@app.post("/api/add_place")
async def add_place(place: Place):
    async with aiosqlite.connect("data.db") as db:
        await db.execute(
            "INSERT INTO places (name, description, discount, contact, expiry, category, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (place.name, place.description, place.discount, place.contact, place.expiry, place.category, place.lat, place.lng)
        )
        await db.commit()
    return {"status": "ok"}
