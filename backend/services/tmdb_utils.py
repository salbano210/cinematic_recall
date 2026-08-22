import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

async def search_actor_by_name(name: str):
    url = f"{TMDB_BASE_URL}/search/person"
    params = {
        "api_key": TMDB_API_KEY,
        "query": name
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
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

async def get_actor_details(actor_id: int):
    """Get actor name, profile image, and details from TMDb"""
    url = f"{TMDB_BASE_URL}/person/{actor_id}"
    params = {"api_key": TMDB_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        profile_path = data.get("profile_path")
        profile_url = f"{TMDB_IMAGE_BASE_URL}/w185{profile_path}" if profile_path else None
        
        return {
            "name": data.get("name"),
            "profile_url": profile_url
        }