import React from 'react';
import { CreditCard, Plus, Layers } from 'lucide-react';

const Flashcards = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Active Recall Flashcards
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm">
            Leverage space repetition to memorize terms, formulas, and conceptual definitions.
          </p>
        </div>
        <button
          className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-dark-900 border border-dark-800 hover:border-dark-700 text-white font-medium transition-colors cursor-pointer"
          disabled
        >
          <Plus className="w-5 h-5" />
          <span>New Deck</span>
        </button>
      </div>

      {/* Empty State */}
      <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center max-w-xl mx-auto mt-8">
        <div className="w-12 h-12 rounded-xl bg-dark-850 flex items-center justify-center text-emerald-400 mx-auto mb-4 border border-dark-800">
          <Layers className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white mb-2">No flashcard decks found</h2>
        <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
          You haven't generated or created any cards yet. Upload documents to generate automatic decks, or write your own.
        </p>
        <div className="p-3 bg-emerald-950/20 border border-emerald-500/10 rounded-xl inline-flex items-center gap-2">
          <CreditCard className="w-4 h-4 text-emerald-400" />
          <span className="text-xs text-emerald-350 font-medium">Automatic card creation via Llama 3.3 is coming next!</span>
        </div>
      </div>
    </div>
  );
};

export default Flashcards;
