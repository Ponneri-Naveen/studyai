import React, { useEffect, useState } from 'react';
import { healthService } from '../services/healthService';
import { parseError } from '../utils/errorParser';
import { useAuth } from '../hooks/useAuth';
import { 
  CheckCircle, XCircle, AlertTriangle, BookOpen, 
  UploadCloud, BrainCircuit, CreditCard, Sparkles, 
  GraduationCap, Clock, Award, Trash2, Eye, X, FileText
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { ROUTES, API_ENDPOINTS } from '../constants';
import api from '../services/api';
import toast from 'react-hot-toast';
import AIStatusIndicator from '../components/ai/AIStatusIndicator';

const Dashboard = () => {
  const { user } = useAuth();
  const [healthStatus, setHealthStatus] = useState('checking'); // checking, success, error
  const [healthData, setHealthData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Materials tracking
  const [materials, setMaterials] = useState([]);
  const [materialsLoading, setMaterialsLoading] = useState(true);

  // Viewer state
  const [viewerMaterial, setViewerMaterial] = useState(null);
  const [isViewerLoading, setIsViewerLoading] = useState(false);

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
    fetchMaterials();
  }, []);

  const fetchMaterials = async () => {
    setMaterialsLoading(true);
    try {
      const response = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(response.data);
    } catch (err) {
      console.error('Failed to load dashboard materials:', err);
    } finally {
      setMaterialsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to permanently delete this material?')) {
      return;
    }
    try {
      await api.delete(`${API_ENDPOINTS.MATERIALS.BASE}/${id}`);
      toast.success('Material deleted successfully.');
      fetchMaterials();
    } catch (err) {
      toast.error('Failed to delete material: ' + parseError(err));
    }
  };

  const handleView = async (item) => {
    setIsViewerLoading(true);
    try {
      const response = await api.get(`${API_ENDPOINTS.MATERIALS.BASE}/${item.id}`);
      setViewerMaterial(response.data);
    } catch (err) {
      toast.error('Failed to load details: ' + parseError(err));
    } finally {
      setIsViewerLoading(false);
    }
  };

  // Sort by date (descending) and take top 3
  const recentMaterials = [...materials]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 3);

  const generatedSummariesCount = materials.filter(m => m.summary_generated || m.summary_status === 'generated').length;
  const generatedDecksCount = materials.filter(m => m.flashcards_generated).length;
  const generatedQuizzesCount = materials.filter(m => m.quiz_generated).length;

  const stats = [
    { 
      name: 'Uploaded Materials', 
      value: materialsLoading ? 'Loading...' : `${materials.length} file${materials.length === 1 ? '' : 's'}`, 
      icon: UploadCloud, 
      color: 'text-blue-400' 
    },
    { 
      name: 'Generated Summaries', 
      value: materialsLoading ? 'Loading...' : `${generatedSummariesCount} summary${generatedSummariesCount === 1 ? '' : 'ies'}`, 
      icon: BookOpen, 
      color: 'text-purple-400' 
    },
    { 
      name: 'Active Flashcard Decks', 
      value: materialsLoading ? 'Loading...' : `${generatedDecksCount} deck${generatedDecksCount === 1 ? '' : 's'}`, 
      icon: CreditCard, 
      color: 'text-emerald-400' 
    },
    { 
      name: 'Active Quiz Sheets', 
      value: materialsLoading ? 'Loading...' : `${generatedQuizzesCount} quiz${generatedQuizzesCount === 1 ? '' : 'zes'}`, 
      icon: BrainCircuit, 
      color: 'text-primary-400' 
    },
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

      {/* Connection Status Banner (Requirement 12) & AI Status Indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-dark-850/60 bg-dark-900/20 backdrop-blur-sm">
        <div className="flex-grow">
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
        <div className="flex-shrink-0 border-t md:border-t-0 md:border-l border-dark-850 pt-3 md:pt-0 md:pl-4 flex items-center">
          <AIStatusIndicator />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
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
              to={ROUTES.ANALYSIS} 
              className="p-4 rounded-xl bg-dark-850 border border-dark-800 hover:border-primary-500/30 transition-all duration-200 text-left group"
            >
              <h3 className="text-sm font-bold text-white group-hover:text-primary-400 transition-colors">Weak Topic Analyzer</h3>
              <p className="text-xs text-dark-450 mt-1">Diagnose performance gaps across tests.</p>
            </Link>
          </div>
        </div>

        {/* Recent Uploads widget */}
        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex flex-col justify-between space-y-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-400" />
              Recent Uploads
            </h2>
            
            {materialsLoading ? (
              <div className="py-8 text-center text-xs text-dark-500 animate-pulse">
                Fetching recent uploads...
              </div>
            ) : recentMaterials.length === 0 ? (
              <div className="mt-8 text-center py-6">
                <Award className="w-12 h-12 text-dark-600 mx-auto mb-3" />
                <p className="text-sm text-dark-400 font-medium">No uploaded files yet.</p>
                <p className="text-xs text-dark-500 mt-1 max-w-xs mx-auto">
                  Use the Upload page to ingest files and start analyzing your material.
                </p>
              </div>
            ) : (
              <div className="mt-4 space-y-3">
                {recentMaterials.map((item) => (
                  <div 
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-dark-850 border border-dark-800"
                  >
                    <div className="flex items-center gap-2.5 truncate mr-2">
                      <FileText className="w-4 h-4 text-primary-400 flex-shrink-0" />
                      <div className="truncate">
                        <p className="text-xs font-bold text-white truncate max-w-[160px] sm:max-w-[200px]" title={item.title}>
                          {item.title}
                        </p>
                        <span className="text-[9px] text-dark-450">
                          {item.subject} • {item.word_count} words
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex gap-1.5 flex-shrink-0">
                      <button 
                        onClick={() => handleView(item)}
                        className="p-1 rounded bg-dark-900 text-dark-300 hover:text-white transition-colors cursor-pointer"
                        title="Quick View"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button 
                        onClick={() => handleDelete(item.id)}
                        className="p-1 rounded bg-dark-900 text-red-400 hover:text-red-300 transition-colors cursor-pointer"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="p-3 bg-primary-950/20 border border-primary-500/10 rounded-xl flex items-start gap-3 mt-auto">
            <AlertTriangle className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-primary-350 leading-relaxed">
              <strong>Tip:</strong> Categorize materials using standard subjects (e.g. Mathematics, Biology) to help StudyAI structure custom quiz categories.
            </p>
          </div>
        </div>
      </div>

      {/* Extracted Text Modal Viewer */}
      {viewerMaterial && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl w-full max-w-3xl h-[80vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-dark-850 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-primary-950/40 text-primary-400 border border-primary-900/10">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white max-w-xs md:max-w-md truncate" title={viewerMaterial.title}>
                    {viewerMaterial.title}
                  </h3>
                  <span className="inline-block text-[10px] font-semibold text-primary-400 bg-primary-950/40 px-2 rounded">
                    {viewerMaterial.subject}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setViewerMaterial(null)}
                className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-850 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 p-6 overflow-y-auto bg-dark-950 text-dark-200 font-sans text-sm leading-relaxed whitespace-pre-wrap select-text">
              {viewerMaterial.extracted_text || 'No text extracted.'}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-dark-850 bg-dark-900 flex justify-between items-center text-xs text-dark-500">
              <div className="flex gap-4">
                <span><strong>Pages:</strong> {viewerMaterial.page_count}</span>
                <span><strong>Words:</strong> {viewerMaterial.word_count}</span>
                <span><strong>Characters:</strong> {viewerMaterial.character_count}</span>
              </div>
              <button
                onClick={() => setViewerMaterial(null)}
                className="bg-primary-650 hover:bg-primary-550 text-white font-bold px-4 py-2 rounded-xl transition-colors cursor-pointer"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {isViewerLoading && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50">
          <div className="bg-dark-900 border border-dark-800 p-4 rounded-xl flex items-center gap-3 text-white">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent"></span>
            <span className="text-sm font-semibold">Loading material data...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
