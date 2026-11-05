import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute';
import WelcomePage from './pages/WelcomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import OnboardingPage from './pages/OnboardingPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import { Clock } from 'lucide-react';

function RootRedirector() {
  const { user, profile, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F7F4] flex flex-col items-center justify-center space-y-3">
        <Clock className="w-8 h-8 text-[#64BC45] animate-spin" />
        <p className="text-sm text-[#788278] font-medium">Loading AtmosAI...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/welcome" replace />;
  }

  const isCompleted = profile?.onboarding_completed ?? user?.onboarding_completed ?? false;
  if (!isCompleted) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Root Smart Redirect */}
          <Route path="/" element={<RootRedirector />} />

          {/* Public Auth Routes */}
          <Route 
            path="/welcome" 
            element={
              <PublicRoute>
                <WelcomePage />
              </PublicRoute>
            } 
          />
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } 
          />
          <Route 
            path="/signup" 
            element={
              <PublicRoute>
                <SignupPage />
              </PublicRoute>
            } 
          />

          {/* Protected Onboarding Route (allows incomplete onboarding to finish) */}
          <Route 
            path="/onboarding" 
            element={
              <ProtectedRoute allowIncompleteOnboarding={true}>
                <OnboardingPage />
              </ProtectedRoute>
            } 
          />

          {/* Protected Dashboard & Feature Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } 
          />

          {/* Fallback Catch-All */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
