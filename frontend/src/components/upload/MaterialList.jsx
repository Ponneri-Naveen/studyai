import React, { useState } from 'react';
import { 
  FileText, Trash2, Eye, Calendar, HardDrive, 
  BookOpen, Clock, FileWarning, HelpCircle 
} from 'lucide-react';
import toast from 'react-hot-toast';

const MaterialList = ({ materials, onDelete, onView }) => {
  const [selectedMaterial, setSelectedMaterial] = useState(null);

  const getFileTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'pdf':
        return 'bg-red-950/40 text-red-400 border border-red-900/20';
      case 'docx':
        return 'bg-blue-950/40 text-blue-400 border border-blue-900/20';
      case 'txt':
      case 'text_paste':
        return 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/20';
      default:
        return 'bg-dark-850 text-dark-300';
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!materials || materials.length === 0) {
    return (
      <div className="bg-dark-900 border border-dark-850 rounded-2xl p-10 text-center">
        <FileWarning className="w-10 h-10 text-dark-500 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-white mb-1">No uploaded materials yet</h3>
        <p className="text-xs text-dark-400 max-w-xs mx-auto leading-relaxed">
          Your active study notes will appear here. Choose a file or paste text above to start.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-bold text-dark-305 uppercase tracking-wider mb-2">
        Ingested Study Materials ({materials.length})
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {materials.map((item) => (
          <div 
            key={item.id} 
            className="bg-dark-900 border border-dark-850 rounded-xl p-5 hover:border-dark-750 transition-all duration-200 flex flex-col justify-between"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg flex-shrink-0 ${getFileTypeIcon(item.file_type)}`}>
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white max-w-[180px] md:max-w-[240px] truncate" title={item.title}>
                      {item.title}
                    </h4>
                    <span className="inline-block mt-1 text-[10px] font-semibold text-primary-400 bg-primary-950/40 px-2 py-0.5 rounded border border-primary-900/10">
                      {item.subject}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => onView(item)}
                    className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-800 transition-colors cursor-pointer"
                    title="View Extracted Text"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDelete(item.id)}
                    className="p-1.5 rounded-lg text-red-500/80 hover:text-red-400 hover:bg-red-950/20 transition-colors cursor-pointer"
                    title="Delete Material"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Statistics Details */}
              <div className="grid grid-cols-3 gap-2 mt-5 text-[10px] text-dark-450 border-t border-dark-850 pt-3">
                <div>
                  <span className="block font-semibold text-dark-350">Pages</span>
                  <span className="text-white font-medium">{item.page_count || 1}</span>
                </div>
                <div>
                  <span className="block font-semibold text-dark-350">Words</span>
                  <span className="text-white font-medium">{item.word_count || 0}</span>
                </div>
                <div>
                  <span className="block font-semibold text-dark-350">Characters</span>
                  <span className="text-white font-medium">{item.character_count || 0}</span>
                </div>
              </div>
            </div>

            {/* File metadata footer */}
            <div className="flex items-center justify-between text-[10px] text-dark-500 mt-4 border-t border-dark-850/50 pt-2">
              <span className="flex items-center gap-1">
                <HardDrive className="w-3 h-3" />
                {formatBytes(item.size_bytes)}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MaterialList;
