import React, { useState, useEffect } from 'react';
import './GameRoom.css';

// TODO: Add card rendering components
// TODO: Add player hand display
// TODO: Add game board visualization
// TODO: Add turn indicators
// TODO: Add action buttons
// TODO: Add animations for card movements

const GameRoom = ({ gameState, playerName, sendMessage, onLeaveRoom }) => {
  const [selectedCards, setSelectedCards] = useState([]);
  const [currentAction, setCurrentAction] = useState(null);

  useEffect(() => {
    // TODO: Initialize game room state
    // TODO: Set up keyboard shortcuts
    // TODO: Add sound effects
  }, []);

  const handleCardSelect = (cardId) => {
    // TODO: Implement card selection logic
    // TODO: Handle multiple selection
    // TODO: Validate selection
    setSelectedCards(prev => 
      prev.includes(cardId) 
        ? prev.filter(id => id !== cardId)
        : [...prev, cardId]
    );
  };

  const handleDrawCard = () => {
    // TODO: Implement draw card action
    // TODO: Validate turn
    // TODO: Send action to server
    sendMessage({
      type: 'player_action',
      action: 'draw_card',
      player_name: playerName
    });
  };

  const handlePlayCards = () => {
    // TODO: Implement card playing logic
    // TODO: Validate play
    // TODO: Send play to server
    if (selectedCards.length === 0) return;

    sendMessage({
      type: 'player_action',
      action: 'play_cards',
      cards: selectedCards,
      player_name: playerName
    });
    
    setSelectedCards([]);
  };

  const handleDiscardCard = () => {
    // TODO: Implement discard logic
    // TODO: Validate discard
    // TODO: Send discard to server
    if (selectedCards.length !== 1) return;

    sendMessage({
      type: 'player_action',
      action: 'discard_card',
      card: selectedCards[0],
      player_name: playerName
    });
    
    setSelectedCards([]);
  };

  const renderPlayerHand = () => {
    // TODO: Implement player hand rendering
    // TODO: Add card components
    // TODO: Add selection indicators
    const currentPlayer = gameState?.players?.find(p => p.name === playerName);
    
    if (!currentPlayer) {
      return <div>Loading your hand...</div>;
    }

    return (
      <div className="player-hand">
        <h3>Your Hand</h3>
        <div className="cards-container">
          {/* TODO: Render actual card components */}
          {currentPlayer.hand?.map((card, index) => (
            <div 
              key={index}
              className={`card ${selectedCards.includes(index) ? 'selected' : ''}`}
              onClick={() => handleCardSelect(index)}
            >
              {/* TODO: Add card face rendering */}
              <div className="card-back">
                🂠
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderGameBoard = () => {
    // TODO: Implement game board rendering
    // TODO: Add discard pile
    // TODO: Add deck display
    // TODO: Add other players' hands
    return (
      <div className="game-board">
        <div className="deck-area">
          <h3>Deck</h3>
          <div className="deck">
            {/* TODO: Show deck count */}
            <div className="card-back">🂠</div>
          </div>
        </div>
        
        <div className="discard-area">
          <h3>Discard Pile</h3>
          <div className="discard-pile">
            {/* TODO: Show top discard card */}
            <div className="card-back">🂠</div>
          </div>
        </div>
        
        <div className="other-players">
          <h3>Other Players</h3>
          {/* TODO: Render other players */}
          {gameState?.players?.filter(p => p.name !== playerName).map(player => (
            <div key={player.id} className="other-player">
              <span>{player.name}</span>
              <span>Cards: {player.hand?.length || 0}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderActionButtons = () => {
    // TODO: Implement action buttons
    // TODO: Disable based on game state
    // TODO: Add loading states
    return (
      <div className="action-buttons">
        <button onClick={handleDrawCard} className="action-button">
          Draw Card
        </button>
        <button 
          onClick={handlePlayCards} 
          className="action-button"
          disabled={selectedCards.length === 0}
        >
          Play Cards ({selectedCards.length})
        </button>
        <button 
          onClick={handleDiscardCard} 
          className="action-button"
          disabled={selectedCards.length !== 1}
        >
          Discard Card
        </button>
      </div>
    );
  };

  return (
    <div className="game-room">
      <div className="game-header">
        <h2>Game Room: {gameState?.room_id}</h2>
        <div className="game-info">
          <span>Round: {gameState?.round_number || 1}</span>
          <span>Phase: {gameState?.phase}</span>
        </div>
        <button onClick={onLeaveRoom} className="leave-button">
          Leave Room
        </button>
      </div>

      <div className="game-content">
        {renderGameBoard()}
        {renderPlayerHand()}
        {renderActionButtons()}
      </div>

      {/* TODO: Add turn indicator */}
      {/* TODO: Add score display */}
      {/* TODO: Add chat component */}
    </div>
  );
};

export default GameRoom;
