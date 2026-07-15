import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const Upload = () => {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);

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
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      addFiles(e.target.files);
    }
  };

  const addFiles = (fileList) => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];
    
    const newFiles = Array.from(fileList).filter(file => {
      const isValid = validTypes.includes(file.type) || file.name.endsWith('.pdf') || file.name.endsWith('.docx') || file.name.endsWith('.txt');
      if (!isValid) {
        toast.error(`Invalid format: ${file.name}. Only PDF, DOCX, TXT allowed.`);
      }
      return isValid;
    });

    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles]);
      toast.success(`${newFiles.length} file(s) added successfully.`);
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    toast.success("File removed.");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Upload Study Material
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Select or drag and drop files you want to analyze, summarize, and use to generate study tools.
        </p>
      </div>

      {/* Upload Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer ${
          dragActive 
            ? 'border-primary-500 bg-primary-950/10' 
            : 'border-dark-800 bg-dark-900/40 hover:border-dark-750'
        }`}
      >
        <input
          type="file"
          id="file-upload"
          multiple
          accept=".pdf,.docx,.txt"
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <div className="p-4 rounded-full bg-dark-850 border border-dark-800 mb-4 text-primary-400 group-hover:scale-105 transition-transform">
          <UploadCloud className="w-10 h-10" />
        </div>

        <p className="text-sm font-semibold text-white">Drag & drop files here, or click to browse</p>
        <p className="text-xs text-dark-400 mt-2">Supports PDF, DOCX, TXT (Max 16MB)</p>
      </div>

      {/* Files List */}
      {files.length > 0 && (
        <div className="bg-dark-900 border border-dark-850 rounded-2xl p-6 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Added Documents ({files.length})</h2>
          <div className="divide-y divide-dark-850">
            {files.map((file, idx) => (
              <div key={idx} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded bg-dark-850 text-primary-400">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white max-w-xs md:max-w-md truncate">{file.name}</p>
                    <p className="text-xs text-dark-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(idx)}
                  className="text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-red-950/20 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={() => {
              toast.success("Processing starts in a future phase!");
            }}
            className="w-full mt-4 bg-primary-600 hover:bg-primary-500 text-white font-semibold py-3 px-4 rounded-xl shadow-lg transition-colors cursor-pointer"
          >
            Process Documents with AI
          </button>
        </div>
      )}
    </div>
  );
};

export default Upload;
