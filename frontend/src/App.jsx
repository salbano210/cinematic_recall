
import { useState } from 'react';
import axios from 'axios';

function App() {
  const [gameId, setGameId] = useState(null);
  const [playerInput, setPlayerInput] = useState("");
  const [turnResult, setTurnResult] = useState(null);
  const [error, setError] = useState(null);

const startGame = async () => {
  try {
    // Get daily actor
    const dailyActorRes = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/daily-actor`);
    const actorId = dailyActorRes.data.actor_id;
    
    // Start game with daily actor
    const gameRes = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/start-game`, null, {
      params: {
        actor_id: actorId,
        difficulty: 'medium'
      }
    });
    
    setGameId(gameRes.data.game_id);
    setTurnResult(null);
    setError(null);
  } catch (err) {
    console.error("Error starting game:", err);
    setError("Failed to start game. " + (err.response?.data?.detail || ""));
  }
};

  const playTurn = async () => {
    try {
const res = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/play-turn`, null, {
  params: {
    game_id: gameId,
    player_movie: playerInput
  }
});
      console.log("Backend response:", res.data);
      setTurnResult(res.data);
      setPlayerInput("");
      setError(null);
    } catch (err) {
      console.error("Turn error:", err);
  
      const apiMessage = err.response?.data?.error || err.response?.data?.detail;
      setError(apiMessage || "Turn failed");
  
      // Clear stale results so the UI doesn’t crash
      setTurnResult(null);
    }
  
  };

  return (
    <div className="p-6 max-w-xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">🎬 Movie Actor Game</h1>

<button
  onClick={startGame}
  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
>
  Start Daily Game
</button>

      {gameId && (
        <div className="space-y-2">
          <p className="text-sm font-mono">🎮 Game ID: {gameId}</p>

          <input
            type="text"
            placeholder="Enter a movie title"
            value={playerInput}
            onChange={(e) => setPlayerInput(e.target.value)}
            className="w-full border p-2 rounded"
          />

          <button
            onClick={playTurn}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Submit Movie
          </button>
        </div>
      )}

{turnResult?.player_move && (
  <div className="mt-4 border-t pt-4">
    <h2 className="text-lg font-semibold">🎯 Turn Result</h2>
    <p>
      ✅ Your movie: <strong>{turnResult.player_move.title}</strong> (Rank #{turnResult.player_move.rank})
    </p>
    {turnResult.computer_move ? (
      <p>
        🤖 Computer: <strong>{turnResult.computer_move.title}</strong> (Rank #{turnResult.computer_move.rank})
      </p>
    ) : (
      <p className="text-green-600 font-bold">🎉 You win!</p>
    )}
    <p>🎞️ Remaining movies: {turnResult.remaining_movies}</p>
  </div>
)}


      {error && <p className="text-red-600 mt-2">{error}</p>}
    </div>
  );
}

export default App;
