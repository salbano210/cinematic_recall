# 🎬 Cinematic Recall

A turn-based memory game where you and the computer alternate naming movies from an actor's filmography. Built with FastAPI (Python) and React (Vite), using data from the TMDb API.

## 🧠 Game Overview

- Choose an actor (currently defaults to Tom Hanks)
- Pick a difficulty: easy, medium, or hard
- You and the computer alternate naming valid movies
- The computer’s knowledge is limited based on difficulty
- You win if the computer runs out of movies first

## 🛠 Tech Stack

Frontend: React + Vite  
Backend: FastAPI (Python 3.9+)  
External API: TMDb (https://www.themoviedb.org/documentation/api)

## 🚀 Local Development

### 1. Clone the repo

git clone https://github.com/salbano210/cinematic_recall.git
cd cinematic_recall

shell
Copy
Edit

### 2. Backend Setup (FastAPI)

cd backend
python3 -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install fastapi uvicorn httpx python-dotenv rapidfuzz

bash
Copy
Edit

Create a `.env` file:

TMDB_API_KEY=your_tmdb_api_key_here

yaml
Copy
Edit

Run the backend:

uvicorn main:app --reload --port 8010

bash
Copy
Edit

Swagger docs: http://localhost:8010/docs

### 3. Frontend Setup (React)

cd ../frontend
npm install
npm run dev

bash
Copy
Edit

Visit: http://localhost:5173

## 📂 Folder Structure

cinematic_recall/
├── backend/ # FastAPI app
│ ├── main.py
│ ├── services/
│ └── .env
├── frontend/ # React + Vite app
│ ├── src/
│ ├── public/
│ └── package.json

markdown
Copy
Edit

## ✨ Features

- Fuzzy matching for user input (e.g., “forrest gum”)
- Popularity-ranked movie knowledge pool
- Computer difficulty scaling
- Full turn logic and win detection
- Game state tracking and manual concede option

## 📌 Coming Soon

- Actor search UI
- Movie posters and links
- Leaderboard or multiplayer

## 📝 License

MIT
