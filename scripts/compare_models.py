"""Control across JuPedSim operational models.

Runs the no-bias control (symmetric avoidance, no individual turn) for each of SFM,
WarpDriver, CSM and AVM, and plots the mean polarization per model against the experimental
M̄. If the flat control is real and not an AVM artefact, every model should sit near zero,
far below the experimental rotation.

Run: PYTHONPATH=src python scripts/compare_models.py
"""

from pathlib import Path

from clockwise.analysis import model_control_plot
from clockwise.experiment import compare_models_control
from clockwise.models import MODELS

OUT = Path("docs/results")
EXPERIMENTAL_MBAR = 0.185  # pooled Spanish trials (see validate_against_data.py)


def main() -> None:
    df = compare_models_control(MODELS, seeds=range(10))
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "model_control.csv", index=False)
    for name, mean in df.groupby("model")["m_bar"].mean().items():
        print(f"{name:32s} control M̄ = {mean:+.3f}")
    model_control_plot(df, OUT / "model_control.png", reference=EXPERIMENTAL_MBAR)
    print(f"wrote {OUT / 'model_control.png'} and {OUT / 'model_control.csv'}")


if __name__ == "__main__":
    main()
