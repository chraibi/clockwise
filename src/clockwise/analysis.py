from pathlib import Path

import numpy as np
import pandas as pd


def mbar_table(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/std of M-bar per (biased_fraction, n_agents)."""
    return (
        df.groupby(["biased_fraction", "n_agents"])["m_bar"]
        .agg(mean="mean", std="std", n="count")
        .reset_index()
        .fillna({"std": 0.0})
    )


def m_pdf_plot(series_by_label: dict[str, list[float]], out_path: Path) -> Path:
    """Probability density of M(t) for each labelled condition (paper Fig 2 style)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5))
    for label, series in series_by_label.items():
        ax.hist(series, bins=40, range=(-1, 1), density=True, histtype="step", label=label)
    ax.axvline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xlabel("M")
    ax.set_ylabel("pdf")
    ax.set_title("Polarization M: control vs biased")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def trajectory_animation(
    trajectory: list[list[tuple[float, float]]], radius: float, out_path: Path, fps: int = 20
) -> Path:
    """Animate agent positions inside the arena to an mp4."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation
    from matplotlib.patches import Circle

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.add_patch(Circle((0, 0), radius, fill=False, color="#5b6b88"))
    scat = ax.scatter([], [], s=40, c="#4e79a7")
    ax.set_xlim(-radius * 1.05, radius * 1.05)
    ax.set_ylim(-radius * 1.05, radius * 1.05)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    def frame(i):
        scat.set_offsets(trajectory[i])
        return [scat]

    anim = animation.FuncAnimation(fig, frame, frames=len(trajectory), interval=1000 / fps)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out_path, writer=animation.FFMpegWriter(fps=fps, bitrate=2400))
    plt.close(fig)
    return out_path


def rotation_frames(
    frames: list[list[tuple[float, float]]], sample_dt: float, smooth_s: float = 0.0
) -> list[list[tuple[float, float, float]]]:
    """Annotate `(x, y)` frames with each agent's rotation -> `(x, y, m)`.

    `m` is the unit-velocity projection on the CCW tangent about the arena centre, from a
    finite-difference velocity (so agent order must be stable across frames). With `smooth_s`
    > 0 the `m` channel is trailing-averaged over that window, since rotation is noisy frame to
    frame."""
    from .polarization import m_individual

    raw = []
    for i, fr in enumerate(frames):
        prev = frames[i - 1] if i > 0 else fr
        raw.append([
            m_individual(((x - px) / sample_dt, (y - py) / sample_dt), (x, y), (0.0, 0.0))
            for (x, y), (px, py) in zip(fr, prev, strict=True)
        ])
    window = max(1, round(smooth_s / sample_dt)) if smooth_s > 0 else 1
    out = []
    for i, fr in enumerate(frames):
        lo = max(0, i - window + 1)
        out.append([
            (x, y, sum(raw[k][j] for k in range(lo, i + 1)) / (i - lo + 1))
            for j, (x, y) in enumerate(fr)
        ])
    return out


def comparison_animation(
    cases: list[tuple[str, list[list[tuple[float, ...]]]]],
    radius: float,
    out_path: Path,
    fps: int = 20,
    ncols: int | None = None,
) -> Path:
    """Animate several labelled cases as arena panels to an mp4.

    cases: list of (label, trajectory). Each frame is a list of points: `(x, y)` for a single
    colour, or `(x, y, m)` to colour each agent by its rotation `m` (blue = CCW, red = CW, with
    a shared colourbar). Panels share a clock; shorter trajectories hold their last frame.
    Panels lay out in a grid of `ncols` columns (default: a single row); a partial last row is
    centred under the rows above it."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation, cm
    from matplotlib.colors import Normalize
    from matplotlib.patches import Circle

    n = len(cases)
    n_frames = max(len(traj) for _, traj in cases)
    ncols = ncols or n
    nrows = (n + ncols - 1) // ncols
    colored = len(cases[0][1][0][0]) == 3
    cmap = "coolwarm_r"

    # Grid is 2 half-columns per panel, so a partial last row can be centred by a 1-column shift.
    fig = plt.figure(figsize=(4.2 * ncols, 4.6 * nrows), layout="constrained")
    gs = fig.add_gridspec(nrows, 2 * ncols)
    axes = []
    for idx in range(n):
        row, col = divmod(idx, ncols)
        row_count = min(ncols, n - row * ncols)
        c0 = (ncols - row_count) + 2 * col  # centre a short row
        axes.append(fig.add_subplot(gs[row, c0:c0 + 2]))

    scatters = []
    labels = []  # per-panel collective-polarization readout (only when colored)
    for ax, (label, _) in zip(axes, cases, strict=True):
        ax.add_patch(Circle((0, 0), radius, fill=False, color="#5b6b88"))
        if colored:
            scatters.append(ax.scatter([], [], s=30, c=[], cmap=cmap, vmin=-1, vmax=1))
            # top-left corner: inside the box, outside the disk
            labels.append(ax.text(0.04, 0.96, "", transform=ax.transAxes, ha="left",
                                  va="top", fontsize=11))
        else:
            scatters.append(ax.scatter([], [], s=30, c="#4e79a7"))
        ax.set_xlim(-radius * 1.05, radius * 1.05)
        ax.set_ylim(-radius * 1.05, radius * 1.05)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(label, fontsize=11)
    if colored:
        sm = cm.ScalarMappable(cmap=cmap, norm=Normalize(-1, 1))
        fig.colorbar(sm, ax=axes, fraction=0.02, pad=0.01,
                     label="agent rotation m  (blue = CCW, red = CW)")

    def frame(i):
        for k, (scat, (_, traj)) in enumerate(zip(scatters, cases, strict=True)):
            pts = traj[min(i, len(traj) - 1)]
            scat.set_offsets([(p[0], p[1]) for p in pts])
            if colored:
                ms = np.array([p[2] for p in pts])
                scat.set_array(ms)
                m_bar = float(ms.mean()) if len(ms) else 0.0
                labels[k].set_text(f"M = {m_bar:+.2f}")
        return scatters

    anim = animation.FuncAnimation(fig, frame, frames=n_frames, interval=1000 / fps)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out_path, writer=animation.FFMpegWriter(fps=fps, bitrate=2400))
    plt.close(fig)
    return out_path


def spatial_field(
    samples: list[tuple[float, float, float]], radius: float, bins: int = 24, min_count: int = 1
):
    """Bin (x, y, m) samples into a bins x bins grid of mean m over [-radius, radius]^2.

    Cells with fewer than `min_count` samples are set to NaN (suppresses sparse, noisy rim
    cells). Returns (grid, extent) where grid[row, col] is the mean m in that cell, indexed
    row=y, col=x for imshow(origin='lower'); extent is (-r, r, -r, r)."""
    xs = np.array([s[0] for s in samples])
    ys = np.array([s[1] for s in samples])
    ms = np.array([s[2] for s in samples])
    edges = np.linspace(-radius, radius, bins + 1)
    sum_m, _, _ = np.histogram2d(xs, ys, bins=[edges, edges], weights=ms)
    count, _, _ = np.histogram2d(xs, ys, bins=[edges, edges])
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = sum_m / count
    mean[count < min_count] = np.nan
    return mean.T, (-radius, radius, -radius, radius)


def radial_profile(
    samples: list[tuple[float, float, float]], radius: float, bins: int = 10
):
    """Mean local m as a function of distance r from the centre.

    Returns (r_centres, mean_m, count) arrays over `bins` equal-width rings in [0, radius]."""
    rs = np.array([np.hypot(s[0], s[1]) for s in samples])
    ms = np.array([s[2] for s in samples])
    edges = np.linspace(0.0, radius, bins + 1)
    sum_m, _ = np.histogram(rs, bins=edges, weights=ms)
    count, _ = np.histogram(rs, bins=edges)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = sum_m / count
    centres = 0.5 * (edges[:-1] + edges[1:])
    return centres, mean, count


def model_control_plot(
    df: pd.DataFrame, out_path: Path, reference: float | None = None
) -> Path:
    """Bar chart of mean control M̄ per operational model (error bars = std over seeds).

    `df` has columns model, seed, m_bar (from experiment.compare_models_control). An optional
    `reference` draws a dashed line (e.g. the experimental M̄) so the flat controls are read
    against the rotation they fail to produce. Model order follows first appearance in `df`."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = list(dict.fromkeys(df["model"]))
    g = df.groupby("model")["m_bar"].agg(["mean", "std"]).reindex(order).fillna({"std": 0.0})
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(range(len(order)), g["mean"], yerr=g["std"], color="#4e79a7", capsize=5)
    ax.axhline(0.0, color="k", lw=0.8)
    if reference is not None:
        ax.axhline(reference, color="#c0392b", lw=1.2, ls="--",
                   label=f"experiment M̄ = {reference:+.2f}")
        ax.legend()
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([m.replace("Model", "") for m in order], rotation=15, ha="right")
    ax.set_ylabel("control M̄  (+ = CCW)")
    ax.set_title("No bias: does collision avoidance alone rotate the crowd?")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


_PROFILE_COLOURS = ["#444", "#c0392b", "#2980b9", "#27ae60", "#8e44ad"]


def radial_profile_plot(
    panels: list[tuple[str, list[tuple[float, float, float]]]],
    radius: float,
    out_path: Path,
    bins: int = 10,
) -> Path:
    """Overlay mean local m against distance from centre, one curve per (label, samples)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5))
    for (label, samples), colour in zip(panels, _PROFILE_COLOURS, strict=False):
        centres, mean, _ = radial_profile(samples, radius, bins)
        ax.plot(centres, mean, "o-", color=colour, label=label)
    ax.axhline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xlabel("distance from centre r (m)")
    ax.set_ylabel("mean local m  (+ = CCW)")
    ax.set_title("Where the rotation lives: local polarization vs radius")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def field_comparison_plot(
    panels: list[tuple[str, list[tuple[float, float, float]]]],
    radius: float,
    out_path: Path,
    bins: int = 24,
    vlim: float = 0.4,
    min_count: int = 5,
) -> Path:
    """Spatial polarization fields side by side, one panel per (label, samples)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    fig, axes = plt.subplots(1, len(panels), figsize=(5.5 * len(panels), 5.2))
    if len(panels) == 1:
        axes = [axes]
    im = None
    for ax, (label, samples) in zip(axes, panels, strict=True):
        grid, extent = spatial_field(samples, radius, bins, min_count)
        im = ax.imshow(grid, origin="lower", extent=extent, cmap="coolwarm_r",
                       vmin=-vlim, vmax=vlim)
        ax.add_patch(Circle((0, 0), radius, fill=False, color="#333"))
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(label)
    assert im is not None
    fig.suptitle("Local polarization m  (blue = CCW, red = CW)")
    fig.colorbar(im, ax=axes, fraction=0.046, label="mean local m")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path
