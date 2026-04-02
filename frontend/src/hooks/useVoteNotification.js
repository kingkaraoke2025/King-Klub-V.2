import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import soundEffects from '@/utils/soundEffects';

const useVoteNotification = (
  setVoteChallenge, 
  onVotingClosed, 
  isAdmin = false, 
  userId = null,
  onQueueUpdate = null,
  onPointsUpdate = null,
  onBattleUpdate = null
) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isConnectingRef = useRef(false);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current) {
      console.log('WebSocket connection already in progress, skipping');
      return;
    }
    
    // Don't reconnect if we shouldn't (component unmounted)
    if (!shouldReconnectRef.current) {
      console.log('WebSocket reconnection disabled, skipping');
      return;
    }
    
    // Close any existing connection first
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      console.log('Closing existing WebSocket connection');
      wsRef.current.close();
    }
    
    isConnectingRef.current = true;
    
    // Determine WebSocket URL - use /api/ws for proper routing through ingress
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws`;
    console.log('Attempting WebSocket connection to:', wsUrl);

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected successfully to:', wsUrl);
        isConnectingRef.current = false;
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
              // Sound effect for voting open
              soundEffects.playBattleStart();
              // Notification for voting open
              toast.info(
                `🗳️ Voting is NOW OPEN!`,
                {
                  description: `${data.challenge?.challengerName || 'Challenger'} vs ${data.challenge?.opponentName || 'Opponent'}`,
                  duration: 8000,
                }
              );
              // Dispatch event for battles page refresh
              window.dispatchEvent(new CustomEvent('battleUpdated', { detail: data }));
              break;
              
            case 'CLOSE_VOTING':
              console.log('Voting closed:', data.challengeId);
              if (onVotingClosed) {
                onVotingClosed(data.challengeId);
              }
              setVoteChallenge(null);
              // Dispatch event for battles page refresh
              window.dispatchEvent(new CustomEvent('battleUpdated', { detail: data }));
              break;
            
            case 'QUEUE_UPDATED':
              console.log('Queue updated:', data.action);
              // Trigger queue refresh in any component listening
              if (onQueueUpdate) {
                onQueueUpdate(data);
              }
              // Dispatch custom event for components not using the hook directly
              window.dispatchEvent(new CustomEvent('queueUpdated', { detail: data }));
              break;
              
            case 'POINTS_UPDATED':
              console.log('Points updated for user:', data.user_id);
              // Trigger points/leaderboard refresh
              if (onPointsUpdate) {
                onPointsUpdate(data);
              }
              // Dispatch custom event for components not using the hook directly
              window.dispatchEvent(new CustomEvent('pointsUpdated', { detail: data }));
              break;
            
            case 'LEADERBOARD_RESET':
              console.log('Nightly leaderboard reset for date:', data.date);
              // Dispatch custom event for leaderboard page to refresh
              window.dispatchEvent(new CustomEvent('leaderboardReset', { detail: data }));
              // Also trigger points update to refresh any points displays
              window.dispatchEvent(new CustomEvent('pointsUpdated', { detail: data }));
              
              // Show champion notification if someone won
              if (data.champion) {
                soundEffects.play('challenge');
                toast.success(
                  `Nightly Champion: ${data.champion.display_name}!`,
                  {
                    description: `Earned ${data.champion.nightly_points} points tonight and wins the Nightly Champion badge!`,
                    duration: 8000,
                  }
                );
              }
              
              if (isAdmin) {
                toast.info(
                  'Nightly Leaderboard Reset',
                  {
                    description: `Tonight's leaderboard has been reset for ${data.date}`,
                    duration: 5000,
                  }
                );
              }
              break;
              
            case 'BATTLE_CHALLENGE':
              // Someone was challenged to a battle
              if (data.opponent_id === userId) {
                // You've been challenged! - play sound
                soundEffects.playChallengeReceived();
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
              // Dispatch event for battles page refresh
              window.dispatchEvent(new CustomEvent('battleUpdated', { detail: data }));
              if (onBattleUpdate) onBattleUpdate(data);
              break;
              
            case 'CHALLENGE_ACCEPTED':
              // Challenge was accepted
              if (data.challenger_id === userId) {
                // Your challenge was accepted! - play sound
                soundEffects.playChallengeAccepted();
                toast.success(
                  `✅ Challenge Accepted!`,
                  {
                    description: `${data.opponent_name} accepted your ${data.challenge_type_name} challenge!`,
                    duration: 8000,
                  }
                );
              } else if (isAdmin) {
                // Admin notification - play sound
                soundEffects.playAdminAlert();
                toast.info(
                  `⚔️ Challenge Accepted`,
                  {
                    description: `${data.opponent_name} accepted ${data.challenger_name}'s ${data.challenge_type_name}!`,
                    duration: 6000,
                  }
                );
              }
              // Dispatch event for battles page refresh
              window.dispatchEvent(new CustomEvent('battleUpdated', { detail: data }));
              if (onBattleUpdate) onBattleUpdate(data);
              break;
              
            case 'BATTLE_ENDED':
              // Battle ended with a winner
              const isParticipant = data.winner_id === userId || data.loser_id === userId;
              const isWinner = data.winner_id === userId;
              
              if (isParticipant) {
                if (isWinner) {
                  soundEffects.playVictory();
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
              // Dispatch event for battles page refresh
              window.dispatchEvent(new CustomEvent('battleUpdated', { detail: data }));
              if (onBattleUpdate) onBattleUpdate(data);
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

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason, 'Was clean:', event.wasClean);
        isConnectingRef.current = false;
        if (wsRef.current?.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
        }
        // Attempt to reconnect after 3 seconds if we should
        if (shouldReconnectRef.current) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', wsRef.current?.readyState);
        isConnectingRef.current = false;
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      isConnectingRef.current = false;
      // Retry connection after 5 seconds if we should
      if (shouldReconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    }
  }, [setVoteChallenge, onVotingClosed, isAdmin, userId, onQueueUpdate, onPointsUpdate, onBattleUpdate]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
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
