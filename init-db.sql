-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create recording table (replaces videos collection)
CREATE TABLE recording (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create analysis table (replaces analysis collection)
CREATE TABLE analysis (
    id BIGSERIAL PRIMARY KEY,
    recording_id BIGINT NOT NULL REFERENCES recording(id) ON DELETE CASCADE,
    total_frames INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_recording_analysis UNIQUE(recording_id)
);

-- Create frame_data table (stores timestamp information for each analyzed frame)
CREATE TABLE frame_data (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL REFERENCES analysis(id) ON DELETE CASCADE,
    timestamp TIME NOT NULL,
    frame_index INTEGER NOT NULL
);

-- Create audio_features table (stores audio analysis data separately from video frames)
CREATE TABLE audio_features (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT NOT NULL REFERENCES analysis(id) ON DELETE CASCADE,
    timestamp TIME NOT NULL,
    pitch_hz DOUBLE PRECISION,
    volume_db DOUBLE PRECISION,
    pitch_confidence DOUBLE PRECISION
);

-- Create landmark table (stores individual landmark data)
CREATE TABLE landmark (
    id BIGSERIAL PRIMARY KEY,
    frame_data_id BIGINT NOT NULL REFERENCES frame_data(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    z DOUBLE PRECISION NOT NULL,
    visibility DOUBLE PRECISION NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_analysis_recording ON analysis(recording_id);
CREATE INDEX idx_frame_data_analysis ON frame_data(analysis_id);
CREATE INDEX idx_audio_features_analysis ON audio_features(analysis_id);
CREATE INDEX idx_landmark_frame ON landmark(frame_data_id);
CREATE INDEX idx_landmark_type ON landmark(type);

-- Convert frame_data table to TimescaleDB hypertable (optional but recommended for time-series data)
-- This enables TimescaleDB's time-series optimizations
-- Note: You may want to add a proper timestamp column instead of using TIME type
-- For now, we'll create hypertable on created_at from analysis table
-- Uncomment the following if you want to enable TimescaleDB hypertable features:
-- SELECT create_hypertable('frame_data', 'id', chunk_time_interval => 1000);

COMMENT ON TABLE recording IS 'Stores video file metadata';
COMMENT ON TABLE analysis IS 'Stores analysis metadata for each recording (1:1 relationship)';
COMMENT ON TABLE frame_data IS 'Stores timestamp information for each analyzed frame (1:many with analysis)';
COMMENT ON TABLE audio_features IS 'Stores audio analysis data (pitch, volume) independently from video frames (1:many with analysis)';
COMMENT ON TABLE landmark IS 'Stores individual landmark coordinates (1:many with frame_data)';