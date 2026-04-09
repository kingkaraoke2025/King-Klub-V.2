import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Crown, Medal, Star, TrendingUp, Moon, Calendar } from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { getRankName } from '@/utils/rankUtils';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Rank colors support both male and female rank names
const rankColors = {
  Peasant: 'bg-gray-500',
  Squire: 'bg-green-500',
  Lady: 'bg-green-500',
  Knight: 'bg-blue-500',
  Dame: 'bg-blue-500',
  Count: 'bg-purple-500',
  Countess: 'bg-purple-500',
  Duke: 'bg-pink-500',
  Duchess: 'bg-pink-500',
  Prince: 'bg-gradient-to-r from-gold-start to-gold-end',
  Princess: 'bg-gradient-to-r from-gold-start to-gold-end',
};

const isMaxRank = (rankName) => rankName === 'Prince' || rankName === 'Princess';

const LeaderboardPage = () => {
  const { user } = useAuth();
  const [allTimeLeaderboard, setAllTimeLeaderboard] = useState([]);
  const [tonightLeaderboard, setTonightLeaderboard] = useState([]);
  const [tonightDate, setTonightDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tonight');

  const [tonightActive, setTonightActive] = useState(false);

  const fetchLeaderboards = useCallback(async () => {
    try {
      const [allTimeRes, tonightRes] = await Promise.all([
        axios.get(`${API}/leaderboard`),
        axios.get(`${API}/leaderboard/tonight`)
      ]);
      setAllTimeLeaderboard(allTimeRes.data);
      setTonightLeaderboard(tonightRes.data.leaderboard || []);
      setTonightDate(tonightRes.data.date || '');
      setTonightActive(tonightRes.data.active || false);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLeaderboards();
    
    // Listen for real-time points updates via WebSocket
    const handlePointsUpdate = () => {
      fetchLeaderboards();
    };
    
    // Listen for leaderboard reset
    const handleLeaderboardReset = () => {
      fetchLeaderboards();
    };
    
    window.addEventListener('pointsUpdated', handlePointsUpdate);
    window.addEventListener('leaderboardReset', handleLeaderboardReset);
    
    return () => {
      window.removeEventListener('pointsUpdated', handlePointsUpdate);
      window.removeEventListener('leaderboardReset', handleLeaderboardReset);
    };
  }, [fetchLeaderboards]);

  const currentLeaderboard = activeTab === 'tonight' ? tonightLeaderboard : allTimeLeaderboard;
  const pointsKey = activeTab === 'tonight' ? 'nightly_points' : 'points';
  const userPosition = currentLeaderboard.findIndex(entry => entry.id === user?.id) + 1;

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading leaderboard...</div>
        </div>
      </Layout>
    );
  }

  const renderPodium = (leaderboard) => {
    if (leaderboard.length < 3) return null;
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-3 gap-4 mb-8"
      >
        {/* 2nd Place */}
        <div className="order-1 pt-8">
          <div className="glass-card p-4 text-center" data-testid="leaderboard-rank-2">
            <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gray-400 flex items-center justify-center">
              <Medal className="w-8 h-8 text-white" />
            </div>
            <div className="text-3xl font-bold text-gray-400 mb-1">2</div>
            <h3 className="font-cinzel font-bold text-white truncate">{leaderboard[1]?.display_name}</h3>
            <p className="text-gold font-bold">{leaderboard[1]?.[pointsKey] || leaderboard[1]?.points} pts</p>
            <span className={`inline-block mt-2 px-2 py-0.5 rounded-full text-xs ${rankColors[getRankName(leaderboard[1]?.rank, leaderboard[1]?.title_preference)]} ${isMaxRank(getRankName(leaderboard[1]?.rank, leaderboard[1]?.title_preference)) ? 'text-black' : 'text-white'}`}>
              {getRankName(leaderboard[1]?.rank, leaderboard[1]?.title_preference)}
            </span>
          </div>
        </div>

        {/* 1st Place */}
        <div className="order-2">
          <div className="glass-card p-6 text-center border-gold/30 animate-gold-glow" data-testid="leaderboard-rank-1">
            <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br from-gold-start to-gold-end flex items-center justify-center">
              <Crown className="w-10 h-10 text-black" />
            </div>
            <div className="text-4xl font-bold text-gold mb-1">1</div>
            <h3 className="font-cinzel font-bold text-xl text-white truncate">{leaderboard[0]?.display_name}</h3>
            <p className="text-gold font-bold text-lg">{leaderboard[0]?.[pointsKey] || leaderboard[0]?.points} pts</p>
            <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm ${rankColors[getRankName(leaderboard[0]?.rank, leaderboard[0]?.title_preference)]} ${isMaxRank(getRankName(leaderboard[0]?.rank, leaderboard[0]?.title_preference)) ? 'text-black' : 'text-white'}`}>
              {getRankName(leaderboard[0]?.rank, leaderboard[0]?.title_preference)}
            </span>
          </div>
        </div>

        {/* 3rd Place */}
        <div className="order-3 pt-12">
          <div className="glass-card p-4 text-center" data-testid="leaderboard-rank-3">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-amber-700 flex items-center justify-center">
              <Medal className="w-7 h-7 text-white" />
            </div>
            <div className="text-2xl font-bold text-amber-700 mb-1">3</div>
            <h3 className="font-cinzel font-bold text-white truncate">{leaderboard[2]?.display_name}</h3>
            <p className="text-gold font-bold">{leaderboard[2]?.[pointsKey] || leaderboard[2]?.points} pts</p>
            <span className={`inline-block mt-2 px-2 py-0.5 rounded-full text-xs ${rankColors[getRankName(leaderboard[2]?.rank, leaderboard[2]?.title_preference)]} ${isMaxRank(getRankName(leaderboard[2]?.rank, leaderboard[2]?.title_preference)) ? 'text-black' : 'text-white'}`}>
              {getRankName(leaderboard[2]?.rank, leaderboard[2]?.title_preference)}
            </span>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderLeaderboardList = (leaderboard) => {
    if (leaderboard.length === 0) {
      return (
        <div className="glass-card p-12 text-center">
          <Trophy className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <p className="text-white/60 text-lg">
            {activeTab === 'tonight' ? 'No points earned tonight yet' : 'No performers yet'}
          </p>
          <p className="text-white/40">
            {activeTab === 'tonight' ? 'Start singing to climb the nightly leaderboard!' : 'Be the first to claim the throne!'}
          </p>
        </div>
      );
    }

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card overflow-hidden"
      >
        <div className="p-4 border-b border-white/10">
          <h2 className="font-cinzel font-bold text-lg text-white">
            {activeTab === 'tonight' ? "Tonight's Performers" : 'All Performers'}
          </h2>
        </div>
        
        <div className="divide-y divide-white/5">
          {leaderboard.map((entry, index) => {
            const entryRankName = getRankName(entry.rank, entry.title_preference);
            const displayPoints = entry[pointsKey] || entry.points;
            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + index * 0.03 }}
                className={`flex items-center gap-4 p-4 leaderboard-row ${
                  entry.id === user?.id ? 'bg-gold/5' : ''
                }`}
                data-testid={`leaderboard-row-${entry.position}`}
              >
                {/* Position */}
                <div className="w-10 text-center">
                  {entry.position <= 3 ? (
                    <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center ${
                      entry.position === 1 ? 'bg-gold' :
                      entry.position === 2 ? 'bg-gray-400' : 'bg-amber-700'
                    }`}>
                      {entry.position === 1 ? (
                        <Crown className="w-4 h-4 text-black" />
                      ) : (
                        <span className="text-white font-bold text-sm">{entry.position}</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-white/60 font-bold">{entry.position}</span>
                  )}
                </div>

                {/* User Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-white truncate">{entry.display_name}</h3>
                    {entry.id === user?.id && (
                      <span className="text-xs bg-gold/20 text-gold px-2 py-0.5 rounded-full">You</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${rankColors[entryRankName]} ${isMaxRank(entryRankName) ? 'text-black' : 'text-white'}`}>
                      {entryRankName}
                    </span>
                    {activeTab === 'alltime' && (
                      <span className="text-white/40 text-xs">{entry.songs_performed} songs</span>
                    )}
                  </div>
                </div>

                {/* Points */}
                <div className="text-right">
                  <p className="text-gold font-bold text-lg">{displayPoints}</p>
                  <p className="text-white/40 text-xs">points</p>
                </div>

                {/* Badges */}
                <div className="hidden sm:flex items-center gap-1">
                  {entry.badges?.slice(0, 3).map((badge, i) => (
                    <div key={i} className="w-6 h-6 bg-white/5 rounded-full flex items-center justify-center">
                      <Star className="w-3 h-3 text-gold" />
                    </div>
                  ))}
                  {entry.badges?.length > 3 && (
                    <span className="text-white/40 text-xs">+{entry.badges.length - 3}</span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    );
  };

  return (
    <Layout>
      <div className="space-y-8" data-testid="leaderboard-page">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-2">
            Royal <span className="text-gold">Leaderboard</span>
          </h1>
          <p className="text-white/60">The kingdom's finest performers</p>
        </motion.div>

        {/* Tabs for Tonight vs All-Time */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full max-w-md mx-auto grid grid-cols-2 bg-white/5 border border-white/10 rounded-lg p-1">
            <TabsTrigger 
              value="tonight" 
              className="flex items-center gap-2 data-[state=active]:bg-gold data-[state=active]:text-black rounded-md transition-all"
              data-testid="tonight-tab"
            >
              <Moon className="w-4 h-4" />
              Tonight
            </TabsTrigger>
            <TabsTrigger 
              value="alltime"
              className="flex items-center gap-2 data-[state=active]:bg-gold data-[state=active]:text-black rounded-md transition-all"
              data-testid="alltime-tab"
            >
              <Calendar className="w-4 h-4" />
              All-Time
            </TabsTrigger>
          </TabsList>

          {/* Tonight's Date Badge */}
          {activeTab === 'tonight' && tonightDate && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center mt-4"
            >
              <span className="inline-flex items-center gap-2 text-white/60 text-sm bg-white/5 px-4 py-2 rounded-full">
                <Moon className="w-4 h-4 text-gold" />
                {new Date(tonightDate + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </span>
            </motion.div>
          )}

          <TabsContent value="tonight" className="mt-6">
            {/* Show message if no active session */}
            {!tonightActive ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-12 text-center"
              >
                <Moon className="w-16 h-16 text-white/20 mx-auto mb-4" />
                <h3 className="font-cinzel font-bold text-xl text-white mb-2">No Active Session</h3>
                <p className="text-white/60">
                  Tonight's leaderboard will appear once the venue opens and generates a new QR code.
                </p>
                <p className="text-white/40 text-sm mt-2">
                  Check in when you arrive to start earning points!
                </p>
              </motion.div>
            ) : (
              <>
                {/* Podium */}
                {renderPodium(tonightLeaderboard)}
                
                {/* User's Position */}
                {userPosition > 0 && activeTab === 'tonight' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass-card p-4 border-gold/30 mb-6"
                    data-testid="user-position"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gold/10 rounded-lg flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-gold" />
                      </div>
                      <div>
                        <p className="text-white/60 text-sm">Your Tonight's Position</p>
                        <p className="text-white font-bold text-xl">
                          #{userPosition} <span className="text-white/60 font-normal text-base">out of {tonightLeaderboard.length}</span>
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* List */}
                {renderLeaderboardList(tonightLeaderboard)}
              </>
            )}
          </TabsContent>

          <TabsContent value="alltime" className="mt-6">
            {/* Podium */}
            {renderPodium(allTimeLeaderboard)}
            
            {/* User's Position */}
            {userPosition > 0 && activeTab === 'alltime' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass-card p-4 border-gold/30 mb-6"
                data-testid="user-position"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gold/10 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-gold" />
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Your All-Time Position</p>
                    <p className="text-white font-bold text-xl">
                      #{userPosition} <span className="text-white/60 font-normal text-base">out of {allTimeLeaderboard.length}</span>
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* List */}
            {renderLeaderboardList(allTimeLeaderboard)}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default LeaderboardPage;
