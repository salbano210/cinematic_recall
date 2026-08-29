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

from services.tmdb_utils import search_actor_by_name, get_actor_filmography, get_actor_details, get_movie_details
from fastapi import Query
import asyncio
from rapidfuzz import process, fuzz
from dotenv import load_dotenv
import os
import datetime
import re

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# ==============================================================================
# ACTOR OVERRIDE CONFIGURATION:
# - Set to None to use the automatic daily rotation schedule.
# - Set to a TMDb Person ID (e.g. 6193 for Leonardo DiCaprio) to force that actor.
# - Set to an actor's name (e.g. "Harrison Ford") to automatically search & use them.
# ==============================================================================
ACTOR_OVERRIDE = 1461 #clooney

@app.get("/")
async def read_root():
    # Kick off a background warm-up of today's actor data so that by the time
    # the player clicks "start", the board is already built (Render free tier
    # cold-starts are slow; this hides the TMDb latency behind the page load).
    asyncio.create_task(warm_daily_cache())
    return {"message": "Cinematic Recall API", "key_loaded": TMDB_API_KEY is not None}


# ----------------------------------------------------------------------
# DAILY CACHE: filmography + actor details cached per actor per day, so the
# root ping can pre-build the board and start-game/daily-actor are instant.
# ----------------------------------------------------------------------
_cache = {}  # actor_id -> {"date": "YYYY-MM-DD", "movies": [...], "details": {...}}

def _cache_key_date():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")

async def get_daily_actor_id() -> int:
    """Resolve today's actor ID (override or rotation) — shared by /daily-actor and warm-up."""
    if ACTOR_OVERRIDE is not None:
        if isinstance(ACTOR_OVERRIDE, int):
            return ACTOR_OVERRIDE
        # If a name like "Russell Crowe" is provided, search TMDb
        search_results = await search_actor_by_name(ACTOR_OVERRIDE)
        if not search_results:
            raise HTTPException(status_code=404, detail=f"Actor '{ACTOR_OVERRIDE}' not found on TMDb")
        return search_results[0]["id"]
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
    return actor_list[day_of_year % len(actor_list)]

async def warm_daily_cache():
    """Pre-fetch today's actor details + filmography into the cache. Safe to call often."""
    try:
        actor_id = await get_daily_actor_id()
        today = _cache_key_date()
        entry = _cache.get(actor_id)
        if entry and entry["date"] == today and "details" in entry:
            return  # already warm for today
        details = await get_actor_details(actor_id)
        movies = await get_actor_filmography(actor_id)
        _cache[actor_id] = {"date": today, "movies": movies, "details": details}
    except Exception:
        # Warm-up is best-effort; real endpoints will fetch on demand
        pass

@app.get("/daily-actor")
async def get_daily_actor():
    actor_id = await get_daily_actor_id()
    today = _cache_key_date()

    # Serve from cache when warm (details were pre-fetched by the root ping)
    entry = _cache.get(actor_id)
    if entry and entry["date"] == today and "details" in entry:
        actor_details = entry["details"]
    else:
        actor_details = await get_actor_details(actor_id)
        _cache[actor_id] = {"date": today, "details": actor_details}

    return {
        "actor_id": actor_id,
        "actor_name": actor_details["name"],
        "actor_image": actor_details["profile_url"]
    }

async def get_ranked_board(actor_id: int) -> list[dict]:
    """Deterministically ranked board for an actor.

    Sort key is (popularity desc, TMDb movie id asc) so the board is identical
    for every player, on every refresh, and across server restarts/deploys —
    no server-side session state needed.
    """
    today = _cache_key_date()
    entry = _cache.get(actor_id)

    # Use the cached filmography when fresh; otherwise fetch and cache
    if entry and entry["date"] == today and "movies" in entry:
        movies = entry["movies"]
    else:
        movies = await get_actor_filmography(actor_id)
        if entry and entry["date"] == today:
            entry["movies"] = movies
        else:
            _cache[actor_id] = {"date": today, "movies": movies}

    # Full (filtered) filmography, deterministic order: popularity desc,
    # movie id as tiebreak so equal popularities never shuffle between loads.
    available_movies = sorted(
        movies,
        key=lambda m: (-(m.get("popularity") or 0), m.get("id") or 0)
    )

    total = len(available_movies)
    ranked_movies = []
    for rank_idx, movie in enumerate(available_movies):
        rank = rank_idx + 1
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

    return ranked_movies


@app.get("/board")
async def get_board(
    actor_id: int = Query(..., description="TMDb actor ID")
):
    """Board metadata only — no titles/years (those stay hidden until guessed)."""
    ranked = await get_ranked_board(actor_id)
    return {
        "actor_id": actor_id,
        "total": len(ranked)
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


def _title_variants(title: str) -> tuple[list[str], list[str]]:
    """Generate matchable variants of a title, split by match strength.

    Returns (primary, heads):
    - primary: the full normalized title, plus the colon-stripped main part
      (e.g. 'Dune: Part Two' -> ['dune 2', 'dune'])
    - heads: short first-3/4-word variants for long titles, fuzzy-matching only
      (e.g. 'The French Dispatch of the Liberty, Kansas Evening Sun'
       -> heads: ['the french dispatch of the', 'the french dispatch'])

    Heads are separate because they can exactly collide with OTHER real titles
    (e.g. "'Ocean's Eleven': The Look of the Con" has head 'ocean s 11', which
    equals the real "Ocean's Eleven") — so they must never win an exact match
    against a title that is itself in the pool.
    """
    norm = _normalize(title)
    primary = [norm]

    if ':' in title:
        main_part = _normalize(title.split(':', 1)[0])
        if main_part and main_part != norm:
            primary.append(main_part)

    heads = []
    words = norm.split()
    if len(words) >= 5:
        for head in (' '.join(words[:4]), ' '.join(words[:3])):
            if head not in primary and head not in heads:
                heads.append(head)

    return primary, heads


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

    # Build map: choice -> (primary_variants, head_variants)
    choice_variants = {c: _title_variants(c) for c in choices}

    # Tier 1a: exact match on the FULL normalized title — strongest signal,
    # always wins over any other title's colon-strip or head variant.
    for choice, (primary, _) in choice_variants.items():
        if primary[0] == norm_guess:
            return choice
        # Try stripping articles on both sides
        if _strip_article(primary[0]) == norm_guess:
            return choice
        if primary[0] == _strip_article(norm_guess):
            return choice

    # Tier 1b: exact match on colon-stripped main parts
    for choice, (primary, _) in choice_variants.items():
        for variant in primary[1:]:
            if variant == norm_guess:
                return choice
            if _strip_article(variant) == norm_guess:
                return choice
            if variant == _strip_article(norm_guess):
                return choice

    # Tier 2: fuzzy match against all variants, keep the best-scoring one
    best_choice = None
    best_score = 0
    best_variant_len = 0
    for choice, (primary, heads) in choice_variants.items():
        for variant in primary + heads:
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


_movie_details_cache = {}  # movie_id -> details dict (immutable per movie, cache forever)

@app.get("/movie-details")
async def movie_details(
    movie_id: int = Query(..., description="TMDb movie ID")
):
    """Synopsis + large poster for the tile popup (proxied from TMDb)."""
    if movie_id in _movie_details_cache:
        return _movie_details_cache[movie_id]

    try:
        details = await get_movie_details(movie_id)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch movie details")

    _movie_details_cache[movie_id] = details
    return details


@app.post("/play-turn")
async def play_turn(
    actor_id: int = Query(..., description="TMDb actor ID"),
    player_movie: str = Query(...),
    filled_ranks: str = Query("", description="Comma-separated ranks already filled by the client")
):
    """Stateless turn: the client reports its filled ranks; the server validates
    the guess against the deterministic daily board. No session state required."""
    try:
        filled = {int(r) for r in filled_ranks.split(",") if r.strip()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filled_ranks")

    ranked_movies = await get_ranked_board(actor_id)

    # Get unused titles for matching (based on client-reported filled ranks)
    unused_lower = {m["title"].lower() for m in ranked_movies if m["rank"] not in filled}

    guess = player_movie.strip().lower()

    # Reject inputs that are too short to be a meaningful guess — unless the
    # guess exactly matches a title (e.g. the movie "21" or "Up").
    if len(guess) < 3 and guess not in unused_lower:
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
    if rank in filled:
        return {"error": "That movie has already been used!"}

    return {
        "movie": {
            "id": movie_entry["id"],
            "title": movie_entry["title"],
            "rank": movie_entry["rank"],
            "percentage": movie_entry["percentage"],
            "poster_url": movie_entry["poster_url"],
            "year": movie_entry.get("year")
        },
        "filled_count": len(filled) + 1,
        "total": len(ranked_movies)
    }

@app.post("/give-up")
async def give_up(
    actor_id: int = Query(..., description="TMDb actor ID"),
    filled_ranks: str = Query("", description="Comma-separated ranks already filled by the client")
):
    try:
        filled = {int(r) for r in filled_ranks.split(",") if r.strip()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filled_ranks")

    ranked_movies = await get_ranked_board(actor_id)

    # Return all movies the player missed
    missed = [
        {
            "id": m["id"],
            "title": m["title"],
            "rank": m["rank"],
            "percentage": m["percentage"],
            "year": m.get("year")
        }
        for m in ranked_movies
        if m["rank"] not in filled
    ]

    return {
        "missed": missed,
        "filled_count": len(filled),
        "total": len(ranked_movies)
    }