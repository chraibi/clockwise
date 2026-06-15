"""Collage video: one real experimental run next to the four model controls.

One Spanish trial (real trajectories) and the no-bias control of each of SFM, WarpDriver, CSM
and AVM, animated together. The real crowd circulates counterclockwise; the bare models mill
with no net sense — the visual form of the model-comparison result.

Run: PYTHONPATH=src python scripts/collage_video.py
"""

import math
import subprocess
from dataclasses import replace
from pathlib import Path

import pandas as pd

from clockwise.analysis import comparison_animation, rotation_frames
from clockwise.config import ArenaConfig
from clockwise.experiment import run_arena
from clockwise.models import MODELS

TRIAL = Path("materials/ExperimentalData/Spain/A9/2.csv")  # 32 peds, clear CCW rotation
OUT = Path("docs/results")
RADIUS = 5.0
SAMPLE_DT = 0.2  # s between rendered frames
FPS = 15
SMOOTH_S = 2.0  # s, trailing window for the per-agent colour (rotation is noisy frame-to-frame)


def experiment_frames(csv: Path, sample_dt: float, smooth_s: float):
    """Frames of (x, y, m) per pedestrian from a trial CSV, sampled every `sample_dt` seconds.
    `m` is the authors' per-agent polarization (`Pol`), trailing-averaged per pedestrian over
    `smooth_s` so the colour reflects sustained rotation, not frame-to-frame jitter."""
    df = pd.read_csv(csv).sort_values(["Id-Ped", "Time(s)"])
    times = sorted(df["Time(s)"].unique())
    win = max(1, round(smooth_s / (times[1] - times[0])))
    df["m"] = df.groupby("Id-Ped")["Pol"].transform(
        lambda s: s.rolling(win, min_periods=1).mean()
    )
    stride = max(1, round(sample_dt / (times[1] - times[0])))
    frames = []
    for t in times[::stride]:
        rows = df[df["Time(s)"] == t]
        frames.append(list(zip(rows["X(m)"], rows["Y(m)"], rows["m"], strict=True)))
    return frames, int(df["Id-Ped"].nunique())


_LABELS = {
    "SocialForceModel": "Social Force",
    "WarpDriverModel": "WarpDriver",
    "CollisionFreeSpeedModel": "Collision-Free Speed",
    "AnticipationVelocityModel": "Anticipation Velocity",
}


def to_gif(mp4: Path, gif: Path) -> None:
    palette = OUT / "_palette.png"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-vf", "fps=12,scale=900:-1:flags=lanczos,palettegen",
         str(palette)], check=True, capture_output=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-i", str(palette), "-lavfi",
         "fps=12,scale=900:-1:flags=lanczos[x];[x][1:v]paletteuse", str(gif)],
        check=True, capture_output=True)
    palette.unlink(missing_ok=True)


def render(exp, starts, base, rec_duration, biased_fraction, stem, warmup_s=0.0) -> None:
    """One collage: experiment beside every model at the given bias share.

    `warmup_s` lets the models settle before recording (the rotation needs time to build); with
    warmup_s = 0 the recording starts at the shared experiment positions."""
    cases = [("experiment", exp)]
    for name in MODELS:
        cfg = replace(base, model=name, biased_fraction=biased_fraction,
                      warmup_s=warmup_s, duration_s=warmup_s + rec_duration)
        res = run_arena(seed=0, cfg=cfg, record_traj=True, starts=starts)
        cases.append((_LABELS[name], rotation_frames(res.trajectory, SAMPLE_DT, SMOOTH_S)))
        print(f"  {name:32s} M̄={res.m_bar:+.3f}")
    n_frames = min(len(traj) for _, traj in cases)  # play in lockstep, no freezing
    cases = [(label, traj[:n_frames]) for label, traj in cases]
    mp4 = OUT / f"{stem}.mp4"
    comparison_animation(cases, radius=RADIUS, out_path=mp4, fps=FPS, ncols=3)
    to_gif(mp4, OUT / f"{stem}.gif")
    print(f"  wrote {stem}.{{mp4,gif}}")


def main() -> None:
    exp, n_ped = experiment_frames(TRIAL, SAMPLE_DT, SMOOTH_S)
    duration = len(exp) * SAMPLE_DT
    print(f"experiment: {n_ped} peds, {len(exp)} frames (~{duration:.0f}s)")

    starts = [(x, y) for x, y, _ in exp[0]]
    gap = min(math.dist(a, b) for i, a in enumerate(starts) for b in starts[i + 1 :])
    radius = min(0.2, gap / 2 - 0.02)  # shrink the body to fit the real crowd spacing
    base = ArenaConfig(n_agents=len(starts), agent_radius=radius)

    # Control: no warm-up, so frame 0 is the shared experiment start.
    print("control (no bias):")
    render(exp, starts, base, duration, biased_fraction=0.0, stem="collage_models")
    # Biased: warm up first so the counterclockwise drift is established before recording.
    print("biased (30% left-turners):")
    render(exp, starts, base, duration, biased_fraction=0.30,
           stem="collage_models_biased", warmup_s=30.0)


if __name__ == "__main__":
    main()
