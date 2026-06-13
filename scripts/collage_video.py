"""Collage video: one real experimental run next to the four model controls.

One Spanish trial (real trajectories) and the no-bias control of each of SFM, WarpDriver, CSM
and AVM, animated together. The real crowd circulates counterclockwise; the bare models mill
with no net sense — the visual form of the model-comparison result.

Run: PYTHONPATH=src python scripts/collage_video.py
"""

import subprocess
from dataclasses import replace
from pathlib import Path

import pandas as pd

from clockwise.analysis import comparison_animation
from clockwise.config import ArenaConfig
from clockwise.experiment import run_arena
from clockwise.models import MODELS
from clockwise.polarization import m_individual

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


def with_rotation(frames, sample_dt, smooth_s):
    """Turn (x, y) model frames into (x, y, m): m from a finite-difference velocity about the
    arena centre, trailing-averaged over `smooth_s`. Agent order is stable across model frames,
    so consecutive frames pair up by index."""
    window = max(1, round(smooth_s / sample_dt))
    raw = []
    for i, fr in enumerate(frames):
        prev = frames[i - 1] if i > 0 else fr
        raw.append([
            m_individual(((x - px) / sample_dt, (y - py) / sample_dt), (x, y), (0.0, 0.0))
            for (x, y), (px, py) in zip(fr, prev, strict=True)
        ])
    out = []
    for i, fr in enumerate(frames):
        lo = max(0, i - window + 1)
        triples = [
            (x, y, sum(raw[k][j] for k in range(lo, i + 1)) / (i - lo + 1))
            for j, (x, y) in enumerate(fr)
        ]
        out.append(triples)
    return out


_LABELS = {
    "SocialForceModel": "Social Force",
    "WarpDriverModel": "WarpDriver",
    "CollisionFreeSpeedModel": "Collision-Free Speed",
    "AnticipationVelocityModel": "Anticipation Velocity",
}


def main() -> None:
    exp, n_ped = experiment_frames(TRIAL, SAMPLE_DT, SMOOTH_S)
    duration = len(exp) * SAMPLE_DT
    print(f"experiment: {n_ped} peds, {len(exp)} frames (~{duration:.0f}s)")

    # Match the crowd size and window; control (no bias) for every model.
    base = ArenaConfig(
        n_agents=n_ped, biased_fraction=0.0, warmup_s=10.0, duration_s=10.0 + duration
    )
    cases = [("experiment (real data)", exp)]
    for name in MODELS:
        res = run_arena(seed=0, cfg=replace(base, model=name), record_traj=True)
        cases.append((_LABELS[name], with_rotation(res.trajectory, SAMPLE_DT, SMOOTH_S)))
        print(f"{name:32s} {len(res.trajectory)} frames, M̄={res.m_bar:+.3f}")

    n_frames = min(len(traj) for _, traj in cases)  # play in lockstep, no freezing
    cases = [(label, traj[:n_frames]) for label, traj in cases]

    mp4 = OUT / "collage_models.mp4"
    comparison_animation(cases, radius=RADIUS, out_path=mp4, fps=FPS, ncols=3)
    print(f"wrote {mp4}")

    gif = OUT / "collage_models.gif"
    palette = OUT / "_palette.png"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-vf", "fps=12,scale=900:-1:flags=lanczos,palettegen",
         str(palette)], check=True, capture_output=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-i", str(palette), "-lavfi",
         "fps=12,scale=900:-1:flags=lanczos[x];[x][1:v]paletteuse", str(gif)],
        check=True, capture_output=True)
    palette.unlink(missing_ok=True)
    print(f"wrote {gif}")


if __name__ == "__main__":
    main()
