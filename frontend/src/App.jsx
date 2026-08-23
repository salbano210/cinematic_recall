import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const getTitleClass = (title) => {
  if (!title) return '';
  const len = title.length;
  if (len <= 10) return 'title-short';
  if (len <= 20) return 'title-medium';
  if (len <= 32) return 'title-long';
  return 'title-xlong';
};

function App() {
  const [actorName, setActorName] = useState(null);
  const [actorImage, setActorImage] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [playerInput, setPlayerInput] = useState("");
  const [filledRanks, setFilledRanks] = useState({});
  const [missedRanks, setMissedRanks] = useState({});
  const [gaveUp, setGaveUp] = useState(false);
  const [totalMovies, setTotalMovies] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [slowLoad, setSlowLoad] = useState(false);

  // Warm up the backend as soon as the page loads. Render's free tier
  // sleeps after 15 min of inactivity and takes 30-50s to cold-start,
  // so ping it in the background before the user clicks anything.
  useEffect(() => {
    axios.get(`${import.meta.env.VITE_BACKEND_URL}/`).catch(() => {
      // Ignore errors — this is just a wake-up ping
    });
  }, []);

  const triggerShake = () => {
    setIsShaking(true);
    setTimeout(() => {
      setIsShaking(false);
    }, 600);
  };

  const revealActor = async () => {
    setLoading(true);
    setError(null);
    setSlowLoad(false);
    // If the request takes more than 3s the server is probably cold-starting
    const slowTimer = setTimeout(() => setSlowLoad(true), 3000);
    try {
      const res = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/daily-actor`);
      const actorId = res.data.actor_id;
      const name = res.data.actor_name || `Actor #${actorId}`;
      const image = res.data.actor_image;
      
      setActorName(name);
      setActorImage(image);
      
      const gameRes = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/start-game`, null, {
        params: {
          actor_id: actorId,
          difficulty: 'medium'
        }
      });
      
      setGameId(gameRes.data.game_id);
      setTotalMovies(gameRes.data.num_available_movies);
    } catch (err) {
      console.error("Error:", err);
      setError("Failed to reveal actor or start game.");
    }
    clearTimeout(slowTimer);
    setSlowLoad(false);
    setLoading(false);
  };

  const resetGame = () => {
    setGameId(null);
    setActorName(null);
    setActorImage(null);
    setFilledRanks({});
    setMissedRanks({});
    setGaveUp(false);
    setPlayerInput("");
    setTotalMovies(0);
  };

  const handleSessionExpired = () => {
    resetGame();
    setError("Your session expired (the server was updated). Click 'Reveal Today\'s Actor' to start fresh!");
  };

  const playTurn = async () => {
    if (!playerInput.trim()) return;
    
    try {
      const res = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/play-turn`, null, {
        params: {
          game_id: gameId,
          player_movie: playerInput
        }
      });
      
      if (res.data.movie) {
        const movie = res.data.movie;
        setFilledRanks(prev => ({
          ...prev,
          [movie.rank]: {
            title: movie.title,
            percentage: movie.percentage,
            year: movie.year
          }
        }));
        setPlayerInput("");
        setError(null);
      } else if (res.data.error) {
        triggerShake();
        setError(res.data.error);
      }
    } catch (err) {
      console.error("Turn error:", err);
      if (err.response?.status === 404 || err.response?.data?.detail === "Game not found") {
        handleSessionExpired();
        return;
      }
      triggerShake();
      const apiMessage = err.response?.data?.error || err.response?.data?.detail;
      setError(apiMessage || "Turn failed");
    }
  };

  const giveUp = async () => {
    try {
      const res = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/give-up`, null, {
        params: { game_id: gameId }
      });

      const missed = {};
      (res.data.missed || []).forEach(m => {
        missed[m.rank] = {
          title: m.title,
          percentage: m.percentage,
          year: m.year
        };
      });
      setMissedRanks(missed);
      setGaveUp(true);
      setError(null);
    } catch (err) {
      console.error("Give up error:", err);
      if (err.response?.status === 404 || err.response?.data?.detail === "Game not found") {
        handleSessionExpired();
        return;
      }
      setError("Failed to reveal answers.");
    }
  };

  return (
    <div className="app">
      <div className="container">
        <h1 className="title">Cinematic Recall</h1>

        {!gameId && (
          <div className="card">
            <h2 className="subtitle">Today's Featured Actor</h2>
            <button
              onClick={revealActor}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? 'Loading...' : 'Reveal Today\'s Actor'}
            </button>
            {loading && slowLoad && (
              <p className="slow-load-note">
                Waking up the game server — first load can take up to a minute...
              </p>
            )}
          </div>
        )}

        {gameId && (
          <div>
            <div className="card">
              {actorImage && (
                <img 
                  src={actorImage} 
                  alt={actorName}
                  className="actor-image"
                />
              )}
              <p className="label">Name movies by:</p>
              <p className="actor-name">{actorName}</p>
              <p className="count">{totalMovies} total movies</p>
            </div>

            <div className="input-group">
              <input
                type="text"
                placeholder="Enter a movie title..."
                value={playerInput}
                onChange={(e) => {
                  setPlayerInput(e.target.value);
                  if (error) setError(null);
                }}
                onKeyDown={(e) => e.key === 'Enter' && playTurn()}
                className={`input ${isShaking ? 'shake-error' : ''}`}
              />
              <button onClick={playTurn} className="btn btn-success">
                Submit
              </button>
              {!gaveUp && (
                <button onClick={giveUp} className="btn btn-giveup">
                  Give Up
                </button>
              )}
            </div>

            {error && (
              <div className="error">
                {error}
              </div>
            )}

            <div className="score">
              {Object.keys(filledRanks).length} / {totalMovies}
            </div>

            <div className="grid">
              {Array.from({ length: totalMovies }).map((_, index) => {
                const rank = index + 1;
                const filled = filledRanks[rank];
                const missed = missedRanks[rank];
                const revealed = filled || missed;
                return (
                  <div
                    key={rank}
                    className={`square ${filled ? 'filled' : ''} ${missed ? 'missed' : ''}`}
                  >
                    {revealed ? (
                      <>
                        <span className={`movie-title ${getTitleClass(revealed.title)}`} title={revealed.title}>
                          {revealed.title}
                        </span>
                        {revealed.year && (
                          <span className="movie-year">({revealed.year})</span>
                        )}
                        <span className="percentage">{revealed.percentage}%</span>
                      </>
                    ) : (
                      <span className="rank-number">{rank}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;