"""Turn an ElevenLabs character alignment into word timings for syncing animation.

Usage: python3 tools/alignment_to_words.py VOICE.alignment.json OUT_words.json [--offset 0.5] [--tempo 1.0]

  --offset  seconds of silence before the voice starts in the video (added to every time)
  --tempo   if the mp3 was later sped up (e.g. ffmpeg atempo=1.15), divide raw times by this factor

Output: [{"w": "word", "s": start_s, "e": end_s}, ...] in video time. Key cuts and labels to word
indexes (cut 2-3 frames before the cue word) so the picture follows the voice exactly.
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("alignment"); ap.add_argument("out")
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--tempo", type=float, default=1.0)
    a = ap.parse_args()
    al = json.load(open(a.alignment))
    al = al.get("alignment", al)
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, s0, e0 = [], "", 0.0, 0.0
    for c, s, e in zip(ch, st, en):
        if c.isspace():
            if cur:
                words.append({"w": cur, "s": round(s0 / a.tempo + a.offset, 3), "e": round(e0 / a.tempo + a.offset, 3)})
                cur = ""
            continue
        if not cur:
            s0 = s
        cur += c
        e0 = e
    if cur:
        words.append({"w": cur, "s": round(s0 / a.tempo + a.offset, 3), "e": round(e0 / a.tempo + a.offset, 3)})
    json.dump(words, open(a.out, "w"), indent=1)
    print(f"{len(words)} words, last ends at {words[-1]['e'] if words else 0:.2f} s")


if __name__ == "__main__":
    main()
