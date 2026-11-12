---
name: stickman-shorts-format
description: Make a 60-second vertical YouTube Short in the measured "stick figures in a 3D world" story-explainer format (the format of the Ricks Clips channel, format only: no characters, stories, voice or footage), built entirely in code with Remotion (SVG and/or three.js), an ElevenLabs voice-over synced by word timestamps, and a measurement loop that scores the render against the format. Use when asked for a viral stickman Short, a Ricks Clips-style Short, or a "true story" explainer Short.
---

# Stickman Shorts format

This skill turns one true story into a ~60-second vertical Short that matches a *measured* format, then checks the render against the same numbers. The numbers come from 13 Shorts of the current Ricks Clips format (analysed frame by frame at 10 fps, plus speech-to-text). Read `STYLE.md` before you design anything.

**Hard rules**
- Copy the format only. Never use the reference channel's characters, stories, names, voice, footage or images.
- Invented characters are fine; every fact must be true. Check facts against sources before you record the voice, and drop what you can't back up.
- No image or video generators and no downloaded images, video or audio. Synthesize sound effects yourself if you have none.
- Never print or commit API keys.

## Workflow

### 1. The script (most of the views live here)
Follow the six beats in `STYLE.md`:
1. Hook on the first frame: one past-tense sentence about a person doing something strange and concrete. No question.
2. "You see," and the context.
3. People doubt or laugh at the main character.
4. Escalation with time markers.
5. The mechanism near the end, in one or two plain sentences, with an everyday comparison.
6. The last sentence is the payoff. No call to action; end abruptly so it loops.
Measured flops opened with a question, explained without a story, or used a fantasy premise.

### 2. The voice
The reference talks at about 3.7 words per second. Many TTS voices read at about 2.5. Decide up front: write about 150 words at natural speed, or write about 210 and time-compress the finished take (ffmpeg `atempo`, pitch preserved, pauses shortened). Say which one you did in your notes. Use the ElevenLabs `with-timestamps` endpoint (`tools/tts.sh`) and drive captions and cuts from the word timings (`tools/alignment_to_words.py`).

### 3. The picture
- Characters: 2D stick figures with big round white heads, dot eyes, expressive brows and mouths.
- World: detailed, lit, 3D-looking. The best-scoring runs used three.js for the world and 2D SVG characters anchored to 3D positions (an invisible 3D stand-in can cast the character's shadow).
- Camera almost always moving; a cut every 3–4 seconds; one-word captions, bold white with a black outline, centred at about 70% of the height.
- On an 8 GB Mac: keep `templates/remotion.config.ts` (system Chrome, concurrency 1) and check every render with `tools/render_glitches.py`.

### 4. Measure and fix
```bash
python3 tools/style_metrics.py out/final.mp4 reports/final.json --fps 10
python3 tools/similarity.py score reference/ricks_profile.json reports/final.json
```
For scale, the reference Shorts score 71.5–97.3 against each other (median 91.0). Fix the weakest parts first (usually motion: share of the picture that changes per frame).

### 5. Notes
Write what you made, the title you'd use, what you would improve, which facts you used and where they came from, and anything you couldn't check (you can't listen to your own mix: say so).

## Measuring a Claude Code run (optional)
`tools/session_cost.py` (tokens and cost at API list prices) and `tools/model_time.py` (time the model was working vs time spent in local tools) read a session transcript from `~/.claude/projects/`.
