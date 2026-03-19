import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Swords, Clock, Crown, X, Vote, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import soundEffects from '@/utils/soundEffects';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VotePopup = ({ challenge, onVote, onClose, userId }) => {
  const [timeLeft, setTimeLeft] = useState(0);
  const [voting, setVoting] = useState(false);
  const [voted, setVoted] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const hasPlayedOpenSound = useRef(false);
  const votingEndsAtRef = useRef(null);

  // Calculate time left from server's end time
  const calculateTimeLeft = (endTimeStr) => {
    if (!endTimeStr) return 0;
    const endTime = new Date(endTimeStr);
    const now = new Date();
    const diff = Math.max(0, Math.floor((endTime - now) / 1000));
    return diff;
  };

  // Play battle start sound when popup opens
  useEffect(() => {
    if (challenge && !hasPlayedOpenSound.current) {
      soundEffects.playBattleStart();
      hasPlayedOpenSound.current = true;
    }
    
    return () => {
      hasPlayedOpenSound.current = false;
    };
  }, [challenge]);

  useEffect(() => {
    if (!challenge) return;

    // Get the voting end time from the challenge data
    const votingEndsAt = challenge.votingEndsAt;
    votingEndsAtRef.current = votingEndsAt;
    
    // Calculate initial time left based on server end time
    const initialTimeLeft = calculateTimeLeft(votingEndsAt);
    setTimeLeft(initialTimeLeft);
    setVoted(false);

    // If voting has already ended, don't start timer
    if (initialTimeLeft <= 0) {
      soundEffects.playVotingClosed();
      return;
    }

    const timer = setInterval(() => {
      const remaining = calculateTimeLeft(votingEndsAtRef.current);
      setTimeLeft(remaining);
      
      if (remaining <= 0) {
        clearInterval(timer);
        soundEffects.playVotingClosed();
        return;
      }
      
      // Play warning sounds
      if (soundEnabled) {
        if (remaining <= 10 && remaining > 0) {
          // Last 10 seconds - urgent warning every second
          soundEffects.playUrgentWarning();
        } else if (remaining <= 30 && remaining % 5 === 0) {
          // Last 30 seconds - tick every 5 seconds
          soundEffects.playTimerTick();
        }
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [challenge, soundEnabled]);

  const toggleSound = () => {
    const newState = !soundEnabled;
    setSoundEnabled(newState);
    soundEffects.setEnabled(newState);
    if (newState) {
      soundEffects.playVoteConfirm(); // Test sound
    }
  };

  const handleVote = async (performerId) => {
    if (voted || voting) return;
    
    // Check if user is a participant
    if (userId === challenge.challengerId || userId === challenge.opponentId) {
      toast.error("Participants cannot vote in their own battle!");
      return;
    }

    setVoting(true);
    try {
      await axios.post(`${API}/challenges/${challenge.id}/vote`, {
        vote_for: performerId
      });
      setVoted(true);
      soundEffects.playVoteConfirm();
      toast.success('Vote recorded!');
      if (onVote) onVote(challenge.id, performerId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to vote');
    } finally {
      setVoting(false);
    }
  };

  if (!challenge) return null;

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const isParticipant = userId === challenge.challengerId || userId === challenge.opponentId;
  const isUrgent = timeLeft <= 30;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        data-testid="vote-popup-overlay"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className={`glass-card p-8 max-w-lg w-full text-center relative ${
            isUrgent ? 'border-red-500/50 animate-pulse' : 'border-gold/30'
          }`}
        >
          {/* Sound toggle & Close button */}
          <div className="absolute top-4 right-4 flex items-center gap-2">
            <button
              onClick={toggleSound}
              className="text-white/40 hover:text-white/60 p-1"
              data-testid="toggle-sound-btn"
              title={soundEnabled ? 'Mute sounds' : 'Enable sounds'}
            >
              {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            </button>
            <button
              onClick={onClose}
              className="text-white/40 hover:text-white/60"
              data-testid="close-vote-popup"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Header */}
          <div className="flex items-center justify-center gap-2 mb-4">
            <Swords className={`w-8 h-8 ${isUrgent ? 'text-red-400' : 'text-gold'}`} />
            <h2 className={`font-cinzel font-bold text-2xl ${isUrgent ? 'text-red-400' : 'text-gold'}`}>
              Battle Vote!
            </h2>
          </div>

          <p className="text-white/60 mb-2">{challenge.typeName}</p>

          {/* VS Display */}
          <div className="flex items-center justify-between py-6 px-4">
            <div className="flex-1 text-center">
              <p className="font-cinzel font-bold text-xl text-white">{challenge.challengerName}</p>
              <p className="text-purple-400 text-sm">Challenger</p>
            </div>
            <div className="px-4">
              <motion.div 
                className={`w-16 h-16 rounded-full flex items-center justify-center ${
                  isUrgent ? 'bg-red-500/20' : 'bg-gold/20'
                }`}
                animate={isUrgent ? { scale: [1, 1.1, 1] } : {}}
                transition={{ duration: 0.5, repeat: isUrgent ? Infinity : 0 }}
              >
                <span className={`font-cinzel font-bold text-2xl ${isUrgent ? 'text-red-400' : 'text-gold'}`}>VS</span>
              </motion.div>
            </div>
            <div className="flex-1 text-center">
              <p className="font-cinzel font-bold text-xl text-white">{challenge.opponentName}</p>
              <p className="text-blue-400 text-sm">Opponent</p>
            </div>
          </div>

          {/* Timer */}
          <div className="mb-6">
            <div className={`flex items-center justify-center gap-2 ${isUrgent ? 'text-red-400' : 'text-white/60'}`}>
              <Clock className={`w-5 h-5 ${isUrgent ? 'animate-pulse' : ''}`} />
              <motion.span 
                className={`font-mono text-3xl font-bold ${isUrgent ? 'text-red-400' : 'text-white'}`}
                animate={isUrgent ? { scale: [1, 1.05, 1] } : {}}
                transition={{ duration: 0.5, repeat: isUrgent ? Infinity : 0 }}
              >
                {minutes}:{seconds.toString().padStart(2, '0')}
              </motion.span>
            </div>
            <p className={`text-sm mt-1 ${isUrgent ? 'text-red-400 font-medium' : 'text-white/40'}`}>
              {isUrgent ? 'VOTE NOW!' : 'Voting ends soon!'}
            </p>
          </div>

          {/* Vote Buttons or Status */}
          {voted ? (
            <motion.div 
              className="bg-green-500/20 rounded-lg p-4"
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
            >
              <p className="text-green-400 font-medium flex items-center justify-center gap-2">
                <Crown className="w-5 h-5" />
                Your vote has been recorded!
              </p>
            </motion.div>
          ) : isParticipant ? (
            <div className="bg-orange-500/20 rounded-lg p-4">
              <p className="text-orange-400 font-medium">
                You're a participant - watch the votes come in!
              </p>
            </div>
          ) : timeLeft === 0 ? (
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-white/60">Voting has ended</p>
            </div>
          ) : (
            <div className="flex gap-4">
              <Button
                onClick={() => handleVote(challenge.challengerId)}
                disabled={voting}
                className="flex-1 bg-purple-600 hover:bg-purple-700 h-14 text-lg transition-transform hover:scale-105"
                data-testid="vote-challenger-btn"
              >
                <Vote className="w-5 h-5 mr-2" />
                {challenge.challengerName?.split(' ')[0]}
              </Button>
              <Button
                onClick={() => handleVote(challenge.opponentId)}
                disabled={voting}
                className="flex-1 bg-blue-600 hover:bg-blue-700 h-14 text-lg transition-transform hover:scale-105"
                data-testid="vote-opponent-btn"
              >
                <Vote className="w-5 h-5 mr-2" />
                {challenge.opponentName?.split(' ')[0]}
              </Button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default VotePopup;
