"""Validate our polarization metric and simulation against the paper's experimental data.

Reads the authors' Spanish confined-arena trajectories (which include a per-agent `Pol`
column = their m_i) from `materials/ExperimentalData/` (must be unzipped locally), then:

  1. recomputes m_i from (VX, VY, X, Y) with our `polarization.m_individual` and checks it
     matches their `Pol` exactly (centre = origin);
  2. computes the experimental collective polarization M(t) = mean_i m_i per frame, pooled
     over all Spanish trials, and its mean M̄;
  3. runs our biased simulation and overlays the two M distributions.

Run: PYTHONPATH=src python scripts/validate_against_data.py
"""

import glob
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from clockwise.analysis import field_comparison_plot, radial_profile_plot
from clockwise.config import ArenaConfig
from clockwise.experiment import run_arena
from clockwise.polarization import m_individual

DATA = Path("materials/ExperimentalData/Spain")
OUT = Path("docs/results")


def experimental_M() -> tuple[list[float], float, float]:
    """Pooled experimental M(t) over all Spanish trials; also returns max|ours-Pol| and M̄."""
    m_series: list[float] = []
    max_diff = 0.0
    for f in sorted(glob.glob(str(DATA / "*" / "*.csv"))):
        df = pd.read_csv(f)
        ours = [
            m_individual((r["VX(m/s)"], r["VY(m/s)"]), (r["X(m)"], r["Y(m)"]), (0.0, 0.0))
            for _, r in df.iterrows()
        ]
        max_diff = max(max_diff, (pd.Series(ours) - df["Pol"]).abs().max())
        m_series.extend(df.groupby("Time(s)")["Pol"].mean().tolist())
    return m_series, max_diff, sum(m_series) / len(m_series)


def simulated_M(biased_fraction: float, seeds: range) -> tuple[list[float], float]:
    m_series: list[float] = []
    for s in seeds:
        res = run_arena(s, ArenaConfig(n_agents=24, biased_fraction=biased_fraction))
        m_series.extend(res.m_series)
    return m_series, sum(m_series) / len(m_series)


def experimental_field(speed_eps: float) -> list[tuple[float, float, float]]:
    """Per-agent (x, y, m_i) samples pooled over all Spanish trials (m_i = their `Pol`).

    Moving agents only (speed >= speed_eps), to match the simulation field, which records
    the same way — otherwise near-stationary milling rows (m_i ~ 0) dilute the experiment."""
    samples: list[tuple[float, float, float]] = []
    for f in sorted(glob.glob(str(DATA / "*" / "*.csv"))):
        df = pd.read_csv(f)
        moving = df[(df["VX(m/s)"] ** 2 + df["VY(m/s)"] ** 2) >= speed_eps**2]
        samples.extend(zip(moving["X(m)"], moving["Y(m)"], moving["Pol"], strict=True))
    return samples


def model_field(cfg: ArenaConfig, seeds: range) -> tuple[list[tuple[float, float, float]], float]:
    """Pooled (x, y, m_i) field samples and M̄ for a given model config."""
    samples: list[tuple[float, float, float]] = []
    mbars: list[float] = []
    for s in seeds:
        res = run_arena(s, cfg, record_field=True)
        samples.extend(res.field_samples)
        mbars.append(res.m_bar)
    return samples, sum(mbars) / len(mbars)


def main() -> None:
    exp, max_diff, exp_mbar = experimental_M()
    print(f"max|ours - Pol| across all Spanish trials = {max_diff:.4f} (0 = exact match)")
    print(f"experimental M̄ (pooled Spain) = {exp_mbar:+.3f}")

    frac = 0.30  # chosen so the simulated M̄ matches the pooled experimental value
    sim, sim_mbar = simulated_M(biased_fraction=frac, seeds=range(10))
    print(f"simulated M̄ ({frac:.0%} left-turners) = {sim_mbar:+.3f}")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(exp, bins=40, range=(-1, 1), density=True, histtype="step", linewidth=2,
            label=f"experiment (Spain), M̄={exp_mbar:+.2f}")
    ax.hist(sim, bins=40, range=(-1, 1), density=True, histtype="step", linewidth=2,
            label=f"simulation ({frac:.0%} left-turners), M̄={sim_mbar:+.2f}")
    ax.axvline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xlabel("M")
    ax.set_ylabel("pdf")
    ax.set_title("Polarization M: experiment vs simulation")
    ax.legend()
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "experiment_vs_sim.png", dpi=120)
    plt.close(fig)
    print(f"wrote {OUT / 'experiment_vs_sim.png'}")

    # Spatial structure: experiment vs the two minimal models.
    # - wall-turn: a share of agents turn left at the wall (matches M̄ by construction).
    # - intrinsic: every agent has a faithful constant left veer (the paper's left bias),
    #   walls symmetric. We report what it actually does, not a tuned match.
    exp_field = experimental_field(ArenaConfig().speed_eps)
    wall_field, wall_mbar = model_field(
        ArenaConfig(n_agents=24, biased_fraction=0.35), seeds=range(10)
    )
    intr_field, intr_mbar = model_field(
        ArenaConfig(n_agents=24, free_curvature=0.10), seeds=range(10)
    )
    print(f"wall-turn model M̄ (35% left-turners) = {wall_mbar:+.3f}")
    print(f"intrinsic-veer model M̄ (left curvature 0.10 rad/step) = {intr_mbar:+.3f}")

    panels = [
        ("experiment", exp_field),
        (f"wall-turn ({wall_mbar:+.2f})", wall_field),
        (f"intrinsic veer ({intr_mbar:+.2f})", intr_field),
    ]
    field_comparison_plot(panels, radius=5.0, out_path=OUT / "polarization_field.png", min_count=20)
    radial_profile_plot(panels, radius=5.0, out_path=OUT / "radial_profile.png")
    print(f"wrote {OUT / 'polarization_field.png'} and {OUT / 'radial_profile.png'}")


if __name__ == "__main__":
    main()
