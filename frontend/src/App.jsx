import { useState } from 'react';
import axios from 'axios';

function App() {
  const [actorName, setActorName] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [playerInput, setPlayerInput] = useState("");
  const [turnResult, setTurnResult] = useState(null);
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
    } catch (err) {
      console.error("Error:", err);
      setError("Failed to reveal actor or start game.");
    }
    setLoading(false);
  };

  const playTurn = async () => {
    try {
      const res = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/play-turn`, null, {
        params: {
          game_id: gameId,
          player_movie: playerInput
        }
      });
      setTurnResult(res.data);
      setPlayerInput("");
      setError(null);
    } catch (err) {
      console.error("Turn error:", err);
      const apiMessage = err.response?.data?.error || err.response?.data?.detail;
      setError(apiMessage || "Turn failed");
      setTurnResult(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-indigo-900 text-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-2">🎬 Cinematic Recall</h1>
          <p className="text-xl text-purple-200">Test your movie knowledge against the computer</p>
        </div>

        {/* Actor Reveal Section */}
        {!gameId && (
          <div className="text-center bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-6">Today's Featured Actor</h2>
            <button
              onClick={revealActor}
              disabled={loading}
              className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold px-8 py-4 rounded-xl text-lg transition-all transform hover:scale-105 disabled:opacity-50"
            >
              {loading ? 'Loading...' : '🎭 Reveal Today\'s Actor'}
            </button>
          </div>
        )}

        {/* Actor Name Display (before game starts) */}
        {actorName && !gameId && (
          <div className="text-center bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8">
            <p className="text-lg text-purple-200 mb-2">Today's Actor Is:</p>
            <p className="text-4xl font-bold mb-6">{actorName}</p>
            <button
              onClick={() => {
                setLoading(true);
                revealActor();
              }}
              disabled={loading}
              className="bg-green-500 hover:bg-green-600 text-white font-bold px-8 py-4 rounded-xl text-lg transition-all transform hover:scale-105"
            >
              Play Now
            </button>
          </div>
        )}

        {/* Game Section */}
        {gameId && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">🎮 Game in Progress</h2>
              <span className="text-sm font-mono bg-white/20 px-3 py-1 rounded">
                {actorName}
              </span>
            </div>

            <div className="space-y-4">
              <input
                type="text"
                placeholder="Enter a movie title..."
                value={playerInput}
                onChange={(e) => setPlayerInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && playTurn()}
                className="w-full border border-white/30 bg-white/10 text-white placeholder-purple-300 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />

              <button
                onClick={playTurn}
                className="w-full bg-green-500 hover:bg-green-600 text-white font-bold px-4 py-3 rounded-lg transition-all"
              >
                Submit Movie
              </button>
            </div>

            {/* Turn Result */}
            {turnResult?.player_move && (
              <div className="mt-6 border-t border-white/20 pt-6">
                <h3 className="text-lg font-semibold mb-3">Last Round</h3>
                <p className="text-purple-200">
                  ✅ You: <strong>{turnResult.player_move.title}</strong> 
                  {turnResult.player_move.rank && ` (Rank #${turnResult.player_move.rank})`}
                </p>
                {turnResult.computer_move ? (
                  <p className="text-purple-200 mt-1">
                    🤖 Computer: <strong>{turnResult.computer_move.title}</strong>
                    {turnResult.computer_move.rank && ` (Rank #${turnResult.computer_move.rank})`}
                  </p>
                ) : (
                  <p className="text-green-400 font-bold text-lg mt-1">🎉 You win!</p>
                )}
                <p className="text-purple-300 text-sm mt-2">
                  🎞️ Remaining: {turnResult.remaining_movies} movies
                </p>
              </div>
            )}

            {error && (
              <div className="mt-4 bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-200">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-purple-300 text-sm">
          <p>Name valid movies from the actor's filmography. Fuzzy matching supported!</p>
        </div>
      </div>
    </div>
  );
}

export default App;