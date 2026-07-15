import React from 'react';
import { Loader2 } from 'lucide-react';

const UploadProgress = ({ progress, message }) => {
  return (
    <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl flex flex-col items-center justify-center space-y-4">
      <div className="flex items-center gap-3 text-primary-400 font-semibold text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>{message || 'Uploading and parsing document content...'}</span>
      </div>

      <div className="w-full bg-dark-950 rounded-full h-2.5 overflow-hidden border border-dark-850">
        <div 
          className="bg-primary-600 h-2.5 rounded-full transition-all duration-300 ease-out" 
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <div className="text-xs text-dark-400 font-medium">
        {progress}% Complete
      </div>
    </div>
  );
};

export default UploadProgress;
