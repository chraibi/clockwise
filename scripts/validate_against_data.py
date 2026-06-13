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


if __name__ == "__main__":
    main()
