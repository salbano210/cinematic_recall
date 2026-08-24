# 🎬 Cinematic Recall

**Cinematic Recall** is a daily movie memory and recall game. Each day features a famous actor from cinema history—your objective is to name as many movies from their filmography as you can and fill the ranked grid!

---

## 🎮 How to Play

1. **Reveal Today's Actor**: Start each day by revealing the featured actor and their filmography count.
2. **Name Movies**: Enter titles you remember that star the featured actor.
3. **Fuzzy Matching**: Intelligent matching forgives minor typos, alternate spellings, and small omissions.
4. **Rank & Popularity Grid**:
   - As you correctly guess movies, they appear in their popularity-ranked grid positions in **green**.
   - Each revealed tile displays the movie title, release year (e.g. `(1994)`), and its popularity percentage score.
5. **Give Up / Reveal Answers**:
   - Ready to see what you missed? Click **Give Up** at any time to fill all remaining un-guessed movies in **red** with their popularity percentages.

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

- 📅 **Daily Actor Rotation**: Automatically rotates to a new featured actor each day based on the calendar year.
- 🎯 **Popularity-Ranked Movie Grid**: Movie squares are ordered by TMDb popularity so you can gauge how well-known each title is.
- 🔤 **Fuzzy String Matching**: Uses rapid string matching to recognize movie titles even with minor typos.
- 📱 **Mobile Responsive & Container Queries**: Auto-sizing typography ensures titles fit within each tile on all screen sizes from mobile to desktop.
- 🛑 **Immediate Error Feedback**: Shakes and glows red on unrecognized movie inputs without clearing your typed text so typos can easily be corrected.
- 💡 **Give Up & Review**: Instantly reveals all missed films in red tiles with release years and popularity percentages.
- 📋 **Share Your Result**: Wordle-style clipboard summary with your score and a performance square (🟥 <25%, 🟨 25–75%, 🟩 75%+).

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
