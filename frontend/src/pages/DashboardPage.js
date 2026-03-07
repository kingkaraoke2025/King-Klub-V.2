import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Crown, Mic2, Trophy, Award, Star, TrendingUp, 
  Calendar, Music, ChevronRight, Sparkles 
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Progress } from '@/components/ui/progress';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const rankIcons = {
  shield: Crown,
  sword: Mic2,
  swords: Trophy,
  crown: Crown,
  gem: Star,
  sparkles: Sparkles,
};

const DashboardPage = () => {
  const { user, refreshUser } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentAccomplishments, setRecentAccomplishments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, accompRes] = await Promise.all([
          axios.get(`${API}/stats`),
          axios.get(`${API}/accomplishments`)
        ]);
        setStats(statsRes.data);
        setRecentAccomplishments(accompRes.data.slice(0, 3));
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    refreshUser();
  }, []);

  const progressToNextRank = user?.next_rank
    ? ((user.points - (user.rank?.min_points || 0)) / 
       (user.next_rank.min_points - (user.rank?.min_points || 0))) * 100
    : 100;

  const RankIcon = rankIcons[user?.rank?.icon] || Crown;

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="dashboard-page">
        {/* Welcome Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-2">
            Welcome, <span className="text-gold">{user?.display_name}</span>
          </h1>
          <p className="text-white/60">Your royal journey continues</p>
        </motion.div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Rank Card - Large */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-2 glass-card p-8"
            data-testid="rank-card"
          >
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
              <div className={`p-6 rounded-2xl ${
                user?.rank?.name === 'Prince' 
                  ? 'bg-gradient-to-br from-gold-start to-gold-end' 
                  : 'bg-purple-deep/50'
              }`}>
                <RankIcon className={`w-12 h-12 ${
                  user?.rank?.name === 'Prince' ? 'text-black' : 'text-gold'
                }`} />
              </div>
              <div className="flex-1">
                <p className="text-white/60 text-sm uppercase tracking-wider mb-1">Current Rank</p>
                <h2 className="font-cinzel font-bold text-4xl text-gold mb-2">
                  {user?.rank?.name}
                </h2>
                <p className="text-white/80 text-lg mb-4">
                  <span className="text-gold font-bold">{user?.points}</span> points earned
                </p>
                
                {user?.next_rank && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-white/60">Progress to {user.next_rank.name}</span>
                      <span className="text-gold">{user.next_rank.min_points - user.points} pts to go</span>
                    </div>
                    <Progress value={progressToNextRank} className="h-2 bg-white/10" />
                  </div>
                )}
                {!user?.next_rank && (
                  <p className="text-gold font-playfair italic">You've reached the highest rank!</p>
                )}
              </div>
            </div>
          </motion.div>

          {/* Quick Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="glass-card p-6 space-y-6"
            data-testid="quick-stats"
          >
            <h3 className="font-cinzel font-bold text-lg text-white">Your Stats</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Music className="w-5 h-5 text-gold" />
                  <span className="text-white/80">Songs Performed</span>
                </div>
                <span className="text-gold font-bold text-xl">{user?.songs_performed || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Award className="w-5 h-5 text-gold" />
                  <span className="text-white/80">Badges Earned</span>
                </div>
                <span className="text-gold font-bold text-xl">{user?.badges?.length || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-gold" />
                  <span className="text-white/80">Visit Streak</span>
                </div>
                <span className="text-gold font-bold text-xl">{user?.consecutive_visits || 0}</span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Join Queue Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Link
              to="/queue"
              data-testid="queue-card-link"
              className="block glass-card p-6 hover:border-gold/30 transition-all group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gold/10 rounded-xl group-hover:bg-gold/20 transition-colors">
                  <Mic2 className="w-6 h-6 text-gold" />
                </div>
                <ChevronRight className="w-5 h-5 text-white/40 group-hover:text-gold transition-colors" />
              </div>
              <h3 className="font-cinzel font-bold text-xl text-white mb-2">Song Queue</h3>
              <p className="text-white/60 text-sm">
                {stats?.current_queue_length || 0} singers waiting
              </p>
            </Link>
          </motion.div>

          {/* Leaderboard Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Link
              to="/leaderboard"
              data-testid="leaderboard-card-link"
              className="block glass-card p-6 hover:border-gold/30 transition-all group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gold/10 rounded-xl group-hover:bg-gold/20 transition-colors">
                  <Trophy className="w-6 h-6 text-gold" />
                </div>
                <ChevronRight className="w-5 h-5 text-white/40 group-hover:text-gold transition-colors" />
              </div>
              <h3 className="font-cinzel font-bold text-xl text-white mb-2">Leaderboard</h3>
              <p className="text-white/60 text-sm">
                {stats?.total_users || 0} performers competing
              </p>
            </Link>
          </motion.div>

          {/* Accomplishments Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <Link
              to="/accomplishments"
              data-testid="accomplishments-card-link"
              className="block glass-card p-6 hover:border-gold/30 transition-all group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gold/10 rounded-xl group-hover:bg-gold/20 transition-colors">
                  <Award className="w-6 h-6 text-gold" />
                </div>
                <ChevronRight className="w-5 h-5 text-white/40 group-hover:text-gold transition-colors" />
              </div>
              <h3 className="font-cinzel font-bold text-xl text-white mb-2">Badges</h3>
              <p className="text-white/60 text-sm">
                {user?.badges?.length || 0} of {Object.keys(recentAccomplishments).length + 6} unlocked
              </p>
            </Link>
          </motion.div>
        </div>

        {/* Recent Accomplishments */}
        {recentAccomplishments.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="glass-card p-6"
            data-testid="recent-accomplishments"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-cinzel font-bold text-xl text-white">Recent Achievements</h3>
              <Link 
                to="/accomplishments" 
                className="text-gold text-sm hover:underline flex items-center gap-1"
              >
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="space-y-3">
              {recentAccomplishments.map((acc) => (
                <div
                  key={acc.id}
                  className="flex items-center gap-4 p-4 bg-white/5 rounded-lg"
                >
                  <div className="p-2 bg-gold/10 rounded-lg">
                    <Star className="w-5 h-5 text-gold" />
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium">{acc.badge_name}</p>
                    <p className="text-white/40 text-sm">
                      {new Date(acc.earned_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Global Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="grid grid-cols-3 gap-4"
          data-testid="global-stats"
        >
          <div className="stat-card">
            <div className="stat-value">{stats?.total_users || 0}</div>
            <div className="stat-label">Total Members</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats?.total_songs_performed || 0}</div>
            <div className="stat-label">Songs Performed</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats?.current_queue_length || 0}</div>
            <div className="stat-label">In Queue Now</div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
