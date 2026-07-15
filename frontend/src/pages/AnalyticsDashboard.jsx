import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { 
  Award, Sparkles, Loader2, RefreshCw, Trophy, Flame, 
  Target, TrendingUp, CheckSquare, Layers, Clock, AlertTriangle, Play 
} from 'lucide-react';
import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';
import toast from 'react-hot-toast';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const AnalyticsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [activities, setActivities] = useState([]);
  
  // AI Insights states
  const [insight, setInsight] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  
  // General Loading flags
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async (force = false) => {
    if (force) setRefreshing(true);
    else setLoadingDashboard(true);
    
    try {
      const dashboardUrl = force 
        ? `${API_ENDPOINTS.ANALYSIS.BASE.replace('analysis', 'analytics')}/refresh`
        : `${API_ENDPOINTS.ANALYSIS.BASE.replace('analysis', 'analytics')}/dashboard`;
      
      const method = force ? api.post : api.get;
      const config = force ? { headers: { 'X-Bypass-Cache': 'true' } } : {};
      const response = await method(dashboardUrl, config);
      setMetrics(response.data);
      
      // Fetch charts timeline
      const performanceResp = await api.get(
        `${API_ENDPOINTS.ANALYSIS.BASE.replace('analysis', 'analytics')}/performance`,
        config
      );
      setTimeline(performanceResp.data.performance_timeline);
      
      // Fetch activity logs
      const activityResp = await api.get(
        `${API_ENDPOINTS.ANALYSIS.BASE.replace('analysis', 'analytics')}/activity`,
        config
      );
      setActivities(activityResp.data.activities);
      
      if (force) toast.success('Analytics metrics dashboard recalculated.');
    } catch (err) {
      toast.error('Failed to load analytics: ' + parseError(err));
    } finally {
      setLoadingDashboard(false);
      setRefreshing(false);
    }
  };

  const handleFetchInsights = async () => {
    setLoadingInsight(true);
    try {
      const response = await api.get(
        `${API_ENDPOINTS.ANALYSIS.BASE.replace('analysis', 'analytics')}/insights`
      );
      setInsight(response.data);
      toast.success('AI performance insights generated.');
    } catch (err) {
      toast.error('AI Insights failed: ' + parseError(err));
    } finally {
      setLoadingInsight(false);
    }
  };

  if (loadingDashboard) {
    return (
      <div className="flex items-center justify-center p-24 bg-dark-950 min-h-[400px]">
        <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
      </div>
    );
  }

  const { overview, trends } = metrics;
  
  // Pie chart data
  const pieData = [
    { name: 'Mastered', value: overview.flashcards_mastered },
    { name: 'Remaining', value: Math.max(0, overview.flashcards_generated - overview.flashcards_mastered) }
  ];

  const tasksData = [
    { name: 'Completed', value: overview.tasks_completed },
    { name: 'Remaining', value: overview.tasks_remaining }
  ];

  return (
    <div className="space-y-8 animate-fadeIn text-white">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight flex items-center gap-2">
            Learning Analytics
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm">
            Deterministic dashboard aggregating performance statistics across all materials.
          </p>
        </div>
        <button
          onClick={() => fetchDashboardData(true)}
          disabled={refreshing}
          className="flex items-center gap-1.5 self-start sm:self-center px-4 py-2.5 rounded-xl bg-dark-900 hover:bg-dark-850 text-white font-semibold text-xs border border-dark-800 cursor-pointer disabled:opacity-50 transition-colors"
        >
          {refreshing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          <span>Refresh Analytics</span>
        </button>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Uploads', val: overview.materials_uploaded, detail: 'Note packages', icon: Layers, style: 'text-indigo-400 border-indigo-500/10' },
          { label: 'Average Score', val: `${overview.avg_quiz_score}%`, detail: `Highest: ${overview.highest_score}%`, icon: Trophy, style: 'text-emerald-400 border-emerald-500/10' },
          { label: 'Consistency Streak', val: `${overview.current_streak} Days`, detail: `Longest: ${overview.longest_streak} days`, icon: Flame, style: 'text-orange-400 border-orange-500/10' },
          { label: 'Consistency Score', val: `${overview.consistency_score}%`, detail: 'Study regularity', icon: Target, style: 'text-purple-400 border-purple-500/10' },
        ].map((item, idx) => (
          <div key={idx} className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs text-dark-400 uppercase font-semibold tracking-wider">{item.label}</p>
              <h3 className="text-2xl font-black mt-2 font-mono">{item.val}</h3>
              <span className="text-[10px] text-dark-500 mt-1 block">{item.detail}</span>
            </div>
            <div className={`p-3 bg-dark-950 rounded-xl border ${item.style}`}>
              <item.icon className="w-5 h-5" />
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Line Chart */}
        <div className="lg:col-span-2 bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary-400" />
            Learning Progress Timeline
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="week" stroke="#737373" style={{ fontSize: '10px' }} />
                <YAxis stroke="#737373" style={{ fontSize: '10px' }} />
                <Tooltip contentStyle={{ backgroundColor: '#171717', borderColor: '#262626', borderRadius: '12px' }} />
                <Line type="monotone" dataKey="accuracy" name="Quiz Accuracy %" stroke="#6366f1" strokeWidth={2} />
                <Line type="monotone" dataKey="cards_mastered" name="Cards Mastered" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Circular Gauges */}
        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-6">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Schedules & Recall
          </h3>

          <div className="grid grid-cols-2 gap-4">
            {/* Doughnut 1: Flashcards */}
            <div className="flex flex-col items-center space-y-2">
              <span className="text-[10px] font-semibold text-dark-400 uppercase tracking-wider text-center">Cards Mastery</span>
              <div className="h-28 w-28 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      innerRadius={30}
                      outerRadius={45}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      <Cell fill="#10b981" />
                      <Cell fill="#262626" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="text-xs font-extrabold font-mono">{overview.flashcards_mastered}</span>
                  <span className="text-[7px] text-dark-500">Mastered</span>
                </div>
              </div>
            </div>

            {/* Doughnut 2: Tasks */}
            <div className="flex flex-col items-center space-y-2">
              <span className="text-[10px] font-semibold text-dark-400 uppercase tracking-wider text-center">Tasks Completion</span>
              <div className="h-28 w-28 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={tasksData}
                      innerRadius={30}
                      outerRadius={45}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      <Cell fill="#6366f1" />
                      <Cell fill="#262626" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="text-xs font-extrabold font-mono">{overview.tasks_completed}</span>
                  <span className="text-[7px] text-dark-500">Done</span>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-dark-850 pt-4 grid grid-cols-2 gap-4 text-center">
            <div>
              <span className="text-[9px] text-dark-400 uppercase block">Recall Velocity</span>
              <span className="text-sm font-bold font-mono text-indigo-400">{trends.learning_velocity} events/week</span>
            </div>
            <div>
              <span className="text-[9px] text-dark-400 uppercase block">Score Trend</span>
              <span className="text-sm font-bold font-mono text-emerald-400 capitalize">{trends.quiz_score_trend}</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Performance Insights Block */}
      <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
        <div className="flex justify-between items-center flex-wrap gap-2">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary-400" />
            AI Performance Strategy Insights
          </h3>
          {!insight && (
            <button
              onClick={handleFetchInsights}
              disabled={loadingInsight}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-semibold text-xs transition-colors cursor-pointer disabled:opacity-50"
            >
              {loadingInsight ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>Generate AI Advice Insights</span>
            </button>
          )}
        </div>

        {loadingInsight ? (
          <div className="flex items-center justify-center p-8 bg-dark-950 rounded-xl">
            <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
          </div>
        ) : insight ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
            <div className="lg:col-span-2 space-y-2">
              <span className="text-[9px] text-primary-400 uppercase tracking-widest font-mono font-bold">Personalized Mentor tips</span>
              <p className="text-xs text-dark-300 leading-relaxed">
                {insight.insight_paragraph}
              </p>
            </div>
            <div className="space-y-3 border-t lg:border-t-0 lg:border-l border-dark-850 pt-4 lg:pt-0 lg:pl-6">
              <span className="text-[9px] text-dark-450 uppercase font-bold tracking-wider">Suggested Focus Actions</span>
              <div className="space-y-1.5">
                {insight.suggested_actions.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-dark-950 border border-dark-850 text-xs text-white">
                    <CheckSquare className="w-3.5 h-3.5 text-primary-400 flex-shrink-0" />
                    <span className="font-semibold truncate">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-dark-400">
            Submit your current diagnostic indicators to allow AI to generate study focus actions.
          </p>
        )}
      </div>

      {/* Grid: Weak Topics Checklist & Activities Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Critical Weak Topics Panel */}
        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
            Weak Subjects Identified
          </h3>
          <div className="space-y-2.5 overflow-y-auto max-h-60 pr-1">
            {metrics.weak_topics_list.map((topic, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-dark-950 border border-red-500/10 text-xs text-white"
              >
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping"></div>
                  <span className="font-bold">{topic}</span>
                </div>
                <span className="text-[9px] uppercase tracking-wider text-red-400 font-bold px-2 py-0.5 bg-red-950/20 border border-red-500/10 rounded">
                  Critical
                </span>
              </div>
            ))}
            {metrics.weak_topics_list.length === 0 && (
              <div className="text-center py-8 text-xs text-dark-500 font-medium">
                No weak subjects detected! Keep up the good work.
              </div>
            )}
          </div>
        </div>

        {/* Timeline logs */}
        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary-400" />
            Recent Activity Logs
          </h3>
          <div className="space-y-3.5 overflow-y-auto max-h-60 pr-1">
            {activities.map((act, idx) => (
              <div key={idx} className="flex gap-3 text-xs leading-relaxed">
                <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1 flex-shrink-0"></div>
                <div>
                  <h4 className="font-bold text-white">{act.event}</h4>
                  <p className="text-[10px] text-dark-400 mt-0.5">{act.detail}</p>
                </div>
              </div>
            ))}
            {activities.length === 0 && (
              <p className="text-xs text-dark-500">No recent activity logged.</p>
            )}
          </div>
        </div>
      </div>

      {/* Achievements Badges grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Award className="w-4 h-4 text-primary-400" />
          Achievement Badges
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {metrics.achievements.map((ach) => (
            <div 
              key={ach.id}
              className={`border p-5 rounded-2xl flex flex-col justify-between space-y-4 transition-all duration-200 ${
                ach.unlocked 
                  ? 'bg-gradient-to-br from-primary-950/20 via-dark-900 to-dark-900 border-primary-500/25'
                  : 'bg-dark-900 border-dark-850 opacity-40'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">{ach.name}</h4>
                  <Award className={`w-4 h-4 ${ach.unlocked ? 'text-primary-400' : 'text-dark-500'}`} />
                </div>
                <p className="text-[10px] text-dark-450 leading-relaxed">{ach.description}</p>
              </div>

              {/* Progress */}
              <div className="space-y-1">
                <div className="flex justify-between text-[8px] font-mono text-dark-400">
                  <span>Progress</span>
                  <span>{Math.round(ach.progress)}%</span>
                </div>
                <div className="w-full bg-dark-950 rounded-full h-1.5 border border-dark-800">
                  <div className="bg-primary-500 h-1 rounded-full" style={{ width: `${ach.progress}%` }}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
