import { useCallback, useEffect, useRef, useState } from "react";

import { useUploadImage } from "../hooks/useUploadImage";

const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function UploadModal({ isOpen, onClose, onSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploadedBy, setUploadedBy] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const upload = useUploadImage();

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setFile(null);
      setPreview(null);
      setUploadedBy("");
      setDragOver(false);
      setValidationError(null);
      upload.reset();
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // Clean up preview URL
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  // Focus trap: focus modal on open
  useEffect(() => {
    if (isOpen && modalRef.current) {
      modalRef.current.focus();
    }
  }, [isOpen]);

  const validateFile = useCallback((f: File): string | null => {
    if (!ACCEPTED_TYPES.includes(f.type)) {
      return "Please select an image file (JPEG, PNG, WebP, or GIF).";
    }
    if (f.size > MAX_FILE_SIZE_BYTES) {
      return `File size exceeds ${MAX_FILE_SIZE_MB}MB limit.`;
    }
    return null;
  }, []);

  const handleFileSelect = useCallback(
    (f: File) => {
      const error = validateFile(f);
      if (error) {
        setValidationError(error);
        setFile(null);
        setPreview(null);
        return;
      }
      setValidationError(null);
      setFile(f);
      if (preview) URL.revokeObjectURL(preview);
      setPreview(URL.createObjectURL(f));
    },
    [validateFile, preview],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) handleFileSelect(dropped);
    },
    [handleFileSelect],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) handleFileSelect(selected);
    },
    [handleFileSelect],
  );

  const handleUpload = useCallback(async () => {
    if (!file) return;
    try {
      await upload.mutateAsync({
        file,
        uploadedBy: uploadedBy.trim() || undefined,
      });
      onSuccess?.();
      onClose();
    } catch {
      // Error state is managed by useMutation
    }
  }, [file, uploadedBy, upload, onSuccess, onClose]);

  if (!isOpen) return null;

  const isLoading = upload.isPending;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Upload garment image"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Modal panel */}
      <div
        ref={modalRef}
        tabIndex={-1}
        className="relative z-10 w-full max-w-lg rounded-md bg-white p-6 shadow-xl
                   animate-[fadeInScale_200ms_ease-out]"
      >
        <h2 className="text-lg font-semibold text-gray-900">
          Upload Garment Image
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Select or drag an image to classify with AI.
        </p>

        {/* Drop zone */}
        <div
          className={`mt-4 flex flex-col items-center justify-center rounded-md border-2 border-dashed
                      p-8 transition-colors duration-150 cursor-pointer
                      ${dragOver ? "border-brand-500 bg-brand-50" : "border-gray-300 hover:border-gray-400"}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          {preview ? (
            <img
              src={preview}
              alt="Preview"
              className="max-h-48 rounded-sm object-contain"
            />
          ) : (
            <>
              <svg
                className="h-10 w-10 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                Drag and drop an image, or{" "}
                <span className="font-medium text-brand-600">browse</span>
              </p>
              <p className="mt-1 text-xs text-gray-400">
                JPEG, PNG, WebP, or GIF up to {MAX_FILE_SIZE_MB}MB
              </p>
            </>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleInputChange}
          />
        </div>

        {file && (
          <p className="mt-2 text-sm text-gray-600 truncate">{file.name}</p>
        )}

        {/* Validation / mutation error */}
        {(validationError || upload.error) && (
          <p className="mt-2 text-sm text-red-600">
            {validationError || upload.error?.message}
          </p>
        )}

        {/* Uploaded by field */}
        <div className="mt-4">
          <label
            htmlFor="uploaded-by"
            className="block text-sm font-medium text-gray-700"
          >
            Uploaded by{" "}
            <span className="font-normal text-gray-400">(optional)</span>
          </label>
          <input
            id="uploaded-by"
            type="text"
            value={uploadedBy}
            onChange={(e) => setUploadedBy(e.target.value)}
            placeholder="e.g. designer1"
            disabled={isLoading}
            className="mt-1 block w-full rounded-sm border border-gray-300 px-3 py-2 text-sm
                       placeholder:text-gray-400
                       focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500
                       disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-sm px-4 py-2 text-sm font-medium text-gray-700
                       hover:bg-gray-100 transition-colors duration-150
                       disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || isLoading}
            className="inline-flex items-center gap-2 rounded-sm bg-brand-600 px-4 py-2
                       text-sm font-medium text-white
                       hover:bg-brand-700 transition-colors duration-150
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading && (
              <svg
                className="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            )}
            {isLoading ? "Uploading..." : "Upload"}
          </button>
        </div>
      </div>
    </div>
  );
}
