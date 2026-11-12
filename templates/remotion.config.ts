/**
 * Render settings that worked for the experiment (Remotion 4, macOS 26, Apple M1, 8 GB RAM).
 * All options: https://remotion.dev/docs/config
 */
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// macOS 26: Remotion's downloaded chrome-headless-shell crashed ("icudtl.dat not found" -> "Target closed").
// Using the installed Google Chrome fixed it. Change the path on Windows/Linux, or remove the line if the default works.
Config.setBrowserExecutable("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");

// With 2 render tabs, the system Chrome produced single tiled/flickering frames. One tab is slower but clean.
// Check every render with tools/render_glitches.py.
Config.setConcurrency(1);
