import type { ImageResponse } from "../../types";

interface AttributePanelProps {
  image: ImageResponse;
}

function AttributeRow({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="flex justify-between py-1.5 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  );
}

export function AttributePanel({ image }: AttributePanelProps) {
  const loc = image.location;
  const hasLocation = loc.continent || loc.country || loc.city || loc.environment;

  return (
    <div className="rounded-md border border-indigo-200 bg-indigo-50/50">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-indigo-200 px-4 py-3">
        <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
          AI Generated
        </span>
        <h3 className="text-sm font-semibold text-gray-900">Classification</h3>
      </div>

      {/* Attributes */}
      <div className="divide-y divide-indigo-100 px-4">
        <AttributeRow label="Type" value={image.garment_type} />
        <AttributeRow label="Style" value={image.style} />
        <AttributeRow label="Material" value={image.material} />
        <AttributeRow label="Pattern" value={image.pattern} />
        <AttributeRow label="Season" value={image.season} />
        <AttributeRow label="Occasion" value={image.occasion} />
        <AttributeRow label="Consumer" value={image.consumer_profile} />
        <AttributeRow label="Brand" value={image.designer_brand} />

        {/* Color palette */}
        {image.color_palette && image.color_palette.length > 0 && (
          <div className="flex items-center justify-between py-1.5 text-sm">
            <span className="text-gray-500">Colors</span>
            <div className="flex flex-wrap gap-1">
              {image.color_palette.map((color, i) => (
                <span
                  key={i}
                  className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700"
                >
                  {color}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Trend notes */}
      {image.trend_notes && (
        <div className="border-t border-indigo-200 px-4 py-3">
          <p className="text-xs font-medium text-gray-500">Trend Notes</p>
          <p className="mt-1 text-sm text-gray-700">{image.trend_notes}</p>
        </div>
      )}

      {/* Location */}
      {hasLocation && (
        <div className="border-t border-indigo-200 px-4 py-3">
          <p className="text-xs font-medium text-gray-500">Location</p>
          <div className="mt-1 space-y-0.5 text-sm text-gray-700">
            {loc.environment && <p>{loc.environment}</p>}
            {(loc.city || loc.country || loc.continent) && (
              <p>
                {[loc.city, loc.country, loc.continent]
                  .filter(Boolean)
                  .join(", ")}
              </p>
            )}
            {loc.confidence != null && (
              <p className="text-xs text-gray-400">
                Confidence: {Math.round(loc.confidence * 100)}%
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
