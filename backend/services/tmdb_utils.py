import os
import asyncio
import httpx
from datetime import date
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# Standard TMDb keywords that indicate behind-the-scenes / non-feature content
BTS_KEYWORDS = {
    "behind the scenes",
    "making of",
    "making-of",
    "featurette",
    "behind the camera",
    "stand-up",
    "stand-up comedy",
    "roast",
    "talk show",
    "concert",
    "tv special",
}

# TMDb genre IDs that aren't feature films players think of as "real" movies
NON_FEATURE_GENRES = {
    99,      # Documentary
    10770,   # TV Movie
}

# Minimum runtime (minutes) to count as a real feature film — filters out
# shorts, specials, and streaming variety shows that are miscategorized
MIN_FEATURE_RUNTIME = 60

# TMDb vote floor: entries below this are untagged specials, tributes, and
# obscurities nobody could guess (e.g. 'Betty White's 90th Birthday...' has
# 1 vote). Real feature films from famous actors reliably have 30+ votes.
MIN_VOTE_COUNT = 10

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

        # Filter 2: remove non-feature content. One /movie/{id} call per film
        # (batched concurrently) gives us full genres, runtime, and keywords —
        # much stronger signals than the genre_ids on the credits response,
        # which often miscategorize specials (e.g. 'The Roast of Tom Brady').
        async def is_feature(movie):
            # Vote floor first — it uses data already in the credits response,
            # so obviously-junk entries skip the per-movie API call entirely.
            if (movie.get("vote_count") or 0) < MIN_VOTE_COUNT:
                return False

            try:
                resp = await client.get(
                    f"{TMDB_BASE_URL}/movie/{movie['id']}",
                    params={"api_key": TMDB_API_KEY, "append_to_response": "keywords"}
                )
                resp.raise_for_status()
                details = resp.json()

                genre_ids = {g["id"] for g in details.get("genres", [])}
                if genre_ids & NON_FEATURE_GENRES:
                    return False

                runtime = details.get("runtime") or 0
                if runtime and runtime < MIN_FEATURE_RUNTIME:
                    return False

                keywords = [k["name"].lower() for k in details.get("keywords", {}).get("keywords", [])]
                if any(k in BTS_KEYWORDS for k in keywords):
                    return False

                return True
            except Exception:
                # On API error, keep the movie rather than silently drop it
                return True

        feature_flags = await asyncio.gather(*(is_feature(m) for m in released))
        return [m for m, is_feature_movie in zip(released, feature_flags) if is_feature_movie]

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