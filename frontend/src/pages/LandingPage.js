import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mic2, Trophy, Users, Star, ArrowRight, Sparkles, Crown } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_karaoke-kingdom/artifacts/ttig1x57_King%20Karaoke%203.png";

const features = [
  {
    icon: Crown,
    title: 'Rise Through the Ranks',
    description: 'Start as a Peasant and climb to royalty. Earn points with every performance.',
  },
  {
    icon: Trophy,
    title: 'Earn Badges & Rewards',
    description: 'Unlock achievements, collect badges, and claim real rewards at the venue.',
  },
  {
    icon: Mic2,
    title: 'Smart Song Queue',
    description: 'Join the queue from your phone. See wait times and get notified when you\'re up.',
  },
  {
    icon: Users,
    title: 'Compete & Connect',
    description: 'Climb the leaderboard and become the ultimate King Karaoke champion.',
  },
];

const ranks = [
  { name: 'Peasant', points: '0+', color: 'bg-gray-500' },
  { name: 'Squire', points: '100+', color: 'bg-green-500' },
  { name: 'Knight', points: '300+', color: 'bg-blue-500' },
  { name: 'Count', points: '600+', color: 'bg-purple-500' },
  { name: 'Duke', points: '1000+', color: 'bg-pink-500' },
  { name: 'Prince', points: '2000+', color: 'bg-gradient-to-r from-gold-start to-gold-end' },
];

const LandingPage = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-royal-bg">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1772537507935-065b8aba4df5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA3MDB8MHwxfHNlYXJjaHwxfHxsdXh1cnklMjBnb2xkJTIwY3Jvd24lMjB2ZWx2ZXQlMjByb3lhbCUyMGFlc3RoZXRpY3xlbnwwfHx8fDE3NzI5MjYyNTh8MA&ixlib=rb-4.1.0&q=85)',
            filter: 'brightness(0.3)'
          }}
        />
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-royal-bg/50 via-royal-bg/70 to-royal-bg" />

        {/* Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* Logo */}
            <div className="flex justify-center mb-6">
              <motion.img 
                src={LOGO_URL} 
                alt="King Karaoke" 
                className="w-48 h-48 sm:w-64 sm:h-64 object-contain drop-shadow-2xl"
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>

            {/* Main Title */}
            <h1 className="font-cinzel font-black text-4xl sm:text-5xl lg:text-6xl tracking-tight mb-6">
              <span className="text-white">Welcome to the</span>
              <br />
              <span className="text-gold-gradient">King Klub</span>
            </h1>

            {/* Subtitle */}
            <p className="font-playfair italic text-xl sm:text-2xl text-white/70 mb-8 max-w-2xl mx-auto">
              Where every performance earns your crown
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  data-testid="go-to-dashboard-btn"
                  className="btn-gold flex items-center gap-2"
                >
                  <span>Enter the Klub</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/register"
                    data-testid="get-started-btn"
                    className="btn-gold flex items-center gap-2"
                  >
                    <Sparkles className="w-5 h-5" />
                    <span>Join the Kingdom</span>
                  </Link>
                  <Link
                    to="/login"
                    data-testid="login-btn"
                    className="bg-white/5 border border-white/20 hover:bg-white/10 text-white backdrop-blur-md rounded-full px-8 py-3 font-medium transition-all"
                  >
                    Already a Member
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center pt-2">
            <div className="w-1.5 h-3 bg-gold rounded-full" />
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-4">
              Your Path to <span className="text-gold">Glory</span>
            </h2>
            <p className="text-white/60 max-w-xl mx-auto">
              King Klub rewards your passion for karaoke with points, badges, and exclusive perks.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-card p-8 hover:border-gold/30 transition-all group"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-gold/10 rounded-xl group-hover:bg-gold/20 transition-colors">
                      <Icon className="w-6 h-6 text-gold" />
                    </div>
                    <div>
                      <h3 className="font-cinzel font-bold text-xl text-white mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-white/60 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Ranks Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-royal-paper/30">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-4">
              The <span className="text-gold">Royal Ranks</span>
            </h2>
            <p className="text-white/60 max-w-xl mx-auto">
              Earn points with every song and rise through the nobility.
            </p>
          </motion.div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {ranks.map((rank, index) => (
              <motion.div
                key={rank.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="glass-card p-4 text-center group hover:scale-105 transition-transform"
              >
                <div className={`w-12 h-12 mx-auto mb-3 rounded-full ${rank.color} flex items-center justify-center`}>
                  <Star className={`w-6 h-6 ${rank.name === 'Prince' ? 'text-black' : 'text-white'}`} />
                </div>
                <h3 className="font-cinzel font-bold text-white text-sm mb-1">{rank.name}</h3>
                <p className="text-xs text-gold">{rank.points} pts</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-6">
              Ready to Claim Your <span className="text-gold">Throne?</span>
            </h2>
            <p className="text-white/60 mb-8 max-w-xl mx-auto">
              Join King Klub today and start earning points with every performance at King Karaoke.
            </p>
            {!isAuthenticated && (
              <Link
                to="/register"
                data-testid="cta-join-btn"
                className="btn-gold inline-flex items-center gap-2"
              >
                <Crown className="w-5 h-5" />
                <span>Begin Your Journey</span>
              </Link>
            )}
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-white/10">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src={LOGO_URL} alt="King Karaoke" className="w-10 h-10 object-contain" />
            <span className="font-cinzel font-bold text-white">King Klub</span>
          </div>
          <p className="text-white/40 text-sm">
            © 2024 King Karaoke. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
