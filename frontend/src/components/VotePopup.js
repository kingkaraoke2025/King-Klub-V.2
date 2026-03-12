import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Swords, Clock, Crown, X, Vote } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VotePopup = ({ challenge, onVote, onClose, userId }) => {
  const [timeLeft, setTimeLeft] = useState(180); // 3 minutes
  const [voting, setVoting] = useState(false);
  const [voted, setVoted] = useState(false);

  useEffect(() => {
    if (!challenge) return;

    // Reset timer when new challenge opens
    setTimeLeft(180);
    setVoted(false);

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [challenge]);

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
          className="glass-card p-8 max-w-lg w-full text-center border-gold/30 relative"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white/40 hover:text-white/60"
            data-testid="close-vote-popup"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Header */}
          <div className="flex items-center justify-center gap-2 mb-4">
            <Swords className="w-8 h-8 text-gold" />
            <h2 className="font-cinzel font-bold text-2xl text-gold">Battle Vote!</h2>
          </div>

          <p className="text-white/60 mb-2">{challenge.typeName}</p>

          {/* VS Display */}
          <div className="flex items-center justify-between py-6 px-4">
            <div className="flex-1 text-center">
              <p className="font-cinzel font-bold text-xl text-white">{challenge.challengerName}</p>
              <p className="text-purple-400 text-sm">Challenger</p>
            </div>
            <div className="px-4">
              <div className="w-16 h-16 bg-gold/20 rounded-full flex items-center justify-center">
                <span className="font-cinzel font-bold text-2xl text-gold">VS</span>
              </div>
            </div>
            <div className="flex-1 text-center">
              <p className="font-cinzel font-bold text-xl text-white">{challenge.opponentName}</p>
              <p className="text-blue-400 text-sm">Opponent</p>
            </div>
          </div>

          {/* Timer */}
          <div className="mb-6">
            <div className="flex items-center justify-center gap-2 text-red-400">
              <Clock className="w-5 h-5" />
              <span className="font-mono text-3xl font-bold">
                {minutes}:{seconds.toString().padStart(2, '0')}
              </span>
            </div>
            <p className="text-white/40 text-sm mt-1">Voting ends soon!</p>
          </div>

          {/* Vote Buttons or Status */}
          {voted ? (
            <div className="bg-green-500/20 rounded-lg p-4">
              <p className="text-green-400 font-medium flex items-center justify-center gap-2">
                <Crown className="w-5 h-5" />
                Your vote has been recorded!
              </p>
            </div>
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
                className="flex-1 bg-purple-600 hover:bg-purple-700 h-14 text-lg"
                data-testid="vote-challenger-btn"
              >
                <Vote className="w-5 h-5 mr-2" />
                {challenge.challengerName?.split(' ')[0]}
              </Button>
              <Button
                onClick={() => handleVote(challenge.opponentId)}
                disabled={voting}
                className="flex-1 bg-blue-600 hover:bg-blue-700 h-14 text-lg"
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
