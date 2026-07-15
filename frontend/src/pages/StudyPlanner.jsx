import React, { useState, useEffect } from 'react';
import { 
  Calendar as CalendarIcon, Sparkles, Loader2, RefreshCw, 
  Trash2, CheckCircle2, Circle, Clock, Flame, 
  Target, AlertCircle, ChevronLeft, ChevronRight, Play, Info
} from 'lucide-react';
import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';
import toast from 'react-hot-toast';

const StudyPlanner = () => {
  const [materials, setMaterials] = useState([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  
  // Generation state values
  const [examDate, setExamDate] = useState('');
  const [totalDays, setTotalDays] = useState(14);
  const [dailyHours, setDailyHours] = useState(3.0);
  const [timePreference, setTimePreference] = useState('morning');
  
  // Loading flags
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(false);
  
  // Plan states
  const [plan, setPlan] = useState(null);
  const [viewMode, setViewMode] = useState('timeline'); // 'timeline' | 'calendar'
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);

  useEffect(() => {
    fetchMaterials();
  }, []);

  useEffect(() => {
    if (selectedMaterialId) {
      const mat = materials.find(m => m.id === selectedMaterialId);
      setSelectedMaterial(mat);
      setPlan(null);
      
      if (mat && mat.plan_generated) {
        fetchActivePlan(selectedMaterialId);
      }
    } else {
      setSelectedMaterial(null);
      setPlan(null);
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

  const fetchActivePlan = async (materialId) => {
    setLoadingPlan(true);
    try {
      const response = await api.get(`${API_ENDPOINTS.PLANS.BASE}/${materialId}`);
      setPlan(response.data);
      setSelectedDayIndex(0);
    } catch (err) {
      console.warn('Failed to load active plan:', err);
      setPlan(null);
    } finally {
      setLoadingPlan(false);
    }
  };

  const handleGeneratePlan = async (forceRegenerate = false) => {
    if (!selectedMaterialId) return;
    
    // Validate inputs
    if (!examDate) {
      toast.error('Please select your target exam date.');
      return;
    }
    
    setGenerating(true);
    const toastId = toast.loading(forceRegenerate ? 'Regenerating personalized study plan...' : 'Building study schedule daily tasks...', { id: 'pl-toast' });
    
    try {
      const response = await api.post(API_ENDPOINTS.PLANS.GENERATE, {
        material_id: selectedMaterialId,
        exam_date: examDate,
        total_days: Number(totalDays),
        daily_study_hours: Number(dailyHours),
        time_preference: timePreference,
        regenerate: forceRegenerate
      });
      
      setPlan(response.data);
      setSelectedDayIndex(0);
      
      // Sync materials state
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      
      toast.success('Study plan generated successfully!', { id: 'pl-toast' });
    } catch (err) {
      toast.error('Generation failed: ' + parseError(err), { id: 'pl-toast' });
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleTask = async (taskId, currentCompleted) => {
    if (!selectedMaterialId || !plan) return;
    
    try {
      const response = await api.patch(
        `${API_ENDPOINTS.PLANS.BASE}/${selectedMaterialId}/task/${taskId}`,
        { completed: !currentCompleted }
      );
      
      // Update plan with returned plan data
      setPlan(response.data);
      toast.success(currentCompleted ? 'Task marked incomplete.' : 'Task completed!');
    } catch (err) {
      toast.error('Failed to update task: ' + parseError(err));
    }
  };

  const handleDeletePlan = async () => {
    if (!selectedMaterialId || !plan) return;
    if (!window.confirm('Are you sure you want to delete this personalized study plan? All checklist completion history will be removed.')) return;
    
    try {
      await api.delete(`${API_ENDPOINTS.PLANS.BASE}/${selectedMaterialId}`);
      setPlan(null);
      
      // Sync materials status
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      toast.success('Study plan deleted successfully.');
    } catch (err) {
      toast.error('Failed to delete study plan: ' + parseError(err));
    }
  };

  const getTaskTypeStyles = (type) => {
    switch (type) {
      case 'reading':
        return { label: 'Reading Review', color: 'text-blue-400 bg-blue-950/20 border-blue-500/10' };
      case 'flashcard_review':
        return { label: 'Flashcards', color: 'text-emerald-400 bg-emerald-950/20 border-emerald-500/10' };
      case 'quiz_practice':
        return { label: 'Practice Quiz', color: 'text-purple-400 bg-purple-950/20 border-purple-500/10' };
      case 'break':
        return { label: 'Break block', color: 'text-amber-400 bg-amber-950/20 border-amber-500/10' };
      default:
        return { label: 'Study session', color: 'text-dark-300 bg-dark-900 border-dark-800' };
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'text-red-400 font-bold';
      case 'high': return 'text-orange-400 font-bold';
      case 'medium': return 'text-yellow-400';
      default: return 'text-dark-400';
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Personalized Study Planner
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Map diagnostics performance indicators to schedule a prioritized study plan.
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
            <CalendarIcon className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">No study materials found</h2>
          <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
            To generate study planners, upload documents first.
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
                disabled={generating || loadingPlan}
                className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer disabled:opacity-50"
              >
                {materials.map((mat) => (
                  <option key={mat.id} value={mat.id}>
                    {mat.title} ({mat.subject})
                  </option>
                ))}
              </select>
            </div>

            {plan && (
              <div className="flex gap-2.5 self-end">
                <button
                  onClick={() => handleGeneratePlan(true)}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-dark-850 hover:bg-dark-800 text-white font-semibold text-xs border border-dark-800 cursor-pointer transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Regenerate</span>
                </button>
                <button
                  onClick={handleDeletePlan}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-red-950/20 hover:bg-red-950/45 text-red-400 font-semibold text-xs border border-red-500/20 cursor-pointer transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Plan</span>
                </button>
              </div>
            )}
          </div>

          {/* Main State Panels */}
          {generating ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
              <h3 className="text-white font-bold text-lg animate-pulse">Building study schedule...</h3>
              <p className="text-xs text-dark-400 max-w-sm leading-relaxed">
                Aggregating topic ranks, structuring review blocks and practice timings.
              </p>
            </div>
          ) : loadingPlan ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-24 text-center">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto" />
            </div>
          ) : !plan ? (
            /* Un-generated configuration form settings */
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-6">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary-400" />
                  Plan Configuration
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-dark-300 mb-2">Target Exam Date</label>
                    <input
                      type="date"
                      value={examDate}
                      onChange={(e) => setExamDate(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-dark-300 mb-2">Study Duration (Days)</label>
                    <select
                      value={totalDays}
                      onChange={(e) => setTotalDays(Number(e.target.value))}
                      className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer"
                    >
                      <option value={7}>7 Days Plan</option>
                      <option value={14}>14 Days Plan</option>
                      <option value={30}>30 Days Plan</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-dark-300 mb-2">Daily Study Limit (Hours)</label>
                    <select
                      value={dailyHours}
                      onChange={(e) => setDailyHours(Number(e.target.value))}
                      className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer"
                    >
                      <option value={1}>1.0 Hour</option>
                      <option value={2}>2.0 Hours</option>
                      <option value={3}>3.0 Hours</option>
                      <option value={4}>4.0 Hours</option>
                      <option value={5}>5.0 Hours</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-dark-300 mb-2">Time of Day Preference</label>
                    <select
                      value={timePreference}
                      onChange={(e) => setTimePreference(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-primary-500 cursor-pointer"
                    >
                      <option value="morning">Morning Review</option>
                      <option value="afternoon">Afternoon Session</option>
                      <option value="evening">Evening Study</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={() => handleGeneratePlan(false)}
                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold text-sm transition-all cursor-pointer shadow-lg hover:shadow-primary-600/25"
                >
                  <CalendarIcon className="w-4 h-4" />
                  <span>Build Study Planner</span>
                </button>
              </div>

              {/* Informational sidebar */}
              <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
                <div className="p-3.5 rounded-xl bg-primary-950/20 text-primary-400 border border-primary-500/10 w-fit">
                  <Info className="w-5 h-5" />
                </div>
                <h4 className="text-white font-bold text-sm">Deterministic Scheduling</h4>
                <p className="text-xs text-dark-350 leading-relaxed">
                  Your plan is organized dynamically based on metrics from the Weak Topic Analyzer:
                </p>
                <ul className="text-xs text-dark-350 list-disc list-inside space-y-1">
                  <li>Critical topics get 45% weight allocation.</li>
                  <li>Weak topics get 30% weight allocation.</li>
                  <li>Daily limits balance overloading day schedules.</li>
                </ul>
              </div>
            </div>
          ) : (
            /* Active Plan presentation grid */
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Streaks, Summary statistics and Carry-forward alerts */}
              <div className="space-y-6">
                {/* Stats ring card */}
                <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-6">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Plan Status</h3>
                  
                  <div className="flex justify-center">
                    {/* Ring progress bar */}
                    <div className="relative w-36 h-36">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="72"
                          cy="72"
                          r="60"
                          stroke="currentColor"
                          strokeWidth="8"
                          className="text-dark-800"
                          fill="transparent"
                        />
                        <circle
                          cx="72"
                          cy="72"
                          r="60"
                          stroke="currentColor"
                          strokeWidth="8"
                          className="text-primary-500"
                          fill="transparent"
                          strokeDasharray={377}
                          strokeDashoffset={377 - (377 * plan.dashboard_preparation.overall_completion_percent) / 100}
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-3xl font-extrabold text-white font-mono">
                          {Math.round(plan.dashboard_preparation.overall_completion_percent)}%
                        </span>
                        <span className="text-[9px] text-dark-400 font-semibold uppercase tracking-wider mt-0.5">Completed</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-center border-t border-dark-850 pt-4">
                    <div>
                      <span className="text-[10px] text-dark-400 uppercase tracking-wider block">Remaining Tasks</span>
                      <span className="text-lg font-bold text-white font-mono">{plan.dashboard_preparation.tasks_remaining}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-dark-400 uppercase tracking-wider block">Completed</span>
                      <span className="text-lg font-bold text-white font-mono">{plan.dashboard_preparation.tasks_completed}</span>
                    </div>
                  </div>
                </div>

                {/* Streak widget */}
                <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">Revision Streak</p>
                    <h3 className="text-2xl font-extrabold text-white mt-1 flex items-center gap-1.5 font-mono">
                      {plan.dashboard_preparation.current_streak} days
                    </h3>
                  </div>
                  <div className="p-3 rounded-xl bg-orange-950/20 text-orange-400 border border-orange-500/10">
                    <Flame className="w-5 h-5 fill-current animate-pulse" />
                  </div>
                </div>

                {/* Motivational Quote */}
                <div className="bg-gradient-to-r from-primary-950/30 via-dark-900 to-dark-900 border border-primary-500/10 p-5 rounded-2xl space-y-2">
                  <h4 className="text-white font-bold text-xs flex items-center gap-1">
                    <Target className="w-3.5 h-3.5 text-primary-400" />
                    Target Exam Focus
                  </h4>
                  <p className="text-xs text-dark-300 italic leading-relaxed">
                    "{plan.motivational_note}"
                  </p>
                </div>
              </div>

              {/* Right Column: Daily timeline task checker checklist */}
              <div className="lg:col-span-2 space-y-6">
                {/* View switcher */}
                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setViewMode('timeline')}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                        viewMode === 'timeline'
                          ? 'bg-primary-600/10 text-primary-400 border-primary-500/20'
                          : 'bg-dark-900 text-dark-300 border-dark-850 hover:bg-dark-800'
                      }`}
                    >
                      Timeline view
                    </button>
                    <button
                      onClick={() => setViewMode('calendar')}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                        viewMode === 'calendar'
                          ? 'bg-primary-600/10 text-primary-400 border-primary-500/20'
                          : 'bg-dark-900 text-dark-300 border-dark-850 hover:bg-dark-800'
                      }`}
                    >
                      Calendar View
                    </button>
                  </div>
                </div>

                {viewMode === 'timeline' ? (
                  /* TIMELINE VIEW (Days tabs + task cards) */
                  <div className="space-y-6">
                    {/* Days tabs list */}
                    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
                      {plan.daily_schedule.map((day, idx) => {
                        const isSelected = selectedDayIndex === idx;
                        const allDone = day.tasks.length > 0 && day.tasks.every(t => t.completed);
                        return (
                          <button
                            key={idx}
                            onClick={() => setSelectedDayIndex(idx)}
                            className={`flex-shrink-0 px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                              isSelected
                                ? 'bg-primary-600 text-white border-primary-500'
                                : allDone
                                  ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/10'
                                  : 'bg-dark-900 text-dark-300 border-dark-850 hover:bg-dark-800'
                            }`}
                          >
                            <span>Day {day.day_number}</span>
                            {allDone && <CheckCircle2 className="w-3.5 h-3.5" />}
                          </button>
                        );
                      })}
                    </div>

                    {/* Day Schedule Panel */}
                    <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
                      <div className="flex justify-between items-center border-b border-dark-850 pb-3">
                        <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                          Day {plan.daily_schedule[selectedDayIndex].day_number} Plan
                        </h4>
                        <span className="text-[10px] text-dark-400 font-mono">
                          {new Date(plan.daily_schedule[selectedDayIndex].date).toLocaleDateString(undefined, {
                            weekday: 'short', month: 'short', day: 'numeric'
                          })}
                        </span>
                      </div>

                      {/* Tasks List */}
                      <div className="space-y-4">
                        {plan.daily_schedule[selectedDayIndex].tasks.map((task) => {
                          const typeStyles = getTaskTypeStyles(task.task_type);
                          return (
                            <div 
                              key={task.task_id}
                              className={`flex items-start gap-4 p-4 rounded-xl border transition-all ${
                                task.completed
                                  ? 'bg-dark-950/40 border-dark-900 opacity-60'
                                  : 'bg-dark-950 border-dark-850 hover:border-dark-800'
                              }`}
                            >
                              {/* Toggle Checkbox */}
                              <button
                                onClick={() => handleToggleTask(task.task_id, task.completed)}
                                className="mt-0.5 text-primary-400 hover:text-primary-300 transition-colors flex-shrink-0 cursor-pointer"
                              >
                                {task.completed ? (
                                  <CheckCircle2 className="w-5 h-5 text-emerald-400 fill-emerald-950/20" />
                                ) : (
                                  <Circle className="w-5 h-5 text-dark-600" />
                                )}
                              </button>

                              {/* Task Details */}
                              <div className="flex-grow space-y-2">
                                <div className="flex justify-between items-start gap-2 flex-wrap">
                                  <span className={`text-[8px] font-bold uppercase px-2 py-0.5 rounded border ${typeStyles.color}`}>
                                    {typeStyles.label}
                                  </span>
                                  {task.carried_forward && (
                                    <span className="text-[8px] font-bold uppercase px-2 py-0.5 rounded border border-orange-500/20 text-orange-400 bg-orange-950/20 animate-pulse">
                                      Carried Forward
                                    </span>
                                  )}
                                  <span className={`text-[9px] font-mono capitalize ${getPriorityColor(task.priority)}`}>
                                    {task.priority} Priority
                                  </span>
                                </div>

                                <p className={`text-xs text-white leading-relaxed ${task.completed ? 'line-through text-dark-500' : ''}`}>
                                  {task.task}
                                </p>

                                <div className="flex items-center gap-3 text-[10px] text-dark-400 font-mono">
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {task.estimated_minutes} mins
                                  </span>
                                  <span className="capitalize">Topic: {task.revision_topic}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })}

                        {plan.daily_schedule[selectedDayIndex].tasks.length === 0 && (
                          <div className="text-center py-6 text-xs text-dark-500">
                            Rest day! Take a break.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* CALENDAR VIEW (Weekly grids mapping tasks) */
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {plan.daily_schedule.map((day, idx) => {
                      const allDone = day.tasks.length > 0 && day.tasks.every(t => t.completed);
                      return (
                        <div 
                          key={idx}
                          className={`bg-dark-900 border p-5 rounded-2xl flex flex-col justify-between space-y-3 ${
                            allDone ? 'border-emerald-500/20 bg-emerald-950/5' : 'border-dark-850'
                          }`}
                        >
                          <div className="flex justify-between items-center border-b border-dark-850 pb-2">
                            <span className="text-xs font-bold text-white">Day {day.day_number}</span>
                            <span className="text-[9px] text-dark-500 font-mono">
                              {new Date(day.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                            </span>
                          </div>

                          <div className="space-y-1.5 flex-grow">
                            {day.tasks.map(t => (
                              <div key={t.task_id} className="flex items-center gap-1.5 text-[10px] text-dark-300">
                                {t.completed ? (
                                  <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                                ) : (
                                  <Circle className="w-3 h-3 text-dark-600 flex-shrink-0" />
                                )}
                                <span className={`truncate max-w-[200px] ${t.completed ? 'line-through text-dark-500' : ''}`} title={t.task}>
                                  {t.task}
                                </span>
                              </div>
                            ))}
                            {day.tasks.length === 0 && <span className="text-[10px] text-dark-500">Rest Day</span>}
                          </div>

                          <button
                            onClick={() => { setSelectedDayIndex(idx); setViewMode('timeline'); }}
                            className="text-left text-[9px] font-bold text-primary-400 hover:text-primary-300 flex items-center gap-0.5 cursor-pointer mt-2"
                          >
                            <span>Open checklist</span>
                            <ArrowRight className="w-2.5 h-2.5" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Help arrow sub-component
const ArrowRight = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
  </svg>
);

export default StudyPlanner;
