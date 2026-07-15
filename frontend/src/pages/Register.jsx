import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants';
import { parseError } from '../utils/errorParser';
import { Lock, Mail, User, Loader2, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast.error('All fields are required.');
      return;
    }
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register(name, email, password);
      toast.success('Account created successfully!');
      navigate(ROUTES.DASHBOARD);
    } catch (err) {
      toast.error(parseError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-white">Create an account</h1>
        <p className="text-xs text-dark-400 mt-1">Get started with StudyAI for high-impact study sessions</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full Name */}
        <div>
          <label className="block text-xs font-semibold text-dark-350 uppercase tracking-wider mb-2">Full Name</label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-dark-600 focus:outline-none focus:border-primary-500 transition-colors"
              required
            />
          </div>
        </div>

        {/* Email */}
        <div>
          <label className="block text-xs font-semibold text-dark-350 uppercase tracking-wider mb-2">Email Address</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-dark-600 focus:outline-none focus:border-primary-500 transition-colors"
              required
            />
          </div>
        </div>

        {/* Password */}
        <div>
          <label className="block text-xs font-semibold text-dark-350 uppercase tracking-wider mb-2">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="•••••••• (Min 6 chars)"
              className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-dark-600 focus:outline-none focus:border-primary-500 transition-colors"
              required
            />
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 text-white font-semibold py-3 px-4 rounded-xl shadow-lg hover:shadow-primary-600/20 transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Creating Account...</span>
            </>
          ) : (
            <>
              <span>Create Account</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="border-t border-dark-850 pt-4 text-center">
        <p className="text-xs text-dark-400">
          Already have an account?{' '}
          <Link to={ROUTES.LOGIN} className="text-primary-400 hover:text-primary-350 font-semibold transition-colors">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
