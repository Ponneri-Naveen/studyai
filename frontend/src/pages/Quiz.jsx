import React from 'react';
import { BrainCircuit, Play } from 'lucide-react';

const Quiz = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Intelligent Quizzes
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Challenge yourself with multiple-choice, true/false, or short-answer quizzes generated from your materials.
        </p>
      </div>

      {/* Empty State */}
      <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center max-w-xl mx-auto mt-8">
        <div className="w-12 h-12 rounded-xl bg-dark-850 flex items-center justify-center text-purple-400 mx-auto mb-4 border border-dark-800">
          <BrainCircuit className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white mb-2">No quizzes available</h2>
        <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
          Upload some study notes or textbook chapters to let the AI create practice tests for you automatically.
        </p>
        <button
          className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-500 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg transition-colors cursor-pointer"
          disabled
        >
          <Play className="w-4 h-4" />
          <span>Start Practice Test</span>
        </button>
      </div>
    </div>
  );
};

export default Quiz;
