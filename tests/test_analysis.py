import pandas as pd

from clockwise.analysis import mbar_table


def test_mbar_table_groups_by_condition():
    df = pd.DataFrame(
        [
            {"biased_fraction": 0.0, "n_agents": 16, "seed": 0, "m_bar": 0.01},
            {"biased_fraction": 0.0, "n_agents": 16, "seed": 1, "m_bar": -0.01},
            {"biased_fraction": 0.45, "n_agents": 16, "seed": 0, "m_bar": 0.20},
            {"biased_fraction": 0.45, "n_agents": 16, "seed": 1, "m_bar": 0.22},
        ]
    )
    table = mbar_table(df)
    row = table[(table["biased_fraction"] == 0.45) & (table["n_agents"] == 16)].iloc[0]
    assert abs(row["mean"] - 0.21) < 1e-9
    assert {"mean", "std", "n"} <= set(table.columns)


def test_m_pdf_plot_writes_png(tmp_path):
    from clockwise.analysis import m_pdf_plot
    out = m_pdf_plot({"control": [0.0, 0.1, -0.1], "biased": [0.2, 0.3, 0.1]}, tmp_path / "p.png")
    assert out.exists()


def test_trajectory_animation_writes_mp4(tmp_path):
    from clockwise.analysis import trajectory_animation
    frames = [[(0.0, 0.0), (1.0, 0.0)], [(0.1, 0.1), (1.0, 0.1)], [(0.2, 0.0), (0.9, 0.2)]]
    out = trajectory_animation(frames, radius=5.0, out_path=tmp_path / "a.mp4", fps=5)
    assert out.exists()
