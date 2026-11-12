"""Similarity score (0-100) of a measured clip to the reference set.

Usage:
  python3 tools/similarity.py build REF_DIR OUT_profile.json      # aggregate reference reports (style_metrics.py JSONs)
  python3 tools/similarity.py score profile.json CLIP_report.json  # score one clip
The bundled profile of the measured Kurzgesagt style is reference/ref_profile.json (statistics only).

Score: for each metric, z = |clip - ref_mean| / max(ref_std, floor). Metric score = exp(-z^2 / 8)
(z=1 -> 88, z=2 -> 61, z=3 -> 32). Palette score = mean nearest-colour distance between the clip's
top colours and the reference palette pool. Final = weighted mean x 100.
Weights are fixed BEFORE the experiment runs, so no tuning to favour any effort level.
"""
import sys, json, glob, math
import numpy as np

METRICS = {  # metric: (weight, floor for std)
    "near_black": (1.0, 0.01), "luma_mean": (1.0, 0.03), "luma_std": (1.0, 0.02), "sat_mean": (1.5, 0.03),
    "flatness": (2.0, 0.03), "edge_density": (1.0, 0.005), "cam_moving": (1.5, 0.05), "cam_speed": (0.5, 0.2),
    "activity": (1.0, 0.05), "change_area": (1.0, 0.01), "events_per_min": (1.0, 5.0), "cuts_per_min": (1.0, 1.0),
}
PALETTE_WEIGHT = 2.0


def build(ref_dir, out):
    reps = [json.load(open(f)) for f in sorted(glob.glob(f"{ref_dir}/*.json"))]
    prof = {"n": len(reps), "metrics": {}, "palette_pool": []}
    for m in METRICS:
        v = np.array([r[m] for r in reps], float)
        prof["metrics"][m] = {"mean": float(v.mean()), "std": float(v.std()), "min": float(v.min()), "max": float(v.max())}
    for r in reps:
        prof["palette_pool"] += [p["rgb"] for p in r["palette"] if p["share"] > 0.03]
    json.dump(prof, open(out, "w"), indent=1)
    print(json.dumps(prof["metrics"], indent=1))


def score(prof_path, rep_path):
    prof = json.load(open(prof_path)); rep = json.load(open(rep_path))
    parts, wsum = {}, 0.0
    total = 0.0
    for m, (w, floor) in METRICS.items():
        st = prof["metrics"][m]
        z = abs(rep[m] - st["mean"]) / max(st["std"], floor)
        s = math.exp(-z * z / 8)
        parts[m] = round(s * 100, 1); total += w * s; wsum += w
    pool = np.array(prof["palette_pool"], float)
    dists = []
    for p in rep["palette"]:
        if p["share"] > 0.03:
            d = np.sqrt(((pool - np.array(p["rgb"], float)) ** 2).sum(axis=1)).min()
            dists.append((d, p["share"]))
    if dists:
        d = sum(x * w for x, w in dists) / sum(w for _, w in dists)
        ps = math.exp(-(d / 60) ** 2)
    else:
        ps = 0.0
    parts["palette"] = round(ps * 100, 1); total += PALETTE_WEIGHT * ps; wsum += PALETTE_WEIGHT
    res = {"clip": rep_path, "score": round(total / wsum * 100, 1), "parts": parts}
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3])
    else:
        score(sys.argv[2], sys.argv[3])
