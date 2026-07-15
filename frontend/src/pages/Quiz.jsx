import React, { useState, useEffect, useRef } from 'react';
import { 
  BrainCircuit, Sparkles, Loader2, RefreshCw, Trash2, 
  ChevronLeft, ChevronRight, Play, CheckCircle, 
  HelpCircle, Eye, EyeOff, Search, Clock, Award, ShieldAlert,
  ArrowRight, ToggleLeft, HelpCircle as HelpIcon, Check, X, Bookmark
} from 'lucide-react';
import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';
import toast from 'react-hot-toast';

const Quiz = () => {
  const [materials, setMaterials] = useState([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  
  // Loading states
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Quiz states
  const [quizId, setQuizId] = useState('');
  const [quizVersion, setQuizVersion] = useState(1);
  const [rawQuestions, setRawQuestions] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  
  // Quiz status
  const [quizState, setQuizState] = useState('settings'); // settings | active | results
  const [answers, setAnswers] = useState({}); // { question_id: answer_text }
  const [flagged, setFlagged] = useState({}); // { question_id: boolean }
  const [questionOrder, setQuestionOrder] = useState([]);
  const [practiceChecked, setPracticeChecked] = useState({}); // { question_id: boolean } (for Practice mode instant check)

  // Settings
  const [quizMode, setQuizMode] = useState('practice'); // practice | exam
  const [questionCount, setQuestionCount] = useState('all'); // all | 5 | 8 | 10
  const [isTimed, setIsTimed] = useState(false);
  const [timeLimitMinutes, setTimeLimitMinutes] = useState(10);
  const [shuffleQuestions, setShuffleQuestions] = useState(false);

  // Timer
  const [timeLeft, setTimeLeft] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);
  const elapsedRef = useRef(null);

  // Grading Result
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchMaterials();
  }, []);

  useEffect(() => {
    if (selectedMaterialId) {
      const mat = materials.find(m => m.id === selectedMaterialId);
      setSelectedMaterial(mat);
      setQuizState('settings');
      setRawQuestions([]);
      setQuestions([]);
      setAnswers({});
      setFlagged({});
      setPracticeChecked({});
      setResult(null);
      
      if (mat && mat.quiz_generated) {
        fetchQuizQuestions(selectedMaterialId);
      }
    } else {
      setSelectedMaterial(null);
      setRawQuestions([]);
      setQuestions([]);
    }
  }, [selectedMaterialId, materials]);

  // Bind Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (quizState !== 'active' || generating || loadingQuiz || submitting) return;
      
      // Ignore if typing in input text field (short answers)
      if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
        return;
      }

      if (e.code === 'ArrowLeft') {
        e.preventDefault();
        handlePrevQuestion();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        handleNextQuestion();
      } else if (['Digit1', 'Digit2', 'Digit3', 'Digit4'].includes(e.code)) {
        const optionIndex = parseInt(e.code.replace('Digit', '')) - 1;
        const currentQ = questions[currentQIndex];
        if (currentQ && currentQ.question_type === 'mcq' && currentQ.choices[optionIndex]) {
          handleSelectAnswer(currentQ.question_id, currentQ.choices[optionIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [quizState, questions, currentQIndex, generating, loadingQuiz, submitting]);

  // Handle active timers
  useEffect(() => {
    if (quizState === 'active') {
      // Elapsed timer
      elapsedRef.current = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);

      // Countdown timer if timed
      if (isTimed) {
        setTimeLeft(timeLimitMinutes * 60);
        timerRef.current = setInterval(() => {
          setTimeLeft(prev => {
            if (prev <= 1) {
              clearInterval(timerRef.current);
              toast.error('Time is up! Submitting quiz...');
              handleSubmitQuiz(true);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }
    } else {
      clearInterval(timerRef.current);
      clearInterval(elapsedRef.current);
    }

    return () => {
      clearInterval(timerRef.current);
      clearInterval(elapsedRef.current);
    };
  }, [quizState, isTimed, timeLimitMinutes]);

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

  const fetchQuizQuestions = async (materialId) => {
    setLoadingQuiz(true);
    try {
      const response = await api.get(`${API_ENDPOINTS.QUIZZES.BASE}/${materialId}`);
      setRawQuestions(response.data.questions || []);
      setQuizId(response.data.quiz_id);
      setQuizVersion(response.data.active_version);
    } catch (err) {
      console.warn('Failed to load quiz question sheet:', err);
      setRawQuestions([]);
    } finally {
      setLoadingQuiz(false);
    }
  };

  const handleGenerateQuiz = async (forceRegenerate = false) => {
    if (!selectedMaterialId) return;

    setGenerating(true);
    setRawQuestions([]);
    setQuizState('settings');
    
    const toastId = toast.loading(forceRegenerate ? 'Regenerating quiz questions sheet...' : 'Generating quiz questions list...', { id: 'qz-toast' });
    
    try {
      const response = await api.post(API_ENDPOINTS.QUIZZES.GENERATE, {
        material_id: selectedMaterialId,
        regenerate: forceRegenerate
      });
      
      const qList = response.data.questions || [];
      setRawQuestions(qList);
      setQuizId(response.data.quiz_id);
      setQuizVersion(response.data.active_version);
      
      // Refetch materials to sync generate flags
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      
      toast.success('AI Quiz sheet generated successfully!', { id: 'qz-toast' });
    } catch (err) {
      toast.error('Quiz generation failed: ' + parseError(err), { id: 'qz-toast' });
      fetchMaterials();
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteQuiz = async () => {
    if (!selectedMaterialId || rawQuestions.length === 0) return;
    if (!window.confirm('Are you sure you want to delete this quiz sheet? History reports will be preserved.')) return;

    try {
      await api.delete(`${API_ENDPOINTS.QUIZZES.BASE}/${selectedMaterialId}`);
      setRawQuestions([]);
      
      // Sync materials status
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      toast.success('Quiz questions deleted successfully.');
    } catch (err) {
      toast.error('Failed to delete quiz: ' + parseError(err));
    }
  };

  const handleStartQuiz = () => {
    if (rawQuestions.length === 0) return;

    // Apply Settings
    let selectedQs = [...rawQuestions];
    
    if (shuffleQuestions) {
      selectedQs.sort(() => Math.random() - 0.5);
    }

    if (questionCount !== 'all') {
      const count = parseInt(questionCount);
      selectedQs = selectedQs.slice(0, count);
    }

    setQuestions(selectedQs);
    setQuestionOrder(selectedQs.map(q => q.question_id));
    setAnswers({});
    setFlagged({});
    setPracticeChecked({});
    setCurrentQIndex(0);
    setElapsedTime(0);
    setQuizState('active');
    
    toast.success(`Starting Quiz in ${quizMode.toUpperCase()} mode!`);
  };

  const handleSelectAnswer = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleFlagQuestion = (questionId) => {
    setFlagged(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
  };

  const handleCheckAnswerPractice = (questionId) => {
    setPracticeChecked(prev => ({
      ...prev,
      [questionId]: true
    }));
  };

  const handleNextQuestion = () => {
    if (currentQIndex < questions.length - 1) {
      setCurrentQIndex(prev => prev + 1);
    }
  };

  const handlePrevQuestion = () => {
    if (currentQIndex > 0) {
      setCurrentQIndex(prev => prev - 1);
    }
  };

  const handleSubmitQuiz = async (forceTimeUp = false) => {
    if (!forceTimeUp && !window.confirm('Are you sure you want to submit your answers?')) return;

    setSubmitting(true);
    const toastId = toast.loading('Grading quiz answers...', { id: 'qz-submit-toast' });

    try {
      const response = await api.post(`${API_ENDPOINTS.QUIZZES.BASE}/${quizId}/submit`, {
        material_id: selectedMaterialId,
        quiz_version: quizVersion,
        mode: quizMode,
        time_taken_seconds: elapsedTime,
        question_order: questionOrder,
        answers: answers
      });

      setResult(response.data);
      setQuizState('results');
      toast.success('Quiz graded successfully!', { id: 'qz-submit-toast' });
    } catch (err) {
      toast.error('Failed to grade quiz: ' + parseError(err), { id: 'qz-submit-toast' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetake = () => {
    setQuizState('settings');
    setResult(null);
  };

  // Helper formatting seconds
  const formatTime = (sec) => {
    const min = Math.floor(sec / 60);
    const s = sec % 60;
    return `${min}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="space-y-8 animate-fadeIn select-none">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Intelligent Quizzes
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Challenge yourself with multiple-choice, true/false, or short-answer tests generated from your AI summaries.
        </p>
      </div>

      {loadingMaterials ? (
        <div className="flex items-center justify-center p-12 bg-dark-900 border border-dark-850 rounded-2xl">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : materials.length === 0 ? (
        /* Empty Materials State */
        <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center max-w-xl mx-auto mt-8">
          <div className="w-12 h-12 rounded-xl bg-dark-850 flex items-center justify-center text-primary-400 mx-auto mb-4 border border-dark-800">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">No study materials found</h2>
          <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
            Upload document files on the Study Upload system first to generate automatic quiz questions sheets.
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
          {/* Material Select Header */}
          {quizState !== 'active' && (
            <div className="flex flex-col lg:flex-row gap-4 bg-dark-900 p-4 rounded-xl border border-dark-850/60 justify-between items-center">
              <div className="w-full lg:max-w-md">
                <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                  Select Study Material
                </label>
                <select
                  value={selectedMaterialId}
                  onChange={(e) => setSelectedMaterialId(e.target.value)}
                  disabled={generating || loadingQuiz || submitting}
                  className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer disabled:opacity-50"
                >
                  {materials.map((mat) => (
                    <option key={mat.id} value={mat.id}>
                      {mat.title} ({mat.subject})
                    </option>
                  ))}
                </select>
              </div>

              {rawQuestions.length > 0 && quizState === 'settings' && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleGenerateQuiz(true)}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-dark-850 hover:bg-dark-800 text-white font-semibold text-xs border border-dark-800 cursor-pointer transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Regenerate Sheet</span>
                  </button>
                  <button
                    onClick={handleDeleteQuiz}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-red-950/20 hover:bg-red-950/45 text-red-400 font-semibold text-xs border border-red-500/20 cursor-pointer transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete Quiz</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Core States switcher panels */}
          {generating ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
              <h3 className="text-white font-bold text-lg animate-pulse">Llama building quiz sheet...</h3>
              <p className="text-xs text-dark-400 max-w-sm leading-relaxed">
                Reading existing Markdown summaries and flashcard decks to generate MCQ, True/False, and short-answer evaluations.
              </p>
            </div>
          ) : loadingQuiz ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-24 text-center">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto" />
            </div>
          ) : rawQuestions.length === 0 ? (
            /* Un-generated state banner */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-6">
              <div className="w-14 h-14 rounded-full bg-primary-950/40 border border-primary-500/20 flex items-center justify-center text-primary-400 animate-pulse">
                <BrainCircuit className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <h3 className="text-white font-bold text-lg">Generate Study Quiz Questions</h3>
                <p className="text-xs text-dark-350 max-w-md leading-relaxed">
                  Automatically generate study test question sheets from this material's summaries. Evaluates MCQs, True/False, and Short answers.
                </p>
              </div>
              <button
                onClick={() => handleGenerateQuiz(false)}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold text-sm transition-all cursor-pointer shadow-lg hover:shadow-primary-600/25"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate Quiz Sheet</span>
              </button>
            </div>
          ) : quizState === 'settings' ? (
            /* Settings Configuration Panel Layout */
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-2 bg-dark-900 border border-dark-850 rounded-2xl p-6 space-y-6">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-primary-400" />
                  Quiz Settings
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {/* Mode */}
                  <div className="space-y-2">
                    <label className="block text-xs font-bold text-dark-300">Mode</label>
                    <div className="grid grid-cols-2 gap-2.5">
                      <button
                        onClick={() => setQuizMode('practice')}
                        className={`py-3.5 rounded-xl border text-xs font-bold transition-all cursor-pointer ${quizMode === 'practice' ? 'bg-primary-950/20 border-primary-500 text-primary-400' : 'bg-dark-950 border-dark-800 text-dark-400 hover:text-white'}`}
                      >
                        Practice Mode
                      </button>
                      <button
                        onClick={() => setQuizMode('exam')}
                        className={`py-3.5 rounded-xl border text-xs font-bold transition-all cursor-pointer ${quizMode === 'exam' ? 'bg-primary-950/20 border-primary-500 text-primary-400' : 'bg-dark-950 border-dark-800 text-dark-400 hover:text-white'}`}
                      >
                        Exam Mode
                      </button>
                    </div>
                    <p className="text-[10px] text-dark-450 leading-relaxed">
                      {quizMode === 'practice' 
                        ? 'Practice mode shows instant answers checking and explanation cards after each question.' 
                        : 'Exam mode locks details, showing countdown timer. Explanations show only after submission.'}
                    </p>
                  </div>

                  {/* Question Count Selection */}
                  <div className="space-y-2">
                    <label className="block text-xs font-bold text-dark-300">Question Count</label>
                    <select
                      value={questionCount}
                      onChange={(e) => setQuestionCount(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3.5 px-4 text-xs text-white focus:outline-none cursor-pointer"
                    >
                      <option value="all">All Available ({rawQuestions.length})</option>
                      {rawQuestions.length >= 5 && <option value="5">5 Questions</option>}
                      {rawQuestions.length >= 8 && <option value="8">8 Questions</option>}
                      {rawQuestions.length >= 10 && <option value="10">10 Questions</option>}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 border-t border-dark-850 pt-6">
                  {/* Timer selection */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="block text-xs font-bold text-dark-300">Enable Timed Quiz</label>
                      <input
                        type="checkbox"
                        checked={isTimed}
                        onChange={(e) => setIsTimed(e.target.checked)}
                        className="w-4 h-4 accent-primary-500 cursor-pointer"
                      />
                    </div>
                    {isTimed && (
                      <div className="flex items-center gap-3">
                        <input
                          type="number"
                          min="1"
                          max="60"
                          value={timeLimitMinutes}
                          onChange={(e) => setTimeLimitMinutes(parseInt(e.target.value) || 10)}
                          className="bg-dark-950 border border-dark-800 rounded-xl py-2 px-3 text-xs text-white focus:outline-none w-20 font-mono text-center"
                        />
                        <span className="text-xs text-dark-400">minutes</span>
                      </div>
                    )}
                  </div>

                  {/* Shuffle order toggle */}
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-bold text-dark-300">Randomize Order</label>
                    <input
                      type="checkbox"
                      checked={shuffleQuestions}
                      onChange={(e) => setShuffleQuestions(e.target.checked)}
                      className="w-4 h-4 accent-primary-500 cursor-pointer"
                    />
                  </div>
                </div>

                <button
                  onClick={handleStartQuiz}
                  className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-sm transition-all cursor-pointer shadow-lg hover:shadow-primary-600/25 mt-6"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Start Practice Quiz</span>
                </button>
              </div>

              {/* Right panel: statistics/info cards */}
              <div className="bg-dark-900 border border-dark-850 rounded-2xl p-5 flex flex-col justify-between">
                <div className="space-y-4">
                  <h4 className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
                    Question Sheet Analysis
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-center text-xs">
                    <div className="bg-dark-950 p-2.5 rounded-lg border border-dark-850">
                      <span className="block text-[8px] text-dark-500 font-bold uppercase">Difficulty</span>
                      <span className="text-primary-400 font-bold font-mono text-sm mt-1 block">Medium</span>
                    </div>
                    <div className="bg-dark-950 p-2.5 rounded-lg border border-dark-850">
                      <span className="block text-[8px] text-dark-500 font-bold uppercase">Questions</span>
                      <span className="text-white font-bold font-mono text-sm mt-1 block">{rawQuestions.length}</span>
                    </div>
                  </div>

                  {/* Downstream metadata registry summaries */}
                  <div className="bg-dark-950 p-3.5 rounded-lg border border-dark-850 space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Quiz Version</span>
                      <span className="text-white font-semibold font-mono">v{quizVersion}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Prompt version</span>
                      <span className="text-white font-semibold font-mono">quiz_v1</span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-dark-850 pt-4 text-[10px] text-dark-400 space-y-1.5 font-mono mt-4">
                  <span className="block font-sans font-bold uppercase text-[9px] text-dark-500 mb-1">Shortcut Keys</span>
                  <div className="flex justify-between"><span>ArrowRight</span> <span>Next card</span></div>
                  <div className="flex justify-between"><span>ArrowLeft</span> <span>Previous card</span></div>
                  <div className="flex justify-between"><span>1, 2, 3, 4</span> <span>A, B, C, D choices</span></div>
                </div>
              </div>
            </div>
          ) : quizState === 'active' ? (
            /* Active Quiz Interface View */
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Left sidebar: Question Palette Navigation */}
              <div className="lg:col-span-1 space-y-6">
                <div className="bg-dark-900 border border-dark-850 rounded-2xl p-5 space-y-4">
                  <h4 className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
                    Question Palette
                  </h4>
                  
                  {/* Palette Indicators Grid */}
                  <div className="grid grid-cols-5 gap-2.5">
                    {questions.map((q, idx) => {
                      const isAnswered = answers[q.question_id] !== undefined && answers[q.question_id] !== '';
                      const isFlagged = flagged[q.question_id];
                      let dotColor = 'bg-dark-950 border border-dark-850 text-dark-400';
                      
                      if (isFlagged) {
                        dotColor = 'bg-purple-950/40 border border-purple-500/40 text-purple-400';
                      } else if (isAnswered) {
                        dotColor = 'bg-primary-950/30 border border-primary-500/40 text-primary-400';
                      }

                      if (idx === currentQIndex) {
                        dotColor += ' ring-2 ring-primary-500 ring-offset-2 ring-offset-dark-900';
                      }

                      return (
                        <button
                          key={q.question_id}
                          onClick={() => setCurrentQIndex(idx)}
                          className={`w-9 h-9 rounded-lg text-xs font-bold transition-all cursor-pointer ${dotColor}`}
                        >
                          {idx + 1}
                        </button>
                      );
                    })}
                  </div>

                  <div className="border-t border-dark-850 pt-4 space-y-2">
                    <button
                      onClick={() => handleFlagQuestion(questions[currentQIndex].question_id)}
                      className="w-full flex items-center justify-center gap-2 bg-dark-850 hover:bg-dark-800 text-white font-semibold py-2 rounded-xl text-xs border border-dark-800 cursor-pointer"
                    >
                      <Bookmark className="w-3.5 h-3.5 text-purple-400" />
                      <span>{flagged[questions[currentQIndex].question_id] ? 'Unmark Question' : 'Mark for Review'}</span>
                    </button>
                    
                    <button
                      onClick={() => handleSubmitQuiz(false)}
                      disabled={submitting}
                      className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl text-xs transition-colors cursor-pointer"
                    >
                      <span>Submit Quiz</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Panel: Question Layout & Choice Pickers */}
              <div className="lg:col-span-3 space-y-6">
                <div className="bg-dark-900 border border-dark-850 rounded-3xl p-8 flex flex-col justify-between min-h-[400px]">
                  {/* Header Row */}
                  <div className="flex justify-between items-center border-b border-dark-850/60 pb-4">
                    <span className="text-[10px] font-bold text-primary-400 uppercase tracking-widest bg-primary-950/30 border border-primary-500/10 px-2 py-1 rounded">
                      {questions[currentQIndex]?.topic}
                    </span>
                    <div className="flex items-center gap-1.5 text-xs text-white bg-dark-950 border border-dark-850 px-3 py-1.5 rounded-xl font-mono">
                      <Clock className="w-4 h-4 text-primary-400" />
                      <span>{isTimed ? `Time Left: ${formatTime(timeLeft)}` : `Time: ${formatTime(elapsedTime)}`}</span>
                    </div>
                  </div>

                  {/* Question details */}
                  <div className="my-6 space-y-6 flex-1">
                    <div className="flex justify-between items-center">
                      <span className="text-[9px] font-bold text-dark-500 uppercase tracking-widest font-mono">
                        Question {currentQIndex + 1} of {questions.length} ({questions[currentQIndex]?.difficulty})
                      </span>
                    </div>

                    <h3 className="text-base md:text-lg font-bold text-white leading-relaxed">
                      {questions[currentQIndex]?.question}
                    </h3>

                    {/* Options area based on question type */}
                    <div className="space-y-3 mt-6">
                      {questions[currentQIndex]?.question_type === 'mcq' && (
                        questions[currentQIndex]?.choices.map((opt, idx) => {
                          const isSelected = answers[questions[currentQIndex].question_id] === opt;
                          return (
                            <button
                              key={idx}
                              onClick={() => handleSelectAnswer(questions[currentQIndex].question_id, opt)}
                              className={`w-full text-left p-4 rounded-xl border text-xs font-semibold flex items-center justify-between cursor-pointer transition-all ${isSelected ? 'bg-primary-950/20 border-primary-500 text-primary-300' : 'bg-dark-950 border-dark-850 text-dark-250 hover:bg-dark-850'}`}
                            >
                              <span>{String.fromCharCode(65 + idx)}. {opt}</span>
                              {isSelected && <Check className="w-4 h-4 text-primary-400" />}
                            </button>
                          );
                        })
                      )}

                      {questions[currentQIndex]?.question_type === 'true_false' && (
                        ['True', 'False'].map((opt, idx) => {
                          const isSelected = answers[questions[currentQIndex].question_id] === opt;
                          return (
                            <button
                              key={idx}
                              onClick={() => handleSelectAnswer(questions[currentQIndex].question_id, opt)}
                              className={`w-full text-left p-4 rounded-xl border text-xs font-semibold flex items-center justify-between cursor-pointer transition-all ${isSelected ? 'bg-primary-950/20 border-primary-500 text-primary-300' : 'bg-dark-950 border-dark-850 text-dark-250 hover:bg-dark-850'}`}
                            >
                              <span>{opt}</span>
                              {isSelected && <Check className="w-4 h-4 text-primary-400" />}
                            </button>
                          );
                        })
                      )}

                      {questions[currentQIndex]?.question_type === 'short_answer' && (
                        <div className="space-y-2">
                          <input
                            type="text"
                            placeholder="Type your answer here..."
                            value={answers[questions[currentQIndex].question_id] || ''}
                            onChange={(e) => handleSelectAnswer(questions[currentQIndex].question_id, e.target.value)}
                            className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3.5 px-4 text-xs text-white focus:outline-none focus:border-primary-500"
                          />
                        </div>
                      )}
                    </div>

                    {/* Instant Check answers (Practice mode support) */}
                    {quizMode === 'practice' && (
                      <div className="border-t border-dark-850/60 pt-6 mt-6">
                        {!practiceChecked[questions[currentQIndex].question_id] ? (
                          <button
                            onClick={() => handleCheckAnswerPractice(questions[currentQIndex].question_id)}
                            disabled={!answers[questions[currentQIndex].question_id]}
                            className="bg-primary-950/20 border border-primary-500/20 text-primary-400 font-bold px-4 py-2 rounded-lg text-xs hover:bg-primary-950/45 disabled:opacity-50 transition-colors cursor-pointer"
                          >
                            Check Answer
                          </button>
                        ) : (
                          <div className="p-4 rounded-xl bg-dark-950 border border-dark-850 space-y-3">
                            <div className="flex items-center gap-2">
                              {answers[questions[currentQIndex].question_id]?.toLowerCase() === questions[currentQIndex].correct_answer.toLowerCase() ? (
                                <span className="text-emerald-400 font-bold text-xs flex items-center gap-1">
                                  <Check className="w-4 h-4" /> Correct Answer!
                                </span>
                              ) : (
                                <span className="text-red-400 font-bold text-xs flex items-center gap-1">
                                  <X className="w-4 h-4" /> Incorrect Answer. Correct is: {questions[currentQIndex].correct_answer}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-dark-350 leading-relaxed font-sans border-t border-dark-850/60 pt-2.5">
                              {questions[currentQIndex].explanation}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Footers navigation control */}
                  <div className="flex justify-between items-center border-t border-dark-850/60 pt-4">
                    <button
                      onClick={handlePrevQuestion}
                      disabled={currentQIndex === 0}
                      className="flex items-center gap-1 text-xs text-dark-400 hover:text-white font-semibold cursor-pointer disabled:opacity-50"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      <span>Back</span>
                    </button>
                    <button
                      onClick={handleNextQuestion}
                      disabled={currentQIndex === questions.length - 1}
                      className="flex items-center gap-1 text-xs text-dark-400 hover:text-white font-semibold cursor-pointer disabled:opacity-50"
                    >
                      <span>Next</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Results & Review Score view */
            <div className="space-y-8 animate-fadeIn">
              {/* Score breakdown metrics card */}
              <div className="bg-dark-900 border border-dark-850 rounded-2xl p-6 grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                <div className="text-center md:border-r border-dark-850 md:pr-6 py-2">
                  <span className="block text-[10px] text-dark-500 font-bold uppercase tracking-wider">Obtained Score</span>
                  <h2 className="text-4xl font-extrabold text-white mt-1 font-mono">
                    {result?.metrics.obtained_marks} / {result?.metrics.total_marks}
                  </h2>
                  <span className="text-xs text-primary-400 font-bold block mt-1.5">{result?.metrics.score_percentage}% Score Accuracy</span>
                </div>

                <div className="grid grid-cols-3 gap-3 md:col-span-2 text-center text-xs">
                  <div className="bg-dark-950 p-3 rounded-xl border border-dark-850">
                    <span className="block text-[8px] text-dark-500 font-bold uppercase">Correct</span>
                    <span className="text-emerald-400 font-bold font-mono text-sm mt-1 block">{result?.metrics.correct_count}</span>
                  </div>
                  <div className="bg-dark-950 p-3 rounded-xl border border-dark-850">
                    <span className="block text-[8px] text-dark-500 font-bold uppercase">Wrong</span>
                    <span className="text-red-400 font-bold font-mono text-sm mt-1 block">{result?.metrics.wrong_count}</span>
                  </div>
                  <div className="bg-dark-950 p-3 rounded-xl border border-dark-850">
                    <span className="block text-[8px] text-dark-500 font-bold uppercase">Skipped</span>
                    <span className="text-dark-400 font-bold font-mono text-sm mt-1 block">{result?.metrics.skipped_count}</span>
                  </div>
                </div>

                <div className="text-center md:pl-6">
                  <button
                    onClick={handleRetake}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-bold text-sm transition-all cursor-pointer shadow-lg hover:shadow-primary-600/20"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Retake Quiz</span>
                  </button>
                </div>
              </div>

              {/* Scored Responses Review Outline */}
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-primary-400" />
                  Detailed Question Review
                </h3>

                <div className="space-y-4">
                  {result?.responses.map((q, idx) => (
                    <div 
                      key={q.question_id}
                      className={`p-6 rounded-2xl bg-dark-900 border ${q.is_correct ? 'border-emerald-500/20' : 'border-red-500/20'} space-y-4`}
                    >
                      <div className="flex justify-between items-center border-b border-dark-850/60 pb-3">
                        <span className="text-[9px] font-bold text-dark-400 uppercase tracking-widest">
                          Question {idx + 1} ({q.question_type.toUpperCase()})
                        </span>
                        
                        <div className="flex gap-2 items-center text-[9px] font-bold">
                          <span className="bg-dark-950 border border-dark-850 px-2 py-1 rounded text-dark-450 uppercase">{q.difficulty}</span>
                          <span className="bg-dark-950 border border-dark-850 px-2 py-1 rounded text-primary-400 uppercase">{q.topic}</span>
                          <span className={q.is_correct ? 'text-emerald-400 bg-emerald-950/20 border border-emerald-500/10 px-2 py-1 rounded' : 'text-red-400 bg-red-950/20 border border-red-500/10 px-2 py-1 rounded'}>
                            {q.is_correct ? 'Correct' : 'Incorrect'}
                          </span>
                        </div>
                      </div>

                      <h4 className="text-xs font-bold text-white leading-relaxed">{q.student_answer ? '' : '[SKIPPED] '}{rawQuestions.find(rq => rq.question_id === q.question_id)?.question}</h4>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                        <div className="bg-dark-950 p-3.5 rounded-xl border border-dark-850 space-y-1">
                          <span className="block text-[8px] text-dark-500 font-bold uppercase">Your Answer</span>
                          <span className={q.is_correct ? 'text-emerald-400 font-bold' : 'text-red-400 font-semibold'}>{q.student_answer || 'No answer submitted.'}</span>
                        </div>
                        <div className="bg-dark-950 p-3.5 rounded-xl border border-dark-850 space-y-1">
                          <span className="block text-[8px] text-dark-500 font-bold uppercase">Correct Answer</span>
                          <span className="text-emerald-400 font-bold">{q.correct_answer}</span>
                        </div>
                      </div>

                      <div className="bg-dark-950 p-4 rounded-xl border border-dark-850 space-y-1.5 text-xs leading-relaxed text-dark-350">
                        <span className="block text-[8px] text-dark-500 font-bold uppercase">Explanation</span>
                        <p>{q.explanation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Quiz;
