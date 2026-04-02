import { useCallback, useState } from "react";

import { useCreateAnnotation } from "../../hooks/useCreateAnnotation";
import { useDeleteAnnotation } from "../../hooks/useDeleteAnnotation";
import type { AnnotationResponse } from "../../types";

interface AnnotationPanelProps {
  imageId: string;
  annotations: AnnotationResponse[];
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function AnnotationPanel({ imageId, annotations }: AnnotationPanelProps) {
  const [note, setNote] = useState("");
  const [tags, setTags] = useState("");
  const [createdBy, setCreatedBy] = useState("");

  const createMutation = useCreateAnnotation();
  const deleteMutation = useDeleteAnnotation();

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const tagList = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      await createMutation.mutateAsync({
        imageId,
        body: {
          note: note.trim() || undefined,
          tags: tagList.length > 0 ? tagList : undefined,
          created_by: createdBy.trim() || undefined,
        },
      });

      setNote("");
      setTags("");
      setCreatedBy("");
    },
    [imageId, note, tags, createdBy, createMutation],
  );

  const handleDelete = useCallback(
    (annotationId: string) => {
      deleteMutation.mutate({ imageId, annotationId });
    },
    [imageId, deleteMutation],
  );

  return (
    <div className="rounded-md border border-emerald-200 bg-emerald-50/50">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-emerald-200 px-4 py-3">
        <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
          Designer Notes
        </span>
        <h3 className="text-sm font-semibold text-gray-900">Annotations</h3>
        {annotations.length > 0 && (
          <span className="text-xs text-gray-400">({annotations.length})</span>
        )}
      </div>

      {/* Annotation list */}
      <div className="divide-y divide-emerald-100">
        {annotations.length === 0 && (
          <p className="px-4 py-6 text-center text-sm text-gray-400">
            No annotations yet. Add the first note below.
          </p>
        )}
        {annotations.map((ann) => (
          <div key={ann.id} className="px-4 py-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                {ann.note && (
                  <p className="text-sm text-gray-700">{ann.note}</p>
                )}
                {ann.tags && ann.tags.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {ann.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <div className="mt-1.5 flex gap-2 text-xs text-gray-400">
                  {ann.created_by && <span>{ann.created_by}</span>}
                  <span>{formatDate(ann.created_at)}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(ann.id)}
                disabled={deleteMutation.isPending}
                className="shrink-0 text-gray-400 hover:text-red-500 transition-colors"
                aria-label="Delete annotation"
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
                    d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                  />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add annotation form */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-emerald-200 px-4 py-3 space-y-3"
      >
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Add a note..."
          rows={2}
          disabled={createMutation.isPending}
          className="w-full rounded-sm border border-gray-300 px-3 py-2 text-sm
                     placeholder:text-gray-400
                     focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500
                     disabled:bg-gray-100"
        />
        <div className="flex gap-2">
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="Tags (comma-separated)"
            disabled={createMutation.isPending}
            className="flex-1 rounded-sm border border-gray-300 px-3 py-1.5 text-sm
                       placeholder:text-gray-400
                       focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500
                       disabled:bg-gray-100"
          />
          <input
            type="text"
            value={createdBy}
            onChange={(e) => setCreatedBy(e.target.value)}
            placeholder="Your name"
            disabled={createMutation.isPending}
            className="w-32 rounded-sm border border-gray-300 px-3 py-1.5 text-sm
                       placeholder:text-gray-400
                       focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500
                       disabled:bg-gray-100"
          />
        </div>

        {createMutation.error && (
          <p className="text-sm text-red-600">{createMutation.error.message}</p>
        )}

        <button
          type="submit"
          disabled={createMutation.isPending || (!note.trim() && !tags.trim())}
          className="inline-flex items-center gap-2 rounded-sm bg-emerald-600 px-3 py-1.5
                     text-sm font-medium text-white
                     hover:bg-emerald-700 transition-colors duration-150
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {createMutation.isPending ? "Adding..." : "Add Note"}
        </button>
      </form>
    </div>
  );
}
