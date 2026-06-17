import { useEffect, useState, useMemo, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
} from 'recharts';
import {
  Leaf,
  BarChart3,
  Calculator,
  LogOut,
  User as UserIcon,
  Calendar,
  Download,
  Loader2,
  AlertCircle,
  TrendingUp,
  Award,
  CheckCircle,
  MessageSquare,
  X,
  Send,
  Sparkles,
  Zap,
} from 'lucide-react';

import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import {
  analyticsService,
  type CarbonTrendPoint,
  type CategoryBreakdownData,
  type HabitCompletionPoint,
  type EcoScoreTrendPoint,
} from '@/services/analyticsService';
import { aiService, type Challenge, type ChatMessage } from '@/services/aiService';

const BREAKDOWN_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#a855f7'];

function formatKg(kg: number): string {
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)}t`;
  return `${kg.toFixed(0)} kg`;
}

export default function DashboardPage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  // Date range state
  const [range, setRange] = useState<'week' | 'month' | 'year' | 'custom'>('month');
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  // Data states
  const [carbonTrend, setCarbonTrend] = useState<CarbonTrendPoint[]>([]);
  const [categoryBreakdown, setCategoryBreakdown] = useState<CategoryBreakdownData>({
    transport: 0,
    energy: 0,
    food: 0,
    shopping: 0,
  });
  const [habitCompletion, setHabitCompletion] = useState<HabitCompletionPoint[]>([]);
  const [ecoScoreTrend, setEcoScoreTrend] = useState<EcoScoreTrendPoint[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);

  // UI state
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [generatingChallenges, setGeneratingChallenges] = useState(false);
  const [completingChallengeId, setCompletingChallengeId] = useState<string | null>(null);
  const [completionNotes, setCompletionNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [challengeMessage, setChallengeMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Chatbot state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hi! I'm your CarbonTrack green assistant. Ask me anything about reducing your carbon footprint or adopting eco-friendly habits!",
    },
  ]);
  const [userInput, setUserInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Fetch all analytics data & challenges
  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        range,
        start: range === 'custom' ? startDate : undefined,
        end: range === 'custom' ? endDate : undefined,
      };

      const [trend, breakdown, habits, ecoTrend, challengeList] = await Promise.all([
        analyticsService.getCarbonTrend(params),
        analyticsService.getCategoryBreakdown(params),
        analyticsService.getHabitCompletion(params),
        analyticsService.getEcoScoreTrend(params),
        aiService.listChallenges(),
      ]);

      setCarbonTrend(trend);
      setCategoryBreakdown(breakdown);
      setHabitCompletion(habits);
      setEcoScoreTrend(ecoTrend);
      setChallenges(challengeList);
    } catch (err: any) {
      console.error(err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Trigger fetch on range change
  useEffect(() => {
    if (range !== 'custom') {
      fetchDashboardData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  // Initial load
  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Scroll chat to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isChatLoading]);

  async function handleLogout() {
    try {
      await authService.logout();
    } catch {
      // Ignore logout errors
    }
    logout();
    navigate('/');
  }

  const handleExportPdf = async () => {
    setExporting(true);
    try {
      const params = {
        range,
        start: range === 'custom' ? startDate : undefined,
        end: range === 'custom' ? endDate : undefined,
      };
      await analyticsService.downloadPdfReport(params);
    } catch (err) {
      console.error(err);
      alert('Failed to generate report. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const handleGenerateChallenges = async () => {
    setGeneratingChallenges(true);
    setChallengeMessage(null);
    try {
      const newChallenges = await aiService.generateChallenges();
      setChallenges(newChallenges);
      setChallengeMessage({ type: 'success', text: 'Personalized challenges generated successfully!' });
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail || 'Failed to generate challenges.';
      setChallengeMessage({ type: 'error', text: detail });
    } finally {
      setGeneratingChallenges(false);
    }
  };

  const handleCompleteChallenge = async (challengeId: string) => {
    try {
      await aiService.completeChallenge(challengeId, completionNotes);
      
      // Update XP & level deterministically by reloading profile details
      const updatedUser = await authService.me();
      useAuthStore.setState({ user: updatedUser });

      // Refresh challenge list and reset completion UI
      const list = await aiService.listChallenges();
      setChallenges(list);
      setCompletingChallengeId(null);
      setCompletionNotes('');
      setChallengeMessage({ type: 'success', text: 'Challenge completed! XP awarded.' });
    } catch (err: any) {
      console.error(err);
      alert('Failed to complete challenge.');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const userMsg = userInput.trim();
    const newHistory = [...chatMessages, { role: 'user', content: userMsg } as ChatMessage];
    
    setChatMessages(newHistory);
    setUserInput('');
    setIsChatLoading(true);

    try {
      // Send chat history and current message
      const response = await aiService.chatSustainability(userMsg, chatMessages);
      setChatMessages([...newHistory, { role: 'assistant', content: response.reply }]);
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || 'Unable to communicate with the assistant. Please try again.';
      setChatMessages([
        ...newHistory,
        { role: 'assistant', content: `⚠️ Error: ${errMsg}` },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Summaries
  const totalCarbon = useMemo(() => {
    return (
      categoryBreakdown.transport +
      categoryBreakdown.energy +
      categoryBreakdown.food +
      categoryBreakdown.shopping
    );
  }, [categoryBreakdown]);

  const avgEcoScore = useMemo(() => {
    if (ecoScoreTrend.length === 0) return 0;
    const sum = ecoScoreTrend.reduce((acc, curr) => acc + curr.score, 0);
    return Math.round(sum / ecoScoreTrend.length);
  }, [ecoScoreTrend]);

  const completedHabitsCount = useMemo(() => {
    return habitCompletion.reduce((acc, curr) => acc + curr.logged_days, 0);
  }, [habitCompletion]);

  // Empty state checking
  const isCarbonTrendEmpty = carbonTrend.length === 0 || carbonTrend.every((d) => d.total === 0);
  const isBreakdownEmpty = totalCarbon === 0;
  const isHabitsEmpty = habitCompletion.length === 0 || habitCompletion.every((h) => h.logged_days === 0);
  const isEcoTrendEmpty = ecoScoreTrend.length === 0;

  const EmptyState = ({ message }: { message: string }) => (
    <div className="flex flex-col items-center justify-center h-[220px] text-center px-4">
      <AlertCircle className="w-8 h-8 text-white/20 mb-2" />
      <p className="text-sm text-white/40 mb-3">{message}</p>
      <Link
        to="/calculator"
        id="dashboard-log-activity-btn"
        className="text-xs px-3 py-1.5 rounded-lg border border-emerald-500/30 text-emerald-400 font-medium hover:bg-emerald-500/10 transition-colors"
      >
        Log Activity
      </Link>
    </div>
  );

  const pieChartData = [
    { name: 'Transportation', value: categoryBreakdown.transport },
    { name: 'Home Energy', value: categoryBreakdown.energy },
    { name: 'Food', value: categoryBreakdown.food },
    { name: 'Shopping', value: categoryBreakdown.shopping },
  ].filter((d) => d.value > 0);

  return (
    <div className="min-h-screen bg-[#030a05] text-white">
      {/* Background decorations */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-emerald-500/2 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-[350px] h-[350px] rounded-full bg-teal-500/2 blur-3xl" />
      </div>

      {/* Navbar */}
      <nav className="relative flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#030a05]/80 backdrop-blur-md z-10">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <Leaf className="w-6 h-6 text-emerald-400" />
          <span className="gradient-text">CarbonTrack</span>
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-sm text-white/40 flex items-center gap-1.5">
            <UserIcon className="w-4 h-4" />
            {user?.username}
          </span>
          <button
            onClick={handleLogout}
            id="logout-btn"
            className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      </nav>

      {/* Content */}
      <main className="relative max-w-5xl mx-auto px-6 py-12 z-10">
        {/* Welcome header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-10">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              Welcome back, <span className="gradient-text">{user?.full_name || user?.username}</span> 👋
            </h1>
            <p className="text-white/40">
              Track your footprint, log habits, and review your environmental metrics.
            </p>
          </div>

          <Link
            to="/calculator"
            id="dashboard-calculator-link"
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-semibold text-sm transition-all shadow-lg hover:shadow-emerald-500/10"
          >
            <Calculator className="w-4 h-4" /> New Calculation
          </Link>
        </div>

        {/* Level and XP Badge */}
        <div className="glass rounded-2xl p-6 mb-8 flex flex-col md:flex-row items-center justify-between gap-6 glow-emerald">
          <div className="flex-1 w-full">
            <div className="flex justify-between items-end mb-2">
              <div>
                <p className="text-xs text-white/40 uppercase tracking-widest mb-1">Total XP</p>
                <p className="text-4xl font-extrabold gradient-text">{user?.xp_total ?? 0}</p>
              </div>
              <span className="text-sm font-semibold text-white/60">Level {user?.level ?? 1}</span>
            </div>
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                style={{ width: `${(user?.xp_total ?? 0) % 100}%` }}
              />
            </div>
            <p className="text-xs text-white/30 mt-1.5">
              {100 - ((user?.xp_total ?? 0) % 100)} XP needed to level up
            </p>
          </div>
          <div className="text-5xl animate-float select-none">🌱</div>
        </div>

        {/* Personalized AI Challenges Section */}
        <div className="glass rounded-2xl p-6 mb-8 border-emerald-500/10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold">Personalized Eco-Challenges</h2>
            </div>
            <button
              onClick={handleGenerateChallenges}
              disabled={generatingChallenges}
              className="px-4 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-semibold border border-emerald-500/30 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              {generatingChallenges ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  <span>Generate Daily Challenges</span>
                </>
              )}
            </button>
          </div>

          {challengeMessage && (
            <div
              className={`p-3 rounded-lg mb-4 text-xs border flex items-center gap-2 ${
                challengeMessage.type === 'success'
                  ? 'bg-emerald-500/5 border-emerald-500/15 text-emerald-300'
                  : 'bg-red-500/5 border-red-500/15 text-red-300'
              }`}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{challengeMessage.text}</span>
            </div>
          )}

          {challenges.length === 0 ? (
            <div className="text-center py-6 text-sm text-white/40 border border-dashed border-white/5 rounded-xl">
              No active challenges. Click 'Generate Daily Challenges' to fetch personalized tasks!
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {challenges.map((c) => (
                <div key={c.id} className="p-4 rounded-xl border border-white/5 bg-white/2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-xs uppercase tracking-widest text-emerald-400 font-semibold">{c.difficulty}</span>
                      <span className="text-[10px] text-teal-400 bg-teal-500/10 border border-teal-500/20 px-2 py-0.5 rounded-full font-bold">+{c.xp_reward} XP</span>
                    </div>
                    <h4 className="font-bold text-sm mb-1">{c.title}</h4>
                    <p className="text-xs text-white/60 leading-relaxed mb-4">{c.description}</p>
                  </div>

                  <div className="mt-auto">
                    <div className="text-[10px] text-white/30 mb-3 font-semibold">
                      CO₂ saved: {c.co2_saved_estimate_kg.toFixed(1)} kg (est.)
                    </div>

                    {completingChallengeId === c.id ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          placeholder="Add completion notes (optional)"
                          value={completionNotes}
                          onChange={(e) => setCompletionNotes(e.target.value)}
                          className="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:border-emerald-500/50 text-white"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCompleteChallenge(c.id)}
                            className="flex-1 py-1 rounded bg-emerald-500 hover:bg-emerald-400 text-black text-[11px] font-bold transition-all cursor-pointer"
                          >
                            Submit
                          </button>
                          <button
                            onClick={() => setCompletingChallengeId(null)}
                            className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-white/60 text-[11px] transition-all cursor-pointer"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setCompletingChallengeId(c.id)}
                        className="w-full py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white font-semibold text-xs transition-all cursor-pointer text-center"
                      >
                        Complete Challenge
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Filters and Actions Bar */}
        <div className="glass rounded-2xl p-4 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <label htmlFor="dashboard-range-select" className="text-sm text-white/40 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-emerald-400" /> Range:
            </label>
            <select
              id="dashboard-range-select"
              value={range}
              onChange={(e) => setRange(e.target.value as any)}
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500/50 text-white cursor-pointer"
            >
              <option value="week" className="bg-[#0c130e]">Last Week</option>
              <option value="month" className="bg-[#0c130e]">Last Month</option>
              <option value="year" className="bg-[#0c130e]">Last Year</option>
              <option value="custom" className="bg-[#0c130e]">Custom Range</option>
            </select>
          </div>

          <button
            id="dashboard-export-pdf-btn"
            onClick={handleExportPdf}
            disabled={exporting || loading}
            className="flex items-center justify-center gap-2 px-4 py-1.5 rounded-lg border border-white/10 hover:border-emerald-500/40 hover:bg-emerald-500/5 text-sm font-medium transition-all w-full sm:w-auto cursor-pointer disabled:opacity-50"
          >
            {exporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                <span>Exporting Report...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4 text-emerald-400" />
                <span>Export PDF Report</span>
              </>
            )}
          </button>
        </div>

        {/* Custom Range Inputs */}
        {range === 'custom' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-4 mb-8 grid grid-cols-1 sm:grid-cols-3 gap-4 items-end"
          >
            <div>
              <label htmlFor="dashboard-start-date" className="block text-xs text-white/40 mb-1.5">Start Date</label>
              <input
                type="date"
                id="dashboard-start-date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500/50 text-white cursor-pointer"
              />
            </div>
            <div>
              <label htmlFor="dashboard-end-date" className="block text-xs text-white/40 mb-1.5">End Date</label>
              <input
                type="date"
                id="dashboard-end-date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-emerald-500/50 text-white cursor-pointer"
              />
            </div>
            <button
              id="dashboard-apply-dates-btn"
              onClick={fetchDashboardData}
              className="w-full py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-semibold text-sm transition-all cursor-pointer shadow-md"
            >
              Apply Dates
            </button>
          </motion.div>
        )}

        {/* Error state */}
        {error && (
          <div className="glass rounded-xl p-4 mb-8 border-red-500/20 bg-red-500/5 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-200">{error}</p>
          </div>
        )}

        {/* Aggregated KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="glass rounded-2xl p-5 border-white/5">
            <p className="text-xs text-white/40 uppercase tracking-widest mb-1">Total Carbon Footprint</p>
            <p className="text-2xl font-bold gradient-text">
              {loading ? '...' : formatKg(totalCarbon)}
            </p>
            <p className="text-[10px] text-white/30 mt-1">Sum of all categories in range</p>
          </div>

          <div className="glass rounded-2xl p-5 border-white/5">
            <p className="text-xs text-white/40 uppercase tracking-widest mb-1">Average Eco-Score</p>
            <p className="text-2xl font-bold text-emerald-400">
              {loading ? '...' : avgEcoScore > 0 ? `${avgEcoScore}/100` : 'No score'}
            </p>
            <p className="text-[10px] text-white/30 mt-1">Average calculated environmental rating</p>
          </div>

          <div className="glass rounded-2xl p-5 border-white/5">
            <p className="text-xs text-white/40 uppercase tracking-widest mb-1">Total Habits Logged</p>
            <p className="text-2xl font-bold text-teal-400">
              {loading ? '...' : `${completedHabitsCount} logs`}
            </p>
            <p className="text-[10px] text-white/30 mt-1">Number of habit entries submitted</p>
          </div>
        </div>

        {/* Analytics Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
            <p className="text-sm text-white/40">Loading analytics dashboards...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Carbon Trend Area Chart */}
            <div className="glass rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <h3 className="font-semibold text-sm text-white/80 mb-1 flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-emerald-400" /> Carbon Footprint Trend
                </h3>
                <p className="text-[11px] text-white/30 mb-4">Total emissions tracked over time</p>
              </div>

              {isCarbonTrendEmpty ? (
                <EmptyState message="No carbon logs found in this period. Use the calculator to log your footprint!" />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={carbonTrend}>
                    <defs>
                      <linearGradient id="colorCarbon" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="period"
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                      stroke="rgba(255,255,255,0.1)"
                    />
                    <YAxis
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                      stroke="rgba(255,255,255,0.1)"
                      unit="kg"
                    />
                    <RechartsTooltip
                      contentStyle={{
                        background: 'rgba(12, 19, 14, 0.9)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        borderRadius: '8px',
                      }}
                      labelStyle={{ color: 'rgba(255, 255, 255, 0.6)', fontWeight: 'bold' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="total"
                      stroke="#10b981"
                      fillOpacity={1}
                      fill="url(#colorCarbon)"
                      name="Emissions (kg CO₂e)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* 2. Category Breakdown Pie Chart */}
            <div className="glass rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <h3 className="font-semibold text-sm text-white/80 mb-1 flex items-center gap-1.5">
                  <BarChart3 className="w-4 h-4 text-emerald-400" /> Emissions Category Breakdown
                </h3>
                <p className="text-[11px] text-white/30 mb-4">Emissions share per activity type</p>
              </div>

              {isBreakdownEmpty ? (
                <EmptyState message="No category breakdown available. Perform a carbon calculation to populate categories." />
              ) : (
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <ResponsiveContainer width="100%" height={220} className="max-w-[200px]">
                    <PieChart>
                      <Pie
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {pieChartData.map((_, index) => (
                          <Cell key={index} fill={BREAKDOWN_COLORS[index % BREAKDOWN_COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip
                        contentStyle={{
                          background: 'rgba(12, 19, 14, 0.9)',
                          border: '1px solid rgba(16, 185, 129, 0.2)',
                          borderRadius: '8px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>

                  <div className="flex flex-col gap-2 flex-1">
                    {pieChartData.map((d, index) => {
                      const percentage = ((d.value / totalCarbon) * 100).toFixed(0);
                      return (
                        <div key={d.name} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-1.5">
                            <span
                              className="w-2.5 h-2.5 rounded-full"
                              style={{ backgroundColor: BREAKDOWN_COLORS[index % BREAKDOWN_COLORS.length] }}
                            />
                            <span className="text-white/60">{d.name}</span>
                          </div>
                          <span className="font-bold text-white/90">
                            {formatKg(d.value)} ({percentage}%)
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* 3. Habit Completion Bar Chart */}
            <div className="glass rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <h3 className="font-semibold text-sm text-white/80 mb-1 flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-emerald-400" /> Daily Habits Completion
                </h3>
                <p className="text-[11px] text-white/30 mb-4">Habit compliance rate in selected window</p>
              </div>

              {isHabitsEmpty ? (
                <EmptyState message="No habits completed. Log your daily habits to see completion stats!" />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={habitCompletion} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      type="number"
                      domain={[0, 1]}
                      tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                      stroke="rgba(255,255,255,0.1)"
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      width={100}
                      tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 9 }}
                      stroke="rgba(255,255,255,0.1)"
                    />
                    <RechartsTooltip
                      formatter={(value: any) => [`${(Number(value) * 100).toFixed(0)}%`, 'Completion Rate']}
                      contentStyle={{
                        background: 'rgba(12, 19, 14, 0.9)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="completion_rate" fill="#14b8a6" radius={[0, 4, 4, 0]}>
                      {habitCompletion.map((_, index) => (
                        <Cell key={index} fill={index % 2 === 0 ? '#10b981' : '#14b8a6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* 4. Eco Score Trend Line Chart */}
            <div className="glass rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <h3 className="font-semibold text-sm text-white/80 mb-1 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-emerald-400" /> Eco-Score Progression
                </h3>
                <p className="text-[11px] text-white/30 mb-4">Historical average eco rating scores</p>
              </div>

              {isEcoTrendEmpty ? (
                <EmptyState message="No eco-score history. Keep calculating to track your eco-score trend." />
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={ecoScoreTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="period"
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                      stroke="rgba(255,255,255,0.1)"
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                      stroke="rgba(255,255,255,0.1)"
                    />
                    <RechartsTooltip
                      contentStyle={{
                        background: 'rgba(12, 19, 14, 0.9)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        borderRadius: '8px',
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#2dd4bf"
                      strokeWidth={2}
                      dot={{ r: 3, stroke: '#2dd4bf', strokeWidth: 1, fill: '#030a05' }}
                      name="Eco Score (/100)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Floating Chat Widget Toggle */}
      <button
        onClick={() => setIsChatOpen(!isChatOpen)}
        className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-emerald-500 hover:bg-emerald-400 text-black shadow-xl hover:shadow-emerald-500/20 transition-all cursor-pointer flex items-center justify-center"
        title="Chat with CarbonTrack Assistant"
      >
        {isChatOpen ? <X className="w-6 h-6" /> : <MessageSquare className="w-6 h-6" />}
      </button>

      {/* Floating Chat Drawer */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 w-[360px] h-[480px] rounded-2xl glass border border-white/10 shadow-2xl flex flex-col z-50 overflow-hidden"
          >
            {/* Chat Header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-[#030a05]/60 backdrop-blur">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <div className="flex-1">
                <h4 className="font-bold text-xs">Sustainability Assistant</h4>
                <p className="text-[9px] text-white/40">Powered by Llama 3 on Groq</p>
              </div>
            </div>

            {/* Message History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#030a05]/30">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-emerald-500 text-black font-medium'
                        : 'bg-white/5 border border-white/5 text-white/95'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}

              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/5 border border-white/5 rounded-xl px-3 py-2 text-xs text-white/40 flex items-center gap-1.5">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input Form */}
            <form
              onSubmit={handleSendMessage}
              className="p-3 border-t border-white/5 bg-[#030a05]/60 backdrop-blur flex gap-2"
            >
              <input
                type="text"
                placeholder="Ask about footprint or green tips..."
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                disabled={isChatLoading}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-emerald-500/50 text-white disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isChatLoading || !userInput.trim()}
                className="p-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black disabled:opacity-40 transition-all flex items-center justify-center cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
