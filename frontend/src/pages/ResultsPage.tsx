import { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { Leaf, Car, Zap, Salad, ShoppingBag, Save, Loader2, ArrowLeft, TrendingDown } from 'lucide-react';
import { calculatorService } from '@/services/calculatorService';
import { useAuthStore } from '@/store/authStore';
import type { CalculationResult, CalculatorInput } from '@/types';

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#a855f7'];

function formatKg(kg: number): string {
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)}t`;
  return `${kg.toFixed(0)} kg`;
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: { fill: string } }>;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg p-3 text-sm">
        <p className="font-semibold text-white">{payload[0].name}</p>
        <p className="text-emerald-400">{formatKg(payload[0].value)} CO₂e/month</p>
      </div>
    );
  }
  return null;
};

export default function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const input = location.state?.input as CalculatorInput | undefined;

  useEffect(() => {
    if (!input) {
      navigate('/calculator');
      return;
    }
    calculatorService
      .calculate(input)
      .then(setResult)
      .catch(() => setError('Failed to calculate. Please try again.'))
      .finally(() => setIsLoading(false));
  }, [input, navigate]);

  async function handleSave() {
    if (!input) return;
    setIsSaving(true);
    setError(null);
    try {
      await calculatorService.save(input);
      setSaved(true);
      // Wait a tiny bit for the UI to show 'Saved!' then redirect
      setTimeout(() => navigate('/dashboard'), 600);
    } catch (err) {
      console.error(err);
      setError('Failed to save results.');
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#030a05] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
          <p className="text-white/40 text-sm">Calculating your footprint…</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-[#030a05] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'No data available.'}</p>
          <Link to="/calculator" className="text-emerald-400 hover:text-emerald-300">
            ← Go back
          </Link>
        </div>
      </div>
    );
  }

  const { breakdown, comparison } = result;

  const chartData = [
    { name: 'Transportation', value: breakdown.transportation_kg },
    { name: 'Home Energy', value: breakdown.home_energy_kg },
    { name: 'Food', value: breakdown.food_kg },
    { name: 'Shopping', value: breakdown.shopping_kg },
  ].filter((d) => d.value > 0);

  const categories = [
    { label: 'Transportation', value: breakdown.transportation_kg, Icon: Car, color: '#3b82f6' },
    { label: 'Home Energy', value: breakdown.home_energy_kg, Icon: Zap, color: '#f59e0b' },
    { label: 'Food', value: breakdown.food_kg, Icon: Salad, color: '#10b981' },
    { label: 'Shopping', value: breakdown.shopping_kg, Icon: ShoppingBag, color: '#a855f7' },
  ];

  return (
    <div className="min-h-screen bg-[#030a05] text-white py-12 px-4">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] rounded-full bg-emerald-500/4 blur-3xl" />
      </div>

      <div className="relative max-w-4xl mx-auto">
        {/* Back + Save */}
        <div className="flex items-center justify-between mb-8">
          <Link
            to="/calculator"
            className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Recalculate
          </Link>
          {isAuthenticated ? (
            <button
              id="save-results-btn"
              onClick={handleSave}
              disabled={isSaving || saved}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-semibold text-sm transition-all duration-200"
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : saved ? (
                <Save className="w-4 h-4" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {saved ? 'Saved! Redirecting...' : 'Save & View Dashboard'}
            </button>
          ) : (
            <Link
              to="/auth"
              className="flex items-center gap-2 px-5 py-2 rounded-lg border border-emerald-500/30 text-emerald-400 text-sm font-medium hover:border-emerald-500/60 transition-colors"
            >
              Sign in to save
            </Link>
          )}
        </div>

        {/* Hero total */}
        <motion.div
          className="glass rounded-2xl p-8 mb-6 text-center glow-emerald"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Leaf className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
          <p className="text-sm text-white/40 uppercase tracking-widest mb-2">
            Your Monthly Carbon Footprint
          </p>
          <p className="text-6xl font-extrabold gradient-text mb-1">
            {formatKg(breakdown.total_monthly_kg)}
          </p>
          <p className="text-sm text-white/40">
            CO₂ equivalent · {formatKg(breakdown.total_annual_kg)} per year
          </p>
          <p className="text-xs text-white/20 mt-2">
            Emission factors v{result.emission_factors_version} · EPA & DEFRA sourced
          </p>
        </motion.div>

        {/* Chart + Categories */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Pie chart */}
          <motion.div
            className="glass rounded-2xl p-6"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="font-semibold mb-4 text-white/80">Breakdown by category</h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {chartData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value) => (
                    <span className="text-xs text-white/60">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Category cards */}
          <motion.div
            className="space-y-3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            {categories.map(({ label, value, Icon, color }) => (
              <div
                key={label}
                className="flex items-center gap-4 p-4 rounded-xl border border-white/5 bg-white/2"
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${color}20`, borderColor: `${color}30`, border: '1px solid' }}
                >
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white/80">{label}</p>
                  <div className="mt-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: color }}
                      initial={{ width: 0 }}
                      animate={{
                        width: `${(value / breakdown.total_monthly_kg) * 100}%`,
                      }}
                      transition={{ delay: 0.5, duration: 0.8, ease: 'easeOut' }}
                    />
                  </div>
                </div>
                <span className="text-sm font-bold text-white/90 flex-shrink-0">
                  {formatKg(value)}
                </span>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Comparisons */}
        <motion.div
          className="glass rounded-2xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="font-semibold mb-4 text-white/80 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-emerald-400" />
            How you compare
          </h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              {
                label: 'vs Global avg',
                pct: comparison.your_vs_global_pct,
                base: formatKg(comparison.global_average_annual_kg),
              },
              {
                label: 'vs US avg',
                pct: comparison.your_vs_us_pct,
                base: formatKg(comparison.us_average_annual_kg),
              },
              {
                label: 'vs Paris target',
                pct: Math.round((breakdown.total_annual_kg / comparison.paris_target_annual_kg) * 100),
                base: formatKg(comparison.paris_target_annual_kg),
              },
            ].map(({ label, pct, base }) => (
              <div key={label} className="text-center p-4 rounded-xl bg-white/3 border border-white/5">
                <p className="text-xs text-white/40 mb-1">{label}</p>
                <p className={`text-2xl font-bold ${pct <= 100 ? 'text-emerald-400' : 'text-orange-400'}`}>
                  {pct}%
                </p>
                <p className="text-xs text-white/20 mt-1">avg: {base}/yr</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Next steps */}
        <motion.div
          className="mt-6 p-5 rounded-xl border border-emerald-500/15 bg-emerald-500/5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <p className="text-sm font-medium text-emerald-400 mb-2">Next steps</p>
          <p className="text-sm text-white/50">
            Sign in to save your results, track your footprint over time, get AI-powered sustainability
            tips, and earn eco badges through daily habit streaks.
          </p>
          {!isAuthenticated && (
            <Link
              to="/auth?tab=register"
              className="inline-flex items-center gap-1.5 mt-3 text-sm text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
            >
              Create a free account →
            </Link>
          )}
        </motion.div>
      </div>
    </div>
  );
}
