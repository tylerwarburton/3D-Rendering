# Roadster vs. Rocket — “What Could Have Been”

An original, speculative 10-second Blender concept film. It is **not footage of
a real launch**, and the car and rocket are unbranded fictional designs.

## Finished outputs

- `../../output/roadster_rocket_what_could_have_been.mp4` — 1920 x 1080,
  H.264/yuv420p, 30 fps, 300 frames, 10.0 seconds, web fast-start enabled.
- `../../output/poster.png` — full-resolution closing hero frame.
- `roadster_rocket_what_could_have_been.blend` — native editable Blender scene.
- `blender_scene.py` — procedural scene, materials, rigs, animation, cameras,
  lighting, smoke, typography, and render setup.
- `../../output/frames/` — 300 lossless PNG masters retained for re-encoding.

## Requirements

- Windows x64 and Git Bash.
- Blender 4.3 or newer. The completed build used the official portable Blender
  4.3.2 binary at
  `/c/Users/tyler/AppData/Local/BlenderPortable/blender-4.3.2-windows-x64/blender.exe`.
- FFmpeg with `libx264`. The render script uses the copy bundled with the
  installed `imageio-ffmpeg` package if `ffmpeg` is not on `PATH`.
- The repository's existing OpenCV and Pillow packages for verification.

No external 3D assets, textures, or paid dependencies are required.

## One-command regeneration

From the repository root in Git Bash:

```bash
bash projects/roadster-rocket/render.sh
```

To select another Blender binary:

```bash
BLENDER_EXE=/c/path/to/blender.exe bash projects/roadster-rocket/render.sh
```

The script rebuilds the `.blend`, renders frames 1–300, encodes the MP4, copies
the poster, and verifies resolution, frame rate, frame count, duration,
decodability, and fast-start placement.

## Open and observe the animation

Open the native project from Git Bash:

```bash
"/c/Users/tyler/AppData/Local/BlenderPortable/blender-4.3.2-windows-x64/blender.exe" \
  projects/roadster-rocket/roadster_rocket_what_could_have_been.blend
```

In Blender, switch the viewport to **Rendered** shading and press **Space** to
play. Timeline camera markers switch between the establishing, launch,
smoke-chase, breakout, and hero cameras. Use Material Preview if Rendered
playback is below 30 fps while observing or screen-recording.

## Timing contract

| Frame | Event |
|---:|---|
| 45 | Car begins analytic acceleration |
| 75 | Engine ignition, exactly 30 frames / 1.0 second later |
| 165 | Rocket liftoff begins |
| 225 | Wide hero camera begins |
| 270 | Closing title and fiction disclosure appear |
| 300 | End of film |

The car X position is driven by a time-based expression. During the one-second
head start it uses constant illustrative acceleration, covering 8.94 m and
reaching 17.88 m/s at ignition. Wheel rotation is driven from that same travel
expression, preventing sliding or teleportation.

## Render time and disk use

On the delivery machine, scene generation took under 10 seconds and the final
300-frame 1080p Eevee pass took about 15 minutes. Expect roughly 10–30 minutes
depending on GPU and driver. The retained lossless sequence uses
substantially more disk than the final MP4 and may be removed after encoding.

## Intentional compromises

- Smoke is overlapping, displaced, translucent 3D geometry rather than a fluid
  simulation. It is fast, deterministic, and art-directable but less natural at
  very close inspection.
- The vehicle and launch infrastructure are detailed procedural approximations,
  not licensed manufacturer models.
- Eevee was selected over Cycles to make the 300-frame rebuild practical.
- The film is silent; the requested deliverable did not specify an audio track.
