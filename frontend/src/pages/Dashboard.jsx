import React, { useEffect, useState } from 'react';
import { healthService } from '../services/healthService';
import { parseError } from '../utils/errorParser';
import { useAuth } from '../hooks/useAuth';
import { 
  CheckCircle, XCircle, AlertTriangle, BookOpen, 
  UploadCloud, BrainCircuit, CreditCard, Sparkles, 
  GraduationCap, Clock, Award
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../constants';

const Dashboard = () => {
  const { user } = useAuth();
  const [healthStatus, setHealthStatus] = useState('checking'); // checking, success, error
  const [healthData, setHealthData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await healthService.checkHealth();
        setHealthStatus('success');
        setHealthData(data);
      } catch (err) {
        setHealthStatus('error');
        setErrorMessage(parseError(err));
      }
    };
    fetchHealth();
  }, []);

  const stats = [
    { name: 'Uploaded Materials', value: '0 files', icon: UploadCloud, color: 'text-blue-400' },
    { name: 'Generated Quizzes', value: '0 created', icon: BrainCircuit, color: 'text-purple-400' },
    { name: 'Active Flashcards', value: '0 cards', icon: CreditCard, color: 'text-emerald-400' },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-primary-900/40 via-primary-850/20 to-dark-900 border border-primary-500/20">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Welcome back, {user?.name || 'Student'}! <Sparkles className="w-6 h-6 text-primary-400 animate-pulse" />
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm md:text-base">
            Ready to supercharge your study session with AI? Upload your lecture notes or textbooks to start.
          </p>
        </div>
        <Link 
          to={ROUTES.UPLOAD} 
          className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-medium shadow-lg hover:shadow-primary-600/30 transition-all duration-200"
        >
          <UploadCloud className="w-5 h-5" />
          <span>Upload Material</span>
        </Link>
      </div>

      {/* Connection Status Banner (Requirement 12) */}
      <div className="rounded-xl border p-4 backdrop-blur-sm transition-all duration-300">
        {healthStatus === 'checking' && (
          <div className="flex items-center gap-3 text-dark-300">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-dark-400 border-t-transparent"></div>
            <span className="text-sm font-medium">Checking server connectivity...</span>
          </div>
        )}

        {healthStatus === 'success' && (
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-3 text-emerald-400 bg-emerald-950/20 px-3 py-1.5 rounded-lg border border-emerald-500/10">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-semibold tracking-wide">Backend Connected Successfully</span>
            </div>
            <span className="text-xs text-dark-400 font-mono">
              Server Version: {healthData?.version || '1.0.0'}
            </span>
          </div>
        )}

        {healthStatus === 'error' && (
          <div className="flex items-center gap-3 text-red-400 bg-red-950/20 p-3 rounded-lg border border-red-500/10">
            <XCircle className="w-5 h-5 flex-shrink-0" />
            <div className="flex-1">
              <span className="text-sm font-semibold block">Connection Failure</span>
              <span className="text-xs text-red-300/80">{errorMessage}</span>
            </div>
          </div>
        )}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between hover:border-dark-800 transition-all duration-200">
            <div>
              <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">{stat.name}</p>
              <h3 className="text-2xl font-bold text-white mt-2">{stat.value}</h3>
            </div>
            <div className={`p-3 rounded-xl bg-dark-850 ${stat.color}`}>
              <stat.icon className="w-6 h-6" />
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity / Next Steps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Quick Tools */}
        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-primary-400" />
            Quick Learning Shortcuts
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link 
              to={ROUTES.QUIZ} 
              className="p-4 rounded-xl bg-dark-850 border border-dark-800 hover:border-primary-500/30 transition-all duration-200 text-left group"
            >
              <h3 className="text-sm font-bold text-white group-hover:text-primary-400 transition-colors">Start Quiz</h3>
              <p className="text-xs text-dark-450 mt-1">Test your recall on saved topics.</p>
            </Link>
            <Link 
              to={ROUTES.FLASHCARDS} 
              className="p-4 rounded-xl bg-dark-850 border border-dark-800 hover:border-primary-500/30 transition-all duration-200 text-left group"
            >
              <h3 className="text-sm font-bold text-white group-hover:text-primary-400 transition-colors">Review Flashcards</h3>
              <p className="text-xs text-dark-450 mt-1">Active recall with generated cards.</p>
            </Link>
            <Link 
              to={ROUTES.SUMMARY} 
              className="p-4 rounded-xl bg-dark-850 border border-dark-800 hover:border-primary-500/30 transition-all duration-200 text-left group"
            >
              <h3 className="text-sm font-bold text-white group-hover:text-primary-400 transition-colors">AI Summaries</h3>
              <p className="text-xs text-dark-450 mt-1">Review key notes from uploaded docs.</p>
            </Link>
            <Link 
              to={ROUTES.SCHEDULE} 
              className="p-4 rounded-xl bg-dark-850 border border-dark-800 hover:border-primary-500/30 transition-all duration-200 text-left group"
            >
              <h3 className="text-sm font-bold text-white group-hover:text-primary-400 transition-colors">Study Plan</h3>
              <p className="text-xs text-dark-450 mt-1">Check scheduled reminders and goals.</p>
            </Link>
          </div>
        </div>

        {/* Study Tip or Empty Activity Feed */}
        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex flex-col justify-between space-y-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-400" />
              Recent Activity
            </h2>
            <div className="mt-8 text-center py-6">
              <Award className="w-12 h-12 text-dark-600 mx-auto mb-3" />
              <p className="text-sm text-dark-400 font-medium">No recent learning activity.</p>
              <p className="text-xs text-dark-500 mt-1 max-w-xs mx-auto">
                Once you start quizzes or generate study material, your performance data will appear here.
              </p>
            </div>
          </div>
          <div className="p-3 bg-primary-950/20 border border-primary-500/10 rounded-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-primary-350 leading-relaxed">
              <strong>Tip:</strong> Upload files with text (.pdf, .docx) for best AI processing. Slides with text can also be scanned.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
