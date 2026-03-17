import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';

const useVoteNotification = (setVoteChallenge, onVotingClosed, isAdmin = false) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send('ping');
          }
        }, 30000);
        wsRef.current.pingInterval = pingInterval;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'OPEN_VOTING') {
            console.log('Voting opened:', data.challenge);
            setVoteChallenge(data.challenge);
          } else if (data.type === 'CLOSE_VOTING') {
            console.log('Voting closed:', data.challengeId);
            if (onVotingClosed) {
              onVotingClosed(data.challengeId);
            }
            setVoteChallenge(null);
          } else if (data.type === 'PERK_USED') {
            // Show notification for perk usage (especially useful for admins)
            toast.info(
              `🎤 ${data.user_name} (${data.rank}) used their perk!`,
              {
                description: `Moved from #${data.old_position} to #${data.new_position} - ${data.song}`,
                duration: 8000,
              }
            );
          }
        } catch (e) {
          // Ignore non-JSON messages (like pong)
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        if (wsRef.current?.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
        }
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      // Retry connection after 5 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 5000);
    }
  }, [setVoteChallenge, onVotingClosed]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current?.pingInterval) {
        clearInterval(wsRef.current.pingInterval);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return wsRef;
};

export default useVoteNotification;
