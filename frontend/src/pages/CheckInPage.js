import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader2, Crown, Flame, Award, PartyPopper } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_karaoke-kingdom/artifacts/ttig1x57_King%20Karaoke%203.png";
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CheckInPage = () => {
  const { venueCode } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated, loading: authLoading, refreshUser } = useAuth();
  const [status, setStatus] = useState('loading'); // loading, success, already, error, login-required
  const [result, setResult] = useState(null);

  useEffect(() => {
    const performCheckIn = async () => {
      if (authLoading) return;
      
      if (!isAuthenticated) {
        setStatus('login-required');
        return;
      }

      try {
        const response = await axios.post(`${API}/checkin/${venueCode}`);
        setResult(response.data);
        
        if (response.data.already_checked_in) {
          setStatus('already');
        } else {
          setStatus('success');
          refreshUser(); // Update user data with new points
          
          // Show toast for badges
          if (response.data.badges_earned?.length > 0) {
            toast.success(`Badge unlocked: ${response.data.badges_earned.join(', ')}!`);
          }
        }
      } catch (error) {
        console.error('Check-in failed:', error);
        setStatus('error');
        setResult({ message: error.response?.data?.detail || 'Check-in failed' });
      }
    };

    performCheckIn();
  }, [venueCode, isAuthenticated, authLoading]);

  // Loading state
  if (status === 'loading' || authLoading) {
    return (
      <div className="min-h-screen bg-royal-bg flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="w-16 h-16 text-gold animate-spin mx-auto mb-4" />
          <p className="text-white/60 font-cinzel text-xl">Checking you in...</p>
        </motion.div>
      </div>
    );
  }

  // Login required
  if (status === 'login-required') {
    return (
      <div className="min-h-screen bg-royal-bg flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-8 max-w-md w-full text-center"
        >
          <img src={LOGO_URL} alt="King Karaoke" className="w-24 h-24 mx-auto mb-6 object-contain" />
          <h1 className="font-cinzel font-bold text-2xl text-white mb-4">
            Welcome to <span className="text-gold">King Karaoke!</span>
          </h1>
          <p className="text-white/60 mb-6">
            Please sign in or create an account to check in and start earning points!
          </p>
          <div className="space-y-3">
            <Link 
              to={`/login?redirect=/checkin/${venueCode}`}
              className="btn-gold w-full block text-center"
              data-testid="login-btn"
            >
              Sign In
            </Link>
            <Link 
              to={`/register?redirect=/checkin/${venueCode}`}
              className="block w-full bg-white/5 border border-white/20 hover:bg-white/10 text-white rounded-full px-8 py-3 font-medium transition-all text-center"
              data-testid="register-btn"
            >
              Create Account
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  // Success state
  if (status === 'success') {
    return (
      <div className="min-h-screen bg-royal-bg flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-8 max-w-md w-full text-center border-gold/30"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          >
            <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h1 className="font-cinzel font-bold text-2xl text-white mb-2">
              Welcome, <span className="text-gold">{user?.display_name}!</span>
            </h1>
            <p className="text-white/60 mb-6">You've successfully checked in!</p>
          </motion.div>

          {/* Points awarded */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-gold/10 rounded-xl p-6 mb-6"
          >
            <div className="flex items-center justify-center gap-2 mb-2">
              <PartyPopper className="w-6 h-6 text-gold" />
              <span className="text-gold font-cinzel font-bold text-3xl">+{result?.points_awarded}</span>
              <span className="text-white/60">points</span>
            </div>
            {result?.bonus_points > 0 && (
              <p className="text-gold text-sm">+{result.bonus_points} bonus points from badges!</p>
            )}
          </motion.div>

          {/* Streak info */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex items-center justify-center gap-4 mb-6"
          >
            <div className="flex items-center gap-2">
              <Flame className={`w-5 h-5 ${result?.consecutive_visits >= 3 ? 'text-orange-400' : 'text-white/40'}`} />
              <span className="text-white">{result?.consecutive_visits} night streak</span>
            </div>
          </motion.div>

          {/* Badges earned */}
          {result?.badges_earned?.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-purple-500/20 rounded-xl p-4 mb-6"
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <Award className="w-5 h-5 text-purple-400" />
                <span className="text-purple-400 font-medium">Badge Unlocked!</span>
              </div>
              {result.badges_earned.map((badge, i) => (
                <p key={i} className="text-white font-cinzel">{badge}</p>
              ))}
            </motion.div>
          )}

          <Button
            onClick={() => navigate('/dashboard')}
            className="btn-gold w-full"
            data-testid="go-to-dashboard-btn"
          >
            <Crown className="w-5 h-5 mr-2" />
            Go to Dashboard
          </Button>
        </motion.div>
      </div>
    );
  }

  // Already checked in
  if (status === 'already') {
    return (
      <div className="min-h-screen bg-royal-bg flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-8 max-w-md w-full text-center"
        >
          <div className="w-20 h-20 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-blue-400" />
          </div>
          
          <h1 className="font-cinzel font-bold text-2xl text-white mb-2">
            Already Checked In!
          </h1>
          <p className="text-white/60 mb-6">
            You've already checked in today, {user?.display_name}. Come back tomorrow for more points!
          </p>

          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-orange-400" />
              <span className="text-white">{user?.consecutive_visits || 0} night streak</span>
            </div>
          </div>

          <Button
            onClick={() => navigate('/dashboard')}
            className="btn-gold w-full"
            data-testid="go-to-dashboard-btn"
          >
            <Crown className="w-5 h-5 mr-2" />
            Go to Dashboard
          </Button>
        </motion.div>
      </div>
    );
  }

  // Error state
  return (
    <div className="min-h-screen bg-royal-bg flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-8 max-w-md w-full text-center"
      >
        <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
          <XCircle className="w-12 h-12 text-red-400" />
        </div>
        
        <h1 className="font-cinzel font-bold text-2xl text-white mb-2">
          Check-in Failed
        </h1>
        <p className="text-white/60 mb-6">
          {result?.message || 'The QR code may be invalid or expired. Please ask staff for assistance.'}
        </p>

        <div className="space-y-3">
          <Button
            onClick={() => navigate('/dashboard')}
            className="btn-gold w-full"
          >
            Go to Dashboard
          </Button>
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
            className="w-full border-white/20 text-white hover:bg-white/10"
          >
            Try Again
          </Button>
        </div>
      </motion.div>
    </div>
  );
};

export default CheckInPage;
