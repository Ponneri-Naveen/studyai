import React, { useState, useEffect } from 'react';
import { 
  Award, Sparkles, Loader2, RefreshCw, Trash2, 
  HelpCircle, CheckCircle, AlertTriangle, Play, 
  ChevronRight, ArrowRight, BookOpen, Clock, Heart, ShieldAlert
} from 'lucide-react';
import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';
import toast from 'react-hot-toast';

const WeakTopics = () => {
  const [materials, setMaterials] = useState([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  
  // Loading states
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  
  // Analysis details
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState(null);
  const [selectedVersion, setSelectedVersion] = useState('');

  useEffect(() => {
    fetchMaterials();
  }, []);

  useEffect(() => {
    if (selectedMaterialId) {
      const mat = materials.find(m => m.id === selectedMaterialId);
      setSelectedMaterial(mat);
      setAnalysis(null);
      setHistory(null);
      setSelectedVersion('');
      
      if (mat && mat.analysis_generated) {
        fetchAnalysis(selectedMaterialId);
        fetchHistory(selectedMaterialId);
      }
    } else {
      setSelectedMaterial(null);
      setAnalysis(null);
    }
  }, [selectedMaterialId, materials]);

  const fetchMaterials = async () => {
    setLoadingMaterials(true);
    try {
      const response = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(response.data);
      if (response.data.length > 0) {
        setSelectedMaterialId(response.data[0].id);
      }
    } catch (err) {
      toast.error('Failed to load study materials: ' + parseError(err));
    } finally {
      setLoadingMaterials(false);
    }
  };

  const fetchAnalysis = async (materialId, version = '') => {
    setLoadingAnalysis(true);
    try {
      const url = version 
        ? `${API_ENDPOINTS.ANALYSIS.BASE}/${materialId}` 
        : `${API_ENDPOINTS.ANALYSIS.BASE}/${materialId}`;
      
      // If version is selected, we query version details from history or fetch endpoint
      const response = await api.get(url);
      setAnalysis(response.data);
      if (!version) {
        setSelectedVersion(response.data.active_version.toString());
      }
    } catch (err) {
      console.warn('Failed to load analysis:', err);
      setAnalysis(null);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const fetchHistory = async (materialId) => {
    try {
      const response = await api.get(`${API_ENDPOINTS.ANALYSIS.BASE}/${materialId}/history`);
      setHistory(response.data);
    } catch (err) {
      console.warn('Failed to load history runs:', err);
      setHistory(null);
    }
  };

  const handleGenerateAnalysis = async (forceRegenerate = false) => {
    if (!selectedMaterialId) return;

    setGenerating(true);
    setAnalysis(null);
    
    const toastId = toast.loading(forceRegenerate ? 'Regenerating analysis diagnostics...' : 'Aggregating quiz and flashcards metrics...', { id: 'an-toast' });
    
    try {
      const response = await api.post(API_ENDPOINTS.ANALYSIS.GENERATE, {
        material_id: selectedMaterialId,
        regenerate: forceRegenerate
      });
      
      setAnalysis(response.data);
      setSelectedVersion(response.data.active_version.toString());
      
      // Refetch materials and history to sync status flags
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      fetchHistory(selectedMaterialId);
      
      toast.success('Performance analysis generated successfully!', { id: 'an-toast' });
    } catch (err) {
      toast.error('Analysis generation failed: ' + parseError(err), { id: 'an-toast' });
      fetchMaterials();
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteAnalysis = async () => {
    if (!selectedMaterialId || !analysis) return;
    if (!window.confirm('Are you sure you want to delete this weak topic analysis diagnostic file? History logs will be cleared.')) return;

    try {
      await api.delete(`${API_ENDPOINTS.ANALYSIS.BASE}/${selectedMaterialId}`);
      setAnalysis(null);
      setHistory(null);
      
      // Sync materials status
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      toast.success('Analysis diagnostics deleted successfully.');
    } catch (err) {
      toast.error('Failed to delete analysis: ' + parseError(err));
    }
  };

  const handleVersionChange = async (ver) => {
    setSelectedVersion(ver);
    // Find version in history or refetch
    if (history && history.versions) {
      const target = history.versions.find(v => v.version.toString() === ver);
      if (target) {
        // Fetch specific version details
        setLoadingAnalysis(true);
        try {
          // In standard design, the backend always serves the active. To load historical version details,
          // we can load the full JSON mapping by adding query parameter, e.g. ?version=x
          const response = await api.get(`${API_ENDPOINTS.ANALYSIS.BASE}/${selectedMaterialId}?version=${ver}`);
          setAnalysis(response.data);
        } catch (err) {
          toast.error('Failed to load version details: ' + parseError(err));
        } finally {
          setLoadingAnalysis(false);
        }
      }
    }
  };

  // Color mapping boundaries based on weakness levels
  const getWeaknessDetails = (level) => {
    switch (level) {
      case 'Excellent':
        return { color: 'text-emerald-400 bg-emerald-950/20 border-emerald-500/10', bar: 'bg-emerald-500', alert: 'border-emerald-500/20 bg-emerald-950/5' };
      case 'Good':
        return { color: 'text-blue-400 bg-blue-950/20 border-blue-500/10', bar: 'bg-blue-500', alert: 'border-blue-500/20 bg-blue-950/5' };
      case 'Needs Review':
        return { color: 'text-amber-400 bg-amber-950/20 border-amber-500/10', bar: 'bg-amber-500', alert: 'border-amber-500/20 bg-amber-950/5' };
      case 'Weak':
        return { color: 'text-orange-400 bg-orange-950/20 border-orange-500/10', bar: 'bg-orange-500', alert: 'border-orange-500/20 bg-orange-950/5' };
      case 'Critical':
        return { color: 'text-red-400 bg-red-950/20 border-red-500/10', bar: 'bg-red-500', alert: 'border-red-500/20 bg-red-950/5' };
      default:
        return { color: 'text-dark-400 bg-dark-950 border-dark-850', bar: 'bg-dark-500', alert: 'border-dark-850 bg-dark-900/5' };
    }
  };

  const getTrendBadge = (trend) => {
    switch (trend) {
      case 'improving':
        return { text: 'Improving', style: 'text-emerald-400 bg-emerald-950/20 border-emerald-500/10' };
      case 'regression':
        return { text: 'Regression', style: 'text-red-400 bg-red-950/20 border-red-500/10' };
      default:
        return { text: 'Stable', style: 'text-dark-300 bg-dark-950 border-dark-800' };
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Weak Topic Analyzer
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm">
            Deterministic diagnostic analysis mapping your performance details across study tools.
          </p>
        </div>
      </div>

      {loadingMaterials ? (
        <div className="flex items-center justify-center p-12 bg-dark-900 border border-dark-850 rounded-2xl">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : materials.length === 0 ? (
        /* Empty Materials State */
        <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center max-w-xl mx-auto mt-8">
          <div className="w-12 h-12 rounded-xl bg-dark-850 flex items-center justify-center text-primary-400 mx-auto mb-4 border border-dark-800">
            <Award className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">No study materials found</h2>
          <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
            To run topic performance diagnostics, upload note packages or documents first.
          </p>
          <a
            href="/upload"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-medium text-sm transition-colors"
          >
            Go to Upload Page
          </a>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Dashboard Control Selectors */}
          <div className="flex flex-col lg:flex-row gap-4 bg-dark-900 p-4 rounded-xl border border-dark-850/60 justify-between items-center">
            <div className="w-full lg:max-w-md">
              <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                Select Study Material
              </label>
              <select
                value={selectedMaterialId}
                onChange={(e) => setSelectedMaterialId(e.target.value)}
                disabled={generating || loadingAnalysis}
                className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer disabled:opacity-50"
              >
                {materials.map((mat) => (
                  <option key={mat.id} value={mat.id}>
                    {mat.title} ({mat.subject})
                  </option>
                ))}
              </select>
            </div>

            {analysis && (
              <div className="flex gap-3 items-center flex-wrap">
                {/* Version Selector */}
                {history && history.versions && history.versions.length > 1 && (
                  <div>
                    <label className="block text-[9px] font-bold text-dark-500 uppercase tracking-wider mb-1">Run History</label>
                    <select
                      value={selectedVersion}
                      onChange={(e) => handleVersionChange(e.target.value)}
                      className="bg-dark-950 border border-dark-800 rounded-xl py-2 px-3 text-xs text-white focus:outline-none cursor-pointer"
                    >
                      {history.versions.map(v => (
                        <option key={v.version} value={v.version}>
                          Version {v.version} ({new Date(v.created_at).toLocaleDateString()})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="flex gap-2 self-end">
                  <button
                    onClick={() => handleGenerateAnalysis(true)}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-dark-850 hover:bg-dark-800 text-white font-semibold text-xs border border-dark-800 cursor-pointer transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Recalculate</span>
                  </button>
                  <button
                    onClick={handleDeleteAnalysis}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-red-950/20 hover:bg-red-950/45 text-red-400 font-semibold text-xs border border-red-500/20 cursor-pointer transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Main State Panels */}
          {generating ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
              <h3 className="text-white font-bold text-lg animate-pulse">Running topic diagnostics...</h3>
              <p className="text-xs text-dark-400 max-w-sm leading-relaxed">
                Parsing attempts history datasets, review logs, and compile weights. No calculations are sent to the AI.
              </p>
            </div>
          ) : loadingAnalysis ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-24 text-center">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto" />
            </div>
          ) : !analysis ? (
            /* Un-generated state banner */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-6">
              <div className="w-14 h-14 rounded-full bg-primary-950/40 border border-primary-500/20 flex items-center justify-center text-primary-400 animate-pulse">
                <Award className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <h3 className="text-white font-bold text-lg">Run Performance Diagnostics</h3>
                <p className="text-xs text-dark-350 max-w-md leading-relaxed">
                  Map your strengths and weaknesses. Analyzes all quiz scores and card reviews to locate critical subjects.
                </p>
              </div>
              <button
                onClick={() => handleGenerateAnalysis(false)}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold text-sm transition-all cursor-pointer shadow-lg hover:shadow-primary-600/25"
              >
                <Sparkles className="w-4 h-4" />
                <span>Analyze Weak Topics</span>
              </button>
            </div>
          ) : (
            /* Main Dashboard analytics layout */
            <div className="space-y-6">
              {/* Aggregated score metrics cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Average Test Accuracy</p>
                    <h3 className="text-3xl font-extrabold text-white mt-2 font-mono">{analysis.dashboard_preparation.average_accuracy}%</h3>
                  </div>
                  <div className="p-3.5 rounded-xl bg-primary-950/20 text-primary-400 border border-primary-500/10">
                    <CheckCircle className="w-6 h-6" />
                  </div>
                </div>

                <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Critical / Weak Topics</p>
                    <h3 className="text-3xl font-extrabold text-red-400 mt-2 font-mono">{analysis.dashboard_preparation.weak_topic_count}</h3>
                  </div>
                  <div className="p-3.5 rounded-xl bg-red-950/20 text-red-400 border border-red-500/10">
                    <AlertTriangle className="w-6 h-6 animate-pulse" />
                  </div>
                </div>

                <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Learning Trend</p>
                    <span className={`inline-block text-xs font-bold px-3 py-1.5 rounded-lg border mt-3.5 ${getTrendBadge(analysis.dashboard_preparation.learning_trend).style}`}>
                      {getTrendBadge(analysis.dashboard_preparation.learning_trend).text}
                    </span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-emerald-950/20 text-emerald-400 border border-emerald-500/10">
                    <Clock className="w-6 h-6" />
                  </div>
                </div>
              </div>

              {/* Topics Performance Breakdown Cards */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Award className="w-4 h-4 text-primary-400" />
                  Topic Rankings
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {analysis.topics_analysis.map((t, idx) => {
                    const styleMeta = getWeaknessDetails(t.weakness_level);
                    return (
                      <div 
                        key={idx}
                        className="bg-dark-900 border border-dark-850 rounded-2xl p-5 flex flex-col justify-between space-y-4"
                      >
                        <div className="space-y-2">
                          <div className="flex justify-between items-start gap-2">
                            <h4 className="text-xs font-bold text-white truncate max-w-[150px] sm:max-w-[180px]" title={t.topic}>
                              {t.topic}
                            </h4>
                            <span className={`text-[8px] font-bold uppercase px-2 py-0.5 rounded border flex-shrink-0 ${styleMeta.color}`}>
                              {t.weakness_level}
                            </span>
                          </div>
                          <span className="block text-[8px] text-dark-500 font-mono">Attempts: {t.attempts} quizzes | Difficulty: {t.difficulty.toUpperCase()}</span>
                        </div>

                        {/* Progress Bar meters */}
                        <div className="space-y-3">
                          <div className="space-y-1">
                            <div className="flex justify-between text-[9px] font-mono">
                              <span className="text-dark-400">Quiz Accuracy</span>
                              <span className="text-white font-bold">{t.accuracy}%</span>
                            </div>
                            <div className="w-full bg-dark-950 rounded-full h-1.5 border border-dark-800">
                              <div className="bg-primary-500 h-1 rounded-full" style={{ width: `${t.accuracy}%` }}></div>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[9px] font-mono">
                              <span className="text-dark-400">Cards Mastery</span>
                              <span className="text-white font-bold">{t.mastery_score}%</span>
                            </div>
                            <div className="w-full bg-dark-950 rounded-full h-1.5 border border-dark-800">
                              <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${t.mastery_score}%` }}></div>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[9px] font-mono">
                              <span className="text-dark-400">Confidence Match</span>
                              <span className="text-white font-bold">{t.confidence_score}%</span>
                            </div>
                            <div className="w-full bg-dark-950 rounded-full h-1.5 border border-dark-800">
                              <div className={`${styleMeta.bar} h-1 rounded-full`} style={{ width: `${t.confidence_score}%` }}></div>
                            </div>
                          </div>
                        </div>

                        {/* Action alert box */}
                        <div className={`p-3 rounded-lg border text-[10px] text-dark-200 leading-relaxed ${styleMeta.alert}`}>
                          <span className="font-bold block text-white uppercase text-[8px] mb-0.5">Recommended Action</span>
                          {t.recommended_action}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* AI personalized study plan advice recommendations */}
              <div className="bg-dark-900 border border-dark-850 rounded-2xl p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-primary-400" />
                    AI Revision Strategy
                  </h3>
                  <p className="text-xs text-dark-300 leading-relaxed pr-4">
                    {analysis.ai_recommendations.personalized_advice}
                  </p>
                  
                  {analysis.ai_recommendations.learning_strategy && (
                    <div className="p-4 rounded-xl bg-dark-950 border border-dark-850 space-y-1.5 text-xs">
                      <span className="font-bold text-[9px] text-primary-400 uppercase tracking-widest font-mono">Spaced recall strategy</span>
                      <p className="text-dark-350 leading-relaxed">{analysis.ai_recommendations.learning_strategy}</p>
                    </div>
                  )}
                </div>

                {/* Study priorities lists */}
                <div className="space-y-4 border-t lg:border-t-0 lg:border-l border-dark-850 pt-4 lg:pt-0 lg:pl-6">
                  <h4 className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
                    Revision Priorities
                  </h4>
                  <div className="space-y-2">
                    {analysis.ai_recommendations.revision_priorities.map((item, idx) => (
                      <div 
                        key={idx}
                        className="flex items-center gap-2 p-2.5 rounded-lg bg-dark-950 border border-dark-850 text-xs text-white"
                      >
                        <ChevronRight className="w-4 h-4 text-red-400 flex-shrink-0" />
                        <span className="font-semibold truncate">{item}</span>
                      </div>
                    ))}
                    {analysis.ai_recommendations.revision_priorities.length === 0 && (
                      <p className="text-xs text-dark-500">No revisions priorities generated.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WeakTopics;
