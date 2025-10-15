import React, { useState, useCallback, useRef } from 'react';
import { Upload, X, File, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import type { Technology } from '../../types/technology';
import type { DocumentUploadResponse } from '../../types/knowledge';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, category: string, technologyId?: number, collection?: string) => Promise<DocumentUploadResponse>;
  technologies: Technology[];
  categories: string[];
  collections: string[];
  currentCollection: string;
}

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  onUpload,
  technologies,
  categories,
  collections,
  currentCollection,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState('');
  const [customCategory, setCustomCategory] = useState('');
  const [technologyId, setTechnologyId] = useState<number | undefined>(undefined);
  const [collection, setCollection] = useState(currentCollection);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetForm = useCallback(() => {
    setFile(null);
    setCategory('');
    setCustomCategory('');
    setTechnologyId(undefined);
    setCollection(currentCollection);
    setStatus('idle');
    setUploadResult(null);
    setError(null);
  }, [currentCollection]);

  const handleClose = useCallback(() => {
    resetForm();
    onClose();
  }, [resetForm, onClose]);

  const handleFileChange = useCallback((selectedFile: File | null) => {
    if (!selectedFile) return;

    const validExtensions = ['pdf', 'md', 'markdown', 'txt', 'text'];
    const extension = selectedFile.name.split('.').pop()?.toLowerCase();

    if (!extension || !validExtensions.includes(extension)) {
      setError('Invalid file type. Please upload PDF, Markdown, or Text files.');
      return;
    }

    setFile(selectedFile);
    setError(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFileChange(droppedFile);
      }
    },
    [handleFileChange]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!file) {
        setError('Please select a file to upload');
        return;
      }

      const finalCategory = category === 'custom' ? customCategory : category;

      if (!finalCategory) {
        setError('Please select or enter a category');
        return;
      }

      try {
        setStatus('uploading');
        setError(null);

        const result = await onUpload(file, finalCategory, technologyId, collection);

        setUploadResult(result);
        setStatus('success');

        // Auto-close after 3 seconds on success
        setTimeout(() => {
          handleClose();
        }, 3000);
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Upload failed');
      }
    },
    [file, category, customCategory, technologyId, collection, onUpload, handleClose]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-white">Upload Document</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-slate-400 transition-colors"
            disabled={status === 'uploading'}
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Document File
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragging
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <File className="text-primary-600" size={32} />
                  <div className="text-left">
                    <p className="font-medium text-white">{file.name}</p>
                    <p className="text-sm text-slate-500">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="ml-4 text-red-600 hover:text-red-700"
                  >
                    <X size={20} />
                  </button>
                </div>
              ) : (
                <div>
                  <Upload className="mx-auto text-gray-400 mb-3" size={48} />
                  <p className="text-slate-400 mb-2">
                    Drag and drop your file here, or click to browse
                  </p>
                  <p className="text-sm text-slate-500">
                    Supported formats: PDF, Markdown (.md), Text (.txt)
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.md,.markdown,.txt,.text"
                    onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    Choose File
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Category Selection */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-slate-300 mb-2">
              Category
            </label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            >
              <option value="">Select a category...</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
              <option value="custom">+ Add New Category</option>
            </select>

            {category === 'custom' && (
              <input
                type="text"
                value={customCategory}
                onChange={(e) => setCustomCategory(e.target.value)}
                placeholder="Enter category name"
                className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              />
            )}
          </div>

          {/* Technology Association (Optional) */}
          <div>
            <label htmlFor="technology" className="block text-sm font-medium text-slate-300 mb-2">
              Associated Technology (Optional)
            </label>
            <select
              id="technology"
              value={technologyId || ''}
              onChange={(e) => setTechnologyId(e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">None</option>
              {technologies.map((tech) => (
                <option key={tech.id} value={tech.id}>
                  {tech.title} - {tech.vendor}
                </option>
              ))}
            </select>
          </div>

          {/* Collection Selection */}
          <div>
            <label htmlFor="collection" className="block text-sm font-medium text-slate-300 mb-2">
              Collection
            </label>
            <select
              id="collection"
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            >
              {collections.map((coll) => (
                <option key={coll} value={coll}>
                  {coll}
                </option>
              ))}
            </select>
          </div>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Success Display */}
          {status === 'success' && uploadResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-800 mb-2">
                <CheckCircle size={20} />
                <span className="font-semibold">Upload Successful!</span>
              </div>
              <div className="text-sm text-green-700 space-y-1">
                <p>File: {uploadResult.filename}</p>
                <p>Chunks added: {uploadResult.chunks_added}</p>
                <p>Collection: {uploadResult.collection}</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              disabled={status === 'uploading'}
              className="px-4 py-2 text-slate-300 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={status === 'uploading' || status === 'success'}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {status === 'uploading' ? (
                <>
                  <Loader size={18} className="animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload size={18} />
                  <span>Upload</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
