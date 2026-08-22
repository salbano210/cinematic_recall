import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

async def search_actor_by_name(name: str):
    url = f"{TMDB_BASE_URL}/search/person"
    params = {
        "api_key": TMDB_API_KEY,
        "query": name
    }
    print(f"🔍 Searching TMDb for: {name}")
    print(f"📦 Using API key: {TMDB_API_KEY}")

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"🔁 Status code: {response.status_code}")
        print(f"🧾 Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    
async def get_actor_filmography(actor_id: int):
    url = f"{TMDB_BASE_URL}/person/{actor_id}/movie_credits"
    params = {"api_key": TMDB_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Combine cast + crew, then deduplicate by movie ID
        movies = data.get("cast", []) + data.get("crew", [])
        unique_movies = {movie["id"]: movie for movie in movies}.values()
        return list(unique_movies)
