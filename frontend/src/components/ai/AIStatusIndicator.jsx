import React, { useEffect, useState } from 'react';
import { Sparkles, CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';
import api from '../../services/api';
import { API_ENDPOINTS } from '../../constants';
import { parseError } from '../../utils/errorParser';
import toast from 'react-hot-toast';

const AIStatusIndicator = () => {
  const [status, setStatus] = useState('checking'); // checking, healthy, unhealthy
  const [details, setDetails] = useState(null);
  
  // Test ping states
  const [showTestModal, setShowTestModal] = useState(false);
  const [testText, setTestText] = useState('Hello StudyAI Ingestion Check');
  const [testResult, setTestResult] = useState(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    checkAIHealth();
  }, []);

  const checkAIHealth = async () => {
    setStatus('checking');
    try {
      const response = await api.get(API_ENDPOINTS.AI.HEALTH);
      setDetails(response.data);
      if (response.data && response.data.status === 'healthy') {
        setStatus('healthy');
      } else {
        setStatus('unhealthy');
      }
    } catch (err) {
      console.warn('AI service check failed:', err);
      setStatus('unhealthy');
    }
  };

  const handleTestPing = async (e) => {
    e.preventDefault();
    if (!testText.trim()) return;

    setIsTesting(true);
    setTestResult(null);
    try {
      const response = await api.post(API_ENDPOINTS.AI.TEST, {
        test_text: testText.trim()
      });
      setTestResult(response.data);
      toast.success('AI Dry-Run Connection Successful!');
    } catch (err) {
      toast.error('AI Connection Test Failed: ' + parseError(err));
      setTestResult({
        error: parseError(err)
      });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Status Badge */}
      {status === 'checking' && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-850 border border-dark-800 text-xs text-dark-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>Checking AI Engine...</span>
        </div>
      )}

      {status === 'healthy' && (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/20 border border-emerald-500/10 text-xs font-semibold text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>AI Engine: Online ({details?.default_model})</span>
          </div>
          <button
            onClick={() => setShowTestModal(true)}
            className="text-[10px] font-bold text-primary-400 hover:text-primary-300 bg-primary-950/20 border border-primary-500/10 px-2.5 py-1.5 rounded-lg transition-colors cursor-pointer"
          >
            Run AI Diagnostics
          </button>
        </div>
      )}

      {status === 'unhealthy' && (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-950/20 border border-red-500/10 text-xs font-semibold text-red-400">
            <XCircle className="w-3.5 h-3.5 text-red-500" />
            <span>AI Ingest: Offline (Check config key)</span>
          </div>
          <button
            onClick={checkAIHealth}
            className="text-[10px] font-bold text-dark-400 hover:text-white bg-dark-850 hover:bg-dark-800 border border-dark-800 px-2.5 py-1.5 rounded-lg transition-colors cursor-pointer"
          >
            Retry Check
          </button>
        </div>
      )}

      {/* Diagnostics Modal */}
      {showTestModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-dark-850 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary-400" />
                AI SDK Integration Diagnostic Ping
              </h3>
              <button 
                onClick={() => {
                  setShowTestModal(false);
                  setTestResult(null);
                }}
                className="text-dark-400 hover:text-white text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-dark-350 leading-relaxed">
              This panel verifies live client-to-model round-trips via your configured Groq model. 
              Submitting a test payload will trigger prompt loading from <code>test_ping.txt</code>.
            </p>

            <form onSubmit={handleTestPing} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                  Diagnostic Input String
                </label>
                <input
                  type="text"
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  disabled={isTesting}
                  className="w-full bg-dark-950 border border-dark-800 rounded-xl py-2.5 px-3.5 text-xs text-white placeholder-dark-600 focus:outline-none focus:border-primary-500"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isTesting || !testText.trim()}
                className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 text-white font-semibold py-2 rounded-xl text-xs shadow-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isTesting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Querying LLM Engine...</span>
                  </>
                ) : (
                  <span>Send Diagnostic Ping</span>
                )}
              </button>
            </form>

            {/* Test Results Output */}
            {testResult && (
              <div className="border-t border-dark-850 pt-4 space-y-3">
                <h4 className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
                  Diagnostic Metrics
                </h4>

                {testResult.error ? (
                  <div className="p-3 bg-red-950/20 border border-red-500/10 rounded-lg text-xs text-red-400 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{testResult.error}</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3 text-center text-xs">
                      <div className="bg-dark-950 p-2 rounded-lg border border-dark-850">
                        <span className="block text-[9px] text-dark-500 font-bold uppercase">Latency</span>
                        <span className="text-white font-medium">{testResult.latency_ms} ms</span>
                      </div>
                      <div className="bg-dark-950 p-2 rounded-lg border border-dark-850">
                        <span className="block text-[9px] text-dark-500 font-bold uppercase">Tokens Ingested</span>
                        <span className="text-white font-medium">{testResult.tokens_used}</span>
                      </div>
                    </div>
                    <div className="bg-dark-950 p-3.5 rounded-lg border border-dark-850 text-xs">
                      <span className="block text-[9px] text-dark-500 font-bold uppercase mb-1">Model Response</span>
                      <code className="text-primary-300 font-mono block break-words whitespace-pre-wrap select-text">
                        {testResult.raw_response}
                      </code>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIStatusIndicator;
