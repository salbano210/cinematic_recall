import { useState } from 'react';
import axios from 'axios';

function App() {
  const [actorName, setActorName] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [playerInput, setPlayerInput] = useState("");
  const [filledRanks, setFilledRanks] = useState({});
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
      
      setActorName(name);
      
      // Start game immediately after revealing
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
            percentage: movie.percentage
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-indigo-900 text-white">
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        
        {/* Header */}
        <h1 className="text-5xl font-bold mb-8">Cinematic Recall</h1>

        {/* Actor Reveal Section */}
        {!gameId && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-6">Today's Featured Actor</h2>
            <button
              onClick={revealActor}
              disabled={loading}
              className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold px-8 py-4 rounded-xl text-lg transition-all transform hover:scale-105 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Reveal Today\'s Actor'}
            </button>
          </div>
        )}

        {/* Game Section */}
        {gameId && (
          <div>
            {/* Actor Name */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-8">
              <p className="text-lg text-purple-200 mb-2">Name movies by:</p>
              <p className="text-4xl font-bold">{actorName}</p>
              <p className="text-purple-300 mt-2">{totalMovies} total movies</p>
            </div>

            {/* Input Area */}
            <div className="flex gap-4 justify-center mb-8">
              <input
                type="text"
                placeholder="Enter a movie title..."
                value={playerInput}
                onChange={(e) => setPlayerInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && playTurn()}
                className="border border-white/30 bg-white/10 text-white placeholder-purple-300 px-4 py-3 rounded-lg w-96 focus:outline-none focus:ring-2 focus:ring-yellow-500 text-center"
              />
              <button
                onClick={playTurn}
                className="bg-green-500 hover:bg-green-600 text-white font-bold px-6 py-3 rounded-lg transition-all"
              >
                Submit
              </button>
            </div>

            {/* Score */}
            <div className="mb-6">
              <p className="text-2xl font-bold">{Object.keys(filledRanks).length} / {totalMovies}</p>
            </div>

            {/* Movie Squares Grid - ordered by rank */}
            <div className="grid grid-cols-5 gap-2 mb-8">
              {Array.from({ length: totalMovies }).map((_, index) => {
                const rank = index + 1;
                const filled = filledRanks[rank];
                return (
                  <div
                    key={rank}
                    className={`aspect-square rounded-lg flex flex-col items-center justify-center p-1 text-xs transition-all ${
                      filled
                        ? 'bg-green-600 text-white'
                        : 'bg-white/10 border border-white/20'
                    }`}
                  >
                    {filled ? (
                      <>
                        <span className="font-bold truncate" title={filled.title}>
                          {filled.title.length > 15 ? filled.title.substring(0, 15) + '...' : filled.title}
                        </span>
                        <span className="text-yellow-300">{filled.percentage}%</span>
                      </>
                    ) : (
                      <span className="text-white/30">{rank}</span>
                    )}
                  </div>
                );
              })}
            </div>

            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-200 mb-4">
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