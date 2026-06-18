import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Leaf, Home, ArrowLeft } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-[#030a05] text-white flex items-center justify-center px-4">
      {/* Background glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-emerald-500/5 blur-3xl" />
      </div>

      <motion.div
        className="relative text-center max-w-md"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Logo */}
        <Link to="/" className="inline-flex items-center gap-2 font-bold text-xl mb-10">
          <Leaf className="w-6 h-6 text-emerald-400" />
          <span className="gradient-text">CarbonTrack</span>
        </Link>

        {/* 404 display */}
        <div className="glass rounded-3xl p-12 glow-emerald mb-8">
          <motion.p
            className="text-[6rem] font-extrabold gradient-text leading-none mb-4 select-none"
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.6, type: 'spring', bounce: 0.3 }}
          >
            404
          </motion.p>
          <h1 className="text-2xl font-bold mb-3">Page not found</h1>
          <p className="text-white/50 text-sm leading-relaxed">
            This page doesn't exist or may have been moved.
            Head back to a known destination below.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/"
            id="not-found-home-btn"
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-sm transition-all duration-200 hover:scale-[1.02]"
          >
            <Home className="w-4 h-4" />
            Back to home
          </Link>
          <Link
            to="/calculator"
            id="not-found-calculator-btn"
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-white/10 hover:border-white/20 text-white/70 hover:text-white font-medium text-sm transition-all duration-200 hover:bg-white/5"
          >
            <ArrowLeft className="w-4 h-4" />
            Go to calculator
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
