from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from services.tmdb_utils import search_actor_by_name, get_actor_filmography, get_actor_details
from fastapi import Query
import asyncio
from rapidfuzz import process, fuzz
from dotenv import load_dotenv
import os
import uuid
import datetime
import re

# Store game sessions by game_id
game_sessions = {}

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# ==============================================================================
# ACTOR OVERRIDE CONFIGURATION:
# - Set to None to use the automatic daily rotation schedule.
# - Set to a TMDb Person ID (e.g. 6193 for Leonardo DiCaprio) to force that actor.
# - Set to an actor's name (e.g. "Harrison Ford") to automatically search & use them.
# ==============================================================================
ACTOR_OVERRIDE = 1233 #PSH

@app.get("/")
def read_root():
    return {"message": "Cinematic Recall API", "key_loaded": TMDB_API_KEY is not None}

@app.get("/daily-actor")
async def get_daily_actor():
    if ACTOR_OVERRIDE is not None:
        if isinstance(ACTOR_OVERRIDE, int):
            actor_id = ACTOR_OVERRIDE
        elif isinstance(ACTOR_OVERRIDE, str):
            # If a name like "Russell Crowe" is provided, search TMDb
            search_results = await search_actor_by_name(ACTOR_OVERRIDE)
            if not search_results:
                raise HTTPException(status_code=404, detail=f"Actor '{ACTOR_OVERRIDE}' not found on TMDb")
            actor_id = search_results[0]["id"]
        else:
            actor_id = int(ACTOR_OVERRIDE)
    else:
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
        
        day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
        actor_id = actor_list[day_of_year % len(actor_list)]

    actor_details = await get_actor_details(actor_id)
    
    return {
        "actor_id": actor_id,
        "actor_name": actor_details["name"],
        "actor_image": actor_details["profile_url"]
    }

@app.post("/start-game")
async def start_game(
    actor_id: int = Query(..., description="TMDb actor ID"),
    difficulty: str = Query("hard", description="Difficulty: easy, medium, or hard")
):
    movies = await get_actor_filmography(actor_id)

    # Sort by popularity descending (most popular first = rank 1)
    sorted_movies = sorted(movies, key=lambda m: m.get("popularity", 0), reverse=True)
    difficulty_levels = {"easy": 0.3, "medium": 0.6, "hard": 1.0}
    limit_ratio = difficulty_levels.get(difficulty.lower(), 1.0)
    limit = int(len(sorted_movies) * limit_ratio)
    available_movies = sorted_movies[:limit]

    # Build ordered list by rank (index 0 = rank 1 = most popular)
    ranked_movies = []
    for rank_idx, movie in enumerate(available_movies):
        rank = rank_idx + 1
        total = len(available_movies)
        # Top movies = higher percentage
        percentage = max(5, int(((total - rank_idx) / total) * 100))
        
        # Get movie poster URL
        poster_path = movie.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE_URL}/w92{poster_path}" if poster_path else None

        # Extract release year (TMDB release_date is "YYYY-MM-DD")
        release_date = movie.get("release_date") or ""
        year = release_date[:4] if release_date else None

        ranked_movies.append({
            "title": movie["title"],
            "id": movie["id"],
            "rank": rank,
            "percentage": percentage,
            "poster_url": poster_url,
            "year": year
        })

    game_id = str(uuid.uuid4())

    game_sessions[game_id] = {
        "actor_id": actor_id,
        "ranked_movies": ranked_movies,
        "filled_ranks": set()
    }

    return {
        "game_id": game_id,
        "num_available_movies": len(available_movies)
    }

LEADING_ARTICLES = ("the ", "a ", "an ")

# --------------------------------------------------------------------------
# NUMBER & SYMBOL NORMALIZATION
# Movie titles are inconsistent in the wild: TMDb uses "Dune: Part Two" while
# users naturally type "dune: part 2". We normalize BOTH sides before matching
# so these are treated as identical, without needing a new library.
# --------------------------------------------------------------------------

WORD_TO_NUM = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20"
}
ROMAN_TO_NUM = {
    "i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5",
    "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10",
    "xi": "11", "xii": "12"
}

def _normalize(title: str) -> str:
    """Normalize a title for comparison:
    - lowercase
    - replace '&' with 'and'
    - strip punctuation (colons, hyphens, apostrophes, etc.)
    - convert number words ('two') and roman numerals ('ii') to digits ('2')
    - collapse whitespace
    """
    t = title.lower().strip()
    t = t.replace("&", " and ")
    # Remove all punctuation except spaces
    t = re.sub(r"[^\w\s]", " ", t)
    # Tokenize and normalize numbers
    tokens = []
    for tok in t.split():
        if tok in WORD_TO_NUM:
            tokens.append(WORD_TO_NUM[tok])
        elif tok in ROMAN_TO_NUM:
            tokens.append(ROMAN_TO_NUM[tok])
        else:
            tokens.append(tok)
    return " ".join(tokens)


def _strip_article(title: str) -> str:
    for article in LEADING_ARTICLES:
        if title.startswith(article):
            return title[len(article):]
    return title


def _title_variants(title: str) -> list[str]:
    """Generate matchable variants of a title:
    - The full normalized title
    - The title with subtitle stripped (everything after a colon)
    - For long titles without a colon, the first 3-4 words (the 'head')
      e.g. 'The French Dispatch of the Liberty, Kansas Evening Sun'
           -> 'the french dispatch'
    """
    norm = _normalize(title)
    variants = {norm}

    # Strip subtitle after colon (in original, before normalization removed it)
    if ':' in title:
        main_part = title.split(':', 1)[0]
        variants.add(_normalize(main_part))

    # For long titles, also accept the first few words as the common name
    words = norm.split()
    if len(words) >= 5:
        variants.add(' '.join(words[:4]))
        variants.add(' '.join(words[:3]))

    return list(variants)


def find_title_match(guess: str, choices) -> str | None:
    """Match a player's guess against the remaining movie titles.

    Uses normalization + title variants so that:
    - 'dune: part 2' ↔ 'Dune: Part Two' (number/punctuation normalization)
    - 'the french dispatch' ↔ 'The French Dispatch of the Liberty, Kansas
      Evening Sun' (long official titles match their common short name)
    - 'oceans 11' ↔ "Ocean's Eleven" (apostrophe/number handling)

    Tier 1 - exact match against any title variant (normalized).
    Tier 2 - fuzzy match (token_set_ratio >= 82) with a 40% length floor,
             checked against the best-matching variant (not the full title),
             so short common names for long titles still pass.
    """
    norm_guess = _normalize(guess)

    # Build map: choice -> list of normalized variants
    choice_variants = {c: _title_variants(c) for c in choices}

    # Tier 1: exact match against any variant
    for choice, variants in choice_variants.items():
        for variant in variants:
            if variant == norm_guess:
                return choice
            # Try stripping articles on both sides
            if _strip_article(variant) == norm_guess:
                return choice
            if variant == _strip_article(norm_guess):
                return choice

    # Tier 2: fuzzy match against all variants, keep the best-scoring one
    best_choice = None
    best_score = 0
    best_variant_len = 0
    for choice, variants in choice_variants.items():
        for variant in variants:
            score = fuzz.token_set_ratio(norm_guess, variant)
            if score > best_score:
                best_score = score
                best_choice = choice
                best_variant_len = len(variant)

    if best_score < 82:
        return None
    # Length floor: guess must be at least 40% of the matched VARIANT's length
    # (using the variant, not the full title, so 'the french dispatch' passes
    # against the 4-word head variant even though the full title is 55 chars)
    if len(norm_guess) < 0.4 * best_variant_len:
        return None
    return best_choice


@app.post("/play-turn")
async def play_turn(
    game_id: str = Query(...),
    player_movie: str = Query(...)
):
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game not found")

    session = game_sessions[game_id]
    ranked_movies = session["ranked_movies"]
    
    # Build map of all movie titles (lowercase -> original)
    title_map = {m["title"].lower(): m for m in ranked_movies}
    
    # Get unused titles for matching
    unused_titles = [m["title"] for m in ranked_movies if m["rank"] not in session["filled_ranks"]]
    unused_lower = {t.lower() for t in unused_titles}

    guess = player_movie.strip().lower()

    # Reject inputs that are too short to be a meaningful guess
    if len(guess) < 3:
        return {"error": "Please type more of the movie title"}

    matched_title = find_title_match(guess, unused_lower)

    if not matched_title:
        return {"error": "Movie not recognized — try spelling it more closely"}

    # Find the actual movie entry
    movie_entry = None
    for m in ranked_movies:
        if m["title"].lower() == matched_title:
            movie_entry = m
            break
    
    if not movie_entry:
        return {"error": "Movie not recognized"}

    rank = movie_entry["rank"]
    
    # Check if this rank is already filled
    if rank in session["filled_ranks"]:
        return {"error": "That movie has already been used!"}

    # Fill this rank
    session["filled_ranks"].add(rank)

    return {
        "movie": {
            "title": movie_entry["title"],
            "rank": movie_entry["rank"],
            "percentage": movie_entry["percentage"],
            "poster_url": movie_entry["poster_url"],
            "year": movie_entry.get("year")
        },
        "filled_count": len(session["filled_ranks"]),
        "total": len(ranked_movies)
    }

@app.post("/give-up")
async def give_up(game_id: str = Query(...)):
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game not found")

    session = game_sessions[game_id]
    ranked_movies = session["ranked_movies"]
    filled_ranks = session["filled_ranks"]

    # Return all movies the player missed
    missed = [
        {
            "title": m["title"],
            "rank": m["rank"],
            "percentage": m["percentage"],
            "year": m.get("year")
        }
        for m in ranked_movies
        if m["rank"] not in filled_ranks
    ]

    return {
        "missed": missed,
        "filled_count": len(filled_ranks),
        "total": len(ranked_movies)
    }

@app.get("/game-state")
def game_state(game_id: str = Query(...)):
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Game not found")

    session = game_sessions[game_id]
    return {
        "filled_ranks": list(session["filled_ranks"]),
        "total": len(session["ranked_movies"])
    }