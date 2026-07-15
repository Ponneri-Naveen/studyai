import React, { useState } from 'react';
import { FileText, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

const ManualTextInput = ({ onSubmit, isUploading }) => {
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('General');
  const [text, setText] = useState('');

  const subjectsList = [
    'General',
    'Mathematics',
    'Physics',
    'Chemistry',
    'Biology',
    'Computer Science',
    'Literature',
    'History',
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title || !title.trim()) {
      toast.error('Please specify a title for this note.');
      return;
    }
    if (!text || !text.trim()) {
      toast.error('Please paste or type your note content.');
      return;
    }
    
    onSubmit({ title: title.trim(), subject, text: text.trim() });
    
    // Clear input fields on submit success (handled in parent or here)
    setTitle('');
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Title & Subject Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-dark-350 uppercase tracking-wider mb-2">
            Material Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isUploading}
            placeholder="e.g. Chapter 3 Notes"
            className="w-full bg-dark-900 border border-dark-800 rounded-xl py-3 px-4 text-sm text-white focus:outline-none focus:border-primary-500 transition-colors disabled:opacity-50"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-dark-350 uppercase tracking-wider mb-2">
            Select Subject Classification
          </label>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isUploading}
            className="w-full bg-dark-900 border border-dark-800 rounded-xl py-3 px-4 text-sm text-white focus:outline-none focus:border-primary-500 transition-colors disabled:opacity-50"
          >
            {subjectsList.map((sub) => (
              <option key={sub} value={sub}>{sub}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Copy-Paste Text Area */}
      <div>
        <label className="block text-xs font-semibold text-dark-350 uppercase tracking-wider mb-2">
          Study Notes / Text Content
        </label>
        <textarea
          rows={8}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isUploading}
          placeholder="Paste or type your study notes here..."
          className="w-full bg-dark-900 border border-dark-800 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-primary-500 transition-colors disabled:opacity-50 font-sans resize-y"
          required
        />
        <div className="flex justify-between items-center mt-2 text-xs text-dark-500">
          <span>Character count: {text.length}</span>
          <span>Max 1,000,000 characters</span>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isUploading}
        className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 text-white font-semibold py-3 px-4 rounded-xl shadow-lg hover:shadow-primary-600/20 transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing Text Ingestion...</span>
          </>
        ) : (
          <>
            <FileText className="w-4 h-4" />
            <span>Save Copied Text Material</span>
          </>
        )}
      </button>
    </form>
  );
};

export default ManualTextInput;
