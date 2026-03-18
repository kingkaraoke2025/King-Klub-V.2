import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';

const useVoteNotification = (setVoteChallenge, onVotingClosed, isAdmin = false, userId = null) => {
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

          switch (data.type) {
            case 'OPEN_VOTING':
              console.log('Voting opened:', data.challenge);
              setVoteChallenge(data.challenge);
              // Notification for voting open
              toast.info(
                `🗳️ Voting is NOW OPEN!`,
                {
                  description: `${data.challenge?.challenger_name || 'Challenger'} vs ${data.challenge?.opponent_name || 'Opponent'}`,
                  duration: 8000,
                }
              );
              break;
              
            case 'CLOSE_VOTING':
              console.log('Voting closed:', data.challengeId);
              if (onVotingClosed) {
                onVotingClosed(data.challengeId);
              }
              setVoteChallenge(null);
              break;
              
            case 'BATTLE_CHALLENGE':
              // Someone was challenged to a battle
              if (data.opponent_id === userId) {
                // You've been challenged!
                toast.warning(
                  `⚔️ You've been challenged!`,
                  {
                    description: `${data.challenger_name} wants a ${data.challenge_type_name} battle!`,
                    duration: 10000,
                  }
                );
              } else if (isAdmin) {
                // Admin notification
                toast.info(
                  `⚔️ New Battle Created`,
                  {
                    description: `${data.challenger_name} vs ${data.opponent_name} (${data.challenge_type_name})`,
                    duration: 5000,
                  }
                );
              }
              break;
              
            case 'BATTLE_ENDED':
              // Battle ended with a winner
              const isParticipant = data.winner_id === userId || data.loser_id === userId;
              const isWinner = data.winner_id === userId;
              
              if (isParticipant) {
                if (isWinner) {
                  toast.success(
                    `🏆 Victory! You won!`,
                    {
                      description: `Congratulations on winning the ${data.challenge_type_name}!`,
                      duration: 10000,
                    }
                  );
                } else {
                  toast.info(
                    `Battle Complete`,
                    {
                      description: `${data.winner_name} won the ${data.challenge_type_name}. Better luck next time!`,
                      duration: 8000,
                    }
                  );
                }
              } else if (isAdmin) {
                // Admin notification
                const resultText = data.admin_decided 
                  ? `Winner: ${data.winner_name} (Admin decision)` 
                  : `Winner: ${data.winner_name} (${data.winner_votes}-${data.loser_votes})`;
                toast.info(
                  `🏆 Battle Ended`,
                  {
                    description: resultText,
                    duration: 5000,
                  }
                );
              } else {
                // General notification for all users
                toast.info(
                  `🏆 Battle Result`,
                  {
                    description: `${data.winner_name} defeated ${data.loser_name} in ${data.challenge_type_name}!`,
                    duration: 5000,
                  }
                );
              }
              break;
              
            case 'PERK_USED':
              // Show notification for perk usage (especially useful for admins)
              toast.info(
                `🎤 ${data.user_name} (${data.rank}) used their perk!`,
                {
                  description: `Moved from #${data.old_position} to #${data.new_position} - ${data.song}`,
                  duration: 8000,
                }
              );
              break;
              
            default:
              console.log('Unknown message type:', data.type);
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
  }, [setVoteChallenge, onVotingClosed, isAdmin, userId]);

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
