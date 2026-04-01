import { useState } from "react";
import { Route, Routes } from "react-router-dom";

import { UploadModal } from "./components/UploadModal";
import { GalleryPage } from "./pages/GalleryPage";

export function App() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-8 py-4">
        <h1 className="text-xl font-semibold text-gray-900">GarmentIQ</h1>
        <button
          type="button"
          onClick={() => setUploadOpen(true)}
          className="inline-flex items-center gap-2 rounded-sm bg-brand-600 px-4 py-2
                     text-sm font-medium text-white
                     hover:bg-brand-700 transition-colors duration-150"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          Upload
        </button>
      </header>

      {/* Content area */}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<GalleryPage />} />
        </Routes>
      </main>

      {/* Upload modal */}
      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
      />
    </div>
  );
}
