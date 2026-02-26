import { useState, useEffect, useRef, useCallback } from 'react';

// TODO: Add connection retry logic
// TODO: Add heartbeat/ping mechanism
// TODO: Add message queuing for offline state
// TODO: Add connection status indicators
// TODO: Add error handling and recovery

const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const messageQueue = useRef([]);
  const heartbeatInterval = useRef(null);
  
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;
  const heartbeatTimeout = 30000;

  const connect = useCallback((wsUrl = url) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      ws.current = new WebSocket(wsUrl);
      setConnectionStatus('connecting');

      ws.current.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        setError(null);
        
        // TODO: Send queued messages
        // TODO: Start heartbeat
        startHeartbeat();
        
        console.log('WebSocket connected');
      };

      ws.current.onmessage = (event) => {
        // TODO: Handle different message types
        // TODO: Validate message format
        // TODO: Handle heartbeat responses
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'pong') {
            // Heartbeat response
            return;
          }
          
          setLastMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
          setError('Invalid message format received');
        }
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        stopHeartbeat();
        
        // TODO: Handle different close codes
        // TODO: Implement reconnection logic
        if (event.code !== 1000) {
          // Abnormal close - attempt reconnection
          handleReconnect();
        }
        
        console.log('WebSocket disconnected:', event.code, event.reason);
      };

      ws.current.onerror = (event) => {
        setError('WebSocket connection error');
        setConnectionStatus('error');
        console.error('WebSocket error:', event);
      };

    } catch (err) {
      setError('Failed to create WebSocket connection');
      setConnectionStatus('error');
      console.error('WebSocket connection error:', err);
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    stopHeartbeat();
    
    if (ws.current) {
      ws.current.close(1000, 'Client disconnect');
      ws.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        const messageString = typeof message === 'string' 
          ? message 
          : JSON.stringify(message);
        
        ws.current.send(messageString);
      } catch (err) {
        console.error('Failed to send message:', err);
        setError('Failed to send message');
      }
    } else {
      // TODO: Queue message for when connection is restored
      messageQueue.current.push(message);
      console.log('Message queued (not connected):', message);
    }
  }, []);

  const handleReconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      return; // Already reconnecting
    }

    // TODO: Implement exponential backoff
    // TODO: Limit reconnection attempts
    reconnectTimeout.current = setTimeout(() => {
      setConnectionStatus('reconnecting');
      connect();
      reconnectTimeout.current = null;
    }, reconnectDelay);
  }, [connect]);

  const startHeartbeat = useCallback(() => {
    // TODO: Implement heartbeat mechanism
    heartbeatInterval.current = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, heartbeatTimeout);
  }, [sendMessage]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // TODO: Add connection status monitoring
  // TODO: Add message history for debugging
  // TODO: Add performance metrics

  return {
    isConnected,
    lastMessage,
    error,
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
    // TODO: Expose additional utilities
    clearError: () => setError(null),
    getMessageQueue: () => [...messageQueue.current],
  };
};

export default useWebSocket;
