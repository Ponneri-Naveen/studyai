import React, { useState, useEffect, useRef } from 'react';
import { 
  CreditCard, Sparkles, Loader2, RefreshCw, Trash2, 
  ChevronLeft, ChevronRight, Shuffle, CheckCircle, 
  HelpCircle, Eye, EyeOff, Search, Layers, Star 
} from 'lucide-react';
import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';
import toast from 'react-hot-toast';

const Flashcards = () => {
  const [materials, setMaterials] = useState([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  
  // Loading states
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadingDeck, setLoadingDeck] = useState(false);
  
  // Cards content and metadata
  const [cards, setCards] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  
  // Search, Filters & Stats
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [hideMastered, setHideMastered] = useState(false);
  const [topicsList, setTopicsList] = useState(['All']);

  const deckContainerRef = useRef(null);

  useEffect(() => {
    fetchMaterials();
  }, []);

  useEffect(() => {
    if (selectedMaterialId) {
      const mat = materials.find(m => m.id === selectedMaterialId);
      setSelectedMaterial(mat);
      setCards([]);
      setCurrentIndex(0);
      setIsFlipped(false);
      
      if (mat && (mat.flashcards_generated)) {
        fetchDeck(selectedMaterialId);
      }
    } else {
      setSelectedMaterial(null);
      setCards([]);
    }
  }, [selectedMaterialId, materials]);

  // Bind Keyboard listeners
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (cards.length === 0 || generating || loadingDeck) return;
      
      // If typing in input, don't execute shortcuts
      if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'SELECT') {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        setIsFlipped(prev => !prev);
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        handlePrevCard();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        handleNextCard();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [cards, currentIndex, generating, loadingDeck]);

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

  const fetchDeck = async (materialId) => {
    setLoadingDeck(true);
    try {
      const response = await api.get(`${API_ENDPOINTS.FLASHCARDS.BASE}/${materialId}`);
      const cardsList = response.data.flashcards || [];
      setCards(cardsList);
      
      // Extract unique topics list
      const topics = ['All', ...new Set(cardsList.map(c => c.topic).filter(Boolean))];
      setTopicsList(topics);
      setCurrentIndex(0);
      setIsFlipped(false);
    } catch (err) {
      console.warn('Failed to load flashcard deck:', err);
      setCards([]);
    } finally {
      setLoadingDeck(false);
    }
  };

  const handleGenerateDeck = async (forceRegenerate = false) => {
    if (!selectedMaterialId) return;

    setGenerating(true);
    setCards([]);
    setIsFlipped(false);
    
    const toastId = toast.loading(forceRegenerate ? 'Regenerating card list...' : 'Generating active-recall cards...', { id: 'fc-toast' });
    
    try {
      const response = await api.post(API_ENDPOINTS.FLASHCARDS.GENERATE, {
        material_id: selectedMaterialId,
        regenerate: forceRegenerate
      });
      
      const cardsList = response.data.flashcards || [];
      setCards(cardsList);
      
      // Extract topics
      const topics = ['All', ...new Set(cardsList.map(c => c.topic).filter(Boolean))];
      setTopicsList(topics);
      setCurrentIndex(0);
      
      // Refetch materials to sync generate flags
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      
      toast.success(forceRegenerate ? 'Deck regenerated successfully!' : 'Flashcards generated successfully!', { id: 'fc-toast' });
    } catch (err) {
      toast.error('Flashcard generation failed: ' + parseError(err), { id: 'fc-toast' });
      fetchMaterials();
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteDeck = async () => {
    if (!selectedMaterialId || cards.length === 0) return;
    if (!window.confirm('Are you sure you want to delete this flashcard deck? This will clear all historical reviews.')) return;

    try {
      await api.delete(`${API_ENDPOINTS.FLASHCARDS.BASE}/${selectedMaterialId}`);
      setCards([]);
      
      // Sync materials status
      const materialsResp = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(materialsResp.data);
      toast.success('Flashcard deck deleted successfully.');
    } catch (err) {
      toast.error('Failed to delete deck: ' + parseError(err));
    }
  };

  const handleToggleMastered = async (card) => {
    try {
      const updatedMastered = !card.mastered;
      await api.patch(`${API_ENDPOINTS.FLASHCARDS.BASE}/${card.flashcard_id}/mastered`, {
        material_id: selectedMaterialId,
        mastered: updatedMastered
      });
      
      // Update local state
      setCards(prev => prev.map(c => c.flashcard_id === card.flashcard_id ? { ...c, mastered: updatedMastered } : c));
      toast.success(updatedMastered ? 'Marked card as Mastered!' : 'Marked card as Learning');
    } catch (err) {
      toast.error('Failed to toggle mastery: ' + parseError(err));
    }
  };

  const handleReviewAnswer = async (card, knewAnswer) => {
    try {
      const response = await api.patch(`${API_ENDPOINTS.FLASHCARDS.BASE}/${card.flashcard_id}/review`, {
        material_id: selectedMaterialId,
        know_answer: knewAnswer
      });
      
      // Update local state metrics
      setCards(prev => prev.map(c => 
        c.flashcard_id === card.flashcard_id 
          ? { 
              ...c, 
              review_count: response.data.review_count,
              last_reviewed: response.data.last_reviewed,
              next_review: response.data.next_review,
              interval_days: response.data.interval_days
            } 
          : c
      ));
      
      toast.success(knewAnswer ? 'SM-2: Interval extended!' : 'SM-2: Reset review interval');
      
      // Advance to next card automatically after review
      setTimeout(() => {
        handleNextCard();
      }, 300);
      
    } catch (err) {
      toast.error('Failed to save review session log: ' + parseError(err));
    }
  };

  const handleShuffle = () => {
    if (filteredCards.length <= 1) return;
    const shuffled = [...cards].sort(() => Math.random() - 0.5);
    setCards(shuffled);
    setCurrentIndex(0);
    setIsFlipped(false);
    toast.success('Deck shuffled!');
  };

  // Filter logic
  const filteredCards = cards.filter(c => {
    const matchesSearch = c.question.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          c.answer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTopic = selectedTopic === 'All' || c.topic === selectedTopic;
    const matchesDiff = selectedDifficulty === 'All' || c.difficulty === selectedDifficulty.toLowerCase();
    const matchesMastered = !hideMastered || !c.mastered;
    
    return matchesSearch && matchesTopic && matchesDiff && matchesMastered;
  });

  const activeCard = filteredCards[currentIndex] || null;

  const handleNextCard = () => {
    if (filteredCards.length === 0) return;
    setIsFlipped(false);
    setCurrentIndex(prev => (prev + 1) % filteredCards.length);
  };

  const handlePrevCard = () => {
    if (filteredCards.length === 0) return;
    setIsFlipped(false);
    setCurrentIndex(prev => (prev - 1 + filteredCards.length) % filteredCards.length);
  };

  // Progress metrics calculation
  const masteredCount = cards.filter(c => c.mastered).length;
  const totalCount = cards.length;
  const learningCount = totalCount - masteredCount;
  const completionPercent = totalCount > 0 ? Math.round((masteredCount / totalCount) * 100) : 0;

  return (
    <div className="space-y-8 animate-fadeIn select-none">
      {/* Header view */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Active Recall Flashcards
          </h1>
          <p className="text-dark-300 mt-1.5 text-sm">
            Retain details, terminology, and key concepts using SuperMemo-2 Spaced Repetition algorithms.
          </p>
        </div>
      </div>

      {loadingMaterials ? (
        <div className="flex items-center justify-center p-12 bg-dark-900 border border-dark-850 rounded-2xl">
          <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
        </div>
      ) : materials.length === 0 ? (
        /* Empty Materials State */
        <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center max-w-xl mx-auto mt-8">
          <div className="w-12 h-12 rounded-xl bg-dark-850 flex items-center justify-center text-emerald-400 mx-auto mb-4 border border-dark-800">
            <Layers className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">No study materials found</h2>
          <p className="text-sm text-dark-300 leading-relaxed max-w-sm mx-auto mb-6">
            To generate flashcard decks, please upload a document first.
          </p>
          <a
            href="/upload"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition-colors"
          >
            Go to Upload Page
          </a>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Controls Bar Selector */}
          <div className="flex flex-col lg:flex-row gap-4 bg-dark-900 p-4 rounded-xl border border-dark-850/60">
            <div className="flex-1">
              <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                Select Study Material
              </label>
              <select
                value={selectedMaterialId}
                onChange={(e) => setSelectedMaterialId(e.target.value)}
                disabled={generating || loadingDeck}
                className="w-full bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer disabled:opacity-50"
              >
                {materials.map((mat) => (
                  <option key={mat.id} value={mat.id}>
                    {mat.title} ({mat.subject})
                  </option>
                ))}
              </select>
            </div>
            
            {/* Subject Filters (Only render when cards exist) */}
            {cards.length > 0 && (
              <div className="flex flex-wrap gap-3 items-end">
                <div>
                  <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                    Topic
                  </label>
                  <select
                    value={selectedTopic}
                    onChange={(e) => { setSelectedTopic(e.target.value); setCurrentIndex(0); }}
                    className="bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none cursor-pointer"
                  >
                    {topicsList.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2">
                    Difficulty
                  </label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => { setSelectedDifficulty(e.target.value); setCurrentIndex(0); }}
                    className="bg-dark-950 border border-dark-800 rounded-xl py-3 px-4 text-xs text-white focus:outline-none cursor-pointer"
                  >
                    <option value="All">All</option>
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                
                <button
                  onClick={() => setHideMastered(prev => !prev)}
                  className={`flex items-center gap-1.5 px-4 py-3 rounded-xl border text-xs font-semibold cursor-pointer transition-colors ${hideMastered ? 'bg-emerald-600 border-emerald-500 text-white' : 'bg-dark-950 border-dark-800 text-dark-400 hover:text-white'}`}
                >
                  {hideMastered ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span>Hide Mastered</span>
                </button>
              </div>
            )}
          </div>

          {/* Loader and Main study views */}
          {generating ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-10 h-10 text-emerald-500 animate-spin" />
              <h3 className="text-white font-bold text-lg animate-pulse">Llama compiling flashcard deck...</h3>
              <p className="text-xs text-dark-450 max-w-sm">
                Structuring active-recall questions, defining categories, and setting initial spaced repetition factors.
              </p>
            </div>
          ) : loadingDeck ? (
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-24 text-center">
              <Loader2 className="w-8 h-8 text-emerald-500 animate-spin mx-auto" />
            </div>
          ) : cards.length === 0 ? (
            /* Un-generated state banner */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-6">
              <div className="w-14 h-14 rounded-full bg-emerald-950/40 border border-emerald-500/20 flex items-center justify-center text-emerald-400 animate-pulse">
                <CreditCard className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <h3 className="text-white font-bold text-lg">Generate Study Flashcard Deck</h3>
                <p className="text-xs text-dark-350 max-w-md leading-relaxed">
                  Automatically generate high-impact active recall cards from this document's AI summaries. No extra PDF processing required.
                </p>
              </div>
              <button
                onClick={() => handleGenerateDeck(false)}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition-all cursor-pointer shadow-lg hover:shadow-emerald-600/25"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate Flashcards</span>
              </button>
            </div>
          ) : filteredCards.length === 0 ? (
            /* Empty filters state */
            <div className="bg-dark-900 border border-dark-850 rounded-2xl p-12 text-center">
              <p className="text-sm text-dark-300">No cards matched your active filters or query. Try adjusting filters or hiding mastered cards.</p>
              <button
                onClick={() => { setSearchTerm(''); setSelectedTopic('All'); setSelectedDifficulty('All'); setHideMastered(false); }}
                className="mt-4 text-xs text-emerald-400 font-bold hover:underline"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            /* Main Deck Panel Views */
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Left Column: Progress dashboard metrics */}
              <div className="lg:col-span-1 space-y-6">
                <div className="bg-dark-900 border border-dark-850 rounded-2xl p-5 space-y-4">
                  <h4 className="text-[10px] font-bold text-dark-400 uppercase tracking-wider">
                    Learning Progress
                  </h4>
                  
                  {/* Progress Gauge */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-dark-400">Mastery Complete</span>
                      <span className="text-emerald-400 font-bold font-mono">{completionPercent}%</span>
                    </div>
                    <div className="w-full bg-dark-950 rounded-full h-2 border border-dark-800">
                      <div 
                        className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${completionPercent}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-center text-xs border-t border-dark-850 pt-4">
                    <div className="bg-dark-950 p-2 rounded-lg border border-dark-850">
                      <span className="block text-[8px] text-dark-500 font-bold uppercase">Mastered</span>
                      <span className="text-emerald-400 font-bold font-mono text-sm">{masteredCount}</span>
                    </div>
                    <div className="bg-dark-950 p-2 rounded-lg border border-dark-850">
                      <span className="block text-[8px] text-dark-500 font-bold uppercase">Learning</span>
                      <span className="text-amber-400 font-bold font-mono text-sm">{learningCount}</span>
                    </div>
                  </div>

                  {/* Actions Column buttons */}
                  <div className="border-t border-dark-850 pt-4 flex flex-col gap-2.5">
                    <button
                      onClick={handleShuffle}
                      className="w-full flex items-center justify-center gap-2 bg-dark-850 hover:bg-dark-800 text-white font-semibold py-2 rounded-xl text-xs border border-dark-800 cursor-pointer"
                    >
                      <Shuffle className="w-3.5 h-3.5 text-dark-400" />
                      <span>Shuffle Deck</span>
                    </button>
                    
                    <button
                      onClick={() => handleGenerateDeck(true)}
                      className="w-full flex items-center justify-center gap-2 bg-emerald-950/20 hover:bg-emerald-950/40 text-emerald-400 font-semibold py-2 rounded-xl text-xs border border-emerald-500/20 cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Regenerate Deck</span>
                    </button>
                    
                    <button
                      onClick={handleDeleteDeck}
                      className="w-full flex items-center justify-center gap-2 bg-red-950/20 hover:bg-red-950/40 text-red-400 font-semibold py-2 rounded-xl text-xs border border-red-500/20 cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete Deck</span>
                    </button>
                  </div>

                  {/* Shortcuts reminder list */}
                  <div className="border-t border-dark-850 pt-4 text-[10px] text-dark-400 space-y-1.5 font-mono">
                    <span className="block font-sans font-bold uppercase text-[9px] text-dark-500 mb-1">Study Shortcuts</span>
                    <div className="flex justify-between"><span>Space</span> <span>Flip card</span></div>
                    <div className="flex justify-between"><span>ArrowRight</span> <span>Next card</span></div>
                    <div className="flex justify-between"><span>ArrowLeft</span> <span>Previous card</span></div>
                  </div>
                </div>
              </div>

              {/* Right Column: Virtual Deck Flipping Area */}
              <div className="lg:col-span-3 space-y-6">
                {/* 3D Flip Card Container */}
                <div 
                  ref={deckContainerRef}
                  onClick={() => setIsFlipped(prev => !prev)}
                  className="w-full aspect-[16/10] min-h-[300px] cursor-pointer group select-none [perspective:1000px]"
                >
                  <div 
                    className={`relative w-full h-full duration-500 [transform-style:preserve-3d] ${isFlipped ? '[transform:rotateY(180deg)]' : ''}`}
                  >
                    {/* Front Side Card */}
                    <div className="absolute inset-0 w-full h-full bg-dark-900 border border-dark-850 rounded-3xl p-8 flex flex-col justify-between [backface-visibility:hidden]">
                      <div className="flex items-center justify-between">
                        <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest bg-emerald-950/30 border border-emerald-500/10 px-2 py-1 rounded">
                          {activeCard?.topic}
                        </span>
                        
                        <button
                          onClick={(e) => { e.stopPropagation(); handleToggleMastered(activeCard); }}
                          className={`p-1.5 rounded-lg border transition-colors ${activeCard?.mastered ? 'bg-emerald-600 border-emerald-500 text-white' : 'bg-dark-950 border-dark-850 text-dark-500 hover:text-white'}`}
                        >
                          <Star className="w-4 h-4 fill-current" />
                        </button>
                      </div>

                      {/* Question Text */}
                      <div className="text-center my-6 space-y-2">
                        <span className="block text-[9px] font-bold text-dark-500 uppercase tracking-widest font-mono">Question</span>
                        <h3 className="text-lg md:text-xl font-bold text-white leading-relaxed px-4">
                          {activeCard?.question}
                        </h3>
                      </div>

                      <div className="flex justify-between items-center text-xs text-dark-500 font-mono">
                        <span>Card {currentIndex + 1} of {filteredCards.length}</span>
                        <span className="flex items-center gap-1 hover:text-white transition-colors">
                          <Eye className="w-3.5 h-3.5" /> Click to reveal answer
                        </span>
                      </div>
                    </div>

                    {/* Back Side Card */}
                    <div className="absolute inset-0 w-full h-full bg-dark-900 border border-dark-850 rounded-3xl p-8 flex flex-col justify-between [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="flex items-center justify-between">
                        <span className="text-[9px] font-bold text-dark-400 uppercase tracking-widest bg-dark-950 border border-dark-800 px-2 py-1 rounded">
                          {activeCard?.difficulty.toUpperCase()}
                        </span>
                        <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest bg-emerald-950/30 border border-emerald-500/10 px-2 py-1 rounded">
                          Answer Card
                        </span>
                      </div>

                      {/* Answer Text */}
                      <div className="text-center my-6 space-y-2">
                        <span className="block text-[9px] font-bold text-dark-500 uppercase tracking-widest font-mono">Correct Answer</span>
                        <p className="text-sm md:text-base text-dark-150 leading-relaxed px-6 select-text">
                          {activeCard?.answer}
                        </p>
                      </div>

                      {/* Spaced repetition interaction options */}
                      <div className="flex justify-between items-center text-xs border-t border-dark-850/60 pt-4" onClick={(e) => e.stopPropagation()}>
                        <span className="text-dark-500 font-mono">Reviews: {activeCard?.review_count || 0}</span>
                        
                        <div className="flex gap-2.5">
                          <button
                            onClick={() => handleReviewAnswer(activeCard, false)}
                            className="bg-red-950/30 hover:bg-red-950/50 border border-red-500/20 hover:border-red-500/40 text-red-400 font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                          >
                            Need Review
                          </button>
                          <button
                            onClick={() => handleReviewAnswer(activeCard, true)}
                            className="bg-emerald-950/30 hover:bg-emerald-950/50 border border-emerald-500/20 hover:border-emerald-500/40 text-emerald-400 font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                          >
                            I Knew This
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Flip deck Controls navigation buttons */}
                <div className="flex justify-between items-center bg-dark-900 border border-dark-850 p-4 rounded-2xl">
                  <button
                    onClick={handlePrevCard}
                    className="flex items-center gap-1.5 text-xs text-dark-400 hover:text-white font-semibold cursor-pointer px-3 py-2 rounded-xl bg-dark-950 hover:bg-dark-850 border border-dark-850 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Previous</span>
                  </button>

                  <span className="text-xs text-dark-400 font-medium select-text">
                    Study session in progress
                  </span>

                  <button
                    onClick={handleNextCard}
                    className="flex items-center gap-1.5 text-xs text-dark-400 hover:text-white font-semibold cursor-pointer px-3 py-2 rounded-xl bg-dark-950 hover:bg-dark-850 border border-dark-850 transition-colors"
                  >
                    <span>Next</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Flashcards;
