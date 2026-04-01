import type { ImageResponse } from "../../types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ImageCardProps {
  image: ImageResponse;
  onClick: () => void;
}

export function ImageCard({ image, onClick }: ImageCardProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer overflow-hidden rounded-md border border-gray-200
                 bg-white shadow-sm transition-shadow hover:shadow-md group"
    >
      <div className="aspect-[3/4] overflow-hidden bg-gray-100">
        <img
          src={`${API_BASE}${image.image_url}`}
          alt={image.ai_description || image.original_filename}
          className="h-full w-full object-cover transition-transform duration-300
                     group-hover:scale-105"
          loading="lazy"
        />
      </div>
      <div className="space-y-1 p-3">
        {image.garment_type && (
          <span
            className="inline-block rounded-full bg-blue-100 px-2 py-0.5
                       text-xs font-medium text-blue-700"
          >
            {image.garment_type}
          </span>
        )}
        <div className="flex gap-2 text-xs text-gray-500">
          {image.style && <span>{image.style}</span>}
          {image.material && <span>&middot; {image.material}</span>}
        </div>
        {image.color_palette && (
          <div className="mt-1 flex gap-1">
            {image.color_palette.slice(0, 4).map((color, i) => (
              <span key={i} className="text-xs text-gray-400">
                {color}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
