# STYLE.md: the Ricks Clips Shorts format (measured)

Source: 15 Shorts from the Ricks Clips YouTube channel, measured frame by frame. 13 of them use the current format (24 Shorts, 237 million views in 29 days; median 9.1 million views per Short). The numbers below describe those 13.

## Format
- Vertical 1080×1920, 30 fps. Length: 31–78 s; the most-viewed ones are 60–65 s.
- True (or true-sounding) "strange history / how things work" stories, told as a mini-story with characters.

## Look
- Characters: 2D stick-figure people with big round white heads, simple dot eyes, expressive eyebrows and mouths, thin limbs or simple clothes (robes, uniforms, hats).
- They stand in detailed, colourful, 3D-looking worlds (palaces, offices, ships, deserts, streets) with soft, cinematic light: sunsets, night scenes, warm interiors. Not flat vector art.
- The camera is almost always moving (slow push-ins, pans, parallax), with a cut every few seconds.
- Captions: one word at a time (sometimes 2–3 short words), centred horizontally at about 70% of the frame height, bold white with a black outline, in sync with the voice.

## Visual measurements (frames downscaled to 320 px width, 10 fps; mean ± std over 13 Shorts)
| Metric | Value | Meaning |
|---|---|---|
| near_black | 0.054 ± 0.051 | share of pixels with luma < 20: almost no pure black |
| luma_mean | 0.41 ± 0.07 | average brightness (0–1) |
| luma_std | 0.24 ± 0.02 | contrast |
| sat_mean | 0.49 ± 0.07 | mean HSV saturation (0–1) |
| flatness | 0.60 ± 0.11 | share of pixels close to a 16-colour version of the frame (1 = flat vector art; 0.60 = textured, lit, 3D-looking) |
| edge_density | 0.082 ± 0.021 | share of edge pixels (Canny): lots of detail |
| cam_moving | 0.81 ± 0.05 | share of frame pairs where the whole image shifts (camera motion) |
| cam_speed | 0.65 ± 0.08 | median global shift when moving, px per frame at 320 px width |
| activity | 0.995 ± 0.007 | share of frame pairs where more than 0.5% of pixels change: something always moves |
| change_area | 0.24 ± 0.06 | mean share of pixels that change between frames |
| events_per_min | 20.1 ± 6.6 | new elements or big motions per minute |
| cuts_per_min | 12.4 ± 4.0 | hard cuts per minute (median shot length 3.6 s) |

## Narration and script (measured on 13 scripts)
- The voice starts on the very first frame (0.0 s). No intro, no title card.
- Pace: 3.35–3.91 words per second (median 3.7, about 220 words per minute).
- Structure that the most-viewed Shorts share:
  1. Hook: one sentence about a person doing something strange and concrete, in the past tense. No questions.
  2. A turn to the context, usually starting with "You see," (10 of 13 scripts).
  3. Other people doubt or laugh at the main character.
  4. Escalation with time markers ("Then…", "weeks later", "by July").
  5. The mechanism, explained near the end in one or two plain sentences, often with an everyday comparison.
  6. The last sentence is the payoff. No call to action, no "subscribe"; the Short ends abruptly, so it loops.
- Shorts that opened with a question, explained without a story, or used a fantasy premise got far fewer views (0.13–0.52 million versus 3–33 million).

## Sound
- Integrated loudness about −14 LUFS, loudness range about 2 LU (heavily compressed), peaks about −2 dBFS.
- A constant bed of music and sound effects sits about 5–6 dB under the voice.
