import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Award, Star, Mic, Trophy, Crown, Heart, Moon, Users, Music, 
  Check, Lock, Video, ThumbsUp, UserPlus, Flame, Coins, Banknote,
  EyeOff, Shuffle, Handshake
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const badgeIcons = {
  mic: Mic,
  star: Star,
  trophy: Trophy,
  crown: Crown,
  music: Music,
  users: Users,
  moon: Moon,
  heart: Heart,
  video: Video,
  'thumbs-up': ThumbsUp,
  'user-plus': UserPlus,
  flame: Flame,
  award: Award,
  coins: Coins,
  banknote: Banknote,
  'eye-off': EyeOff,
  shuffle: Shuffle,
  'heart-handshake': Handshake,
};

const categoryInfo = {
  performance: { name: 'Performance', icon: Mic, color: 'from-purple-500 to-purple-700' },
  challenge: { name: 'Challenges', icon: Trophy, color: 'from-orange-500 to-red-600' },
  social: { name: 'Social', icon: Users, color: 'from-blue-500 to-cyan-500' },
  loyalty: { name: 'Loyalty', icon: Heart, color: 'from-pink-500 to-rose-600' },
  generosity: { name: 'Generosity', icon: Coins, color: 'from-gold-start to-gold-end' },
};

const AccomplishmentsPage = () => {
  const { user } = useAuth();
  const [allBadges, setAllBadges] = useState([]);
  const [pointActions, setPointActions] = useState([]);
  const [accomplishments, setAccomplishments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [badgesRes, actionsRes, accompRes] = await Promise.all([
          axios.get(`${API}/badges`),
          axios.get(`${API}/point-actions`),
          axios.get(`${API}/accomplishments`)
        ]);
        setAllBadges(badgesRes.data);
        setPointActions(actionsRes.data);
        setAccomplishments(accompRes.data);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const earnedBadgeIds = user?.badges || [];
  
  // Group badges by category
  const badgesByCategory = allBadges.reduce((acc, badge) => {
    const category = badge.category || 'performance';
    if (!acc[category]) acc[category] = [];
    acc[category].push(badge);
    return acc;
  }, {});

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading badges...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="accomplishments-page">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-2">
            Royal <span className="text-gold">Achievements</span>
          </h1>
          <p className="text-white/60">
            {earnedBadgeIds.length} of {allBadges.length} badges earned
          </p>
        </motion.div>

        {/* Progress Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6"
        >
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gold/10 rounded-xl">
              <Award className="w-8 h-8 text-gold" />
            </div>
            <div className="flex-1">
              <h2 className="font-cinzel font-bold text-xl text-white mb-2">Badge Collection</h2>
              <div className="w-full bg-white/10 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-gold-start to-gold-end h-3 rounded-full transition-all duration-500"
                  style={{ width: `${(earnedBadgeIds.length / allBadges.length) * 100}%` }}
                />
              </div>
              <p className="text-white/60 text-sm mt-2">
                {Math.round((earnedBadgeIds.length / allBadges.length) * 100)}% complete
              </p>
            </div>
          </div>
        </motion.div>

        <Tabs defaultValue="badges" className="w-full">
          <TabsList className="w-full sm:w-auto bg-royal-paper border border-white/10">
            <TabsTrigger 
              value="badges"
              data-testid="badges-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Award className="w-4 h-4 mr-2" />
              Badges
            </TabsTrigger>
            <TabsTrigger 
              value="points"
              data-testid="points-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Star className="w-4 h-4 mr-2" />
              Point System
            </TabsTrigger>
            <TabsTrigger 
              value="history"
              data-testid="history-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Trophy className="w-4 h-4 mr-2" />
              History
            </TabsTrigger>
          </TabsList>

          {/* Badges Tab */}
          <TabsContent value="badges" className="mt-6 space-y-8">
            {Object.entries(categoryInfo).map(([categoryKey, categoryData]) => {
              const badges = badgesByCategory[categoryKey] || [];
              if (badges.length === 0) return null;
              
              const CategoryIcon = categoryData.icon;
              const earnedInCategory = badges.filter(b => earnedBadgeIds.includes(b.id)).length;
              
              return (
                <motion.div
                  key={categoryKey}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`p-2 rounded-lg bg-gradient-to-br ${categoryData.color}`}>
                      <CategoryIcon className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="font-cinzel font-bold text-xl text-white">{categoryData.name}</h2>
                    <span className="text-white/40 text-sm">({earnedInCategory}/{badges.length})</span>
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {badges.map((badge, index) => {
                      const isEarned = earnedBadgeIds.includes(badge.id);
                      const Icon = badgeIcons[badge.icon] || Star;
                      
                      return (
                        <motion.div
                          key={badge.id}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.03 * index }}
                          className={`glass-card p-5 ${isEarned ? 'border-gold/30' : 'opacity-50'}`}
                          data-testid={`badge-${badge.id}`}
                        >
                          <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${isEarned ? 'bg-gold/20' : 'bg-white/5'}`}>
                              {isEarned ? (
                                <Icon className="w-6 h-6 text-gold" />
                              ) : (
                                <Lock className="w-6 h-6 text-white/30" />
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className={`font-cinzel font-bold ${isEarned ? 'text-white' : 'text-white/50'}`}>
                                  {badge.name}
                                </h3>
                                {isEarned && (
                                  <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                                    <Check className="w-3 h-3 text-white" />
                                  </div>
                                )}
                              </div>
                              <p className={`text-sm ${isEarned ? 'text-white/60' : 'text-white/30'}`}>
                                {badge.description}
                              </p>
                              <p className={`text-sm mt-2 ${isEarned ? 'text-gold' : 'text-white/30'}`}>
                                +{badge.points_reward} bonus points
                              </p>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </motion.div>
              );
            })}
          </TabsContent>

          {/* Point System Tab */}
          <TabsContent value="points" className="mt-6">
            <div className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/10 bg-gold/5">
                <h2 className="font-cinzel font-bold text-lg text-gold">How to Earn Points</h2>
                <p className="text-white/60 text-sm mt-1">Complete these actions to earn points and level up!</p>
              </div>
              <div className="divide-y divide-white/5">
                {pointActions.map((action, index) => (
                  <motion.div
                    key={action.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.05 * index }}
                    className="flex items-center gap-4 p-4 hover:bg-white/5 transition-colors"
                    data-testid={`point-action-${action.id}`}
                  >
                    <div className="flex-1">
                      <h3 className="text-white font-medium">{action.name}</h3>
                      <p className="text-white/50 text-sm">{action.description}</p>
                    </div>
                    <div className="text-right">
                      <span className={`font-cinzel font-bold text-xl ${
                        action.points >= 100 ? 'text-gold' : 
                        action.points >= 50 ? 'text-purple-400' : 'text-white'
                      }`}>
                        +{action.points}
                      </span>
                      <p className="text-white/40 text-xs">points</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
            
            {/* Point Tiers Legend */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mt-6 glass-card p-6"
            >
              <h3 className="font-cinzel font-bold text-lg text-white mb-4">Point Values</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-white font-bold text-lg">10 pts</div>
                  <div className="text-white/40 text-sm">Standard Actions</div>
                </div>
                <div>
                  <div className="text-purple-400 font-bold text-lg">25-100 pts</div>
                  <div className="text-white/40 text-sm">Special Actions</div>
                </div>
                <div>
                  <div className="text-gold font-bold text-lg">200-250 pts</div>
                  <div className="text-white/40 text-sm">Epic Challenges</div>
                </div>
              </div>
            </motion.div>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="mt-6">
            {accomplishments.length > 0 ? (
              <div className="glass-card overflow-hidden">
                <div className="p-4 border-b border-white/10">
                  <h2 className="font-cinzel font-bold text-lg text-white">Achievement History</h2>
                </div>
                <div className="divide-y divide-white/5">
                  {accomplishments.map((acc, index) => {
                    const badge = allBadges.find(b => b.id === acc.badge_id);
                    const Icon = badge ? (badgeIcons[badge.icon] || Star) : Star;
                    
                    return (
                      <motion.div
                        key={acc.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.05 * index }}
                        className="flex items-center gap-4 p-4"
                        data-testid={`accomplishment-${acc.id}`}
                      >
                        <div className="p-2 bg-gold/10 rounded-lg">
                          <Icon className="w-5 h-5 text-gold" />
                        </div>
                        <div className="flex-1">
                          <p className="text-white font-medium">{acc.badge_name}</p>
                          <p className="text-white/40 text-sm">
                            Earned on {new Date(acc.earned_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric'
                            })}
                          </p>
                        </div>
                        <div className="text-gold">
                          <Check className="w-5 h-5" />
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="glass-card p-12 text-center">
                <Award className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/60 text-lg">No badges earned yet</p>
                <p className="text-white/40">Start performing to unlock your first badge!</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default AccomplishmentsPage;
