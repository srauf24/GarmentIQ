-- TG-002: Full schema for GarmentIQ

-- Images table
CREATE TABLE images (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path       VARCHAR(512) NOT NULL,

    -- AI-generated classification
    ai_description      TEXT,
    garment_type        VARCHAR(100),
    style               VARCHAR(100),
    material            VARCHAR(100),
    color_palette       TEXT[],
    pattern             VARCHAR(100),
    season              VARCHAR(50),
    occasion            VARCHAR(100),
    consumer_profile    VARCHAR(200),
    designer_brand      VARCHAR(200),
    trend_notes         TEXT,

    -- Location: AI-inferred
    location_environment    VARCHAR(100),
    location_inferred_geo   VARCHAR(200),
    location_confidence     FLOAT,

    -- Location: used for filters
    location_continent  VARCHAR(50),
    location_country    VARCHAR(100),
    location_city       VARCHAR(100),

    -- Upload metadata
    uploaded_by     VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Full-text search
    search_vector   TSVECTOR
);

-- Annotations table
CREATE TABLE annotations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id    UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    note        TEXT,
    tags        TEXT[],
    created_by  VARCHAR(100),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- B-tree indexes on filter columns
CREATE INDEX idx_images_garment_type ON images(garment_type);
CREATE INDEX idx_images_style ON images(style);
CREATE INDEX idx_images_material ON images(material);
CREATE INDEX idx_images_pattern ON images(pattern);
CREATE INDEX idx_images_season ON images(season);
CREATE INDEX idx_images_occasion ON images(occasion);
CREATE INDEX idx_images_location_continent ON images(location_continent);
CREATE INDEX idx_images_location_country ON images(location_country);
CREATE INDEX idx_images_location_city ON images(location_city);

-- GIN indexes for full-text search and array queries
CREATE INDEX idx_images_search_vector ON images USING GIN(search_vector);
CREATE INDEX idx_annotations_tags ON annotations USING GIN(tags);

-- Trigger function: build weighted tsvector on insert/update
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.ai_description, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.trend_notes, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.garment_type, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.style, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.material, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.pattern, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.season, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.occasion, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.designer_brand, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_update_search_vector
    BEFORE INSERT OR UPDATE ON images
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();
