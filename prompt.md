# The prompt

## Exactly as used in the experiment (all six runs, word for word)
Each run got a blank Remotion 4 project with `STYLE.md` in it, plus `../../.env` (ElevenLabs key, voice and model) and `../../assets/music` (three royalty-free tracks; `assets/sfx` was empty).

```
Make a 60-second vertical YouTube Short: "How people made ice in the desert, long before electricity" (the Persian yakhchal). Use the format described in STYLE.md (measurements of the Ricks Clips Shorts).

Rules:
- Copy the format only. Do not use Ricks Clips' characters, stories, names, footage or images, and don't download or watch their videos: STYLE.md is your only reference. Everything must be original.
- You decide the story and what to show. Invented characters are fine, but every fact must be true.
- This folder is a blank Remotion 4 project. Build the whole Short here: write the narration, design and animate every visual in code (SVG, Canvas, CSS or WebGL/three.js: your choice), add captions and sound. No image or video generators, and no downloaded images, video or audio.
- Output: 1080x1920, 30 fps, 60 seconds (±2 s), rendered to out/final.mp4. Keep the render settings in remotion.config.ts. This computer is a Mac M1 with 8 GB of RAM.
- Narration: write it to narration.txt (English) and generate the voice-over with the ElevenLabs API, using ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID and ELEVENLABS_MODEL_ID from ../../.env, voice settings {"stability": 0.5}, output format mp3_44100_192. Use exactly this voice and these settings; don't change them. Sync the animation and the captions to the voice-over. Use curl for HTTP calls (Python on this machine has no SSL certificates).
- Music and sound effects: only files from ../../assets/music and ../../assets/sfx, or sounds you synthesize yourself.
- Work on your own from start to finish. Don't ask me anything. When you're done, write NOTES.md: the title you would give this Short, what you made, what you'd improve, and anything that didn't work.
```

## Reusable template
```
Make a 60-second vertical YouTube Short: "<your true story>". Use the format described in STYLE.md.

Rules:
- Copy the format only: original characters, story and visuals. Invented characters are fine, but every fact must be true; check facts against sources before you record the voice.
- Build everything in code in this Remotion project (SVG, Canvas or three.js). No image or video generators, no downloaded images, video or audio.
- Output: 1080x1920, 30 fps, 60 seconds (±2 s), out/final.mp4.
- Voice: ElevenLabs with-timestamps (see tools/tts.sh). The format runs at about 3.7 words per second: either write a short script, or time-compress the finished take, and say which.
- When done, measure the render with tools/style_metrics.py and tools/similarity.py, fix the weakest metrics once, and write NOTES.md.
```
