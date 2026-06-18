import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Leaf, BarChart3, Cpu, Trophy, ArrowRight, ChevronDown, Globe } from 'lucide-react';

const features = [
  {
    icon: BarChart3,
    title: 'Carbon Calculator',
    description: 'Multi-category emission tracking using EPA & DEFRA verified emission factors across transport, energy, food, and shopping.',
  },
  {
    icon: Cpu,
    title: 'AI Sustainability Advisor',
    description: 'Personalized, numerically-grounded tips powered by Groq AI — scoped to your actual footprint data.',
  },
  {
    icon: Trophy,
    title: 'Gamified Eco Habits',
    description: 'Daily habit streaks, XP rewards, achievement badges, and a community leaderboard to keep you motivated.',
  },
  {
    icon: Globe,
    title: 'Analytics Dashboard',
    description: 'Recharts-powered visualizations of your carbon trend over time, category breakdown, and eco score progression.',
  },
];

const stats = [
  { value: '4.8T', label: 'kg CO₂ global avg/year' },
  { value: '2.0T', label: 'kg Paris Climate Target' },
  { value: '60%', label: 'reduction achievable' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#030a05] text-white overflow-x-hidden">
      {/* ── Navbar ─────────────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-6 py-4 border-b border-white/5 backdrop-blur-md bg-black/20">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <Leaf className="w-6 h-6 text-emerald-400" />
          <span className="gradient-text">CarbonTrack</span>
        </Link>
        <div className="flex items-center gap-4">
          <Link
            to="/auth"
            className="text-sm text-white/60 hover:text-white transition-colors"
          >
            Sign in
          </Link>
          <Link
            to="/auth?tab=register"
            className="text-sm px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-semibold transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-24 px-6 bg-mesh">
        {/* Background glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-emerald-500/5 blur-3xl" />
          <div className="absolute top-1/2 left-1/4 w-[300px] h-[300px] rounded-full bg-teal-500/5 blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Powered by Groq AI + EPA/DEFRA Data
            </span>
          </motion.div>

          <motion.h1
            className="text-5xl md:text-7xl font-extrabold leading-tight mb-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            Track your
            <br />
            <span className="gradient-text">carbon footprint</span>
            <br />
            and act on it.
          </motion.h1>

          <motion.p
            className="text-lg text-white/60 max-w-2xl mx-auto mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
          >
            Calculate your emissions, get AI-personalized sustainability advice,
            track eco-habits with gamification, and visualize your progress over time.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
          >
            <Link
              to="/calculator"
              className="group flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-base transition-all duration-200 glow-emerald hover:scale-[1.02]"
            >
              Calculate my footprint
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/auth"
              className="flex items-center justify-center gap-2 px-8 py-4 rounded-xl border border-white/10 hover:border-white/20 text-white/80 hover:text-white font-medium text-base transition-all duration-200 hover:bg-white/5"
            >
              Sign in to save results
            </Link>
          </motion.div>

          {/* Animated Carbon Meter */}
          <motion.div
            className="mt-16 glass rounded-2xl p-8 max-w-md mx-auto glow-emerald"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.5 }}
          >
            <p className="text-xs text-white/40 uppercase tracking-widest mb-3">Your Eco Score</p>
            <div className="relative flex items-center justify-center">
              <svg viewBox="0 0 200 120" className="w-48 h-auto">
                {/* Background arc */}
                <path
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke="#1a2e1a"
                  strokeWidth="16"
                  strokeLinecap="round"
                />
                {/* Score arc */}
                <motion.path
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke="url(#scoreGradient)"
                  strokeWidth="16"
                  strokeLinecap="round"
                  strokeDasharray="251.2"
                  initial={{ strokeDashoffset: 251.2 }}
                  animate={{ strokeDashoffset: 251.2 * 0.3 }}
                  transition={{ duration: 1.5, delay: 0.8, ease: 'easeOut' }}
                />
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="100%" stopColor="#2dd4bf" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute bottom-4 text-center">
                <motion.span
                  className="text-4xl font-extrabold gradient-text"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.2 }}
                >
                  72
                </motion.span>
                <p className="text-xs text-white/40 mt-1">Eco Conscious</p>
              </div>
            </div>
          </motion.div>
        </div>

        <motion.div
          className="flex justify-center mt-12"
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <ChevronDown className="w-5 h-5 text-white/20" />
        </motion.div>
      </section>

      {/* ── Stats ──────────────────────────────────────────────── */}
      <section className="py-16 px-6 border-y border-white/5">
        <div className="max-w-4xl mx-auto grid grid-cols-3 gap-8">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              className="text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <p className="text-3xl md:text-4xl font-extrabold gradient-text">{stat.value}</p>
              <p className="text-sm text-white/40 mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything you need to
              <span className="gradient-text"> go green</span>
            </h2>
            <p className="text-white/50 max-w-xl mx-auto">
              Built on verified emission factors, not guesswork. Every number is auditable.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                className="group p-6 rounded-2xl border border-white/5 bg-white/2 hover:border-emerald-500/20 hover:bg-emerald-500/3 transition-all duration-300"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
                    <feature.icon className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-sm text-white/50 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <motion.div
          className="max-w-2xl mx-auto text-center glass rounded-3xl p-12 glow-emerald"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <Leaf className="w-12 h-12 text-emerald-400 mx-auto mb-6 animate-float" />
          <h2 className="text-3xl font-bold mb-4">Ready to take action?</h2>
          <p className="text-white/50 mb-8">
            Join thousands of users tracking their footprint and making a real difference.
          </p>
          <Link
            to="/auth?tab=register"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold transition-all duration-200 hover:scale-105"
          >
            Start for free
            <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="py-8 px-6 border-t border-white/5 text-center">
        <p className="text-white/20 text-sm">
          © {new Date().getFullYear()} CarbonTrack · Emission factors sourced from EPA & DEFRA ·{' '}
          <Link to="/auth" className="hover:text-white/40 transition-colors">Sign in</Link>
        </p>
      </footer>
    </div>
  );
}
