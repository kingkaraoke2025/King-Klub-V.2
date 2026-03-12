import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Swords, Crown, Users, Trophy, Search, X, Check, 
  Vote, Flame, Eye, Shuffle, Music2, Loader2
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const challengeIcons = {
  royal_duel: Swords,
  blind_challenge: Eye,
  rank_battle: Crown,
  roulette: Shuffle,
  harmony_duel: Music2,
};

const BattlesPage = () => {
  const { user, refreshUser } = useAuth();
  const [challenges, setChallenges] = useState([]);
  const [myChallenges, setMyChallenges] = useState([]);
  const [challengeTypes, setChallengeTypes] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [challengeDialogOpen, setChallengeDialogOpen] = useState(false);
  const [selectedOpponent, setSelectedOpponent] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [userSearch, setUserSearch] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchData = async () => {
    try {
      const [challengesRes, myRes, typesRes, leaderboardRes] = await Promise.all([
        axios.get(`${API}/challenges`),
        axios.get(`${API}/challenges/my`),
        axios.get(`${API}/challenges/types`),
        axios.get(`${API}/leaderboard`)
      ]);
      setChallenges(challengesRes.data);
      setMyChallenges(myRes.data);
      setChallengeTypes(typesRes.data);
      setUsers(leaderboardRes.data.filter(u => u.id !== user?.id));
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [user]);

  const handleIssueChallenge = async () => {
    if (!selectedOpponent || !selectedType) {
      toast.error('Please select an opponent and challenge type');
      return;
    }
    
    setCreating(true);
    try {
      await axios.post(`${API}/challenges`, {
        opponent_id: selectedOpponent.id,
        challenge_type: selectedType
      });
      toast.success(`Challenge issued to ${selectedOpponent.display_name}!`);
      setChallengeDialogOpen(false);
      setSelectedOpponent(null);
      setSelectedType(null);
      refreshUser();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to issue challenge');
    } finally {
      setCreating(false);
    }
  };

  const handleAcceptChallenge = async (challengeId) => {
    try {
      await axios.post(`${API}/challenges/${challengeId}/accept`);
      toast.success('Challenge accepted! Let the battle begin!');
      refreshUser();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to accept');
    }
  };

  const handleDeclineChallenge = async (challengeId) => {
    try {
      await axios.post(`${API}/challenges/${challengeId}/decline`);
      toast.success('Challenge declined');
      fetchData();
    } catch (error) {
      toast.error('Failed to decline');
    }
  };

  const handleVote = async (challengeId, voteFor) => {
    try {
      await axios.post(`${API}/challenges/${challengeId}/vote`, { vote_for: voteFor });
      toast.success('Vote recorded!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to vote');
    }
  };

  const filteredUsers = users.filter(u =>
    u.display_name.toLowerCase().includes(userSearch.toLowerCase())
  );

  const pendingForMe = myChallenges.filter(
    c => c.status === 'pending' && c.opponent_id === user?.id
  );

  const activeBattles = challenges.filter(c => c.status === 'accepted');

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading battles...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="battles-page">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Swords className="w-6 h-6 text-gold" />
              <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white">
                Battle <span className="text-gold">Arena</span>
              </h1>
            </div>
            <p className="text-white/60">Challenge others to vocal combat!</p>
          </div>
          <Button
            onClick={() => setChallengeDialogOpen(true)}
            data-testid="issue-challenge-btn"
            className="btn-gold"
          >
            <Swords className="w-5 h-5 mr-2" />
            Issue Challenge
          </Button>
        </motion.div>

        {/* Pending Challenges for Me */}
        {pendingForMe.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6 border-orange-500/30"
          >
            <h2 className="font-cinzel font-bold text-lg text-orange-400 mb-4 flex items-center gap-2">
              <Flame className="w-5 h-5" />
              Incoming Challenges ({pendingForMe.length})
            </h2>
            <div className="space-y-3">
              {pendingForMe.map((challenge) => {
                const TypeIcon = challengeIcons[challenge.type] || Swords;
                return (
                  <div
                    key={challenge.id}
                    className="flex items-center justify-between p-4 bg-white/5 rounded-lg"
                    data-testid={`pending-challenge-${challenge.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-orange-500/20 rounded-lg">
                        <TypeIcon className="w-5 h-5 text-orange-400" />
                      </div>
                      <div>
                        <p className="text-white font-medium">
                          <span className="text-gold">{challenge.challenger?.display_name}</span> challenges you!
                        </p>
                        <p className="text-white/50 text-sm">{challenge.type_info?.name}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleAcceptChallenge(challenge.id)}
                        className="bg-green-600 hover:bg-green-700"
                        data-testid={`accept-${challenge.id}`}
                      >
                        <Check className="w-4 h-4 mr-1" /> Accept
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDeclineChallenge(challenge.id)}
                        data-testid={`decline-${challenge.id}`}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        <Tabs defaultValue="active" className="w-full">
          <TabsList className="bg-royal-paper border border-white/10">
            <TabsTrigger 
              value="active"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Flame className="w-4 h-4 mr-2" />
              Active Battles ({activeBattles.length})
            </TabsTrigger>
            <TabsTrigger 
              value="my"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Crown className="w-4 h-4 mr-2" />
              My Battles
            </TabsTrigger>
          </TabsList>

          {/* Active Battles */}
          <TabsContent value="active" className="mt-6">
            {activeBattles.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <Swords className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/60 text-lg">No active battles</p>
                <p className="text-white/40">Issue a challenge to start one!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {activeBattles.map((battle) => {
                  const TypeIcon = challengeIcons[battle.type] || Swords;
                  const isParticipant = [battle.challenger_id, battle.opponent_id].includes(user?.id);
                  
                  return (
                    <motion.div
                      key={battle.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="glass-card p-6 border-gold/20"
                      data-testid={`battle-${battle.id}`}
                    >
                      {/* Battle Type Header */}
                      <div className="flex items-center gap-2 mb-4">
                        <TypeIcon className="w-5 h-5 text-gold" />
                        <span className="text-gold font-medium">{battle.type_info?.name}</span>
                        <span className="ml-auto text-white/40 text-sm">{battle.vote_count} votes</span>
                      </div>

                      {/* VS Display */}
                      <div className="flex items-center justify-between mb-6">
                        <div className="text-center flex-1">
                          <p className="font-cinzel font-bold text-lg text-white">{battle.challenger?.display_name}</p>
                          <p className="text-white/40 text-sm">{battle.challenger?.points} pts</p>
                        </div>
                        <div className="px-4">
                          <div className="w-12 h-12 bg-gold/20 rounded-full flex items-center justify-center">
                            <span className="font-cinzel font-bold text-gold">VS</span>
                          </div>
                        </div>
                        <div className="text-center flex-1">
                          <p className="font-cinzel font-bold text-lg text-white">{battle.opponent?.display_name}</p>
                          <p className="text-white/40 text-sm">{battle.opponent?.points} pts</p>
                        </div>
                      </div>

                      {/* Vote Buttons */}
                      {!isParticipant && (
                        <div className="flex gap-3">
                          <Button
                            onClick={() => handleVote(battle.id, battle.challenger_id)}
                            className="flex-1 bg-purple-600 hover:bg-purple-700"
                            data-testid={`vote-challenger-${battle.id}`}
                          >
                            <Vote className="w-4 h-4 mr-2" />
                            Vote {battle.challenger?.display_name?.split(' ')[0]}
                          </Button>
                          <Button
                            onClick={() => handleVote(battle.id, battle.opponent_id)}
                            className="flex-1 bg-blue-600 hover:bg-blue-700"
                            data-testid={`vote-opponent-${battle.id}`}
                          >
                            <Vote className="w-4 h-4 mr-2" />
                            Vote {battle.opponent?.display_name?.split(' ')[0]}
                          </Button>
                        </div>
                      )}
                      {isParticipant && (
                        <p className="text-center text-white/40 text-sm">
                          You're a participant - cannot vote
                        </p>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          {/* My Battles */}
          <TabsContent value="my" className="mt-6">
            {myChallenges.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <Trophy className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/60 text-lg">No battles yet</p>
                <p className="text-white/40">Issue your first challenge!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {myChallenges.map((battle) => {
                  const TypeIcon = challengeIcons[battle.type] || Swords;
                  const isChallenger = battle.challenger_id === user?.id;
                  const opponentName = isChallenger ? battle.opponent?.display_name : battle.challenger?.display_name;
                  
                  return (
                    <motion.div
                      key={battle.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`glass-card p-4 ${
                        battle.status === 'completed' && battle.winner_id === user?.id
                          ? 'border-gold/30'
                          : ''
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg ${
                          battle.status === 'completed'
                            ? battle.winner_id === user?.id
                              ? 'bg-gold/20'
                              : 'bg-white/10'
                            : battle.status === 'accepted'
                            ? 'bg-green-500/20'
                            : 'bg-orange-500/20'
                        }`}>
                          <TypeIcon className={`w-5 h-5 ${
                            battle.status === 'completed' && battle.winner_id === user?.id
                              ? 'text-gold'
                              : 'text-white/60'
                          }`} />
                        </div>
                        <div className="flex-1">
                          <p className="text-white font-medium">
                            {isChallenger ? 'vs ' : 'from '} 
                            <span className="text-gold">{opponentName}</span>
                          </p>
                          <p className="text-white/40 text-sm">{battle.type_info?.name}</p>
                        </div>
                        <div className="text-right">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            battle.status === 'completed'
                              ? battle.winner_id === user?.id
                                ? 'bg-gold/20 text-gold'
                                : 'bg-white/10 text-white/60'
                              : battle.status === 'accepted'
                              ? 'bg-green-500/20 text-green-400'
                              : battle.status === 'pending'
                              ? 'bg-orange-500/20 text-orange-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            {battle.status === 'completed'
                              ? battle.winner_id === user?.id ? 'WON' : 'LOST'
                              : battle.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Issue Challenge Dialog */}
      <Dialog open={challengeDialogOpen} onOpenChange={setChallengeDialogOpen}>
        <DialogContent className="bg-royal-paper border-white/10 text-white max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-cinzel text-2xl text-gold flex items-center gap-2">
              <Swords className="w-6 h-6" />
              Issue Challenge
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 mt-4">
            {/* Select Opponent */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Select Opponent</label>
              <div className="relative mb-3">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="text"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  placeholder="Search users..."
                  className="w-full royal-input pl-10 h-10 text-sm"
                />
              </div>
              <div className="max-h-40 overflow-y-auto space-y-2">
                {filteredUsers.slice(0, 10).map((u) => (
                  <button
                    key={u.id}
                    onClick={() => setSelectedOpponent(u)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
                      selectedOpponent?.id === u.id
                        ? 'bg-gold/20 border border-gold/50'
                        : 'bg-white/5 hover:bg-white/10'
                    }`}
                  >
                    <div className="text-left">
                      <p className="text-white font-medium">{u.display_name}</p>
                      <p className="text-white/40 text-xs">{u.rank?.name} · {u.points} pts</p>
                    </div>
                    {selectedOpponent?.id === u.id && (
                      <Check className="w-5 h-5 text-gold" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Select Challenge Type */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Challenge Type</label>
              <div className="grid grid-cols-1 gap-2">
                {challengeTypes.map((type) => {
                  const TypeIcon = challengeIcons[type.id] || Swords;
                  return (
                    <button
                      key={type.id}
                      onClick={() => setSelectedType(type.id)}
                      className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                        selectedType === type.id
                          ? 'bg-gold/20 border border-gold/50'
                          : 'bg-white/5 hover:bg-white/10'
                      }`}
                    >
                      <TypeIcon className={`w-5 h-5 ${selectedType === type.id ? 'text-gold' : 'text-white/60'}`} />
                      <div className="text-left flex-1">
                        <p className={`font-medium ${selectedType === type.id ? 'text-gold' : 'text-white'}`}>
                          {type.name}
                        </p>
                        <p className="text-white/40 text-xs">{type.description}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-gold text-sm">+{type.points_winner}</p>
                        <p className="text-white/40 text-xs">winner</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Issue Button */}
            <Button
              onClick={handleIssueChallenge}
              disabled={!selectedOpponent || !selectedType || creating}
              className="w-full btn-gold"
              data-testid="confirm-challenge-btn"
            >
              {creating ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Issuing...
                </>
              ) : (
                <>
                  <Swords className="w-5 h-5 mr-2" />
                  Challenge {selectedOpponent?.display_name || 'Opponent'}
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default BattlesPage;
