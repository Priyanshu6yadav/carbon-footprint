import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

// ─── Lazy-loaded pages (code splitting) ───────────────────────────
const LandingPage    = lazy(() => import('@/pages/LandingPage'));
const AuthPage       = lazy(() => import('@/pages/AuthPage'));
const CalculatorPage = lazy(() => import('@/pages/CalculatorPage'));
const ResultsPage    = lazy(() => import('@/pages/ResultsPage'));
const DashboardPage  = lazy(() => import('@/pages/DashboardPage'));
const NotFoundPage   = lazy(() => import('@/pages/NotFoundPage'));

// ─── Global loading fallback ──────────────────────────────────────
function PageLoader() {
  return (
    <div className="min-h-screen bg-[#030a05] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/calculator" element={<CalculatorPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          {/* 404 — explicit not-found page instead of silent redirect */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
