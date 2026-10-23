# Design log

## Round 1 - renderer proof (2026-10-15)

- Tested the repository's installed VTK renderer after the existing Blender 4.3
  installation was found to be missing `blender.exe`.
- Rejected the VTK look during visual review. It was too crude for the brief and
  none of its preview renders were used in the delivered film.

## Round 2 - native Blender cinematic (2026-10-15)

- Used an official Blender 4.3.2 portable build after verifying its SHA-256.
- Built an original 3D roadster, stainless launch vehicle, launch mount, tower,
  wet tarmac, lights, tanks, vapor, exhaust, and expanding smoke in Blender.
- Used Eevee Next PBR rendering, AgX color management, motion blur, depth of
  field, emissive practicals, and compositor glow.
- Locked car motion to frame 45 and ignition to frame 75. The first second uses
  constant illustrative acceleration and reaches 17.88 m/s after 8.94 m.
- Used deterministic displaced smoke geometry instead of a long fluid bake. It
  keeps the build fully procedural and the silhouette readable.
- Rendered 300 1920 x 1080 PNG frames and encoded a 30 fps H.264 fast-start MP4.
- Verified all 300 video frames decode, the duration is 10.0 seconds, the first
  and last frames open, the poster is 1920 x 1080, and timing tests pass.
