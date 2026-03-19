-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create recording table (replaces videos collection)
CREATE TABLE recording
(
    id         BIGSERIAL PRIMARY KEY,
    filename   VARCHAR(255) NOT NULL,
    fps        DOUBLE PRECISION NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Create frame_data table (stores timestamp information for each analyzed frame)
CREATE TABLE frame_data
(
    id           BIGSERIAL PRIMARY KEY,
    recording_id BIGINT  NOT NULL REFERENCES recording (id) ON DELETE CASCADE,
    timestamp    TIME    NOT NULL,
    frame_index  INTEGER NOT NULL
);

-- Create landmark table (stores individual landmark data)
CREATE TABLE landmark
(
    id            BIGSERIAL PRIMARY KEY,
    frame_data_id BIGINT           NOT NULL REFERENCES frame_data (id) ON DELETE CASCADE,
    type          VARCHAR(50)      NOT NULL,
    x             DOUBLE PRECISION NOT NULL,
    y             DOUBLE PRECISION NOT NULL,
    z             DOUBLE PRECISION NOT NULL,
    visibility    DOUBLE PRECISION NOT NULL
);

-- Create word table (stores individual transcript words with timestamps)
CREATE TABLE word
(
    id           BIGSERIAL PRIMARY KEY,
    recording_id BIGINT           NOT NULL REFERENCES recording (id) ON DELETE CASCADE,
    start_time   DOUBLE PRECISION NOT NULL,
    end_time     DOUBLE PRECISION NOT NULL,
    word         TEXT             NOT NULL,
    probability  DOUBLE PRECISION NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_frame_data_recording ON frame_data (recording_id);
CREATE INDEX idx_landmark_frame ON landmark (frame_data_id);
CREATE INDEX idx_landmark_type ON landmark (type);
CREATE INDEX idx_word_recording ON word (recording_id);
CREATE INDEX idx_word_time ON word (recording_id, start_time);

-- Convert frame_data table to TimescaleDB hypertable (optional but recommended for time-series data)
-- This enables TimescaleDB's time-series optimizations
-- Note: You may want to add a proper timestamp column instead of using TIME type
-- Uncomment the following if you want to enable TimescaleDB hypertable features:
-- SELECT create_hypertable('frame_data', 'id', chunk_time_interval => 1000);

COMMENT ON TABLE recording IS 'Stores video file metadata';
COMMENT ON TABLE frame_data IS 'Stores timestamp information for each analyzed frame (1:many with recording)';
COMMENT ON TABLE audio_features IS 'Stores audio analysis data (pitch, volume) independently from video frames (1:many with recording)';
COMMENT ON TABLE landmark IS 'Stores individual landmark coordinates (1:many with frame_data)';
COMMENT ON TABLE word IS 'Stores transcribed words with timestamps and confidence scores from Whisper (1:many with recording)';