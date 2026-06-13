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


def test_comparison_animation_writes_mp4(tmp_path):
    from clockwise.analysis import comparison_animation
    a = [[(0.0, 0.0)], [(0.1, 0.0)], [(0.2, 0.0)]]
    b = [[(0.0, 1.0)], [(0.0, 1.1)]]  # shorter: holds last frame
    out = comparison_animation([("control", a), ("biased", b)], radius=5.0,
                               out_path=tmp_path / "c.mp4", fps=5)
    assert out.exists()


def test_spatial_field_bins_mean_and_marks_empty():
    import math

    from clockwise.analysis import spatial_field
    # Two samples in the same +x,+y cell average; the rest of the grid is empty (NaN).
    grid, extent = spatial_field([(2.0, 2.0, 0.4), (2.1, 2.1, 0.6)], radius=5.0, bins=2)
    assert extent == (-5.0, 5.0, -5.0, 5.0)
    # row = y (>0 -> upper), col = x (>0 -> right): top-right cell holds the mean.
    assert abs(grid[1, 1] - 0.5) < 1e-9
    assert math.isnan(grid[0, 0])


def test_radial_profile_increases_toward_wall():
    from clockwise.analysis import radial_profile
    # Calm centre, strong CCW near the rim.
    samples = [(0.2, 0.0, 0.0), (0.0, 0.3, 0.05), (4.5, 0.0, 0.9), (0.0, 4.6, 0.95)]
    centres, mean, count = radial_profile(samples, radius=5.0, bins=5)
    assert count.sum() == 4
    assert mean[-1] > mean[0]  # outer ring more CCW than the core


def test_field_and_radial_plots_write_png(tmp_path):
    from clockwise.analysis import field_comparison_plot, radial_profile_plot
    exp = [(1.0, 0.0, 0.1), (0.0, 3.0, 0.3), (-2.0, 1.0, 0.2)]
    sim = [(1.0, 0.0, 0.05), (0.0, 4.0, 0.6), (-2.0, 1.0, 0.1)]
    panels = [("experiment", exp), ("wall-turn", sim), ("intrinsic", sim)]
    f = field_comparison_plot(panels, radius=5.0, out_path=tmp_path / "field.png")
    r = radial_profile_plot(panels, radius=5.0, out_path=tmp_path / "radial.png")
    assert f.exists() and r.exists()
