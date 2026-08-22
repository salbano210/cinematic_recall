import { useState } from 'react';
import axios from 'axios';
import './App.css';

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

  const revealActor = async () => {
    setLoading(true);
    setError(null);
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
    setLoading(false);
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
      }
      
      setPlayerInput("");
      setError(null);
    } catch (err) {
      console.error("Turn error:", err);
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
                onChange={(e) => setPlayerInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && playTurn()}
                className="input"
              />
              <button onClick={playTurn} className="btn btn-success">
                Submit
              </button>
            </div>

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
                        <span className="movie-title" title={revealed.title}>
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

            {!gaveUp && (
              <button onClick={giveUp} className="btn btn-giveup">
                Give Up
              </button>
            )}

            {error && (
              <div className="error">
                {error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;