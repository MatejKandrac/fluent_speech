# Hip Analysis Service

A microservice that analyzes hip movements in presentation videos to assess body stability, posture, and movement patterns.

## What This Service Does

This service analyzes hip landmarks from pose detection to identify:
- Body stability and sway
- Hip positioning and alignment
- Movement patterns during presentation
- Posture consistency

## Why Analyze Hip Movement?

### Body Language Significance:
Hips are the center of mass and reveal important presentation behaviors:

**Stable hips indicate:**
- Confidence and groundedness
- Professional posture
- Controlled body language
- Audience focus

**Excessive hip movement indicates:**
- Nervousness or fidgeting
- Pacing or swaying
- Lack of confidence
- Distraction from message

**Asymmetric hip positioning:**
- Leaning to one side
- Poor posture
- Discomfort or fatigue
- Unprofessional appearance

## Processing Pipeline

### Step 1: Fetch Hip Landmark Data
Retrieves left_hip and right_hip landmarks from the database.

**Data source:**
- Extracted by video_processing_ms using MediaPipe Pose Detection
- Stored in PostgreSQL database
- Linked to recording ID and frame index

**Landmarks:**
- Left hip: 3D coordinates (x, y, z) + visibility score
- Right hip: 3D coordinates (x, y, z) + visibility score

### Step 2: Calculate Hip Metrics
Computes various hip movement measurements.

**Hip Center:**
- Midpoint between left and right hip
- Formula: `center = (left_hip + right_hip) / 2`
- Represents overall body position

**Hip Distance (Width):**
- Distance between left and right hip
- Formula: `sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)`
- Indicates shoulder width and stance

**Hip Sway:**
- Lateral (X-axis) movement of hip center
- Indicates side-to-side movement
- Measure of stability

### Step 3: Generate Visualizations
Creates comprehensive plots showing hip movement patterns.

**Six subplots created:**

1. **Hip Center - Lateral Movement (X)**
   - Side-to-side sway
   - Key indicator of nervousness/stability

2. **Hip Center - Vertical Movement (Y)**
   - Up and down motion
   - Indicates standing vs. sitting, weight shifts

3. **Hip Center - Depth Movement (Z)**
   - Forward/backward movement
   - Shows leaning or moving toward/away from camera

4. **Hip Distance (Width)**
   - Variation in stance width
   - Should be relatively constant

5. **Left vs Right Hip - Lateral Position**
   - Shows asymmetry
   - Identifies leaning or poor posture

6. **Hip Sway Statistics**
   - Summary metrics
   - Text display of key statistics

**Output:** `debug/{recording_id}/hip_movement.png`

### Step 4: Calculate Statistics
Computes summary statistics for the entire recording.

**Metrics:**
- Total frames with hip data
- Valid frames (both hips visible)
- Hip sway: mean, std, range for X, Y axes
- Hip distance: mean, std, min, max

## API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Analyze Hip Movement
```
POST /api/v1/hip/{recording_id}/analyze/
```

**Parameters:**
- `recording_id` (int): Database ID of the recording

**Response:**
```json
{
  "success": true,
  "recording_id": 1,
  "statistics": {
    "total_frames": 500,
    "valid_frames": 485,
    "hip_sway": {
      "x_mean": 0.5,
      "x_std": 0.02,
      "x_range": 0.15,
      "y_mean": 0.7,
      "y_std": 0.01,
      "y_range": 0.08
    },
    "hip_distance": {
      "mean": 0.25,
      "std": 0.01,
      "min": 0.23,
      "max": 0.27
    }
  }
}
```

## Interpreting Results

### Excellent Stability:
- **X standard deviation:** <0.02 (normalized coordinates)
- **X range:** <0.10
- Minimal lateral sway
- Indicates confidence and control
- Professional presentation style

### Good Stability:
- **X standard deviation:** 0.02-0.05
- **X range:** 0.10-0.20
- Some natural movement
- Balanced and natural
- Engaging without distraction

### Moderate Sway:
- **X standard deviation:** 0.05-0.10
- **X range:** 0.20-0.40
- Noticeable swaying
- May indicate nervousness
- Could be distracting

### Excessive Sway:
- **X standard deviation:** >0.10
- **X range:** >0.40
- Significant swaying or pacing
- Indicates high nervousness
- Very distracting for audience
- Unprofessional appearance

### Hip Distance Analysis:
- **Low std (<0.02):** Consistent stance (good)
- **High std (>0.05):** Changing stance frequently (fidgeting)

### Vertical Movement:
- **Minimal change:** Standing still (professional)
- **Gradual decrease:** Possibly getting tired/slumping
- **Large variations:** Moving between sitting/standing or bouncing

## Configuration

Set in `.env` file:

```bash
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fluent
DB_USERNAME=postgres
DB_PASSWORD=your_password
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

3. Configure `.env` file

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver 8007
```

The service will be available at `http://localhost:8007`

## Dependencies

- **matplotlib**: Visualization
- **numpy**: Numerical computations
- **Django**: Web framework
- **PostgreSQL**: Database for landmark data

## Technical Notes

### Data Flow:
1. video_processing_ms → Extracts pose landmarks → Stores in database
2. This service → Queries hip landmarks → Analyzes movement → Returns statistics

### Coordinate System:
- Normalized MediaPipe coordinates (relative to frame size)
- X: 0 (left) to 1 (right)
- Y: 0 (top) to 1 (bottom)
- Z: Depth (relative to hips, can be negative)

### Frame Rate:
- Depends on video processing frame rate
- Typically 15-30 fps
- 5-minute presentation = 4,500-9,000 frames

### Performance:
- Processing time: <1 second per presentation
- Lightweight analysis (no video processing)
- Only database queries and calculations

## Debug Output

Visualizations are saved to: `debug/{recording_id}/hip_movement.png`

**What to look for:**
- Flat X-axis line → Very stable (excellent)
- Small waves in X-axis → Natural movement (good)
- Large swings in X-axis → Excessive sway (poor)
- Symmetric left/right hip → Good posture
- Asymmetric left/right hip → Leaning or poor posture

## Example Usage

```bash
# Analyze hip movement for recording ID 1
curl -X POST http://localhost:8007/api/v1/hip/1/analyze/
```

## Combining with Other Analyses

### Hip + Arm Movement:
- Stable hips + active arms = Professional gesturing
- Swaying hips + minimal arms = Nervous, unsure
- Stable hips + minimal arms = Too static (boring)

### Hip + Eye Contact:
- Stable hips + good eye contact = Confident presenter
- Swaying hips + poor eye contact = Very nervous

### Hip + Volume/Pitch:
- Stable hips + varied pitch/volume = Engaging speaker
- Swaying hips + monotone = Nervous and unprepared

## Common Patterns

### Confident Presenter:
- Minimal lateral sway (x_std < 0.02)
- Consistent hip distance
- Slight natural movement
- Symmetric posture

### Nervous Presenter:
- Excessive lateral sway (x_std > 0.08)
- Frequent stance changes
- Asymmetric posture (leaning)
- Erratic movements

### Tired Presenter:
- Gradual Y-axis decrease (slumping)
- Increasing sway over time
- Shifting weight frequently

## Future Improvements

- Detect specific movement patterns (pacing, swaying, shifting)
- Analyze posture changes over time
- Compare against "ideal" presenter patterns
- Combine with other body parts for full posture analysis
- Real-time feedback on stance and posture
- Detect asymmetry and recommend corrections
