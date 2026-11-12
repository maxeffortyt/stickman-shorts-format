"""Measure the visual style of a video clip.

Usage: python3 tools/style_metrics.py VIDEO OUT.json [--fps 10] [--max-seconds 120]
Needs: opencv-python, numpy. Analyse references and your own render at the same fps (10 by default).

Metrics (all computed on frames downscaled to 320 px width):
  palette        dominant colours (k-means, k=8) with share of pixels
  near_black     share of pixels with luma < 20 (pure-ish black)
  luma_mean/std  brightness and contrast
  sat_mean       mean HSV saturation (0-1)
  flatness       share of pixels within 12 RGB units of their frame's 16-colour quantisation
                 (high = flat vector look, low = textured/photographic)
  edge_density   share of Canny edge pixels
  cam_moving     share of frame pairs where global shift > 0.15 px (phase correlation)
  cam_speed      median global shift in px/frame when moving
  activity       share of frame pairs where >0.5% of pixels change noticeably
  change_area    mean share of pixels changing per frame pair
  events_per_min peaks in change signal (new element / big motion) per minute
  cuts_per_min   hard cuts per minute (histogram distance)
  shot_median_s  median shot length in seconds
"""
import sys, json, argparse
import numpy as np
import cv2


def kmeans_palette(pixels, k=8):
    pixels = np.float32(pixels)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k) / len(labels)
    order = np.argsort(-counts)
    return [{"rgb": [int(c) for c in centers[i][::-1]], "share": round(float(counts[i]), 4)} for i in order]


def flatness(frame):
    small = frame.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 2.0)
    _, labels, centers = cv2.kmeans(small, 16, None, crit, 1, cv2.KMEANS_PP_CENTERS)
    recon = centers[labels.flatten()]
    err = np.abs(small - recon).max(axis=1)
    return float((err < 12).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=10)
    ap.add_argument("--max-seconds", type=float, default=120)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, int(round(src_fps / a.fps)))
    eff_fps = src_fps / step
    frames, idx = [], 0
    while True:
        ok, f = cap.read()
        if not ok or idx / src_fps > a.max_seconds:
            break
        if idx % step == 0:
            h, w = f.shape[:2]
            frames.append(cv2.resize(f, (320, int(320 * h / w)), interpolation=cv2.INTER_AREA))
        idx += 1
    cap.release()
    if len(frames) < 3:
        sys.exit("too few frames")
    dur = len(frames) / eff_fps

    # colour statistics (sample ~2 fps)
    samp = frames[:: max(1, int(eff_fps // 2))]
    pix = np.concatenate([s.reshape(-1, 3) for s in samp])
    if len(pix) > 200000:
        pix = pix[np.random.default_rng(0).choice(len(pix), 200000, replace=False)]
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    luma = np.concatenate([g.flatten() for g in grays[:: max(1, int(eff_fps // 2))]])
    hsv = np.concatenate([cv2.cvtColor(s, cv2.COLOR_BGR2HSV).reshape(-1, 3) for s in samp])
    flat = float(np.mean([flatness(s) for s in samp[:: max(1, len(samp) // 20)]]))
    edges = float(np.mean([(cv2.Canny(g, 80, 160) > 0).mean() for g in grays[:: max(1, int(eff_fps))]]))

    # motion, activity, cuts
    win = cv2.createHanningWindow(grays[0].shape[::-1], cv2.CV_32F)
    shifts, change, hist_d = [], [], []
    prev_h = None
    for i in range(1, len(grays)):
        g0 = np.float32(grays[i - 1]); g1 = np.float32(grays[i])
        (dx, dy), _ = cv2.phaseCorrelate(g0, g1, win)
        shifts.append(float(np.hypot(dx, dy)))
        change.append(float((cv2.absdiff(grays[i - 1], grays[i]) > 18).mean()))
        h = cv2.calcHist([frames[i]], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        h = cv2.normalize(h, h).flatten()
        if prev_h is None:
            prev_h = cv2.normalize(cv2.calcHist([frames[0]], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3), None).flatten()
        hist_d.append(float(cv2.compareHist(prev_h, h, cv2.HISTCMP_BHATTACHARYYA)))
        prev_h = h
    shifts = np.array(shifts); change = np.array(change); hist_d = np.array(hist_d)
    # Hard cuts, detector v2 (9.11.2026, before any experiment run): v1 required hist_d > 0.45 AND
    # change > 0.35 and missed cuts between dark scenes (space backgrounds keep the histogram similar).
    # v2: a single-pair spike in pixel change or histogram distance vs both neighbours, or the v1
    # condition; spikes closer than 0.5 s are merged (flashes / glitch effects). Slow transitions
    # (wipes, zoom-throughs) are NOT counted, so this is a lower bound on scene changes.
    raw = []
    for k in range(1, len(change) - 1):
        nb_c = max(change[k - 1], change[k + 1], 0.02); nb_h = max(hist_d[k - 1], hist_d[k + 1], 0.03)
        if (change[k] > 0.2 and change[k] >= 2.0 * nb_c) or (hist_d[k] > 0.3 and hist_d[k] >= 2.5 * nb_h) \
                or (hist_d[k] > 0.45 and change[k] > 0.35):
            if not raw or k - raw[-1] > 0.5 * eff_fps:
                raw.append(k)
    cut_idx = np.array(raw, dtype=int)
    moving = shifts > 0.15
    # events: local maxima of change signal above an adaptive threshold
    thr = max(0.02, np.percentile(change, 75) * 1.5)
    ev = [i for i in range(1, len(change) - 1) if change[i] > thr and change[i] >= change[i - 1] and change[i] >= change[i + 1]]
    cut_t = np.concatenate([[0], (cut_idx + 1) / eff_fps, [dur]])
    shots = np.diff(cut_t)

    out = {
        "video": a.video, "seconds": round(dur, 2), "analysed_fps": round(eff_fps, 2), "frames": len(frames),
        "palette": kmeans_palette(pix),
        "near_black": round(float((luma < 20).mean()), 4),
        "luma_mean": round(float(luma.mean()) / 255, 4),
        "luma_std": round(float(luma.std()) / 255, 4),
        "sat_mean": round(float(hsv[:, 1].mean()) / 255, 4),
        "flatness": round(flat, 4),
        "edge_density": round(edges, 4),
        "cam_moving": round(float(moving.mean()), 4),
        "cam_speed": round(float(np.median(shifts[moving])) if moving.any() else 0.0, 3),
        "activity": round(float((change > 0.005).mean()), 4),
        "change_area": round(float(change.mean()), 4),
        "events_per_min": round(len(ev) / dur * 60, 2),
        "cuts_per_min": round(len(cut_idx) / dur * 60, 2),
        "shot_median_s": round(float(np.median(shots)), 2),
    }
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "palette"}))


if __name__ == "__main__":
    main()
