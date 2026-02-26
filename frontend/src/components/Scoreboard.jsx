import React from 'react';
import './Scoreboard.css';

// TODO: Add score breakdown details
// TODO: Add round history
// TODO: Add winner celebration
// TODO: Add play again functionality
// TODO: Add score animations

const Scoreboard = ({ gameState, onPlayAgain }) => {
  // TODO: Sort players by score
  // TODO: Calculate final scores
  // TODO: Determine winner
  const sortedPlayers = gameState?.players?.sort((a, b) => a.score - b.score) || [];
  const winner = sortedPlayers[0];

  const renderScoreRow = (player, index) => {
    // TODO: Add position indicators
    // TODO: Add score change indicators
    // TODO: Add special badges for winner
    const isWinner = index === 0;
    
    return (
      <div key={player.id} className={`score-row ${isWinner ? 'winner' : ''}`}>
        <div className="rank">
          {isWinner ? '👑' : `#${index + 1}`}
        </div>
        <div className="player-name">
          {player.name}
          {isWinner && <span className="winner-badge">Winner!</span>}
        </div>
        <div className="score">
          {player.score}
        </div>
        <div className="score-details">
          {/* TODO: Add score breakdown */}
          <small>Details coming soon</small>
        </div>
      </div>
    );
  };

  const renderGameSummary = () => {
    // TODO: Add game statistics
    // TODO: Add round summaries
    // TODO: Add notable achievements
    return (
      <div className="game-summary">
        <h3>Game Summary</h3>
        <div className="summary-stats">
          <div className="stat">
            <span className="stat-label">Rounds Played:</span>
            <span className="stat-value">{gameState?.round_number || 1}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Players:</span>
            <span className="stat-value">{gameState?.players?.length || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Duration:</span>
            <span className="stat-value">Coming soon</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="scoreboard">
      <div className="scoreboard-container">
        <div className="scoreboard-header">
          <h1>Game Over!</h1>
          {winner && (
            <div className="winner-announcement">
              🎉 {winner.name} Wins! 🎉
            </div>
          )}
        </div>

        <div className="scores-container">
          <h2>Final Scores</h2>
          <div className="scores-list">
            {sortedPlayers.map((player, index) => renderScoreRow(player, index))}
          </div>
        </div>

        {renderGameSummary()}

        <div className="actions">
          <button onClick={onPlayAgain} className="play-again-button">
            Play Again
          </button>
          {/* TODO: Add share results button */}
          {/* TODO: Add view replay button */}
        </div>

        {/* TODO: Add confetti animation for winner */}
        {/* TODO: Add sound effects */}
      </div>
    </div>
  );
};

export default Scoreboard;
