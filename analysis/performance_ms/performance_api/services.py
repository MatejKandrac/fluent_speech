from typing import Dict, Any, List, Optional


RECOMMENDATIONS = {
    'voice_monotone': (
        "Váš hlas bol monotónny vo veľkej časti prezentácie. "
        "Skúste viac varirovať výšku hlasu, najmä pri kľúčových myšlienkach."
    ),
    'voice_volume': (
        "Hlasitosť vášho prejavu bola často mimo optimálneho rozsahu (príticho alebo prihlas). "
        "Snažte sa udržiavať konzistentnú, zreteľnú hlasitosť."
    ),
    'fluency_filler': (
        "Používate príliš veľa výplňových slov (ehm, teda, takže...). "
        "Namiesto výplňových slov skúste krátku pauzu — pôsobí sebaisto."
    ),
    'body_no_movement': (
        "Vaše ruky boli po dlhú dobu takmer bez pohybu. "
        "Prirodzená gestikulácia podporuje prejav a drží pozornosť publika."
    ),
    'body_excessive_movement': (
        "Ruky ste pohybovali príliš rýchlo alebo nervózne. "
        "Skúste zámernejšiu a pomalšiu gestikuláciu."
    ),
    'body_hip_sway': (
        "Počas prezentácie ste sa výrazne kývali na bokoch. "
        "Stabilný postoj zvyšuje dôveryhodnosť — skúste stáť pevne na oboch nohách."
    ),
    'eye_contact_away': (
        "Príliš často ste sa pozerali mimo publikum. "
        "Snažte sa udržiavať očný kontakt s rôznymi časťami publika."
    ),
    'eye_contact_staring': (
        "Dlho ste sa fixovali na jedno miesto. "
        "Rozdeľujte pohľad rovnomerne po celom publiku."
    ),
    'eye_contact_back': (
        "Otočili ste sa chrbtom k publiku. "
        "Vždy hovorte čelom k publiku, aj keď odkazujete na premietaný obsah."
    ),
}

LOCATION_SUFFIXES = {
    'beginning':  'Prejavilo sa to najmä na začiatku prezentácie.',
    'middle':     'Prejavilo sa to najmä v strednej časti prezentácie.',
    'end':        'Prejavilo sa to najmä na konci prezentácie.',
    'throughout': 'Vyskytovalo sa to počas celej prezentácie.',
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _get_total_duration(pitch, volume, filler, arm, hip, eye) -> float:
    """Best-effort total presentation duration in seconds.

    Tries sources in order of reliability: eye contact (analyzes every video
    frame) → hip (also frame-based) → filler (audio-derived) → 0 as fallback.
    """
    for source, keys in [
        (eye,    ['statistics', 'total_duration']),
        (hip,    ['statistics', 'total_duration']),
    ]:
        if source:
            try:
                val = source
                for k in keys:
                    val = val[k]
                if val and float(val) > 0:
                    return float(val)
            except (KeyError, TypeError):
                pass

    if filler:
        d = filler.get('duration', 0)
        if d and float(d) > 0:
            return float(d)

    return 0.0


def _locate_events(
    events: list,
    total_duration: float,
    start_key: str = 'start_timestamp',
    end_key: str = 'end_timestamp',
) -> Optional[str]:
    """Return 'beginning' | 'middle' | 'end' if events cluster in one third
    of the presentation (>55 % of total event duration).  Returns None when
    events are evenly spread or there is not enough data.
    """
    if not events or total_duration <= 0:
        return None

    third = total_duration / 3.0
    buckets = [0.0, 0.0, 0.0]

    for e in events:
        start = float(e.get(start_key) or 0)
        end   = float(e.get(end_key)   or start)
        if end < start:
            end = start
        # Distribute the event's duration across whichever thirds it overlaps.
        # A long segment spanning multiple thirds is split proportionally rather
        # than assigned entirely to the third containing its center point.
        for i in range(3):
            third_start = i * third
            third_end   = (i + 1) * third
            overlap = max(0.0, min(end, third_end) - max(start, third_start))
            buckets[i] += overlap

    total = sum(buckets)
    if total <= 0:
        return None

    fractions = [b / total for b in buckets]
    best = max(range(3), key=lambda i: fractions[i])

    if fractions[best] > 0.55:
        return ['beginning', 'middle', 'end'][best]

    return 'throughout'


def _make_recommendation(issue_key: str, location: Optional[str] = None) -> str:
    base = RECOMMENDATIONS.get(issue_key, '')
    if location and location in LOCATION_SUFFIXES:
        return f"{base} {LOCATION_SUFFIXES[location]}"
    return base


# ---------------------------------------------------------------------------
# Voice dimension  (weight 0.25)
# ---------------------------------------------------------------------------

def _score_voice(
    pitch: Optional[Dict],
    volume: Optional[Dict],
    total_duration: float,
) -> Dict[str, Any]:
    """
    Penalties:
      - monotone_pct  : % voiced frames in monotone segments  → 0 % → 0 pen, ≥ 70 % → 50 pen
      - volume_pct    : % total frames with bad volume         → 0 % → 0 pen, ≥ 50 % → 50 pen
    """
    penalty = 0.0
    issues: List[str] = []
    issue_locations: Dict[str, Optional[str]] = {}

    # --- pitch monotony ---
    if pitch:
        voiced_frames = pitch.get('voiced_frames', 0)
        monotone_segments = pitch.get('monotonous_segments', [])

        if voiced_frames > 0 and monotone_segments:
            duration_per_frame = pitch.get('duration_per_frame')
            if duration_per_frame and duration_per_frame > 0:
                monotone_frames = sum(
                    s.get('duration_seconds', 0) / duration_per_frame
                    for s in monotone_segments
                )
            else:
                total_duration_seg = sum(s.get('duration_seconds', 0) for s in monotone_segments)
                monotone_frames = (total_duration_seg / max(total_duration_seg, 1)) * voiced_frames

            monotone_pct = min(monotone_frames / voiced_frames, 1.0) * 100.0
        else:
            monotone_pct = 0.0

        monotone_penalty = _clamp(monotone_pct / 70.0 * 50.0, 0.0, 50.0)
        penalty += monotone_penalty
        if monotone_penalty >= 20:
            issues.append('voice_monotone')
            issue_locations['voice_monotone'] = _locate_events(
                monotone_segments, total_duration
            )

    # --- volume ---
    if volume:
        total_frames = volume.get('volume_frames', 1)
        bad_segments = (
            volume.get('too_soft_segments', []) +
            volume.get('too_loud_segments', [])
        )
        bad_frames = sum(s.get('duration_seconds', 0) for s in bad_segments)
        volume_pct = min(bad_frames / max(total_frames * 0.018, 1.0), 1.0) * 100.0
        volume_penalty = _clamp(volume_pct / 50.0 * 50.0, 0.0, 50.0)
        penalty += volume_penalty
        if volume_penalty >= 20:
            issues.append('voice_volume')
            issue_locations['voice_volume'] = _locate_events(
                bad_segments, total_duration
            )

    score = _clamp(100.0 - penalty)
    return {'score': round(score, 1), 'issues': issues, 'issue_locations': issue_locations}


# ---------------------------------------------------------------------------
# Fluency dimension  (weight 0.20)
# ---------------------------------------------------------------------------

def _score_fluency(
    filler: Optional[Dict],
    total_duration: float,
) -> Dict[str, Any]:
    """
    Filler words per minute:
      0–2  → 0 penalty
      2–5  → linear 0–40 penalty
      5+   → linear 40–100 penalty (capped at 100)
    """
    issues: List[str] = []
    issue_locations: Dict[str, Optional[str]] = {}

    if not filler:
        return {'score': 100.0, 'issues': issues, 'issue_locations': issue_locations}

    duration_sec = filler.get('duration', 0)
    total_fillers = filler.get('total_filler_occurrences', 0)

    if duration_sec <= 0:
        return {'score': 100.0, 'issues': issues, 'issue_locations': issue_locations}

    fpm = total_fillers / (duration_sec / 60.0)

    if fpm <= 2.0:
        penalty = 0.0
    elif fpm <= 5.0:
        penalty = (fpm - 2.0) / 3.0 * 40.0
    else:
        penalty = 40.0 + min((fpm - 5.0) / 10.0 * 60.0, 60.0)

    penalty = _clamp(penalty, 0.0, 100.0)
    if penalty >= 20:
        issues.append('fluency_filler')
        occurrences = filler.get('filler_occurrences', [])
        issue_locations['fluency_filler'] = _locate_events(
            occurrences, total_duration,
            start_key='start_time', end_key='end_time',
        )

    score = _clamp(100.0 - penalty)
    return {
        'score': round(score, 1),
        'issues': issues,
        'issue_locations': issue_locations,
        'filler_per_minute': round(fpm, 2),
    }


# ---------------------------------------------------------------------------
# Body movement dimension  (weight 0.25)
# ---------------------------------------------------------------------------

def _score_body(
    arm: Optional[Dict],
    hip: Optional[Dict],
    total_duration: float,
) -> Dict[str, Any]:
    """
    Arm:
      - no_movement_pct  (% frames in no-movement periods)  → 0 % → 0, ≥ 60 % → 35
      - excessive_pct    (% frames in excessive periods)     → 0 % → 0, ≥ 30 % → 35
    Hip:
      - swaying_pct      (% frames in swaying segments)      → 0 % → 0, ≥ 40 % → 30
    """
    penalty = 0.0
    issues: List[str] = []
    issue_locations: Dict[str, Optional[str]] = {}

    if arm:
        total_frames = max(arm.get('total_frames', 1), 1)
        anomalies = arm.get('anomalies', {})

        no_move_periods = anomalies.get('no_movement_periods', [])
        excessive_periods = anomalies.get('excessive_movement_periods', [])

        no_move_frames = sum(p.get('duration_frames', 0) for p in no_move_periods)
        excessive_frames = sum(p.get('duration_frames', 0) for p in excessive_periods)

        no_move_pct = no_move_frames / total_frames * 100.0
        excessive_pct = excessive_frames / total_frames * 100.0

        no_move_penalty = _clamp(no_move_pct / 60.0 * 35.0, 0.0, 35.0)
        excessive_penalty = _clamp(excessive_pct / 30.0 * 35.0, 0.0, 35.0)

        penalty += no_move_penalty + excessive_penalty

        if no_move_penalty >= 15:
            issues.append('body_no_movement')
            issue_locations['body_no_movement'] = _locate_events(
                no_move_periods, total_duration
            )
        if excessive_penalty >= 15:
            issues.append('body_excessive_movement')
            issue_locations['body_excessive_movement'] = _locate_events(
                excessive_periods, total_duration
            )

    if hip:
        total_frames = hip.get('statistics', {}).get('total_frames', None)
        swaying_segments = hip.get('swaying_segments', [])
        fps = hip.get('statistics', {}).get('fps', 30)

        if total_frames and total_frames > 0 and swaying_segments:
            swaying_frames = sum(
                (s.get('end_timestamp', 0) - s.get('start_timestamp', 0)) * fps
                for s in swaying_segments
            )
            swaying_pct = swaying_frames / total_frames * 100.0
            hip_penalty = _clamp(swaying_pct / 40.0 * 30.0, 0.0, 30.0)
        else:
            hip_penalty = 0.0

        penalty += hip_penalty
        if hip_penalty >= 10:
            issues.append('body_hip_sway')
            issue_locations['body_hip_sway'] = _locate_events(
                swaying_segments, total_duration
            )

    score = _clamp(100.0 - penalty)
    return {'score': round(score, 1), 'issues': issues, 'issue_locations': issue_locations}


# ---------------------------------------------------------------------------
# Eye contact dimension  (weight 0.30)
# ---------------------------------------------------------------------------

def _score_eye_contact(
    eye: Optional[Dict],
    total_duration: float,
) -> Dict[str, Any]:
    """
    - back_facing_pct   : % analyzed frames facing back  → 0 % → 0, ≥ 5 % → 40
    - looking_away_pct  : % looking away from audience
    - staring_pct       : % in staring events
    """
    issues: List[str] = []
    issue_locations: Dict[str, Optional[str]] = {}

    if not eye:
        return {'score': 100.0, 'issues': issues, 'issue_locations': issue_locations}

    stats = eye.get('statistics', {})
    total_frames = max(stats.get('total_frames', 1), 1)

    looking_away_pct = stats.get('looking_away_percentage', 0.0)
    staring_events = eye.get('staring_events', [])
    looking_away_events = eye.get('looking_away_events', [])

    staring_frames = sum(e.get('duration_frames', 0) for e in staring_events)
    staring_pct = staring_frames / total_frames * 100.0

    back_facing_count = eye.get('back_facing_frames', 0)
    back_facing_pct = back_facing_count / total_frames * 100.0

    back_penalty    = _clamp(back_facing_pct  /  5.0 * 40.0, 0.0, 40.0)
    away_penalty    = _clamp(looking_away_pct / 50.0 * 35.0, 0.0, 35.0)
    staring_penalty = _clamp(staring_pct      / 40.0 * 25.0, 0.0, 25.0)

    penalty = back_penalty + away_penalty + staring_penalty

    if back_penalty >= 10:
        issues.append('eye_contact_back')
        # back-facing events are captured inside looking_away_events (extreme yaw)
        issue_locations['eye_contact_back'] = _locate_events(
            looking_away_events, total_duration
        )
    if away_penalty >= 15:
        issues.append('eye_contact_away')
        issue_locations['eye_contact_away'] = _locate_events(
            looking_away_events, total_duration
        )
    if staring_penalty >= 10:
        issues.append('eye_contact_staring')
        issue_locations['eye_contact_staring'] = _locate_events(
            staring_events, total_duration
        )

    score = _clamp(100.0 - penalty)
    return {'score': round(score, 1), 'issues': issues, 'issue_locations': issue_locations}


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

DIMENSION_WEIGHTS = {
    'voice':       0.25,
    'fluency':     0.20,
    'body':        0.25,
    'eye_contact': 0.30,
}

SCORE_LABELS = [
    (90, 'Výborné'),
    (75, 'Dobré'),
    (60, 'Priemer'),
    (40, 'Potrebuje zlepšenie'),
    (0,  'Slabé'),
]


def _label(score: float) -> str:
    for threshold, lbl in SCORE_LABELS:
        if score >= threshold:
            return lbl
    return 'Slabé'


class PerformanceService:

    def calculate_performance(self, body: Dict[str, Any]) -> Dict[str, Any]:
        pitch  = body.get('pitch')
        volume = body.get('volume')
        filler = body.get('filler_words')
        arm    = body.get('arm_movement')
        hip    = body.get('hip_movement')
        eye    = body.get('eye_contact')

        total_duration = _get_total_duration(pitch, volume, filler, arm, hip, eye)

        voice_result   = _score_voice(pitch, volume, total_duration)
        fluency_result = _score_fluency(filler, total_duration)
        body_result    = _score_body(arm, hip, total_duration)
        eye_result     = _score_eye_contact(eye, total_duration)

        dimensions = {
            'voice':       voice_result,
            'fluency':     fluency_result,
            'body':        body_result,
            'eye_contact': eye_result,
        }

        total_score = sum(
            dimensions[dim]['score'] * weight
            for dim, weight in DIMENSION_WEIGHTS.items()
        )
        total_score = round(_clamp(total_score), 1)

        recommendations = []
        for dim_result in dimensions.values():
            locations = dim_result.get('issue_locations', {})
            for issue in dim_result.get('issues', []):
                if issue in RECOMMENDATIONS:
                    recommendations.append(
                        _make_recommendation(issue, locations.get(issue))
                    )

        return {
            'success': True,
            'recording_id': body.get('recording_id'),
            'total_score': total_score,
            'total_label': _label(total_score),
            'dimensions': {
                dim: {
                    'score': dimensions[dim]['score'],
                    'label': _label(dimensions[dim]['score']),
                    'weight': DIMENSION_WEIGHTS[dim],
                    **{k: v for k, v in dimensions[dim].items() if k not in ('score',)},
                }
                for dim in dimensions
            },
            'recommendations': recommendations,
        }
