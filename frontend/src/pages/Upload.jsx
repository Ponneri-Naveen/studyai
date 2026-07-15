import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, FileText, FileWarning, Eye, Trash2, 
  Sparkles, X, BookOpen, CheckCircle, HelpCircle, Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';

import api from '../services/api';
import { API_ENDPOINTS } from '../constants';
import { parseError } from '../utils/errorParser';

// Components
import DragDropZone from '../components/upload/DragDropZone';
import ManualTextInput from '../components/upload/ManualTextInput';
import UploadProgress from '../components/upload/UploadProgress';
import MaterialList from '../components/upload/MaterialList';
import { MaterialCardSkeleton } from '../components/ui/Skeleton';

const Upload = () => {
  const [materials, setMaterials] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('file'); // 'file' or 'text'
  
  // Ingestion states
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');

  // Viewer state
  const [viewerMaterial, setViewerMaterial] = useState(null);
  const [isViewerLoading, setIsViewerLoading] = useState(false);

  // Duplicate prompt state
  const [duplicatePrompt, setDuplicatePrompt] = useState(null);

  useEffect(() => {
    fetchMaterials();
  }, []);

  const fetchMaterials = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(API_ENDPOINTS.MATERIALS.BASE);
      setMaterials(response.data);
    } catch (err) {
      toast.error('Failed to load study materials: ' + parseError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const executeFileUpload = async (file, subject, force = false) => {
    setIsUploading(true);
    setUploadProgress(0);
    setProgressMessage(`Ingesting ${file.name}...`);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject', subject);

    try {
      const endpoint = force 
        ? `${API_ENDPOINTS.MATERIALS.UPLOAD}?force=true` 
        : API_ENDPOINTS.MATERIALS.UPLOAD;

      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
          if (percentCompleted === 100) {
            setProgressMessage('Extracting document text and statistics...');
          }
        },
      });

      // Handle duplicate warnings
      if (response.data && response.data.warning === 'duplicate_detected') {
        // Trigger verification confirm
        setDuplicatePrompt({
          file,
          subject,
          message: response.data.message
        });
        setIsUploading(false);
        return;
      }

      toast.success(`${file.name} uploaded and processed successfully!`);
      fetchMaterials();
    } catch (err) {
      toast.error(`Upload failed: ${parseError(err)}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleFilesSelected = (files, subject) => {
    // Process first file (upload page is single/multi-file sequential)
    if (files && files[0]) {
      executeFileUpload(files[0], subject, false);
    }
  };

  const handleTextSubmit = async ({ title, subject, text }) => {
    setIsUploading(true);
    setUploadProgress(40);
    setProgressMessage('Saving notes...');
    
    try {
      await api.post(API_ENDPOINTS.MATERIALS.TEXT, {
        title,
        subject,
        text
      });
      setUploadProgress(100);
      toast.success(`Notes "${title}" saved successfully!`);
      fetchMaterials();
    } catch (err) {
      toast.error(`Ingestion failed: ${parseError(err)}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to permanently delete this material?')) {
      return;
    }
    
    try {
      await api.delete(`${API_ENDPOINTS.MATERIALS.BASE}/${id}`);
      toast.success('Material deleted successfully.');
      fetchMaterials();
    } catch (err) {
      toast.error('Failed to delete material: ' + parseError(err));
    }
  };

  const handleView = async (item) => {
    setIsViewerLoading(true);
    try {
      const response = await api.get(`${API_ENDPOINTS.MATERIALS.BASE}/${item.id}`);
      setViewerMaterial(response.data);
    } catch (err) {
      toast.error('Failed to load text details: ' + parseError(err));
    } finally {
      setIsViewerLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2 font-display">
          Study Materials Ingestion <Sparkles className="w-6 h-6 text-primary-400" />
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Load your textbooks, notes or study guides. StudyAI will extract text contents and build structured models.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-850 gap-4">
        <button
          onClick={() => !isUploading && setActiveTab('file')}
          disabled={isUploading}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === 'file' 
              ? 'border-primary-500 text-primary-400' 
              : 'border-transparent text-dark-400 hover:text-white'
          } disabled:opacity-50`}
        >
          Upload Document (.pdf, .docx, .txt)
        </button>
        <button
          onClick={() => !isUploading && setActiveTab('text')}
          disabled={isUploading}
          className={`pb-3 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === 'text' 
              ? 'border-primary-500 text-primary-400' 
              : 'border-transparent text-dark-400 hover:text-white'
          } disabled:opacity-50`}
        >
          Copy & Paste Notes
        </button>
      </div>

      {/* Upload panels / loaders */}
      {isUploading ? (
        <UploadProgress progress={uploadProgress} message={progressMessage} />
      ) : activeTab === 'file' ? (
        <DragDropZone onFilesSelected={handleFilesSelected} isUploading={isUploading} />
      ) : (
        <ManualTextInput onSubmit={handleTextSubmit} isUploading={isUploading} />
      )}

      {/* List section */}
      <div className="border-t border-dark-850 pt-8">
        {isLoading ? (
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-dark-350 uppercase tracking-wider mb-2">
              Loading Materials...
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MaterialCardSkeleton />
              <MaterialCardSkeleton />
            </div>
          </div>
        ) : (
          <MaterialList 
            materials={materials} 
            onDelete={handleDelete} 
            onView={handleView} 
          />
        )}
      </div>

      {/* Duplicate override Modal */}
      {duplicatePrompt && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-950 text-primary-400 border border-primary-800 mx-auto">
              <HelpCircle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white text-center">Duplicate File Detected</h3>
            <p className="text-sm text-dark-300 text-center leading-relaxed">
              {duplicatePrompt.message} Would you like to upload it as a new duplicate copy anyway?
            </p>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setDuplicatePrompt(null)}
                className="flex-1 bg-dark-850 hover:bg-dark-800 border border-dark-800 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
              >
                No, Cancel
              </button>
              <button
                onClick={() => {
                  const { file, subject } = duplicatePrompt;
                  setDuplicatePrompt(null);
                  executeFileUpload(file, subject, true);
                }}
                className="flex-1 bg-primary-600 hover:bg-primary-500 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors cursor-pointer"
              >
                Yes, Upload
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Extracted Text Modal Viewer */}
      {viewerMaterial && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl w-full max-w-3xl h-[80vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-dark-850 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-primary-950/40 text-primary-400 border border-primary-900/10">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white max-w-xs md:max-w-md truncate" title={viewerMaterial.title}>
                    {viewerMaterial.title}
                  </h3>
                  <span className="inline-block text-[10px] font-semibold text-primary-400 bg-primary-950/40 px-2 rounded">
                    {viewerMaterial.subject}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setViewerMaterial(null)}
                className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-850 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 p-6 overflow-y-auto bg-dark-950 text-dark-200 font-sans text-sm leading-relaxed whitespace-pre-wrap select-text">
              {viewerMaterial.extracted_text || 'No text extracted.'}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-dark-850 bg-dark-900 flex justify-between items-center text-xs text-dark-500">
              <div className="flex gap-4">
                <span><strong>Pages:</strong> {viewerMaterial.page_count}</span>
                <span><strong>Words:</strong> {viewerMaterial.word_count}</span>
                <span><strong>Characters:</strong> {viewerMaterial.character_count}</span>
              </div>
              <button
                onClick={() => setViewerMaterial(null)}
                className="bg-primary-650 hover:bg-primary-550 text-white font-bold px-4 py-2 rounded-xl transition-colors cursor-pointer"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* In-Modal loader overlay */}
      {isViewerLoading && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50">
          <div className="bg-dark-900 border border-dark-800 p-4 rounded-xl flex items-center gap-3 text-white">
            <Loader2 className="w-5 h-5 animate-spin text-primary-400" />
            <span className="text-sm font-semibold">Loading material data...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;
