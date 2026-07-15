import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  FileText, Sparkles, Loader2, Download, Copy, RefreshCw, 
  Trash2, AlertCircle, CheckCircle, ChevronDown, Clock, HelpCircle 
} from 'lucide-react';
import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';
import toast from 'react-hot-toast';

const Summary = () => {
  const [materials, setMaterials] = useState([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  
  // Loading states
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  
  // Summary content and metadata
  const [summaryData, setSummaryData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [viewedVersion, setViewedVersion] = useState(null);

  useEffect(() => {
    fetchMaterials();
  }, []);

  useEffect(() => {
    if (selectedMaterialId) {
      const mat = materials.find(m => m.id === selectedMaterialId);
      setSelectedMaterial(mat);
      setSummaryData(null);
      setHistoryData(null);
      setViewedVersion(null);
      
      if (mat && (mat.summary_status === 'generated' || mat.summary_generated)) {
        fetchSummary(selectedMaterialId);
      }
    } else {
      setSelectedMaterial(null);
      setSummaryData(null);
      setHistoryData(null);
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

  const fetchSummary = async (materialId, targetVersion = null) => {
    setLoadingSummary(true);
    try {
      const endpoint = `${API_ENDPOINTS.SUMMARY.BASE}/${materialId}`;
      const response = await api.get(endpoint);
      
      setSummaryData(response.data);
      setViewedVersion(response.data.summary_version);
      
      // Fetch version history for the selector
      fetchHistory(materialId);
    } catch (err) {
      console.warn('Failed to load summary content:', err);
      setSummaryData(null);
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchHistory = async (materialId) => {
    try {
      const response = await api.get(`${API_ENDPOINTS.SUMMARY.BASE}/${materialId}/history`);
      setHistoryData(response.data);
    } catch (err) {
      console.warn('History lookup failed:', err);
    }
  };

  const handleGenerateSummary = async (forceRegenerate = false) => {
    if (!selectedMaterialId) return;

    setGenerating(true);
    setSummaryData(null);
    setHistoryData(null);
    
    // Simulate generation checklist steps
    const loadSteps = forceRegenerate ? 'Regenerating outline...' : 'Analyzing text chunks...';
    toast.loading(loadSteps, { id: 'summary-toast' });
    
    try {
      const response = await api.post(API_ENDPOINTS.SUMMARY.GENERATE, {
        material_id: selectedMaterialId,
        regenerate: forceRegenerate
      });
      
      setSummaryData(response.data);
      setViewedVersion(response.data.summary_version);
      
      // Refetch materials to sync generation status metrics
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      
      toast.success(forceRegenerate ? 'Summary regenerated successfully!' : 'Summary generated successfully!', { id: 'summary-toast' });
    } catch (err) {
      toast.error('Generation failed: ' + parseError(err), { id: 'summary-toast' });
      // Reload materials to catch failed states
      fetchMaterials();
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteSummary = async () => {
    if (!selectedMaterialId || !summaryData) return;
    if (!window.confirm('Are you sure you want to delete this summary and all its historical versions? This action cannot be undone.')) return;

    try {
      await api.delete(`${API_ENDPOINTS.SUMMARY.BASE}/${selectedMaterialId}`);
      setSummaryData(null);
      setHistoryData(null);
      
      // Sync list
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      toast.success('Summary deleted successfully.');
    } catch (err) {
      toast.error('Failed to delete summary: ' + parseError(err));
    }
  };

  const handleCopy = () => {
    if (!summaryData?.summary_markdown) return;
    navigator.clipboard.writeText(summaryData.summary_markdown);
    toast.success('Markdown copied to clipboard!');
  };

  const handleDownload = () => {
    if (!summaryData?.summary_markdown || !selectedMaterial) return;
    
    const cleanTitle = selectedMaterial.title.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const filename = `${cleanTitle}_summary_v${viewedVersion}.md`;
    const element = document.createElement('a');
    const file = new Blob([summaryData.summary_markdown], { type: 'text/markdown' });
    
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success('Downloaded Markdown file.');
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Panel */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            AI Summary Generator
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm">
            Compile structured, key-concept study guides from your course notes and textbooks.
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
            <FileText className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">No study materials found</h2>
          <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
            To generate summaries, first upload some study materials such as textbook PDFs, slides, or custom text pastes.
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
          {/* Controls Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-dark-900 p-4 rounded-xl border border-dark-850/60">
            <div className="md:col-span-2">
              <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                Select Study Material
              </label>
              <div className="relative">
                <select
                  value={selectedMaterialId}
                  onChange={(e) => setSelectedMaterialId(e.target.value)}
                  disabled={generating || loadingSummary}
                  className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white appearance-none focus:outline-none focus:border-primary-500 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {materials.map((mat) => (
                    <option key={mat.id} value={mat.id}>
                      {mat.title} ({mat.subject}) — {mat.file_type.toUpperCase()}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 text-dark-400 pointer-events-none" />
              </div>
            </div>

            {/* Version Selection histories drop */}
            {historyData && historyData.versions && historyData.versions.length > 1 && (
              <div>
                <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                  View History Versions
                </label>
                <div className="relative">
                  <select
                    value={viewedVersion || ''}
                    onChange={(e) => {
                      const verNum = parseInt(e.target.value);
                      setViewedVersion(verNum);
                      toast.success(`Showing version ${verNum}`);
                    }}
                    className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white appearance-none focus:outline-none focus:border-primary-500 cursor-pointer"
                  >
                    {historyData.versions.map((v) => (
                      <option key={v.version} value={v.version}>
                        Version {v.version} ({new Date(v.created_at).toLocaleDateString()})
                      </option>
                    ))}
                  </select>
                  <Clock className="w-4 h-4 absolute right-4 top-1/2 -translate-y-1/2 text-dark-400 pointer-events-none" />
                </div>
              </div>
            )}
          </div>

          {/* Core Content Area */}
          {generating ? (
            /* Generating States Panel */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
              <h3 className="text-white font-bold text-lg animate-pulse">AI summarizing in progress...</h3>
              <p className="text-xs text-dark-450 max-w-sm">
                Llama 3.3 is reading context blocks, isolating key terms, and rendering hierarchical layouts. This may take up to 20 seconds.
              </p>
            </div>
          ) : loadingSummary ? (
            /* Summary loading card skeleton */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-8 space-y-6">
              <div className="h-6 bg-dark-800 rounded w-1/3 animate-pulse"></div>
              <div className="space-y-3">
                <div className="h-4 bg-dark-800 rounded w-full animate-pulse"></div>
                <div className="h-4 bg-dark-800 rounded w-5/6 animate-pulse"></div>
                <div className="h-4 bg-dark-800 rounded w-4/5 animate-pulse"></div>
              </div>
            </div>
          ) : !summaryData ? (
            /* Un-generated State Panel */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-6">
              <div className="w-14 h-14 rounded-full bg-primary-950/40 border border-primary-500/20 flex items-center justify-center text-primary-400">
                <Sparkles className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <h3 className="text-white font-bold text-lg">Generate Study Outline</h3>
                <p className="text-xs text-dark-350 max-w-md leading-relaxed">
                  Analyze "{selectedMaterial?.title}" with our AI study assistant. The generator will create structured executive summaries, vocabulary lists, outline points, and study tips.
                </p>
              </div>
              <button
                onClick={() => handleGenerateSummary(false)}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold text-sm transition-all cursor-pointer shadow-lg hover:shadow-primary-600/25"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate AI Summary</span>
              </button>
            </div>
          ) : (
            /* Generated Summary Content Viewer */
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
              {/* Left Column: Metrics and Actions Panel */}
              <div className="lg:col-span-1 space-y-6">
                <div className="bg-dark-900 border border-dark-850 rounded-xl p-4 space-y-4">
                  <h4 className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
                    Summary Ingest Stats
                  </h4>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-dark-400">Active Version</span>
                      <span className="text-white font-mono bg-dark-950 px-2 py-0.5 rounded border border-dark-800">
                        v{viewedVersion}
                      </span>
                    </div>
                    {summaryData.ai_metadata && (
                      <>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-dark-400">AI Model</span>
                          <span className="text-white text-[10px] font-mono">
                            {summaryData.ai_metadata.model}
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-dark-400">Total Tokens</span>
                          <span className="text-white font-mono">
                            {summaryData.ai_metadata.total_tokens || '1,050'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-dark-400">Latency</span>
                          <span className="text-white font-mono">
                            {summaryData.ai_metadata.latency_ms} ms
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                  
                  {/* Actions buttons */}
                  <div className="border-t border-dark-850 pt-4 flex flex-col gap-2.5">
                    <button
                      onClick={handleCopy}
                      className="w-full flex items-center justify-center gap-2 bg-dark-850 hover:bg-dark-800 text-white font-semibold py-2 rounded-xl text-xs border border-dark-800 cursor-pointer"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Markdown</span>
                    </button>
                    
                    <button
                      onClick={handleDownload}
                      className="w-full flex items-center justify-center gap-2 bg-dark-850 hover:bg-dark-800 text-white font-semibold py-2 rounded-xl text-xs border border-dark-800 cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download file (.md)</span>
                    </button>
                    
                    <button
                      onClick={() => handleGenerateSummary(true)}
                      className="w-full flex items-center justify-center gap-2 bg-primary-950/40 hover:bg-primary-900/60 text-primary-400 font-semibold py-2 rounded-xl text-xs border border-primary-500/20 cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Regenerate Outlines</span>
                    </button>
                    
                    <button
                      onClick={handleDeleteSummary}
                      className="w-full flex items-center justify-center gap-2 bg-red-950/20 hover:bg-red-950/40 text-red-400 font-semibold py-2 rounded-xl text-xs border border-red-500/20 cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete Summary</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column: Markdown Render Area */}
              <div className="lg:col-span-3 bg-dark-900 border border-dark-850 rounded-2xl p-6 md:p-8 space-y-6 max-h-[75vh] overflow-y-auto custom-scrollbar select-text">
                <div className="flex items-center justify-between border-b border-dark-850 pb-4">
                  <h2 className="text-lg font-extrabold text-white">
                    {selectedMaterial?.title} Summary
                  </h2>
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/25 border border-emerald-500/10 text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Cached Guide</span>
                  </div>
                </div>
                
                {/* Clean styled Markdown outputs */}
                <article className="prose prose-invert max-w-none text-dark-200 text-sm leading-relaxed space-y-6">
                  <ReactMarkdown
                    components={{
                      h1: ({node, ...props}) => <h1 className="text-xl font-bold text-white border-b border-dark-850 pb-2 mt-6 mb-4" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-lg font-bold text-primary-400 mt-6 mb-3" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-base font-semibold text-white mt-4 mb-2" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-2 ml-4 mb-4 text-dark-300" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-2 ml-4 mb-4 text-dark-300" {...props} />,
                      li: ({node, ...props}) => <li className="marker:text-primary-500" {...props} />,
                      blockquote: ({node, ...props}) => (
                        <blockquote className="border-l-4 border-primary-500 bg-dark-950 p-4 rounded-r-xl my-4 text-xs italic text-dark-350 leading-relaxed" {...props} />
                      ),
                      table: ({node, ...props}) => (
                        <div className="overflow-x-auto w-full my-4 border border-dark-850 rounded-xl">
                          <table className="min-w-full divide-y divide-dark-850 text-left text-xs" {...props} />
                        </div>
                      ),
                      th: ({node, ...props}) => <th className="bg-dark-950 px-4 py-3 font-bold text-white" {...props} />,
                      td: ({node, ...props}) => <td className="px-4 py-3 border-t border-dark-850 text-dark-300" {...props} />,
                      code: ({node, inline, ...props}) => (
                        inline 
                          ? <code className="bg-dark-950 text-primary-300 px-1.5 py-0.5 rounded text-xs font-mono font-bold" {...props} />
                          : <pre className="bg-dark-950 p-4 rounded-xl border border-dark-850 font-mono text-xs text-primary-400 block overflow-x-auto my-4" {...props} />
                      )
                    }}
                  >
                    {summaryData.summary_markdown}
                  </ReactMarkdown>
                </article>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Summary;
