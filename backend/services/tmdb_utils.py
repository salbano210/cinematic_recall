import os
import asyncio
import httpx
from datetime import date
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# Standard TMDb keywords that indicate behind-the-scenes / making-of content
BTS_KEYWORDS = {
    "behind the scenes",
    "making of",
    "making-of",
    "featurette",
    "behind the camera",
}

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

        # Only use CAST credits — the actor must appear in the movie.
        # Including crew credits pulls in films they merely produced/crewed
        # (e.g. Tom Hanks producing 'Mamma Mia' or 'My Big Fat Greek Wedding').
        movies = data.get("cast", [])
        unique_movies = list({movie["id"]: movie for movie in movies}.values())

        # Filter 1: remove unreleased films (no release date, or dated in future)
        today = date.today().isoformat()
        released = [
            m for m in unique_movies
            if m.get("release_date") and m["release_date"] <= today
        ]

        # Filter 2: remove behind-the-scenes / making-of content by checking
        # TMDb keywords for each movie (batched concurrently for speed)
        async def is_bts(movie):
            try:
                resp = await client.get(
                    f"{TMDB_BASE_URL}/movie/{movie['id']}/keywords",
                    params={"api_key": TMDB_API_KEY}
                )
                resp.raise_for_status()
                keywords = resp.json().get("keywords", [])
                return any(k["name"].lower() in BTS_KEYWORDS for k in keywords)
            except Exception:
                # On API error, keep the movie rather than silently drop it
                return False

        bts_flags = await asyncio.gather(*(is_bts(m) for m in released))
        return [m for m, is_bts_movie in zip(released, bts_flags) if not is_bts_movie]

async def get_movie_details(movie_id: int):
    """Get a movie's synopsis and large poster from TMDb (for the info popup)."""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        poster_path = data.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE_URL}/w500{poster_path}" if poster_path else None

        return {
            "title": data.get("title"),
            "overview": data.get("overview"),
            "poster_url": poster_url,
            "year": (data.get("release_date") or "")[:4] or None,
            "runtime": data.get("runtime"),
        }

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