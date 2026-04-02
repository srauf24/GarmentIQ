import { useNavigate } from "react-router-dom";

import type { ImageResponse } from "../../types";
import { ImageCard } from "./ImageCard";

interface ImageGridProps {
  images: ImageResponse[];
  isLoading: boolean;
}

export function ImageGrid({ images, isLoading }: ImageGridProps) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="aspect-[3/4] animate-pulse rounded-md bg-gray-200"
          />
        ))}
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg text-gray-400">No images yet</p>
        <p className="mt-1 text-sm text-gray-400">
          Upload your first garment photo to get started
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {images.map((image) => (
        <ImageCard
          key={image.id}
          image={image}
          onClick={() => navigate(`/images/${image.id}`)}
        />
      ))}
    </div>
  );
}
