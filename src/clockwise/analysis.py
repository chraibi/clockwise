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


def comparison_animation(
    cases: list[tuple[str, list[list[tuple[float, float]]]]],
    radius: float,
    out_path: Path,
    fps: int = 20,
) -> Path:
    """Animate several labelled cases side by side (one arena panel each) to an mp4.

    cases: list of (label, trajectory). Panels share a clock; shorter trajectories hold
    their last frame."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation
    from matplotlib.patches import Circle

    n = len(cases)
    n_frames = max(len(traj) for _, traj in cases)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.6))
    if n == 1:
        axes = [axes]
    scatters = []
    for ax, (label, _) in zip(axes, cases, strict=True):
        ax.add_patch(Circle((0, 0), radius, fill=False, color="#5b6b88"))
        scatters.append(ax.scatter([], [], s=30, c="#4e79a7"))
        ax.set_xlim(-radius * 1.05, radius * 1.05)
        ax.set_ylim(-radius * 1.05, radius * 1.05)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(label, fontsize=11)
    fig.tight_layout()

    def frame(i):
        for scat, (_, traj) in zip(scatters, cases, strict=True):
            scat.set_offsets(traj[min(i, len(traj) - 1)])
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


def radial_profile_plot(
    exp_samples: list[tuple[float, float, float]],
    sim_samples: list[tuple[float, float, float]],
    radius: float,
    out_path: Path,
    bins: int = 10,
) -> Path:
    """Overlay experiment vs simulation mean local m against distance from centre."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5))
    for label, samples, colour in [
        ("experiment", exp_samples, "#444"),
        ("simulation", sim_samples, "#c0392b"),
    ]:
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
    exp_samples: list[tuple[float, float, float]],
    sim_samples: list[tuple[float, float, float]],
    radius: float,
    out_path: Path,
    bins: int = 24,
    vlim: float = 0.4,
    min_count: int = 5,
) -> Path:
    """Side-by-side spatial polarization fields: experiment vs simulation."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    panels = [("experiment", exp_samples), ("simulation", sim_samples)]
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
