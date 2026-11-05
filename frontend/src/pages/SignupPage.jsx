import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Wind, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  AlertCircle, 
  Clock, 
  ShieldCheck 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function SignupPage() {
  const navigate = useNavigate();
  const { signUp, authDisclaimer } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const validate = () => {
    if (!fullName.trim()) return 'Please enter your full name.';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) return 'Please provide a valid email address.';
    if (password.length < 6) return 'Password must be at least 6 characters long.';
    if (password !== confirmPassword) return 'Passwords do not match.';
    if (!agreedToTerms) return 'You must agree to the Terms of Service and Privacy Policy to proceed.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      await signUp({
        email,
        password,
        fullName
      });
      // Redirect to multi-step onboarding
      navigate('/onboarding', { replace: true });
    } catch (err) {
      console.error('Signup failed:', err);
      setError(err.message || 'Registration failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
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
        <h2 className="text-2xl font-extrabold text-[#263329] tracking-tight">Create your account</h2>
        <p className="mt-1 text-xs text-[#788278]">
          Join AtmosAI for personalized environmental safety and verified air quality forecasts.
        </p>
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
            {/* Full Name */}
            <div>
              <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Ananya Rao"
                className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] placeholder-[#788278]/60 focus:outline-none focus:border-[#64BC45] focus:ring-2 focus:ring-[#C2EBBA] transition"
              />
            </div>

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
                placeholder="ananya@example.com"
                className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] placeholder-[#788278]/60 focus:outline-none focus:border-[#64BC45] focus:ring-2 focus:ring-[#C2EBBA] transition"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
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

            {/* Confirm Password */}
            <div>
              <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  className="w-full px-4 py-2.5 pr-10 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] placeholder-[#788278]/60 focus:outline-none focus:border-[#64BC45] focus:ring-2 focus:ring-[#C2EBBA] transition"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#788278] hover:text-[#263329]"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Terms and conditions */}
            <div className="pt-1">
              <label className="flex items-start space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded border-[#E8ECE7] text-[#64BC45] focus:ring-[#64BC45]"
                />
                <span className="text-xs text-[#788278] leading-tight">
                  I agree to the <span className="text-[#469A36] font-semibold underline">Terms of Service</span> and acknowledge that AtmosAI offers non-medical environmental advisories based on CPCB standards.
                </span>
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
                    <span>Creating Profile...</span>
                  </>
                ) : (
                  <>
                    <span>Continue to Personalization</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-[#E8ECE7] text-center">
            <p className="text-xs text-[#788278]">
              Already have an account?{' '}
              <Link to="/login" className="text-[#469A36] font-bold hover:underline">
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
