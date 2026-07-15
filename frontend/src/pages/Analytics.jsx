import React from 'react';
import { BarChart3, LineChart, TrendingUp, Trophy } from 'lucide-react';

const Analytics = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Learning Analytics
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Track your progress, recall performance, study hours, and review quiz metrics.
        </p>
      </div>

      {/* Grid of placeholders */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Time Spent', val: '0m', icon: TrendingUp },
          { label: 'Quiz Accuracy', val: '0%', icon: Trophy },
          { label: 'Decks Practiced', val: '0', icon: BarChart3 },
          { label: 'Lessons Completed', val: '0', icon: LineChart },
        ].map((item, idx) => (
          <div key={idx} className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs text-dark-400 uppercase font-semibold tracking-wider">{item.label}</p>
              <p className="text-2xl font-bold text-white mt-2">{item.val}</p>
            </div>
            <div className="p-3 bg-dark-850 rounded-xl text-primary-400">
              <item.icon className="w-5 h-5" />
            </div>
          </div>
        ))}
      </div>

      <div className="bg-dark-900 border border-dark-850 p-8 rounded-2xl text-center py-16">
        <BarChart3 className="w-12 h-12 text-dark-600 mx-auto mb-4" />
        <h2 className="text-lg font-bold text-white mb-2">Analytics graphs will appear once you practice</h2>
        <p className="text-sm text-dark-400 max-w-sm mx-auto">
          Start answering quizzes or reviewing active-recall flashcard decks to let StudyAI visualize your stats.
        </p>
      </div>
    </div>
  );
};

export default Analytics;
