"""Regenerate the rotation videos with agents coloured by turning direction.

Writes the three-up comparison (0% / 45% / 100% left-turners) and the three individual clips,
each agent coloured by its rotation m (blue = CCW, red = CW) with the live collective
polarization M in the corner — the same encoding as the model collage.

Run: PYTHONPATH=src python scripts/make_rotation_media.py
"""

import subprocess
from dataclasses import replace
from pathlib import Path

from clockwise.analysis import comparison_animation, rotation_frames
from clockwise.config import ArenaConfig
from clockwise.experiment import run_arena

OUT = Path("docs/results")
SAMPLE_DT = 0.2  # run_arena records a frame every 0.2 s
SMOOTH_S = 2.0
FPS = 20
SEED = 0

CASES = [
    ("0% left-turners", 0.0, "rotation_control"),
    ("45% left-turners", 0.45, "rotation_f45"),
    ("100% left-turners", 1.0, "rotation_f100"),
]


def to_gif(mp4: Path, gif: Path) -> None:
    palette = OUT / "_palette.png"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-vf", "fps=12,scale=520:-1:flags=lanczos,palettegen",
         str(palette)], check=True, capture_output=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-i", str(palette), "-lavfi",
         "fps=12,scale=520:-1:flags=lanczos[x];[x][1:v]paletteuse", str(gif)],
        check=True, capture_output=True)
    palette.unlink(missing_ok=True)


def main() -> None:
    base = ArenaConfig()
    OUT.mkdir(parents=True, exist_ok=True)
    cases = []
    for label, frac, stem in CASES:
        res = run_arena(SEED, replace(base, biased_fraction=frac), record_traj=True)
        frames = rotation_frames(res.trajectory, SAMPLE_DT, SMOOTH_S)
        cases.append((label, frames))
        mp4 = OUT / f"{stem}.mp4"
        comparison_animation([(label, frames)], radius=base.radius, out_path=mp4, fps=FPS)
        to_gif(mp4, OUT / f"{stem}.gif")
        print(f"{label:20s} M̄={res.m_bar:+.3f}  wrote {stem}.{{mp4,gif}}")

    mp4 = OUT / "comparison.mp4"
    comparison_animation(cases, radius=base.radius, out_path=mp4, fps=FPS)
    to_gif(mp4, OUT / "comparison.gif")
    print(f"wrote {mp4} and comparison.gif")


if __name__ == "__main__":
    main()
