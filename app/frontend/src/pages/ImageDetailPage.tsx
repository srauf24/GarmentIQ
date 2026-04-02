import { useNavigate, useParams } from "react-router-dom";

import { AnnotationPanel } from "../components/ImageDetail/AnnotationPanel";
import { AttributePanel } from "../components/ImageDetail/AttributePanel";
import { useImage } from "../hooks/useImage";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function ImageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: image, isLoading, isError, error } = useImage(id!);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <svg
          className="h-8 w-8 animate-spin text-brand-600"
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
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-8 mt-6 rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-700">
          Failed to load image.{" "}
          {error?.message && (
            <span className="text-red-500">{error.message}</span>
          )}
        </p>
      </div>
    );
  }

  if (!image) return null;

  return (
    <div className="px-8 py-6">
      {/* Back button */}
      <button
        type="button"
        onClick={() => navigate("/")}
        className="mb-4 inline-flex items-center gap-1 text-sm text-gray-500
                   hover:text-gray-700 transition-colors"
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
            d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
          />
        </svg>
        Back to gallery
      </button>

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: image + description */}
        <div>
          <div className="overflow-hidden rounded-md border border-gray-200 bg-gray-100">
            <img
              src={`${API_BASE}${image.image_url}`}
              alt={image.ai_description || image.original_filename}
              className="h-auto w-full object-contain"
            />
          </div>

          {image.ai_description && (
            <div className="mt-4 rounded-md border border-gray-200 bg-white p-4">
              <p className="text-xs font-medium text-gray-400">AI Description</p>
              <p className="mt-1 text-sm leading-relaxed text-gray-700">
                {image.ai_description}
              </p>
            </div>
          )}

          <p className="mt-2 text-xs text-gray-400">
            {image.original_filename}
            {image.uploaded_by && <span> &middot; by {image.uploaded_by}</span>}
            {image.created_at && (
              <span>
                {" "}
                &middot;{" "}
                {new Date(image.created_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            )}
          </p>
        </div>

        {/* Right: panels */}
        <div className="space-y-4">
          <AttributePanel image={image} />
          <AnnotationPanel
            imageId={image.id}
            annotations={image.annotations}
          />
        </div>
      </div>
    </div>
  );
}
