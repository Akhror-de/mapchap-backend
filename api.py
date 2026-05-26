from fastapi import FastAPI, HTTPException
import aiosqlite
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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
