import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Mic2, Star, Trophy, Crown, Swords, Users, Heart, 
  Moon, Flame, Award, Coins, Gift, Calendar, Video,
  ThumbsUp, UserPlus, Music, Shuffle, EyeOff, Megaphone,
  Beer, Banknote, HeartHandshake, Sparkles, Shield
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icon mapping for badges
const iconMap = {
  mic: Mic2,
  star: Star,
  trophy: Trophy,
  crown: Crown,
  swords: Swords,
  users: Users,
  heart: Heart,
  moon: Moon,
  flame: Flame,
  award: Award,
  coins: Coins,
  gift: Gift,
  calendar: Calendar,
  video: Video,
  'thumbs-up': ThumbsUp,
  'user-plus': UserPlus,
  'users-round': Users,
  music: Music,
  shuffle: Shuffle,
  'eye-off': EyeOff,
  megaphone: Megaphone,
  beer: Beer,
  banknote: Banknote,
  'heart-handshake': HeartHandshake,
  sparkles: Sparkles,
  shield: Shield,
};

// Category colors and icons
const categoryConfig = {
  performance: { color: 'from-blue-500 to-blue-700', icon: Mic2, label: 'Performance' },
  challenge: { color: 'from-orange-500 to-red-600', icon: Flame, label: 'Challenges' },
  social: { color: 'from-pink-500 to-purple-600', icon: Users, label: 'Social' },
  loyalty: { color: 'from-red-500 to-pink-600', icon: Heart, label: 'Loyalty' },
  generosity: { color: 'from-yellow-500 to-amber-600', icon: Coins, label: 'Generosity' },
  battle: { color: 'from-purple-500 to-indigo-600', icon: Swords, label: 'Battle' },
};

const HowToEarnPage = () => {
  const [pointActions, setPointActions] = useState([]);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('actions');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [actionsRes, badgesRes] = await Promise.all([
          axios.get(`${API}/point-actions`),
          axios.get(`${API}/badges`)
        ]);
        setPointActions(actionsRes.data);
        setBadges(badgesRes.data);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Group badges by category
  const badgesByCategory = badges.reduce((acc, badge) => {
    const category = badge.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(badge);
    return acc;
  }, {});

  // Calculate totals
  const totalActionPoints = pointActions.reduce((sum, a) => sum + a.points, 0);
  const totalBadgePoints = badges.reduce((sum, b) => sum + b.points_reward, 0);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="font-cinzel text-4xl md:text-5xl font-bold text-gold mb-4" data-testid="how-to-earn-title">
            How to Earn Points
          </h1>
          <p className="text-white/70 text-lg max-w-2xl mx-auto">
            Rise through the ranks from Peasant to Prince/Princess! Earn points through actions and unlock badges for bonus rewards.
          </p>
        </motion.div>

        {/* Stats Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        >
          <div className="glass-card p-4 text-center">
            <p className="text-3xl font-bold text-gold">{pointActions.length}</p>
            <p className="text-white/60 text-sm">Point Actions</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-3xl font-bold text-gold">{badges.length}</p>
            <p className="text-white/60 text-sm">Badges</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-3xl font-bold text-green-400">{totalActionPoints}</p>
            <p className="text-white/60 text-sm">Action Points</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-3xl font-bold text-purple-400">{totalBadgePoints}</p>
            <p className="text-white/60 text-sm">Badge Bonus Points</p>
          </div>
        </motion.div>

        {/* Rank Progression */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass-card p-6 mb-8"
        >
          <h2 className="font-cinzel text-2xl font-bold text-gold mb-4 flex items-center gap-2">
            <Crown className="w-6 h-6" />
            Rank Progression
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { name: 'Peasant', female: 'Peasant', points: 0, icon: Shield },
              { name: 'Squire', female: 'Lady', points: 500, icon: Star },
              { name: 'Knight', female: 'Dame', points: 1000, icon: Swords },
              { name: 'Count', female: 'Countess', points: 1500, icon: Crown },
              { name: 'Duke', female: 'Duchess', points: 2000, icon: Sparkles },
              { name: 'Prince', female: 'Princess', points: 2500, icon: Crown },
            ].map((rank, idx) => {
              const Icon = rank.icon;
              return (
                <div key={rank.name} className="text-center p-4 rounded-lg bg-white/5 border border-white/10">
                  <Icon className={`w-8 h-8 mx-auto mb-2 ${idx === 5 ? 'text-gold' : 'text-white/60'}`} />
                  <p className="font-cinzel font-bold text-white">{rank.name}</p>
                  <p className="text-white/40 text-xs">{rank.female}</p>
                  <p className="text-gold text-sm mt-1">{rank.points}+ pts</p>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('actions')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'actions'
                ? 'bg-gold text-black'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
            data-testid="tab-actions"
          >
            Point Actions ({pointActions.length})
          </button>
          <button
            onClick={() => setActiveTab('badges')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'badges'
                ? 'bg-gold text-black'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
            data-testid="tab-badges"
          >
            Badges ({badges.length})
          </button>
        </div>

        {/* Point Actions Tab */}
        {activeTab === 'actions' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            <div className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/10 bg-white/5">
                <h2 className="font-cinzel text-xl font-bold text-gold flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  Earn Points by Doing These Actions
                </h2>
                <p className="text-white/60 text-sm mt-1">
                  Staff can award these points when you complete actions at King Karaoke
                </p>
              </div>
              <div className="divide-y divide-white/5">
                {pointActions.map((action, idx) => (
                  <motion.div
                    key={action.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="p-4 hover:bg-white/5 transition-colors"
                    data-testid={`action-${action.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-gold/20 flex items-center justify-center flex-shrink-0">
                        <Star className="w-5 h-5 text-gold" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-medium text-white text-sm sm:text-base">{action.name}</h3>
                          <span className="text-gold font-bold text-lg sm:text-xl whitespace-nowrap">+{action.points}</span>
                        </div>
                        <p className="text-white/50 text-xs sm:text-sm mt-1">{action.description}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Badges Tab */}
        {activeTab === 'badges' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {Object.entries(categoryConfig).map(([categoryKey, config]) => {
              const categoryBadges = badgesByCategory[categoryKey] || [];
              if (categoryBadges.length === 0) return null;
              
              const CategoryIcon = config.icon;
              const totalCategoryPoints = categoryBadges.reduce((sum, b) => sum + b.points_reward, 0);
              
              return (
                <motion.div
                  key={categoryKey}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-card overflow-hidden"
                >
                  <div className={`p-4 border-b border-white/10 bg-gradient-to-r ${config.color} bg-opacity-20`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <h2 className="font-cinzel text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                        <CategoryIcon className="w-5 h-5" />
                        {config.label} Badges
                      </h2>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-white/80">{categoryBadges.length} badges</span>
                        <span className="text-gold font-medium">+{totalCategoryPoints} pts total</span>
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
                    {categoryBadges.map((badge, idx) => {
                      const BadgeIcon = iconMap[badge.icon] || Star;
                      return (
                        <motion.div
                          key={badge.id}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: idx * 0.05 }}
                          className="p-4 rounded-lg bg-white/5 border border-white/10 hover:border-gold/30 transition-all"
                          data-testid={`badge-${badge.id}`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br ${config.color} flex items-center justify-center flex-shrink-0`}>
                              <BadgeIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-2">
                                <h3 className="font-cinzel font-bold text-white text-sm sm:text-base">{badge.name}</h3>
                                <span className="text-gold font-bold text-sm sm:text-base whitespace-nowrap">+{badge.points_reward}</span>
                              </div>
                              <p className="text-white/50 text-xs sm:text-sm mt-1">{badge.description}</p>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* Tips Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8 glass-card p-6"
        >
          <h2 className="font-cinzel text-2xl font-bold text-gold mb-4">Pro Tips</h2>
          <ul className="space-y-3 text-white/80">
            <li className="flex items-start gap-3">
              <Mic2 className="w-5 h-5 text-gold mt-0.5 flex-shrink-0" />
              <span>Sing regularly to earn performance badges and climb the leaderboard!</span>
            </li>
            <li className="flex items-start gap-3">
              <Users className="w-5 h-5 text-gold mt-0.5 flex-shrink-0" />
              <span>Share your referral link with friends - earn badges when they join!</span>
            </li>
            <li className="flex items-start gap-3">
              <Calendar className="w-5 h-5 text-gold mt-0.5 flex-shrink-0" />
              <span>Visit on consecutive nights to unlock loyalty badges and bonus points.</span>
            </li>
            <li className="flex items-start gap-3">
              <Swords className="w-5 h-5 text-gold mt-0.5 flex-shrink-0" />
              <span>Challenge other singers in the Battle Arena for extra points and glory!</span>
            </li>
          </ul>
        </motion.div>
      </div>
    </Layout>
  );
};

export default HowToEarnPage;
