import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Crown, Mic2, Trophy, Award, Star, TrendingUp, 
  Calendar, Music, ChevronRight, Sparkles, Share2, Copy, Check, Users
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Progress } from '@/components/ui/progress';
import { getRankName } from '@/utils/rankUtils';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const FRONTEND_URL = window.location.origin;

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
  const [referralStats, setReferralStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, accompRes, referralRes] = await Promise.all([
          axios.get(`${API}/stats`),
          axios.get(`${API}/accomplishments`),
          axios.get(`${API}/auth/referral-stats`)
        ]);
        setStats(statsRes.data);
        setRecentAccomplishments(accompRes.data.slice(0, 3));
        setReferralStats(referralRes.data);
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
  const currentRankName = getRankName(user?.rank, user?.title_preference);
  const nextRankName = getRankName(user?.next_rank, user?.title_preference);
  const isMaxRank = currentRankName === 'Prince' || currentRankName === 'Princess';

  const referralLink = referralStats ? `${FRONTEND_URL}/register?ref=${referralStats.referral_code}` : '';

  const handleCopyLink = async () => {
    if (!referralLink) {
      toast.error('Referral link not available');
      return;
    }
    
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(referralLink);
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement('textarea');
        textArea.value = referralLink;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopied(true);
      toast.success('Referral link copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
      // Show the link in an alert as last resort
      toast.info('Copy this link: ' + referralLink);
    }
  };

  const handleShare = async () => {
    if (!referralLink) {
      toast.error('Referral link not available');
      return;
    }
    
    // Check if Web Share API is available and we're in a secure context
    if (navigator.share && window.isSecureContext) {
      try {
        await navigator.share({
          title: 'Join me at King Karaoke!',
          text: 'Join King Klub and start your karaoke journey! Sign up with my link to get started.',
          url: referralLink,
        });
        toast.success('Thanks for sharing!');
      } catch (err) {
        // User cancelled or share failed - try copy instead
        if (err.name !== 'AbortError') {
          handleCopyLink();
        }
      }
    } else {
      // Fallback to copy
      handleCopyLink();
    }
  };

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
                isMaxRank 
                  ? 'bg-gradient-to-br from-gold-start to-gold-end' 
                  : 'bg-purple-deep/50'
              }`}>
                <RankIcon className={`w-12 h-12 ${
                  isMaxRank ? 'text-black' : 'text-gold'
                }`} />
              </div>
              <div className="flex-1">
                <p className="text-white/60 text-sm uppercase tracking-wider mb-1">Current Rank</p>
                <h2 className="font-cinzel font-bold text-4xl text-gold mb-2">
                  {currentRankName}
                </h2>
                <p className="text-white/80 text-lg mb-4">
                  <span className="text-gold font-bold">{user?.points}</span> points earned
                </p>
                
                {user?.next_rank && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-white/60">Progress to {nextRankName}</span>
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

        {/* Referral Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.55 }}
          className="glass-card p-6"
          data-testid="referral-section"
        >
          <div className="flex flex-col lg:flex-row lg:items-center gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-xl">
                  <Users className="w-6 h-6 text-pink-400" />
                </div>
                <div>
                  <h3 className="font-cinzel font-bold text-xl text-white">Invite Friends</h3>
                  <p className="text-white/60 text-sm">Earn badges when friends join!</p>
                </div>
              </div>
              
              {referralStats && (
                <div className="flex items-center gap-4 mt-4">
                  <div className="text-center px-4 py-2 bg-white/5 rounded-lg">
                    <p className="text-2xl font-bold text-gold">{referralStats.total_referrals}</p>
                    <p className="text-white/50 text-xs">Friends Invited</p>
                  </div>
                  {referralStats.next_badge && (
                    <div className="text-center px-4 py-2 bg-white/5 rounded-lg">
                      <p className="text-lg font-bold text-purple-400">{referralStats.referrals_to_next}</p>
                      <p className="text-white/50 text-xs">to {referralStats.next_badge}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex-1 space-y-3">
              <div className="relative">
                <input
                  type="text"
                  readOnly
                  value={referralLink}
                  className="w-full royal-input pr-24 text-sm text-white/70"
                  data-testid="referral-link-input"
                />
                <button
                  onClick={handleCopyLink}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm flex items-center gap-1 transition-colors"
                  data-testid="copy-referral-btn"
                >
                  {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              
              <button
                onClick={handleShare}
                className="w-full py-3 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 rounded-lg text-white font-medium flex items-center justify-center gap-2 transition-all"
                data-testid="share-referral-btn"
              >
                <Share2 className="w-5 h-5" />
                Share Your Referral Link
              </button>
            </div>
          </div>
        </motion.div>

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
