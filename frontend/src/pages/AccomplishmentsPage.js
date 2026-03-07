import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Award, Star, Mic, Trophy, Crown, Heart, Moon, Users, Music, Guitar, Check, Lock } from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const badgeIcons = {
  mic: Mic,
  star: Star,
  trophy: Trophy,
  crown: Crown,
  guitar: Guitar,
  music: Music,
  users: Users,
  moon: Moon,
  heart: Heart,
};

const AccomplishmentsPage = () => {
  const { user } = useAuth();
  const [allBadges, setAllBadges] = useState([]);
  const [accomplishments, setAccomplishments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [badgesRes, accompRes] = await Promise.all([
          axios.get(`${API}/badges`),
          axios.get(`${API}/accomplishments`)
        ]);
        setAllBadges(badgesRes.data);
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
            Royal <span className="text-gold">Badges</span>
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

        {/* All Badges Grid */}
        <div>
          <h2 className="font-cinzel font-bold text-xl text-white mb-4">All Badges</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {allBadges.map((badge, index) => {
              const isEarned = earnedBadgeIds.includes(badge.id);
              const Icon = badgeIcons[badge.icon] || Star;
              
              return (
                <motion.div
                  key={badge.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.05 * index }}
                  className={`glass-card p-5 ${isEarned ? 'border-gold/30' : 'opacity-60'}`}
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
        </div>

        {/* Recent Accomplishments */}
        {accomplishments.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h2 className="font-cinzel font-bold text-xl text-white mb-4">Achievement History</h2>
            <div className="glass-card overflow-hidden">
              <div className="divide-y divide-white/5">
                {accomplishments.map((acc, index) => (
                  <motion.div
                    key={acc.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + index * 0.05 }}
                    className="flex items-center gap-4 p-4"
                    data-testid={`accomplishment-${acc.id}`}
                  >
                    <div className="p-2 bg-gold/10 rounded-lg">
                      <Star className="w-5 h-5 text-gold" />
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
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {accomplishments.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card p-12 text-center"
          >
            <Award className="w-12 h-12 text-white/20 mx-auto mb-4" />
            <p className="text-white/60 text-lg">No badges earned yet</p>
            <p className="text-white/40">Start performing to unlock your first badge!</p>
          </motion.div>
        )}
      </div>
    </Layout>
  );
};

export default AccomplishmentsPage;
