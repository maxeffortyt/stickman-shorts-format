# stickman-shorts-format

A free Claude Code skill for making 60-second vertical "stick figures in a 3D world" story-explainer Shorts, in the **measured** format of the Ricks Clips channel, and for checking the result with numbers instead of vibes.

It comes from an experiment: one prompt, six blind Claude Code runs (Claude Fable 5.2 at low, medium, high, extra high and max effort, plus Claude Opus 5.5 at extra high), each making the same Short: *"How people made ice in the desert, long before electricity"* (the Persian yakhchal), in code only.

> Format only. This skill contains **no** Ricks Clips frames, footage, characters, stories, voice or audio, only numbers measured from 13 Shorts. Not affiliated with or endorsed by Ricks Clips. Go watch the real thing: https://www.youtube.com/@RicksClips3000

## Results of the experiment (all measured)
| Run | Clock time | Model working | Cost at API prices | Score vs format (0–100) |
|---|---|---|---|---|
| Fable 5.2 low | 19.8 min | 12.1 min | $5.64 | 77.0 |
| Fable 5.2 medium | 29.3 min | 18.4 min | $8.25 | 87.4 |
| Fable 5.2 high | 51.1 min* | 32.3 min | $14.91 | 89.5 |
| Fable 5.2 extra high | 101.6 min* | 68.8 min | $36.70 | 93.6 |
| Fable 5.2 max | 135.1 min* | 96.0 min | $51.14 | 93.4 |
| Opus 5.5 extra high | 57.2 min* | 37.0 min | $12.48 | 78.7 |

\* These four ran at the same time on one 8 GB M1 laptop, so their clock times include waiting for each other. "Model working" is the time spent generating, from the session transcripts (`tools/model_time.py`). For scale: the reference Shorts score 71.5–97.3 against each other (median 91.0).

## What's inside
| file | what it is |
|---|---|
| `SKILL.md` | the workflow: script beats → voice decision → picture → measure and fix → notes |
| `STYLE.md` | the measured format: 12 visual metrics, narration pace, script structure, sound |
| `prompt.md` | the exact prompt used in the experiment and a reusable template |
| `LESSONS.md` | lessons from the six runs |
| `reference/ricks_profile.json` | reference statistics for the similarity score (numbers only) |
| `tools/style_metrics.py`, `tools/similarity.py` | measure a video and score it 0–100 against the profile (weights fixed before the experiment) |
| `tools/render_glitches.py` | finds single corrupted frames in a render |
| `tools/tts.sh`, `tools/alignment_to_words.py` | ElevenLabs voice-over with character timestamps (curl) → word timings |
| `tools/session_cost.py`, `tools/model_time.py` | tokens, cost and working time of a Claude Code session |
| `templates/remotion.config.ts` | render settings that worked (system Chrome on macOS, concurrency 1) |

## Install
```bash
git clone https://github.com/maxeffortyt/stickman-shorts-format ~/.claude/skills/stickman-shorts-format
```
Then ask Claude Code for a stickman Short about any true story, or point it at `SKILL.md`.

**Requirements:** Node 20+ and Remotion 4, Python 3 with `opencv-python` and `numpy`, Google Chrome (used by the render config), an ElevenLabs API key for the voice.

## License
MIT. See `LICENSE`.
