import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Eye, EyeOff, Sparkles, Crown, UserPlus } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_karaoke-kingdom/artifacts/ttig1x57_King%20Karaoke%203.png";

const RegisterPage = () => {
  const [searchParams] = useSearchParams();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [titlePreference, setTitlePreference] = useState('male');
  const [referralCode, setReferralCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();
  const redirectUrl = searchParams.get('redirect');

  // Check for referral code in URL
  useEffect(() => {
    const ref = searchParams.get('ref');
    if (ref) {
      setReferralCode(ref);
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      await register(email, password, displayName, titlePreference, referralCode || null);
      toast.success('Welcome to the Kingdom, noble Peasant!');
      // Redirect to the original destination or dashboard
      navigate(redirectUrl || '/dashboard');
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed. Please try again.';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-royal-bg flex items-center justify-center">
      {/* Centered Form */}
      <div className="w-full max-w-md flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 mb-8" data-testid="logo-link">
            <img src={LOGO_URL} alt="King Karaoke" className="w-16 h-16 object-contain" />
            <span className="font-cinzel font-bold text-2xl text-gold-gradient">King Klub</span>
          </Link>

          {/* Header */}
          <div className="mb-8">
            <h1 className="font-cinzel font-bold text-3xl text-white mb-2">Join the Kingdom</h1>
            <p className="text-white/60">Begin your journey to royal stardom</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Stage Name</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Your performer name"
                  required
                  data-testid="display-name-input"
                  className="w-full royal-input pl-12"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  data-testid="email-input"
                  className="w-full royal-input pl-12"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a password"
                  required
                  data-testid="password-input"
                  className="w-full royal-input pl-12 pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60"
                  data-testid="toggle-password-btn"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  data-testid="confirm-password-input"
                  className="w-full royal-input pl-12"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                <Crown className="inline w-4 h-4 mr-1 text-gold" />
                Royal Title Preference
              </label>
              <div className="flex gap-4">
                <label className={`flex-1 cursor-pointer p-3 rounded-lg border transition-all ${
                  titlePreference === 'male' 
                    ? 'border-gold bg-gold/10 text-gold' 
                    : 'border-white/20 text-white/60 hover:border-white/40'
                }`}>
                  <input
                    type="radio"
                    name="titlePreference"
                    value="male"
                    checked={titlePreference === 'male'}
                    onChange={(e) => setTitlePreference(e.target.value)}
                    className="sr-only"
                    data-testid="title-male-radio"
                  />
                  <span className="block text-center font-cinzel">
                    Squire / Knight / Count / Duke / Prince
                  </span>
                </label>
                <label className={`flex-1 cursor-pointer p-3 rounded-lg border transition-all ${
                  titlePreference === 'female' 
                    ? 'border-gold bg-gold/10 text-gold' 
                    : 'border-white/20 text-white/60 hover:border-white/40'
                }`}>
                  <input
                    type="radio"
                    name="titlePreference"
                    value="female"
                    checked={titlePreference === 'female'}
                    onChange={(e) => setTitlePreference(e.target.value)}
                    className="sr-only"
                    data-testid="title-female-radio"
                  />
                  <span className="block text-center font-cinzel">
                    Lady / Dame / Countess / Duchess / Princess
                  </span>
                </label>
              </div>
            </div>

            {/* Referral Code */}
            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                <UserPlus className="inline w-4 h-4 mr-1 text-gold" />
                Referral Code <span className="text-white/40">(optional)</span>
              </label>
              <div className="relative">
                <UserPlus className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="text"
                  value={referralCode}
                  onChange={(e) => setReferralCode(e.target.value)}
                  placeholder="Enter friend's referral code"
                  data-testid="referral-code-input"
                  className="w-full royal-input pl-12"
                />
              </div>
              {referralCode && (
                <p className="text-green-400 text-xs mt-1">Joining via referral link!</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              data-testid="register-submit-btn"
              className="w-full btn-gold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span>Creating Account...</span>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Begin My Journey</span>
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className="mt-8 text-center text-white/60">
            Already a member?{' '}
            <Link 
              to={redirectUrl ? `/login?redirect=${encodeURIComponent(redirectUrl)}` : '/login'}
              data-testid="login-link"
              className="text-gold hover:underline font-medium"
            >
              Sign In
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default RegisterPage;
