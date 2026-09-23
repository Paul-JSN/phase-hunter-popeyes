"""Cut the filmed reaction clips into looping card videos.

Run on the machine that holds the raw footage:

    python3 scripts/make_clip_cards.py

For each clip it looks only inside the usable part of the take (the tail where
the phone is picked up is excluded), finds the two seconds with the most motion,
composites them over a backdrop we drew, and writes a ping-pong loop so the card
never jumps on repeat.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIPS = ROOT / "game/clips"
OUT = CLIPS / "cards"
WORK = CLIPS / "_work"
WINDOW = 2.0          # seconds kept from each take
SAMPLE_FPS = 8

# file -> (usable seconds from the start, backdrop)
TAKES = {
    "beat_agent.mov.mp4": (3.0, "stadium"),
    "reveal_low.mp4":     (8.0, "highway"),
    "noisy_ping.mp4":     (5.0, "lab"),
    "broke.mp4":          (8.0, "night"),
    "reveal_high.mp4":    (7.0, "stadium"),
}


def run(args: list[str]) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def best_window(source: pathlib.Path, usable: float) -> float:
    """Start time of the most eventful WINDOW seconds inside the usable take."""
    with tempfile.TemporaryDirectory() as tmp:
        run(["ffmpeg", "-v", "error", "-y", "-t", f"{usable}", "-i", str(source),
             "-vf", f"fps={SAMPLE_FPS},scale=96:96", "-pix_fmt", "gray", f"{tmp}/f_%04d.png"])
        frames = sorted(pathlib.Path(tmp).glob("f_*.png"))
        if len(frames) < SAMPLE_FPS * WINDOW + 2:
            return 0.0
        images = [np.asarray(Image.open(f), dtype=np.float32) for f in frames]
        motion = np.array([np.abs(b - a).mean() for a, b in zip(images, images[1:])])
    span = int(WINDOW * SAMPLE_FPS)
    totals = np.convolve(motion, np.ones(span), mode="valid")
    start = float(np.argmax(totals)) / SAMPLE_FPS
    return min(start, max(0.0, usable - WINDOW))


def build(source: pathlib.Path, backdrop: pathlib.Path, start: float, destination: pathlib.Path) -> None:
    chain = (
        # the take: square, softly framed, gently pushing in
        "[0:v]scale=214:214,setsar=1,"
        "zoompan=z='min(zoom+0.0009,1.10)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=214x214:fps=24,"
        "pad=224:224:5:5:0x3CC8B4[clip];"
        # backdrop, very slowly drifting
        "[1:v]scale=520:384,crop=460:340:'(in_w-out_w)/2+8*sin(t/3)':'(in_h-out_h)/2'[bg];"
        "[bg][clip]overlay=(W-w)/2:52:shortest=1,format=yuv420p,split[a][b];"
        "[b]reverse[r];[a][r]concat=n=2:v=1[v]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start}", "-t", f"{WINDOW}", "-i", str(source),
         "-loop", "1", "-i", str(backdrop), "-filter_complex", chain, "-map", "[v]", "-an",
         "-r", "24", "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "38", "-row-mt", "1", str(destination)])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (usable, backdrop) in TAKES.items():
        source = CLIPS / name
        if not source.exists():
            print(f"skip {name}: not found")
            continue
        card = name.split(".")[0]
        start = best_window(source, usable)
        destination = OUT / f"{card}.webm"
        build(source, WORK / f"bd_{backdrop}.png", start, destination)
        run(["ffmpeg", "-v", "error", "-y", "-ss", "0.8", "-i", str(destination),
             "-frames:v", "1", str(WORK / f"card_{card}.png")])
        print(f"{card:12} window {start:4.1f}-{start+WINDOW:4.1f}s on {backdrop:8} "
              f"{destination.stat().st_size/1024:5.0f} KB")


if __name__ == "__main__":
    main()
