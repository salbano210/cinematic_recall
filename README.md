# 🎬 Cinematic Recall

**Cinematic Recall** is a daily movie memory and recall game. Each day features a famous actor from cinema history—your objective is to name as many movies from their filmography as you can and fill the ranked grid!

---

## 🎮 How to Play

1. **Reveal Today's Actor**: Start each day by revealing the featured actor and their filmography count.
2. **Name Movies**: Enter titles you remember that star the featured actor.
3. **Fuzzy Matching**: Intelligent matching forgives minor typos, alternate spellings, number words vs. digits (`two` ↔ `2`), roman numerals, and common short names for long titles.
4. **Rank & Popularity Grid**:
   - As you correctly guess movies, they appear in their popularity-ranked grid positions in **green**.
   - Each revealed tile displays the movie title, release year (e.g. `(1994)`), and its popularity percentage score.
5. **Give Up / Reveal Answers**:
   - Ready to see what you missed? Click **Give Up** at any time to fill all remaining un-guessed movies in **red** with their popularity percentages.
6. **Movie Info Popups**: Click any revealed tile to open a popup with the film's poster, synopsis, and runtime — the title links straight to its TMDb page.
7. **Come Back Anytime**: Your board is saved in your browser, so refreshing (or closing the tab) never loses your progress. A new game starts automatically at midnight Eastern.

---

## 🛠 Tech Stack

- **Frontend**: React 18, Vite, CSS (Modern Fluid Typography + Container Queries)
- **Backend**: FastAPI (Python 3.9+), Uvicorn, RapidFuzz (fuzzy title matching)
- **External API**: [The Movie Database (TMDb) API](https://www.themoviedb.org/documentation/api)
- **Deployment**: Render.com (FastAPI Web Service + React Static Site)

---

## 🚀 Local Development

### 1. Clone the repository

```bash
git clone https://github.com/salbano210/cinematic_recall.git
cd cinematic_recall
```

### 2. Backend Setup (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder:

```env
TMDB_API_KEY=your_tmdb_api_key_here

# Optional — force a specific actor instead of the daily rotation:
# ACTOR_OVERRIDE=6193            # by TMDb person ID, or
# ACTOR_OVERRIDE=Harrison Ford   # by name
```

Run the backend server:

```bash
uvicorn main:app --reload --port 8010
```

- API Docs / Swagger UI: `http://localhost:8010/docs`

### 3. Frontend Setup (React)

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Create a `.env` file in the `frontend/` folder:

```env
VITE_BACKEND_URL=http://localhost:8010
```

Open `http://localhost:5173` in your browser.

---

## 📁 Project Structure

```text
cinematic_recall/
├── backend/
│   ├── services/
│   │   └── tmdb_utils.py    # TMDb API integration & helpers
│   ├── Dockerfile           # Backend container definition
│   ├── main.py              # FastAPI endpoints & game logic
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (API keys)
├── frontend/
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── App.jsx          # Main Game UI & turn management
│   │   ├── App.css          # Responsive styling & container queries
│   │   └── main.jsx         # React application root
│   ├── index.html           # HTML entry point
│   ├── package.json         # Frontend dependencies & scripts
│   └── vite.config.js       # Vite configuration
├── DEPLOYMENT.md            # Render.com deployment guide
└── README.md                # Project documentation
```

---

## ✨ Features

- 📅 **Daily Actor Rotation**: A new featured actor every day at midnight US Eastern, drawn from a verified 40-actor list of cinema's biggest stars (heavy on the 80s–2000s era). No scheduler needed — the board is derived from the date.
- 🔧 **No-Code Actor Override**: Force a specific actor for a day by setting `ACTOR_OVERRIDE` (TMDb ID or name) in the backend's environment — changes take effect on the next deploy without touching code.
- 🎯 **Deterministic Daily Board**: The full filmography is ranked by popularity with a stable tiebreak, so every player gets the identical board all day — and it survives server restarts and deploys.
- 🚫 **Curated Filmography**: Documentaries, TV movies, shorts (<60 min), making-ofs, roast/variety specials, untagged tribute/TV-event entries, and other non-feature content are filtered out, so the board only contains "real" movies.
- 🔤 **Fuzzy String Matching**: Normalization + variant matching recognizes titles despite typos, punctuation differences, number words vs. digits, roman numerals, and common abbreviations of long titles.
- 💾 **Progress Persistence**: Game state is saved to `localStorage` and restored on reload; the server itself is stateless, so deploys never interrupt an in-progress game.
- ⚡ **Cold-Start Warm-Up**: The day's board is pre-fetched in the background when the site loads, hiding TMDb latency (and Render free-tier cold starts) behind the start screen.
- 🎞️ **Movie Info Popups**: Click a revealed tile for the poster, synopsis, and runtime, with a direct link to the film's TMDb page.
- 📱 **Mobile Responsive & Container Queries**: Auto-sizing typography ensures titles fit within each tile on all screen sizes from mobile to desktop.
- 🛑 **Immediate Error Feedback**: Shakes and glows red on unrecognized movie inputs without clearing your typed text so typos can easily be corrected.
- 💡 **Give Up & Review**: Instantly reveals all missed films in red tiles with release years and popularity percentages.
- 📋 **Share Your Result**: Wordle-style clipboard summary with the date, link, your score, and a 10-block progress bar:

  ```
  🎬 Cinematic Recall
  📅 August 30, 2026
  🔗 https://cinematic-recall.onrender.com
  Named: 48/113 Movies 🎞️
  [🟩🟩🟩🟩⬛⬛⬛⬛⬛⬛]
  ```

---

## 🔌 API Overview

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Health check; kicks off background warm-up of today's board |
| `/daily-actor` | GET | Today's featured actor (ID, name, image) |
| `/board?actor_id=` | GET | Board metadata — total movie count (titles stay hidden) |
| `/play-turn?actor_id=&player_movie=&filled_ranks=` | POST | Validate a guess against the daily board (stateless) |
| `/give-up?actor_id=&filled_ranks=` | POST | Reveal all un-guessed movies |
| `/movie-details?movie_id=` | GET | Synopsis, poster & runtime for the info popup |

All game state lives in the client; the server only validates guesses against the deterministic daily board.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
