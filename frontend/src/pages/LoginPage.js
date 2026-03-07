import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_karaoke-kingdom/artifacts/ttig1x57_King%20Karaoke%203.png";

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(email, password);
      toast.success('Welcome back to the Kingdom!');
      navigate('/dashboard');
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed. Please try again.';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-royal-bg flex">
      {/* Left Side - Image */}
      <div className="hidden lg:block lg:w-1/2 relative">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1703353312021-a1965f5a7ddd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwxfHxrYXJhb2tlJTIwbWljcm9waG9uZSUyMHN0YWdlJTIwbGlnaHRzJTIwZGFyayUyMGF0bW9zcGhlcmV8ZW58MHx8fHwxNzcyOTI2MjU3fDA&ixlib=rb-4.1.0&q=85)',
            filter: 'brightness(0.4)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-royal-bg via-royal-bg/50 to-transparent" />
        <div className="absolute bottom-12 left-12 right-12">
          <h2 className="font-cinzel font-bold text-4xl text-white mb-4">
            The Stage <span className="text-gold">Awaits</span>
          </h2>
          <p className="text-white/70 font-playfair italic text-lg">
            Every voice deserves to be heard. Claim your spotlight.
          </p>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
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
            <h1 className="font-cinzel font-bold text-3xl text-white mb-2">Welcome Back</h1>
            <p className="text-white/60">Sign in to continue your royal journey</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
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
                  placeholder="Enter your password"
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

            <button
              type="submit"
              disabled={loading}
              data-testid="login-submit-btn"
              className="w-full btn-gold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span>Entering...</span>
              ) : (
                <>
                  <span>Enter the Kingdom</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          {/* Register Link */}
          <p className="mt-8 text-center text-white/60">
            New to the Kingdom?{' '}
            <Link 
              to="/register" 
              data-testid="register-link"
              className="text-gold hover:underline font-medium"
            >
              Join Now
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
