"""
Evaluation script for Fluent Speech microservices accuracy measurement.

Usage:
    python evaluate.py
    python evaluate.py --service eye_contact
    python evaluate.py --video V1
    python evaluate.py --bin-size 0.5 --output report.json

Directory layout:
    annotations/
        eye_contact/    <- only videos where camera is front-facing
            V1_gt.json
            V3_gt.json
        arm_movement/
            V1_gt.json
            ...
        hip/
        filler_words/
        pitch/
        volume/
    results/
        V1_orchestrator.json
        V2_orchestrator.json
        ...

Ground-truth JSON schema (one file per video per service):
{
  "video_id": "V1",
  "duration_s": 65.0,
  "annotator": "Matej",
  "notes": "optional",
  "annotations": {
    "<dim>": [{"start": 10.0, "end": 15.0}, ...],
    ...
  }
}

Filler words use point events:
  "filler_words": [{"start": 10.5, "end": 10.9, "word": "ehm"}, ...]
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Binary timeline helpers
# ---------------------------------------------------------------------------

def _intervals_to_bins(intervals: list, duration: float, bin_size: float) -> list:
    n = max(1, math.ceil(duration / bin_size))
    bins = [0] * n
    for iv in intervals:
        start = iv.get("start", iv.get("start_timestamp", 0))
        end   = iv.get("end",   iv.get("end_timestamp",   0))
        lo = max(0, int(start / bin_size))
        hi = min(n, math.ceil(end / bin_size))
        for i in range(lo, hi):
            bins[i] = 1
    return bins


def _segment_metrics(gt_bins: list, pred_bins: list, bin_size: float = 1.0) -> dict:
    tp = sum(g == 1 and p == 1 for g, p in zip(gt_bins, pred_bins))
    fp = sum(g == 0 and p == 1 for g, p in zip(gt_bins, pred_bins))
    fn = sum(g == 1 and p == 0 for g, p in zip(gt_bins, pred_bins))
    tn = sum(g == 0 and p == 0 for g, p in zip(gt_bins, pred_bins))

    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    recall    = tp / (tp + fn) if (tp + fn) > 0 else float("nan")

    # F1 = 0 when GT has events but no TP exist (regardless of FP count).
    # Without this, tp+fp=0 causes precision=NaN → f1=NaN → _safe_mean skips the
    # video entirely, making the aggregate look better than it actually is.
    if tp == 0 and fn > 0:
        f1 = 0.0
    elif not (math.isnan(precision) or math.isnan(recall) or (precision + recall) == 0):
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = float("nan")

    iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else float("nan")

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "gt_seconds":   round(tp * bin_size + fn * bin_size, 2),
        "pred_seconds": round(tp * bin_size + fp * bin_size, 2),
        "precision": round(precision, 4),
        "recall":    round(recall,    4),
        "f1":        round(f1,        4),
        "iou":       round(iou,       4),
    }


# ---------------------------------------------------------------------------
# Point-event helpers (filler words)
# ---------------------------------------------------------------------------

def _filler_metrics(gt_events: list, pred_events: list, tolerance_s: float = 1.0) -> dict:
    matched_gt   = set()
    matched_pred = set()

    pairs = []
    for pi, pe in enumerate(pred_events):
        pt = pe.get("start_time", pe.get("start_timestamp", pe.get("start", 0)))
        for gi, ge in enumerate(gt_events):
            gt_t = ge.get("start", ge.get("start_time", ge.get("start_timestamp", 0)))
            if abs(pt - gt_t) <= tolerance_s:
                pairs.append((abs(pt - gt_t), pi, gi))

    pairs.sort()
    for _, pi, gi in pairs:
        if pi not in matched_pred and gi not in matched_gt:
            matched_pred.add(pi)
            matched_gt.add(gi)

    tp = len(matched_gt)
    fp = len(pred_events) - tp
    fn = len(gt_events)   - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    recall    = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if not (math.isnan(precision) or math.isnan(recall) or (precision + recall) == 0)
          else float("nan"))

    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision":   round(precision, 4),
        "recall":      round(recall,    4),
        "f1":          round(f1,        4),
        "tolerance_s": tolerance_s,
    }


# ---------------------------------------------------------------------------
# Extractors from orchestrator results.*
# ---------------------------------------------------------------------------

def _extract_eye(svc: dict) -> dict:
    return {
        "eye_contact_away": svc.get("looking_away_events", []),
        "eye_contact_back": svc.get("back_facing_events",  []),
    }


def _extract_arm(svc: dict) -> dict:
    anomalies = svc.get("anomalies", {})
    return {
        "arm_no_gesture": anomalies.get("no_movement_periods",       []),
        "arm_excessive":  anomalies.get("excessive_movement_periods", []),
    }


def _extract_hip(svc: dict) -> dict:
    return {"hip_sway": svc.get("swaying_segments", [])}


def _extract_filler(svc: dict) -> dict:
    return {"filler_words": svc.get("filler_occurrences", [])}


def _extract_pitch(svc: dict) -> dict:
    segs = [
        {"start": s["start_timestamp"], "end": s["end_timestamp"]}
        for s in svc.get("monotonous_segments", [])
        if "start_timestamp" in s and "end_timestamp" in s
    ]
    return {"pitch_monotone": segs}


def _extract_volume(svc: dict) -> dict:
    def _norm(segs):
        return [{"start": s.get("start_timestamp", s.get("start", 0)),
                 "end":   s.get("end_timestamp",   s.get("end",   0))}
                for s in segs]
    return {
        "volume_too_quiet": _norm(svc.get("too_soft_segments", [])),
        "volume_too_loud":  _norm(svc.get("too_loud_segments", [])),
    }


# ---------------------------------------------------------------------------
# Service registry
# ---------------------------------------------------------------------------

# Maps annotation subdirectory name -> service config
SERVICES = {
    "eye_contact": {
        "orchestrator_key": "eye_contact",
        "extractor":        _extract_eye,
        "dims":             ["eye_contact_away", "eye_contact_back"],
        "dim_types":        {"eye_contact_away": "segment", "eye_contact_back": "segment"},
    },
    "arm_movement": {
        "orchestrator_key": "arm_movement",
        "extractor":        _extract_arm,
        "dims":             ["arm_no_gesture", "arm_excessive"],
        "dim_types":        {"arm_no_gesture": "segment", "arm_excessive": "segment"},
    },
    "hip": {
        "orchestrator_key": "hip",
        "extractor":        _extract_hip,
        "dims":             ["hip_sway"],
        "dim_types":        {"hip_sway": "segment"},
    },
    "filler_words": {
        "orchestrator_key": "filler_words",
        "extractor":        _extract_filler,
        "dims":             ["filler_words"],
        "dim_types":        {"filler_words": "point"},
    },
    "pitch": {
        "orchestrator_key": "pitch",
        "extractor":        _extract_pitch,
        "dims":             ["pitch_monotone"],
        "dim_types":        {"pitch_monotone": "segment"},
    },
    "volume": {
        "orchestrator_key": "volume",
        "extractor":        _extract_volume,
        "dims":             ["volume_too_quiet", "volume_too_loud"],
        "dim_types":        {"volume_too_quiet": "segment", "volume_too_loud": "segment"},
    },
}


# ---------------------------------------------------------------------------
# Per-video evaluation for one service
# ---------------------------------------------------------------------------

def evaluate_video_service(gt: dict, orchestrator: dict, svc_name: str, bin_size: float) -> dict:
    cfg          = SERVICES[svc_name]
    gt_annots    = gt.get("annotations", {})
    # Extend duration if any GT interval reaches past duration_s (guards against annotation errors).
    all_gt_ends = [iv.get("end", iv.get("end_timestamp", 0))
                   for ivs in gt_annots.values() for iv in ivs]
    duration = max(gt["duration_s"], max(all_gt_ends, default=0))
    svc_result   = orchestrator.get("results", {}).get(cfg["orchestrator_key"], {})

    if not svc_result.get("success"):
        err = svc_result.get("error", "no result in orchestrator output")
        print(f"    [WARN] {svc_name} not available: {err}")
        return {}

    pred_map = cfg["extractor"](svc_result)
    metrics  = {}

    for dim in cfg["dims"]:
        gt_intervals   = gt_annots.get(dim, [])
        pred_intervals = pred_map.get(dim, [])

        if cfg["dim_types"][dim] == "point":
            m = _filler_metrics(gt_intervals, pred_intervals)
            m["gt_count"]   = len(gt_intervals)
            m["pred_count"] = len(pred_intervals)
        else:
            gt_bins   = _intervals_to_bins(gt_intervals,   duration, bin_size)
            pred_bins = _intervals_to_bins(pred_intervals, duration, bin_size)
            max_len   = max(len(gt_bins), len(pred_bins))
            gt_bins   += [0] * (max_len - len(gt_bins))
            pred_bins += [0] * (max_len - len(pred_bins))
            m = _segment_metrics(gt_bins, pred_bins, bin_size)
            m["gt_intervals"]   = len(gt_intervals)
            m["pred_intervals"] = len(pred_intervals)

        metrics[dim] = m

    return metrics


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _safe_mean(values: list):
    valid = [v for v in values if v is not None and not math.isnan(v)]
    return round(sum(valid) / len(valid), 4) if valid else None


def aggregate_service(per_video: dict, svc_name: str) -> dict:
    dims = SERVICES[svc_name]["dims"]
    agg  = {}
    for dim in dims:
        keys = ["precision", "recall", "f1"]
        if SERVICES[svc_name]["dim_types"][dim] == "segment":
            keys.append("iou")
        collected = {k: [] for k in keys}
        for vid_metrics in per_video.values():
            if dim in vid_metrics:
                for k in keys:
                    collected[k].append(vid_metrics[dim].get(k))
        agg[dim] = {k: _safe_mean(collected[k]) for k in keys}
        agg[dim]["n_videos"] = sum(1 for v in per_video.values() if dim in v)
    return agg


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "  N/A "
    return f"{v:6.3f}"


def print_service_results(svc_name: str, per_video: dict, agg: dict, bin_size: float):
    cfg  = SERVICES[svc_name]
    dims = cfg["dims"]

    print(f"\n{'=' * 70}")
    print(f"  SERVICE: {svc_name.upper()}   (bin={bin_size}s)")
    print(f"{'=' * 70}")

    for vid, vid_metrics in sorted(per_video.items()):
        if not vid_metrics:
            continue
        print(f"\n  Video {vid}:")
        print(f"  {'Dimension':<24} {'P':>7} {'R':>7} {'F1':>7} {'IoU':>7}")
        print(f"  {'-' * 54}")
        for dim in dims:
            m = vid_metrics.get(dim, {})
            is_point = cfg["dim_types"][dim] == "point"
            iou_str  = "       " if is_point else _fmt(m.get("iou"))
            gt_n  = m.get("gt_count", m.get("gt_intervals", "?"))
            pr_n  = m.get("pred_count", m.get("pred_intervals", "?"))
            if is_point:
                detail = f"GT={gt_n} events, pred={pr_n} events"
            else:
                gt_s  = m.get("gt_seconds",   "?")
                pr_s  = m.get("pred_seconds", "?")
                detail = f"GT={gt_n} segs={gt_s}s, pred={pr_n} segs={pr_s}s"
            print(f"  {dim:<24} {_fmt(m.get('precision'))} {_fmt(m.get('recall'))}"
                  f" {_fmt(m.get('f1'))} {iou_str}  ({detail})")

    if len(per_video) > 1:
        print(f"\n  AGGREGATE ({agg[dims[0]].get('n_videos', '?')} videos):")
        print(f"  {'Dimension':<24} {'P':>7} {'R':>7} {'F1':>7} {'IoU':>7}")
        print(f"  {'-' * 54}")
        for dim in dims:
            m       = agg.get(dim, {})
            is_point = cfg["dim_types"][dim] == "point"
            iou_str  = "       " if is_point else _fmt(m.get("iou"))
            print(f"  {dim:<24} {_fmt(m.get('precision'))} {_fmt(m.get('recall'))}"
                  f" {_fmt(m.get('f1'))} {iou_str}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_json(path: Path):
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Fluent Speech microservice accuracy per service."
    )
    parser.add_argument("--annotations", default="annotations",
                        help="Root annotations dir containing service subdirs (default: annotations/)")
    parser.add_argument("--results", default="results",
                        help="Dir with *_orchestrator.json files (default: results/)")
    parser.add_argument("--bin-size", type=float, default=1.0,
                        help="Bin size in seconds for segment metrics (default: 1.0)")
    parser.add_argument("--service", default=None,
                        help="Evaluate only this service (e.g. eye_contact). Default: all.")
    parser.add_argument("--video", default=None,
                        help="Evaluate only this video ID (e.g. V1). Default: all.")
    parser.add_argument("--output", default=None,
                        help="Save full results as JSON to this path.")
    args = parser.parse_args()

    ann_root    = Path(args.annotations)
    results_dir = Path(args.results)

    if not ann_root.is_dir():
        print(f"ERROR: annotations directory not found: {ann_root}", file=sys.stderr)
        sys.exit(1)

    services_to_run = ([args.service] if args.service else list(SERVICES.keys()))
    full_output: dict[str, Any] = {"bin_size_s": args.bin_size, "services": {}}

    for svc_name in services_to_run:
        svc_dir = ann_root / svc_name
        if not svc_dir.is_dir():
            print(f"\n[SKIP] {svc_name}: no annotations/{svc_name}/ directory.")
            continue

        gt_files = sorted(svc_dir.glob("*_gt.json"))
        if not gt_files:
            print(f"\n[SKIP] {svc_name}: no *_gt.json files in annotations/{svc_name}/")
            continue

        per_video: dict[str, dict] = {}

        for gt_path in gt_files:
            gt  = load_json(gt_path)
            if gt is None:
                continue
            vid = gt.get("video_id", gt_path.stem.replace("_gt", ""))
            if args.video and vid != args.video:
                continue

            orch_path    = results_dir / f"{vid}_orchestrator.json"
            orchestrator = load_json(orch_path)
            if orchestrator is None:
                print(f"  [WARN] {orch_path} not found, skipping {vid} for {svc_name}.")
                continue

            metrics = evaluate_video_service(gt, orchestrator, svc_name, args.bin_size)
            if metrics:
                per_video[vid] = metrics

        if not per_video:
            print(f"\n[SKIP] {svc_name}: no evaluated videos.")
            continue

        agg = aggregate_service(per_video, svc_name)
        print_service_results(svc_name, per_video, agg, args.bin_size)
        full_output["services"][svc_name] = {"per_video": per_video, "aggregate": agg}

    if args.output:
        Path(args.output).write_text(
            json.dumps(full_output, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nFull results saved to: {args.output}")


if __name__ == "__main__":
    main()
