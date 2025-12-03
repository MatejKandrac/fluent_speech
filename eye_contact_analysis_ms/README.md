# Eye Contact Analysis Service

A microservice that analyzes head pose and gaze direction in presentation videos to provide feedback on eye contact with the audience.

## What This Service Does

This service takes facial landmark data from videos and analyzes head orientation to:
- Track where the presenter is looking throughout the presentation
- Detect when the presenter looks away from the audience
- Generate a heatmap showing gaze distribution
- Calculate eye contact statistics

## Analysis Pipeline

The service processes data in 6 steps:

### Step 1: Fetch Data
Retrieves facial landmark data from the database for a given recording ID.

**Required landmarks:** nose, left_eye, right_eye, left_ear, right_ear

### Step 2: Calculate Head Angles
Computes yaw (left-right) and pitch (up-down) angles from facial landmarks.

#### Yaw Calculation (Horizontal Rotation)

**What is yaw?**
- Negative yaw = looking left
- Positive yaw = looking right
- 0° = looking straight ahead
- Range: -60° to +60°

**How it's calculated:**

1. **Calculate ear ratio** (which ear is closer to the nose):
   ```
   dist_to_left_ear = distance(nose, left_ear)
   dist_to_right_ear = distance(nose, right_ear)
   ear_ratio = dist_to_left_ear / dist_to_right_ear
   ```

   - `ear_ratio < 1.0` → left ear is closer → looking left
   - `ear_ratio > 1.0` → right ear is closer → looking right
   - `ear_ratio ≈ 1.0` → both ears equidistant → looking forward

2. **Convert ear ratio to angle using logarithm** (for smooth transitions):
   ```
   ear_yaw = log(ear_ratio) × 50
   ```

3. **Calculate nose offset** (where nose is relative to face center):
   ```
   face_center_x = (left_eye.x + right_eye.x) / 2
   nose_offset_x = nose.x - face_center_x
   nose_yaw = nose_offset_x × 100
   ```

4. **Combine both signals** (weighted average):
   ```
   yaw = ear_yaw × 0.7 + nose_yaw × 0.3
   ```

   Ear ratio is weighted more heavily because it's more reliable.

5. **Clamp to valid range**:
   ```
   yaw = max(-60, min(60, yaw))
   ```

**Example values:**
- Looking straight: `ear_ratio ≈ 1.0` → `yaw ≈ 0°`
- Looking 45° left: `ear_ratio ≈ 0.6` → `yaw ≈ -25°`
- Looking 45° right: `ear_ratio ≈ 1.7` → `yaw ≈ +27°`

#### Pitch Calculation (Vertical Rotation)

**What is pitch?**
- Negative pitch = looking down
- Positive pitch = looking up
- 0° = looking straight ahead
- Range: -30° to +30°

**How it's calculated:**

1. **Calculate eye level** (average y-coordinate of eyes):
   ```
   eye_level_y = (left_eye.y + right_eye.y) / 2
   ```

2. **Measure nose position relative to eye level**:
   ```
   nose_offset_y = nose.y - eye_level_y
   ```

   - If nose is below eye level → looking down
   - If nose is above eye level → looking up

3. **Scale to pitch angle**:
   ```
   pitch = -nose_offset_y × 150
   ```

   Note: Negative sign because in image coordinates, +y is down

4. **Clamp to valid range**:
   ```
   pitch = max(-30, min(30, pitch))
   ```

**Example values:**
- Looking straight: `nose_offset_y ≈ 0` → `pitch ≈ 0°`
- Looking down (at notes): `nose_offset_y > 0` → `pitch ≈ -20°`
- Looking up (at ceiling): `nose_offset_y < 0` → `pitch ≈ +15°`

### Step 3: Build Heatmap
Creates a 2D grid showing where the presenter looked and for how long.

**How it works:**
1. Divide the angle space into bins:
   - Yaw bins: -60° to +60° in 5° increments (24 bins)
   - Pitch bins: -30° to +30° in 5° increments (12 bins)

2. For each frame, find which bin the (yaw, pitch) falls into

3. Count how many frames in each bin

4. Convert frame counts to duration:
   ```
   duration_seconds = frame_count / 15.0
   ```
   (Assuming 15 FPS video)

**Result:** A 24×12 matrix showing time spent looking in each direction.

**Visualization:** Saved as PNG heatmap with:
- Hot colors (red/yellow) = looked there for a long time
- Cool colors (blue/purple) = looked there briefly or not at all
- Green box = "audience zone" (where you should be looking)

### Step 4: Detect Looking Away Events
Identifies periods when the presenter is NOT looking at the audience.

**Audience zone definition:**
- Yaw: -30° to +30° (60° total width)
- Pitch: -15° to +15° (30° total height)

**Detection logic:**
```
looking_away = (
    yaw < -30° OR yaw > +30° OR
    pitch < -15° OR pitch > +15°
)
```

**Event recording:**
- Tracks consecutive frames of looking away
- Only records events lasting at least `MIN_CONSECUTIVE_FRAMES` (default: 5 frames)
- Classifies direction: "left", "right", "up", "down", "down-left", etc.

**Example event:**
```json
{
  "start_timestamp": "00:00:12.340",
  "end_timestamp": "00:00:15.670",
  "duration_frames": 50,
  "duration_seconds": 3.33,
  "direction": "right",
  "avg_yaw": 42.3,
  "avg_pitch": -2.1
}
```

### Step 5: Calculate Statistics
Computes summary metrics for the entire presentation.

**Metrics calculated:**
- Total frames analyzed
- Total duration (seconds)
- Looking at audience: frames, duration, percentage
- Looking away: frames, duration, percentage
- Number of looking away events
- Average yaw and pitch (where presenter typically looks)
- Yaw range and pitch range (how much they scan around)

**Good presentation indicators:**
- Looking at audience percentage > 80%
- Wide yaw range (30°-50°) → scanning the audience
- Low pitch range (< 20°) → not looking up/down too much
- Few looking away events (< 5 for a 5-minute talk)

**Poor presentation indicators:**
- Looking at audience percentage < 60%
- Narrow yaw range (< 20°) → staring at one spot
- High pitch range (> 30°) → looking at ceiling/floor frequently
- Many looking away events (> 10)

### Step 6: Generate Visualization
Creates a 3-panel graph saved as PNG.

**Panel 1: Heatmap**
- Shows gaze distribution across all directions
- Green box indicates audience zone
- Reveals patterns (staring at one person vs. scanning audience)

**Panel 2: Yaw Over Time**
- Blue line shows yaw angle for each frame
- Green dashed lines show audience zone boundaries
- Helps identify when presenter looked left/right

**Panel 3: Pitch Over Time**
- Red line shows pitch angle for each frame
- Green dashed lines show audience zone boundaries
- Helps identify when presenter looked up/down

**Output:** `debug_output/{recording_id}/gaze_heatmap_{recording_id}.png`

## API Response Structure

```json
{
  "success": true,
  "recording_id": 3,
  "total_frames": 450,
  "analyzed_frames": 448,
  "visualization_path": "C:/path/to/gaze_heatmap_3.png",

  "statistics": {
    "total_frames": 448,
    "total_duration": 29.87,
    "looking_at_audience_frames": 380,
    "looking_at_audience_duration": 25.33,
    "looking_at_audience_percentage": 84.82,
    "looking_away_frames": 68,
    "looking_away_duration": 4.53,
    "looking_away_percentage": 15.18,
    "avg_yaw": -2.15,
    "avg_pitch": 3.42,
    "yaw_range": 45.23,
    "pitch_range": 18.67,
    "num_looking_away_events": 3
  },

  "heatmap": {
    "yaw_bins": [-60, -55, -50, ..., 55, 60],
    "pitch_bins": [-30, -25, -20, ..., 25, 30],
    "duration_matrix": [[0.2, 0.5, ...], ...],
    "bin_size": {
      "yaw": 5,
      "pitch": 5
    },
    "shape": {
      "n_yaw_bins": 24,
      "n_pitch_bins": 12
    }
  },

  "looking_away_events": [
    {
      "start_timestamp": "00:00:08.200",
      "end_timestamp": "00:00:10.500",
      "duration_frames": 35,
      "duration_seconds": 2.33,
      "direction": "left",
      "avg_yaw": -38.5,
      "avg_pitch": 1.2
    }
  ],

  "audience_zone_thresholds": {
    "yaw_min": -30,
    "yaw_max": 30,
    "pitch_min": -15,
    "pitch_max": 15
  },

  "message": "Eye contact analysis completed successfully."
}
```

## Understanding the Results

### Good Eye Contact Pattern:
- **Looking at audience:** > 80%
- **Yaw range:** 30-50° (scanning the audience left to right)
- **Pitch range:** < 20° (keeping head level)
- **Heatmap:** Spread horizontally within audience zone, centered around 0°
- **Events:** Few brief looking away moments (< 5 events, < 2 seconds each)

**What this looks like:**
- Presenter scans across the audience
- Occasionally glances at slides/notes briefly
- Returns focus to audience quickly
- Maintains relatively level head position

### Poor Eye Contact Pattern:
- **Looking at audience:** < 60%
- **Yaw range:** < 20° (staring at one spot or slides)
- **Pitch range:** > 25° (looking up at slides or down at notes frequently)
- **Heatmap:** Concentrated in one spot OR heavily outside audience zone
- **Events:** Many long looking away periods (> 10 events, > 3 seconds each)

**What this looks like:**
- Presenter reads from slides constantly
- Stares at notes on podium
- Looks at back wall instead of audience
- Never makes eye contact with different audience sections

## Configuration Guide

All parameters can be tuned in `.env`:

```bash
# Yaw (horizontal) angle range
YAW_MIN=-60          # Minimum yaw angle (looking far left)
YAW_MAX=60           # Maximum yaw angle (looking far right)
YAW_BIN_SIZE=5       # Heatmap bin width in degrees

# Pitch (vertical) angle range
PITCH_MIN=-30        # Minimum pitch angle (looking down)
PITCH_MAX=30         # Maximum pitch angle (looking up)
PITCH_BIN_SIZE=5     # Heatmap bin height in degrees

# Audience zone definition (what counts as "looking at audience")
AUDIENCE_YAW_MIN=-30     # Left boundary (negative = left)
AUDIENCE_YAW_MAX=30      # Right boundary (positive = right)
AUDIENCE_PITCH_MIN=-15   # Lower boundary (negative = down)
AUDIENCE_PITCH_MAX=15    # Upper boundary (positive = up)

# Event detection
MIN_CONSECUTIVE_FRAMES=5  # Minimum frames to count as an event
```

### Tuning Tips:

#### Adjusting Audience Zone

**Too strict? (Detecting too many looking away events)**
- Increase audience zone size:
  ```bash
  AUDIENCE_YAW_MIN=-40
  AUDIENCE_YAW_MAX=40
  AUDIENCE_PITCH_MIN=-20
  AUDIENCE_PITCH_MAX=20
  ```

**Too lenient? (Not detecting obvious looking away)**
- Decrease audience zone size:
  ```bash
  AUDIENCE_YAW_MIN=-20
  AUDIENCE_YAW_MAX=20
  AUDIENCE_PITCH_MIN=-10
  AUDIENCE_PITCH_MAX=10
  ```

**Presenter often looks down at notes (not a problem for your use case)?**
- Make pitch range more lenient downward:
  ```bash
  AUDIENCE_PITCH_MIN=-25  # Allow looking down more
  AUDIENCE_PITCH_MAX=15   # Keep upward limit
  ```

#### Adjusting Event Detection

**Getting too many short events (false positives)?**
- Increase minimum duration:
  ```bash
  MIN_CONSECUTIVE_FRAMES=10  # Require 0.67 seconds instead of 0.33
  ```

**Missing brief but important looking away moments?**
- Decrease minimum duration:
  ```bash
  MIN_CONSECUTIVE_FRAMES=3   # Detect events as short as 0.2 seconds
  ```

#### Adjusting Heatmap Resolution

**Heatmap too coarse (not enough detail)?**
- Decrease bin size:
  ```bash
  YAW_BIN_SIZE=2.5    # More bins = finer resolution
  PITCH_BIN_SIZE=2.5
  ```

**Heatmap too noisy (too much detail)?**
- Increase bin size:
  ```bash
  YAW_BIN_SIZE=10     # Fewer bins = smoother heatmap
  PITCH_BIN_SIZE=10
  ```

## Common Use Cases

### Scenario 1: Large Auditorium Presentation
Wide audience → need wider yaw range
```bash
AUDIENCE_YAW_MIN=-45
AUDIENCE_YAW_MAX=45
AUDIENCE_PITCH_MIN=-10  # Audience mostly level
AUDIENCE_PITCH_MAX=10
```

### Scenario 2: Small Meeting Room
Close audience → narrower range is fine
```bash
AUDIENCE_YAW_MIN=-25
AUDIENCE_YAW_MAX=25
AUDIENCE_PITCH_MIN=-15
AUDIENCE_PITCH_MAX=15
```

### Scenario 3: Presenter with Notes on Podium
Allow looking down occasionally
```bash
AUDIENCE_YAW_MIN=-30
AUDIENCE_YAW_MAX=30
AUDIENCE_PITCH_MIN=-30  # Extended downward range
AUDIENCE_PITCH_MAX=15
MIN_CONSECUTIVE_FRAMES=10  # Ignore quick glances
```

### Scenario 4: Strict Eye Contact Requirements
Only want direct eye contact
```bash
AUDIENCE_YAW_MIN=-15  # Narrow horizontal range
AUDIENCE_YAW_MAX=15
AUDIENCE_PITCH_MIN=-10  # Narrow vertical range
AUDIENCE_PITCH_MAX=10
MIN_CONSECUTIVE_FRAMES=3  # Catch brief looking away
```

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `.env` file (see Configuration Guide above)

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver 8003
```

The service will be available at `http://localhost:8003`

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Eye Contact
```
POST /api/v1/analyze/eye-contact/{recording_id}/
```

**Example:**
```bash
curl -X POST http://localhost:8003/api/v1/analyze/eye-contact/3/
```

## Example Usage

```python
from gaze_api.services import EyeContactAnalysisService

service = EyeContactAnalysisService()
result = service.analyze_eye_contact(recording_id=3)

if result['success']:
    stats = result['statistics']
    print(f"Looking at audience: {stats['looking_at_audience_percentage']:.1f}%")
    print(f"Average yaw: {stats['avg_yaw']:.1f}° (negative=left, positive=right)")
    print(f"Found {stats['num_looking_away_events']} looking away events")

    for event in result['looking_away_events']:
        print(f"  - Looked {event['direction']} for {event['duration_seconds']:.1f}s")
else:
    print(f"Error: {result['error']}")
```

## Technical Notes

### Data Flow:
1. Video → Face Detection (video_analysis_ms) → Landmarks stored in PostgreSQL
2. Landmarks → This service → Head pose analysis
3. Analysis results → Returned to client

### Angle Calculation Accuracy:
- **Yaw:** ±5° accuracy for frontal poses, ±10° for extreme angles
- **Pitch:** ±5° accuracy within ±20°, degrades beyond that
- Works best when face is clearly visible
- Accuracy decreases with poor lighting or occlusion

### Limitations:
- Assumes camera is in front of presenter (audience POV)
- Doesn't track actual eye gaze (only head direction)
- Cannot detect closed eyes or reading from laptop screen
- Ear landmarks may be less visible in profile views

### Dependencies:
- **matplotlib**: Heatmap and graph generation
- **numpy**: Matrix operations for heatmap
- **Django**: Web framework
- **PostgreSQL**: Database (via TimescaleDB)
- **math**: Angle calculations

### Performance:
- Processes ~100 frames in <0.5 seconds
- Typical presentation (5 minutes at 15 fps) = ~4500 frames ≈ 2-3 seconds processing time
- Heatmap generation adds ~0.5 seconds

## Interpreting the Heatmap

### Ideal Heatmap Pattern:
```
          Left        Center       Right
         [-60°]       [0°]        [+60°]
Up   [+30°]  ░░         ░░░         ░░       Light activity on sides
        [+15°]  ░░░░     ▓▓▓▓▓     ░░░░      Some looking up at audience
Center  [0°]   ░░░░░   ███████   ░░░░░     Heavy center focus (audience)
       [-15°]  ░░░░     ▓▓▓▓▓     ░░░░      Occasional downward glances
Down  [-30°]  ░          ░░         ░       Minimal looking down (notes)

Legend: ░ = <1s, ▓ = 1-3s, █ = >3s
```
This shows:
- Concentrated attention on center (audience)
- Scanning left and right (engaging different audience sections)
- Minimal looking down (not reading slides excessively)

### Bad Heatmap Patterns:

**Pattern 1: Slide Reader**
```
Up   [+30°]     ░░░░░   ███████   ░░░░░    <- Staring at slides on wall
Center  [0°]    ░░░░     ░░░░░     ░░░░     <- Little time on audience
Down  [-30°]    ░          ░         ░
```

**Pattern 2: Note Reader**
```
Up   [+30°]     ░          ░         ░
Center  [0°]    ░░░░     ░░░░░     ░░░░     <- Little time on audience
Down  [-30°]    ░░░░░   ███████   ░░░░░    <- Reading from notes/laptop
```

**Pattern 3: Stare at One Person**
```
Center  [0°]    ░          ███         ░    <- Concentrated hot spot
                         (one person)
```
No horizontal distribution = not engaging full audience

## Future Improvements

Potential enhancements:
- Integrate actual eye tracking (iris detection)
- Detect specific gaze targets (specific people, slides, notes)
- Real-time feedback during presentation
- Compare against "ideal presenter" gaze patterns
- Detect reading behavior vs. spontaneous speaking
- Analyze blink rate (nervousness indicator)