import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Clock } from 'lucide-react';

export function ProtectedRoute({ children, allowIncompleteOnboarding = false }) {
  const { user, profile, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F7F4] flex flex-col items-center justify-center space-y-3">
        <Clock className="w-8 h-8 text-[#64BC45] animate-spin" />
        <p className="text-sm text-[#788278] font-medium">Verifying active session...</p>
      </div>
    );
  }

  // Not logged in -> redirect to login (save destination for post-login return)
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const isOnboardingDone = profile?.onboarding_completed ?? user?.onboarding_completed ?? false;

  // Logged in but onboarding not done -> redirect to onboarding
  if (!isOnboardingDone && !allowIncompleteOnboarding) {
    return <Navigate to="/onboarding" replace />;
  }

  // If user completed onboarding but is trying to visit /onboarding directly, redirect to /dashboard
  if (isOnboardingDone && allowIncompleteOnboarding && location.pathname === '/onboarding') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export function PublicRoute({ children }) {
  const { user, profile, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F7F4] flex flex-col items-center justify-center space-y-3">
        <Clock className="w-8 h-8 text-[#64BC45] animate-spin" />
        <p className="text-sm text-[#788278] font-medium">Loading AtmosAI...</p>
      </div>
    );
  }

  if (user) {
    const isOnboardingDone = profile?.onboarding_completed ?? user?.onboarding_completed ?? false;
    if (isOnboardingDone) {
      return <Navigate to="/dashboard" replace />;
    } else {
      return <Navigate to="/onboarding" replace />;
    }
  }

  return children;
}

