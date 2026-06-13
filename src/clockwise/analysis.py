from pathlib import Path

import pandas as pd


def mbar_table(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/std of M-bar per (bias_beta, n_agents)."""
    return (
        df.groupby(["bias_beta", "n_agents"])["m_bar"]
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
