import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { Leaf, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import type { AxiosError } from 'axios';

// ─── Validation schemas ────────────────────────────────────────────
const loginSchema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(1, 'Password is required'),
});

const registerSchema = z.object({
  email: z.string().email('Valid email required'),
  username: z
    .string()
    .min(3, 'At least 3 characters')
    .max(30, 'Max 30 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Letters, numbers, _ and - only'),
  password: z
    .string()
    .min(8, 'At least 8 characters')
    .regex(/[A-Z]/, 'One uppercase letter required')
    .regex(/[a-z]/, 'One lowercase letter required')
    .regex(/\d/, 'One number required'),
  full_name: z.string().optional(),
});

type LoginForm = z.infer<typeof loginSchema>;
type RegisterForm = z.infer<typeof registerSchema>;

// ─── Shared Input Component ────────────────────────────────────────
function FormInput({
  label,
  id,
  type = 'text',
  placeholder,
  error,
  showToggle,
  onToggle,
  showPassword,
  ...rest
}: {
  label: string;
  id: string;
  type?: string;
  placeholder?: string;
  error?: string;
  showToggle?: boolean;
  onToggle?: () => void;
  showPassword?: boolean;
  [key: string]: unknown;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-white/70">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={showToggle ? (showPassword ? 'text' : 'password') : type}
          placeholder={placeholder}
          className={`w-full px-4 py-2.5 rounded-lg bg-white/5 border text-white placeholder-white/20 text-sm outline-none transition-all duration-200 focus:ring-2 focus:ring-emerald-500/50 ${
            error ? 'border-red-500/50' : 'border-white/10 focus:border-emerald-500/50'
          }`}
          {...rest}
        />
        {showToggle && (
          <button
            type="button"
            onClick={onToggle}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          {error}
        </p>
      )}
    </div>
  );
}

export default function AuthPage() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(
    searchParams.get('tab') === 'register' ? 'register' : 'login'
  );
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  // ─── Login Form ──────────────────────────────────────────────────
  const loginForm = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });
  const registerForm = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  async function onLogin(data: LoginForm) {
    setApiError(null);
    try {
      const res = await authService.login(data);
      setAuth(res.user, res.access_token);
      navigate('/dashboard');
    } catch (err) {
      const e = err as AxiosError<{ detail: string }>;
      setApiError(e.response?.data?.detail || 'Login failed. Please try again.');
    }
  }

  async function onRegister(data: RegisterForm) {
    setApiError(null);
    try {
      const res = await authService.register(data);
      setAuth(res.user, res.access_token);
      navigate('/dashboard');
    } catch (err) {
      const e = err as AxiosError<{ detail: string }>;
      setApiError(e.response?.data?.detail || 'Registration failed. Please try again.');
    }
  }

  return (
    <div className="min-h-screen bg-[#030a05] flex items-center justify-center px-4 py-12">
      {/* Background glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-emerald-500/5 blur-3xl" />
      </div>

      <motion.div
        className="relative w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-2 font-bold text-xl mb-8">
          <Leaf className="w-6 h-6 text-emerald-400" />
          <span className="gradient-text">CarbonTrack</span>
        </Link>

        <div className="glass rounded-2xl p-8">
          {/* Tab switcher */}
          <div className="flex rounded-lg bg-white/5 p-1 mb-8">
            {(['login', 'register'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => { setActiveTab(tab); setApiError(null); }}
                className={`flex-1 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  activeTab === tab
                    ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20'
                    : 'text-white/50 hover:text-white'
                }`}
                id={`auth-tab-${tab}`}
              >
                {tab === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          {/* API Error */}
          {apiError && (
            <motion.div
              className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400 text-sm"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {apiError}
            </motion.div>
          )}

          <AnimatePresence mode="wait">
            {activeTab === 'login' ? (
              <motion.form
                key="login"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                onSubmit={loginForm.handleSubmit(onLogin)}
                className="space-y-5"
                id="login-form"
              >
                <FormInput
                  label="Email"
                  id="login-email"
                  type="email"
                  placeholder="you@example.com"
                  error={loginForm.formState.errors.email?.message}
                  {...loginForm.register('email')}
                />
                <FormInput
                  label="Password"
                  id="login-password"
                  showToggle
                  showPassword={showPassword}
                  onToggle={() => setShowPassword((v) => !v)}
                  placeholder="••••••••"
                  error={loginForm.formState.errors.password?.message}
                  {...loginForm.register('password')}
                />
                <button
                  id="login-submit"
                  type="submit"
                  disabled={loginForm.formState.isSubmitting}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-semibold text-sm transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25"
                >
                  {loginForm.formState.isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : 'Sign in'}
                </button>
                <p className="text-center text-xs text-white/30">
                  No account?{' '}
                  <button
                    type="button"
                    onClick={() => setActiveTab('register')}
                    className="text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Create one
                  </button>
                </p>
              </motion.form>
            ) : (
              <motion.form
                key="register"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                onSubmit={registerForm.handleSubmit(onRegister)}
                className="space-y-5"
                id="register-form"
              >
                <FormInput
                  label="Email"
                  id="register-email"
                  type="email"
                  placeholder="you@example.com"
                  error={registerForm.formState.errors.email?.message}
                  {...registerForm.register('email')}
                />
                <FormInput
                  label="Username"
                  id="register-username"
                  placeholder="eco_hero"
                  error={registerForm.formState.errors.username?.message}
                  {...registerForm.register('username')}
                />
                <FormInput
                  label="Full name (optional)"
                  id="register-fullname"
                  placeholder="Alex Green"
                  {...registerForm.register('full_name')}
                />
                <FormInput
                  label="Password"
                  id="register-password"
                  showToggle
                  showPassword={showPassword}
                  onToggle={() => setShowPassword((v) => !v)}
                  placeholder="Min 8 chars, uppercase, number"
                  error={registerForm.formState.errors.password?.message}
                  {...registerForm.register('password')}
                />
                <button
                  id="register-submit"
                  type="submit"
                  disabled={registerForm.formState.isSubmitting}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-semibold text-sm transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25"
                >
                  {registerForm.formState.isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : 'Create account'}
                </button>
                <p className="text-center text-xs text-white/30">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => setActiveTab('login')}
                    className="text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Sign in
                  </button>
                </p>
              </motion.form>
            )}
          </AnimatePresence>
        </div>

        <p className="text-center text-xs text-white/20 mt-6">
          By continuing you agree to our Terms and Privacy Policy.
        </p>
      </motion.div>
    </div>
  );
}
