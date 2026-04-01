import type {
  AnnotationCreate,
  AnnotationResponse,
  FilterValuesResponse,
  ImageFilters,
  ImageResponse,
  PaginatedResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  return handleResponse(res);
}

export async function fetchImages(
  params?: ImageFilters,
): Promise<PaginatedResponse<ImageResponse>> {
  const query = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, String(value));
      }
    }
  }
  const qs = query.toString();
  const url = `${API_BASE}/api/images${qs ? `?${qs}` : ""}`;
  const res = await fetch(url);
  return handleResponse(res);
}

export async function uploadImage(
  file: File,
  uploadedBy?: string,
): Promise<ImageResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (uploadedBy) {
    formData.append("uploaded_by", uploadedBy);
  }
  const res = await fetch(`${API_BASE}/api/images/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function fetchFilterValues(): Promise<FilterValuesResponse> {
  const res = await fetch(`${API_BASE}/api/filters`);
  return handleResponse(res);
}

export async function createAnnotation(
  imageId: string,
  body: AnnotationCreate,
): Promise<AnnotationResponse> {
  const res = await fetch(`${API_BASE}/api/images/${imageId}/annotations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function deleteAnnotation(
  imageId: string,
  annotationId: string,
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/api/images/${imageId}/annotations/${annotationId}`,
    { method: "DELETE" },
  );
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${detail}`);
  }
}
