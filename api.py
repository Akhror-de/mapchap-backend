from fastapi import FastAPI
import aiosqlite
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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