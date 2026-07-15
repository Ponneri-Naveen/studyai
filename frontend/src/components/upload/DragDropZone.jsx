import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';

const DragDropZone = ({ onFilesSelected, isUploading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [subject, setSubject] = useState('General');
  const fileInputRef = useRef(null);

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

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (isUploading) return;
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndProcessFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (isUploading) return;
    if (e.target.files && e.target.files[0]) {
      validateAndProcessFiles(e.target.files);
    }
  };

  const validateAndProcessFiles = (fileList) => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];
    
    const acceptedFiles = Array.from(fileList).filter(file => {
      const extension = file.name.split('.').pop().toLowerCase();
      const isValidType = validTypes.includes(file.type) || 
                          file.name.endsWith('.pdf') || 
                          file.name.endsWith('.docx') || 
                          file.name.endsWith('.txt');
                          
      if (!isValidType) {
        toast.error(`Invalid format: ${file.name}. Only PDF, DOCX, TXT allowed.`);
        return false;
      }
      
      const isSizeValid = file.size <= 16 * 1024 * 1024;
      if (!isSizeValid) {
        toast.error(`File too large: ${file.name}. Maximum size limit is 16MB.`);
        return false;
      }
      
      return true;
    });

    if (acceptedFiles.length > 0) {
      onFilesSelected(acceptedFiles, subject);
      // Clear file input value to allow re-uploading the same file
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Subject Selector */}
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

      {/* Drag zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center transition-all duration-200 ${
          isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        } ${
          dragActive 
            ? 'border-primary-500 bg-primary-950/10 scale-[1.01]' 
            : 'border-dark-800 bg-dark-900/40 hover:border-dark-750'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          multiple
          accept=".pdf,.docx,.txt"
          onChange={handleChange}
          disabled={isUploading}
          className="hidden"
        />

        <div className="p-4 rounded-full bg-dark-850 border border-dark-800 mb-4 text-primary-400">
          <UploadCloud className="w-10 h-10" />
        </div>

        <p className="text-sm font-semibold text-white">Drag & drop documents here, or click to browse</p>
        <p className="text-xs text-dark-400 mt-2">Supports PDF, DOCX, TXT up to 16MB</p>

        <div className="mt-6 flex items-center gap-2 text-xs text-dark-500 bg-dark-900/60 py-1.5 px-3 rounded-lg border border-dark-850">
          <AlertTriangle className="w-3.5 h-3.5 text-primary-500" />
          <span>OCR for image-only scans is not supported in this version.</span>
        </div>
      </div>
    </div>
  );
};

export default DragDropZone;
