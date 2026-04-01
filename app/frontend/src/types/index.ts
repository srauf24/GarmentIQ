export interface LocationResponse {
  environment: string | null;
  inferred_geo: string | null;
  confidence: number | null;
  continent: string | null;
  country: string | null;
  city: string | null;
}

export interface AnnotationResponse {
  id: string;
  image_id: string;
  note: string | null;
  tags: string[] | null;
  created_by: string | null;
  created_at: string;
}

export interface ImageResponse {
  id: string;
  filename: string;
  original_filename: string;
  image_url: string;
  ai_description: string | null;
  garment_type: string | null;
  style: string | null;
  material: string | null;
  color_palette: string[] | null;
  pattern: string | null;
  season: string | null;
  occasion: string | null;
  consumer_profile: string | null;
  designer_brand: string | null;
  trend_notes: string | null;
  location: LocationResponse;
  uploaded_by: string | null;
  created_at: string;
  annotations: AnnotationResponse[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FilterValuesResponse {
  garment_type: string[];
  style: string[];
  material: string[];
  color_palette: string[];
  pattern: string[];
  season: string[];
  occasion: string[];
  consumer_profile: string[];
  designer_brand: string[];
  location_continent: string[];
  location_country: string[];
  location_city: string[];
  year: number[];
  month: number[];
  uploaded_by: string[];
}

export interface AnnotationCreate {
  note?: string | null;
  tags?: string[] | null;
  created_by?: string | null;
}

export interface ImageFilters {
  garment_type?: string;
  style?: string;
  material?: string;
  color_palette?: string;
  pattern?: string;
  season?: string;
  occasion?: string;
  consumer_profile?: string;
  designer_brand?: string;
  location_continent?: string;
  location_country?: string;
  location_city?: string;
  year?: number;
  month?: number;
  uploaded_by?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
