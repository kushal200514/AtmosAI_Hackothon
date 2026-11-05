import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { 
  Wind, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  AlertCircle, 
  Clock, 
  ShieldCheck,
  KeyRound
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, resetPassword, authDisclaimer } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Forgot password modal state
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotStatus, setForgotStatus] = useState(null);
  const [forgotLoading, setForgotLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setLoading(true);
    try {
      const loggedUser = await signIn({
        email,
        password,
        rememberMe
      });

      // If user has not completed onboarding, resume onboarding
      if (!loggedUser.onboarding_completed) {
        navigate('/onboarding', { replace: true });
      } else {
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      }
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail.trim()) return;
    setForgotLoading(true);
    try {
      const res = await resetPassword(forgotEmail);
      setForgotStatus(res.message);
    } catch (err) {
      setForgotStatus('Error: ' + err.message);
    } finally {
      setForgotLoading(false);
    }
  };

  const handleQuickDemoFill = () => {
    setEmail('demo@atmosai.org');
    setPassword('DemoUser2026!');
  };

  return (
    <div className="min-h-screen bg-[#F5F7F4] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans selection:bg-[#64BC45] selection:text-white">
      {/* Disclaimer Banner */}
      {authDisclaimer && (
        <div className="max-w-md mx-auto w-full mb-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start space-x-2">
          <ShieldCheck className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <span>{authDisclaimer}</span>
        </div>
      )}

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div 
          onClick={() => navigate('/welcome')}
          className="inline-flex items-center space-x-2.5 cursor-pointer mb-3"
        >
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#469A36] to-[#64BC45] flex items-center justify-center text-white shadow-sm shadow-[#64BC45]/20">
            <Wind className="w-6 h-6 stroke-[2.2]" />
          </div>
          <span className="text-2xl font-black text-[#263329]">Atmos<span className="text-[#64BC45]">AI</span></span>
        </div>
        <h2 className="text-2xl font-extrabold text-[#263329] tracking-tight">Sign in to AtmosAI</h2>
        <p className="mt-1 text-xs text-[#788278]">
          Access your personalized environmental dashboard and saved air quality alerts.
        </p>

        {/* Quick Demo Pill */}
        <div className="mt-3">
          <button
            type="button"
            onClick={handleQuickDemoFill}
            className="text-[11px] font-bold text-[#469A36] bg-[#F1F8ED] border border-[#C2EBBA] px-3 py-1 rounded-full hover:bg-[#C2EBBA]/50 transition cursor-pointer"
          >
            Click to fill Demo Account (demo@atmosai.org)
          </button>
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-[#E8ECE7] rounded-3xl sm:px-10">
          {error && (
            <div className="mb-5 p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            {/* Email Address */}
            <div>
              <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@atmosai.org"
                className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] placeholder-[#788278]/60 focus:outline-none focus:border-[#64BC45] focus:ring-2 focus:ring-[#C2EBBA] transition"
              />
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-[#263329] uppercase tracking-wider">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setIsForgotPasswordOpen(true)}
                  className="text-xs text-[#469A36] font-semibold hover:underline"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-4 py-2.5 pr-10 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] placeholder-[#788278]/60 focus:outline-none focus:border-[#64BC45] focus:ring-2 focus:ring-[#C2EBBA] transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#788278] hover:text-[#263329]"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-[#E8ECE7] text-[#64BC45] focus:ring-[#64BC45]"
                />
                <span className="text-xs text-[#788278]">Remember me on this browser</span>
              </label>
            </div>

            {/* Submit */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-[#64BC45] hover:bg-[#469A36] text-white text-sm font-bold shadow-sm shadow-[#64BC45]/25 transition flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer"
              >
                {loading ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-[#E8ECE7] text-center">
            <p className="text-xs text-[#788278]">
              Don&apos;t have an account?{' '}
              <Link to="/signup" className="text-[#469A36] font-bold hover:underline">
                Sign Up
              </Link>
            </p>
          </div>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {isForgotPasswordOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-sm w-full p-6 border border-[#E8ECE7] shadow-xl">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-[#F1F8ED] text-[#469A36] flex items-center justify-center">
                <KeyRound className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-[#263329]">Reset Password</h3>
            </div>
            <p className="text-xs text-[#788278] mb-4">
              Enter your email address and we will provide password reset instructions.
            </p>

            {forgotStatus && (
              <div className="mb-4 p-3 rounded-xl bg-[#F1F8ED] border border-[#C2EBBA] text-xs text-[#263329]">
                {forgotStatus}
              </div>
            )}

            <form onSubmit={handleForgotPassword} className="space-y-3">
              <input
                type="email"
                required
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full px-3 py-2 rounded-xl border border-[#E8ECE7] text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
              />
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsForgotPasswordOpen(false);
                    setForgotStatus(null);
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[#788278] hover:bg-[#F5F7F4]"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-[#64BC45] text-white hover:bg-[#469A36]"
                >
                  {forgotLoading ? 'Sending...' : 'Send Link'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
