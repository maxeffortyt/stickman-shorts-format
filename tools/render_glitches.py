"""Find single corrupted frames in a rendered video.

Usage: python3 tools/render_glitches.py VIDEO.mp4        (a clean render prints "glitch frames: []")

A glitch is a single frame that differs a lot from both neighbours while the two neighbours match
each other (for example a tiled or flickering frame from a render tab that misbehaved). Every frame is
checked, downscaled to 320x180. Needs: opencv-python, numpy.
"""
import sys
import cv2
import numpy as np


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    cap = cv2.VideoCapture(sys.argv[1])
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(cv2.resize(f, (320, 180)).astype(np.int16))
    d = lambda a, b: float(np.abs(fr[a] - fr[b]).mean())
    g = [i for i in range(1, len(fr) - 1)
         if d(i, i - 1) > 15 and d(i, i + 1) > 15 and d(i - 1, i + 1) < 0.5 * min(d(i, i - 1), d(i, i + 1))]
    print(sys.argv[1].split("/")[-1], "frames", len(fr), "glitch frames:", g)


if __name__ == "__main__":
    main()
