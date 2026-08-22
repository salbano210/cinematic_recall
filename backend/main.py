from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("✅ CORS middleware added")

from services.tmdb_utils import search_actor_by_name, get_actor_filmography
from services.tmdb_utils import search_actor_by_name
from fastapi import Query
import asyncio
from rapidfuzz import process, fuzz
from dotenv import load_dotenv
import os
import uuid
import datetime

# Store game sessions by game_id
game_sessions = {}


print("Launching FastAPI app...")

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

print("Defining /search-actor route...")

@app.get("/")
def read_root():
    return {"message": "TMDb API key loaded?", "key_loaded": TMDB_API_KEY is not None}

@app.get("/daily-actor")
async def get_daily_actor():
    # List of popular actors (IDs from TMDb)
    actor_list = [
        31,     # Tom Hanks
        2888,   # Will Smith
        1233,   # Johnny Depp
        1892,   # Matt Damon
        190,    # Morgan Freeman
        3061,   # Ryan Reynolds
        380,    # Robert De Niro
        6193,   # Leonardo DiCaprio
        64,     # Brad Pitt
        287,    # Bruce Willis
        2231,   # Samuel L. Jackson
        11856,  # Nicolas Cage
        113,    # Keanu Reeves
        3223,   # Robert Downey Jr.
        1245,   # Scarlett Johansson
        10912,  # Emma Stone
        54693,  # Emma Watson
        17605,  # Jennifer Lawrence
        5081,   # Meryl Streep
        11701   # Denzel Washington
    ]
    
    # Get day of year (0-365)
    day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
    actor_id = actor_list[day_of_year % len(actor_list)]
    
    return {"actor_id": actor_id}

@app.get("/search-actor")
async def search_actor(name: str = Query(..., description="Name of the actor or actress to search")):
    raw_results = await search_actor_by_name(name)
    processed_results = []

    for person in raw_results:
        processed_results.append({
            "name": person.get("name"),
            "id": person.get("id"),
            "tmdb_url": f"https://www.themoviedb.org/person/{person.get('id')}"
        })

    return {"results": processed_results}

@app.get("/actor-filmography")
async def actor_filmography(
    actor_id: int = Query(..., description="TMDb actor ID"),
    difficulty: str = Query("hard", description="Difficulty: easy, medium, or hard")
):
    movies = await get_actor_filmography(actor_id)

    # Sort by popularity descending
    sorted_movies = sorted(movies, key=lambda m: m.get("popularity", 0), reverse=True)

    # Limit by difficulty
    difficulty_levels = {"easy": 0.3, "medium": 0.6, "hard": 1.0}
    limit_ratio = difficulty_levels.get(difficulty.lower(), 1.0)
    limit = int(len(sorted_movies) * limit_ratio)
    filtered_movies = sorted_movies[:limit]

    # Simplify response
    return [
        {
            "title": movie.get("title"),
            "id": movie.get("id"),
            "release_date": movie.get("release_date"),
            "popularity": movie.get("popularity"),
            "tmdb_url": f"https://www.themoviedb.org/movie/{movie.get('id')}"
        }
        for movie in filtered_movies
    ]
@app.post("/start-game")
async def start_game(
    actor_id: int = Query(..., description="TMDb actor ID"),
    difficulty: str = Query("hard", description="Difficulty: easy, medium, or hard")
):
    movies = await get_actor_filmography(actor_id)

    # Sort by popularity
    sorted_movies = sorted(movies, key=lambda m: m.get("popularity", 0), reverse=True)
    difficulty_levels = {"easy": 0.3, "medium": 0.6, "hard": 1.0}
    limit_ratio = difficulty_levels.get(difficulty.lower(), 1.0)
    limit = int(len(sorted_movies) * limit_ratio)
    available_movies = sorted_movies[:limit]

    # Generate a unique game ID
    game_id = str(uuid.uuid4())

    game_sessions[game_id] = {
        "actor_id": actor_id,
        "movies": available_movies,
        "used_titles": [],
        "turn": "player"
    }

    return {
        "game_id": game_id,
        "num_available_movies": len(available_movies),
        "first_turn": "player"
    }
from fastapi import HTTPException
import random
from rapidfuzz import process

#PLAYING Turns
@app.post("/play-turn")
async def play_turn(
    game_id: str = Query(...),
    player_movie: str = Query(...)
):
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game not found")

    session = game_sessions[game_id]

    # Enforce turn order
    if session["turn"] != "player":
        return {"error": "It's not your turn yet!"}

    all_movies = session["movies"]
    used_titles = [t.lower() for t in session["used_titles"]]

    # Build list of unused titles
    remaining_titles = [
        m["title"] for m in all_movies
        if m["title"].lower() not in used_titles
    ]
    
    # Debug prints to help inspect the matching logic
    print("🎯 Player submitted:", player_movie)
    print("🎯 Remaining titles in pool:", remaining_titles)

# Normalize and map lowercase → original
    title_map = {title.lower(): title for title in remaining_titles}
    normalized_titles = list(title_map.keys())

    print("🎯 Player submitted:", player_movie)
    print("🎯 Normalized titles:", normalized_titles)

# Fuzzy match against normalized list
    match_result = process.extractOne(
    player_movie.lower(),
    normalized_titles,
    scorer=fuzz.WRatio,
    score_cutoff=70
)

    print("🧪 Match result:", match_result)

    if not match_result:
        return {"error": "Movie not recognized — try spelling it more closely"}

    matched_title = title_map[match_result[0]]

    # Check for reuse
    if matched_title.lower() in used_titles:
        return {"error": "That movie has already been used!"}

    session["used_titles"].append(matched_title)
    session["turn"] = "computer"


    # Rank all movies by popularity
    ranked_movies = sorted(all_movies, key=lambda m: m.get("popularity", 0), reverse=True)
    title_to_rank = {m["title"]: i + 1 for i, m in enumerate(ranked_movies)}

    player_stats = {
        "title": matched_title,
        "rank": title_to_rank.get(matched_title)
    }

    # Get remaining movies for computer
    remaining_movies = [
        m for m in all_movies
        if m["title"].lower() not in [t.lower() for t in session["used_titles"]]
    ]

    if not remaining_movies:
        return {
            "result": "You win! The computer has no more movies.",
            "player_move": player_stats,
            "computer_move": None,
            "remaining_movies": 0
        }

    # Computer picks next
    computer_choice = random.choice(remaining_movies)
    session["used_titles"].append(computer_choice["title"])
    session["turn"] = "player"

    computer_stats = {
        "title": computer_choice["title"],
        "rank": title_to_rank.get(computer_choice["title"]),
        "tmdb_url": f"https://www.themoviedb.org/movie/{computer_choice['id']}"
    }

    return {
        "player_move": player_stats,
        "computer_move": computer_stats,
        "remaining_movies": len(remaining_movies) - 1
    }

# RECORDING the state of the game
@app.get("/game-state")
def game_state(game_id: str = Query(...)):
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game not found")

    session = game_sessions[game_id]

    return {
        "actor_id": session["actor_id"],
        "turn": session["turn"],
        "used_titles": session["used_titles"],
        "remaining_movies": len([
            m for m in session["movies"]
            if m["title"].lower() not in [t.lower() for t in session["used_titles"]]
        ])
    }

# CONCEDING the game
@app.post("/concede")
def concede_game(game_id: str = Query(...)):
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game not found")

    # End the game and remove the session
    del game_sessions[game_id]

    return {
        "result": "You conceded. The computer wins!",
        "game_over": True,
        "winner": "computer"
    }
