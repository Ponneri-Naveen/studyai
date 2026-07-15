import React from 'react';
import { FileText, Search, Sparkles } from 'lucide-react';

const Summary = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            AI Summaries
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm">
            Read AI-generated summaries and structured key takeaways from your study materials.
          </p>
        </div>
      </div>

      {/* Filter / Search Stub */}
      <div className="flex gap-4">
        <div className="relative flex-grow">
          <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-dark-500" />
          <input
            type="text"
            placeholder="Search summaries..."
            className="w-full bg-dark-900 border border-dark-800 rounded-xl py-3 pl-11 pr-4 text-sm text-white placeholder-dark-550 focus:outline-none focus:border-primary-500 transition-colors"
            disabled
          />
        </div>
      </div>

      {/* Empty State */}
      <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center max-w-xl mx-auto mt-8">
        <div className="w-12 h-12 rounded-xl bg-dark-850 flex items-center justify-center text-primary-400 mx-auto mb-4 border border-dark-800">
          <FileText className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white mb-2">No summaries generated yet</h2>
        <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
          To read study summaries, please go to the Upload page and submit your textbook chapters, study sheets, or slides.
        </p>
        <div className="p-3 bg-primary-950/20 border border-primary-500/10 rounded-xl inline-flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary-400" />
          <span className="text-xs text-primary-350 font-medium">AI will organize your docs into high-impact outlines!</span>
        </div>
      </div>
    </div>
  );
};

export default Summary;
