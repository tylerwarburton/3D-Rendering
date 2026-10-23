#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=$(cd "$PROJECT_DIR/../.." && pwd)
OUTPUT_DIR="$REPO_DIR/output"
FRAMES_DIR="$OUTPUT_DIR/frames"

if [[ -n "${BLENDER_EXE:-}" ]]; then
  BLENDER_BIN=$BLENDER_EXE
elif command -v blender >/dev/null 2>&1; then
  BLENDER_BIN=$(command -v blender)
else
  BLENDER_BIN='/c/Users/tyler/AppData/Local/BlenderPortable/blender-4.3.2-windows-x64/blender.exe'
fi

if [[ ! -x "$BLENDER_BIN" ]]; then
  echo "Blender not found. Set BLENDER_EXE to a Blender 4.3+ executable." >&2
  exit 1
fi

mkdir -p "$FRAMES_DIR"
"$BLENDER_BIN" --background --factory-startup \
  --python "$PROJECT_DIR/blender_scene.py" -- --build
"$BLENDER_BIN" --background \
  "$PROJECT_DIR/roadster_rocket_what_could_have_been.blend" -a

FFMPEG_BIN=$(python - <<'PY'
import shutil
try:
    import imageio_ffmpeg
    print(imageio_ffmpeg.get_ffmpeg_exe())
except Exception:
    print(shutil.which("ffmpeg") or "")
PY
)
if [[ -z "$FFMPEG_BIN" ]]; then
  echo "FFmpeg not found. Install ffmpeg or imageio-ffmpeg." >&2
  exit 1
fi

cp "$FRAMES_DIR/frame_0285.png" "$OUTPUT_DIR/poster.png"
"$FFMPEG_BIN" -y -hide_banner -loglevel warning \
  -framerate 30 -start_number 1 -i "$FRAMES_DIR/frame_%04d.png" \
  -frames:v 300 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -movflags +faststart "$OUTPUT_DIR/roadster_rocket_what_could_have_been.mp4"

python - "$OUTPUT_DIR" <<'PY'
import sys
from pathlib import Path
import cv2
from PIL import Image

out = Path(sys.argv[1])
video = out / "roadster_rocket_what_could_have_been.mp4"
cap = cv2.VideoCapture(str(video))
assert cap.isOpened(), "MP4 could not be opened"
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
first_ok, _ = cap.read()
cap.set(cv2.CAP_PROP_POS_FRAMES, frames - 1)
last_ok, _ = cap.read()
cap.release()
with Image.open(out / "poster.png") as image:
    poster_size = image.size
raw = video.read_bytes()
faststart = 0 < raw.find(b"moov") < raw.find(b"mdat")
assert (w, h) == (1920, 1080)
assert abs(fps - 30.0) < 0.01 and frames == 300
assert first_ok and last_ok and poster_size == (1920, 1080) and faststart
print(f"Verified {w}x{h}, {fps:g} fps, {frames} frames, {frames/fps:.1f} s, fast-start")
PY

