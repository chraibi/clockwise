import argparse
from pathlib import Path

from .analysis import m_pdf_plot, mbar_table
from .config import ArenaConfig
from .experiment import run_arena, sweep


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Counterclockwise roaming study in JuPedSim.")
    p.add_argument("--fractions", nargs="+", type=float, default=[0.0, 0.45])
    p.add_argument("--sizes", nargs="+", type=int, default=[16, 24, 32])
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--out", type=Path, default=Path("study-output"))
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    df = sweep(args.fractions, args.sizes, list(range(args.seeds)))
    df.to_csv(args.out / "m_bar_sweep.csv", index=False)
    table = mbar_table(df)
    table.to_csv(args.out / "m_bar_table.csv", index=False)
    n0 = args.sizes[0]
    lo, hi = min(args.fractions), max(args.fractions)
    control = run_arena(0, ArenaConfig(n_agents=n0, biased_fraction=lo))
    biased = run_arena(0, ArenaConfig(n_agents=n0, biased_fraction=hi))
    m_pdf_plot(
        {f"control ({lo:.0%} left-turners)": control.m_series,
         f"biased ({hi:.0%} left-turners)": biased.m_series},
        args.out / "m_pdf.png",
    )
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
