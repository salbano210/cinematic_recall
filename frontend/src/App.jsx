import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const STORAGE_KEY = 'cinematic_recall_state';

// YYYY-MM-DD for today, used to detect "same day" persistence
const getTodayString = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

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
  const [actorId, setActorId] = useState(null);
  const [playerInput, setPlayerInput] = useState("");
  const [filledRanks, setFilledRanks] = useState({});
  const [missedRanks, setMissedRanks] = useState({});
  const [gaveUp, setGaveUp] = useState(false);
  const [totalMovies, setTotalMovies] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [slowLoad, setSlowLoad] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);
  const [popupMovie, setPopupMovie] = useState(null);   // tile data of the clicked movie
  const [popupDetails, setPopupDetails] = useState(null); // fetched synopsis/poster
  const [popupLoading, setPopupLoading] = useState(false);

  // Warm up the backend as soon as the page loads. Render's free tier
  // sleeps after 15 min of inactivity and takes 30-50s to cold-start,
  // so ping it in the background before the user clicks anything.
  useEffect(() => {
    axios.get(`${import.meta.env.VITE_BACKEND_URL}/`).catch(() => {
      // Ignore errors — this is just a wake-up ping
    });

    // Restore today's in-progress or completed game from localStorage,
    // but only if the featured actor hasn't been overridden mid-day.
    // The game is stateless (board derived from actor + date), so restoring
    // is purely visual — no server session needed.
    const restoreGame = async () => {
      try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
        if (!saved || saved.date !== getTodayString()) {
          localStorage.removeItem(STORAGE_KEY);
          return;
        }

        // Check if the actor is still the current one (guards against mid-day overrides)
        const res = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/daily-actor`);
        if (res.data.actor_id !== saved.actorId) {
          localStorage.removeItem(STORAGE_KEY);
          return;
        }

        setActorId(saved.actorId);
        setActorName(saved.actorName);
        setActorImage(saved.actorImage);
        setFilledRanks(saved.filledRanks || {});
        setMissedRanks(saved.missedRanks || {});
        setGaveUp(saved.gaveUp || false);
        setTotalMovies(saved.totalMovies || 0);
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    };
    restoreGame();
  }, []);

  // Persist game state to localStorage whenever it changes (only when a game
  // is active and actor data exists)
  useEffect(() => {
    if (!actorName) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        date: getTodayString(),
        actorId,
        actorName,
        actorImage,
        filledRanks,
        missedRanks,
        gaveUp,
        totalMovies,
      }));
    } catch {
      // localStorage full or unavailable (private browsing) — ignore
    }
  }, [actorId, actorName, actorImage, filledRanks, missedRanks, gaveUp, totalMovies]);

  const triggerShake = () => {
    setIsShaking(true);
    setTimeout(() => {
      setIsShaking(false);
    }, 600);
  };

  // ---- Movie info popup ----
  const closePopup = () => {
    setPopupMovie(null);
    setPopupDetails(null);
    setPopupLoading(false);
  };

  const openMoviePopup = (movie) => {
    setPopupMovie(movie);
    setPopupDetails(null);
    if (movie.id) {
      setPopupLoading(true);
      axios.get(`${import.meta.env.VITE_BACKEND_URL}/movie-details`, {
        params: { movie_id: movie.id }
      }).then(res => {
        setPopupDetails(res.data);
      }).catch(() => {
        // Synopsis unavailable — popup still shows what we know locally
        setPopupDetails(null);
      }).finally(() => {
        setPopupLoading(false);
      });
    }
  };

  // Close the popup with the Escape key
  useEffect(() => {
    if (!popupMovie) return;
    const onKey = (e) => {
      if (e.key === 'Escape') closePopup();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [popupMovie]);

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
      
      setActorId(actorId);
      setActorName(name);
      setActorImage(image);

      const boardRes = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/board`, {
        params: { actor_id: actorId }
      });

      setTotalMovies(boardRes.data.total);
    } catch (err) {
      console.error("Error:", err);
      setError("Failed to reveal actor or load the board.");
    }
    clearTimeout(slowTimer);
    setSlowLoad(false);
    setLoading(false);
  };

  // Helper: comma-separated filled ranks for the stateless API calls
  const getFilledRanksParam = () =>
    Object.keys(filledRanks).join(",");

  const playTurn = async () => {
    if (!playerInput.trim()) return;

    try {
      const res = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/play-turn`, null, {
        params: {
          actor_id: actorId,
          player_movie: playerInput,
          filled_ranks: getFilledRanksParam()
        }
      });
      
      if (res.data.movie) {
        const movie = res.data.movie;
        setFilledRanks(prev => ({
          ...prev,
          [movie.rank]: {
            id: movie.id,
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
      triggerShake();
      const apiMessage = err.response?.data?.error || err.response?.data?.detail;
      setError(apiMessage || "Turn failed");
    }
  };

  const giveUp = async () => {
    try {
      const res = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/give-up`, null, {
        params: {
          actor_id: actorId,
          filled_ranks: getFilledRanksParam()
        }
      });

      const missed = {};
      (res.data.missed || []).forEach(m => {
        missed[m.rank] = {
          id: m.id,
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

  // Progress-bar share format: Named: X/Y Movies 🎞️ + 10-block bar
  const buildShareText = () => {
    const gotten = Object.keys(filledRanks).length;
    const ratio = totalMovies > 0 ? gotten / totalMovies : 0;
    const filled = Math.round(ratio * 10);
    const bar = '🟩'.repeat(filled) + '⬛'.repeat(10 - filled);
    const date = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
    return [
      '🎬 Cinematic Recall',
      `📅 ${date}`,
      `🔗 ${window.location.href}`,
      `Named: ${gotten}/${totalMovies} Movies 🎞️`,
      `[${bar}]`
    ].join('\n');
  };

  const shareResult = async () => {
    const text = buildShareText();
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback for older browsers / non-secure contexts
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    setShareCopied(true);
    setTimeout(() => setShareCopied(false), 2000);
  };

  return (
    <div className="app">
      <div className="container">
        <h1 className="title">Cinematic Recall</h1>

        {!actorName && (
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

        {actorName && (
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
              {!gaveUp ? (
                <>
                  <button onClick={playTurn} className="btn btn-success">
                    Submit
                  </button>
                  <button onClick={giveUp} className="btn btn-giveup">
                    Give Up
                  </button>
                </>
              ) : (
                <button onClick={shareResult} className="btn btn-share">
                  {shareCopied ? '✅ Copied to clipboard!' : '📋 Share My Result'}
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
                    className={`square ${filled ? 'filled' : ''} ${missed ? 'missed' : ''} ${revealed ? 'clickable' : ''}`}
                    onClick={() => revealed && openMoviePopup({ ...revealed, rank })}
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

        {popupMovie && (
          <div className="popup-overlay" onClick={closePopup}>
            <div className="popup-card" onClick={(e) => e.stopPropagation()}>
              <button className="popup-close" onClick={closePopup} aria-label="Close">×</button>

              <div className="popup-content">
                <div className="popup-poster">
                  {popupDetails?.poster_url || popupMovie.poster_url ? (
                    <img
                      src={popupDetails?.poster_url || popupMovie.poster_url}
                      alt={popupMovie.title}
                    />
                  ) : (
                    <div className="popup-poster-placeholder">🎞️</div>
                  )}
                </div>

                <div className="popup-info">
                  <p className="popup-rank">
                    #{popupMovie.rank} · {popupMovie.percentage}% match
                    {popupMovie.year && ` · ${popupMovie.year}`}
                  </p>
                  <a
                    className="popup-title"
                    href={popupMovie.id
                      ? `https://www.themoviedb.org/movie/${popupMovie.id}`
                      : `https://www.themoviedb.org/search?query=${encodeURIComponent(popupMovie.title)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {popupMovie.title} ↗
                  </a>

                  {popupLoading ? (
                    <p className="popup-synopsis">Loading synopsis...</p>
                  ) : (
                    <p className="popup-synopsis">
                      {popupDetails?.overview || "No synopsis available."}
                    </p>
                  )}

                  {popupDetails?.runtime && (
                    <p className="popup-runtime">{popupDetails.runtime} min</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;