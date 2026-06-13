import jupedsim as jps
import pytest

from clockwise.config import ArenaConfig
from clockwise.experiment import compare_models_control, run_arena
from clockwise.models import MODELS, build_agent_params, build_model


def test_registry_lists_the_four_models():
    assert set(MODELS) == {
        "SocialForceModel",
        "WarpDriverModel",
        "CollisionFreeSpeedModel",
        "AnticipationVelocityModel",
    }


@pytest.mark.parametrize("name", MODELS)
def test_build_model_and_params(name):
    model = build_model(name, seed=0)
    assert isinstance(model, getattr(jps, name))
    params = build_agent_params(name, (1.0, 0.0), ArenaConfig(), journey_id=1, stage_id=2)
    assert isinstance(params, getattr(jps, name + "AgentParameters"))


@pytest.mark.parametrize("name", MODELS)
def test_each_model_runs_and_returns_finite_mbar(name):
    cfg = ArenaConfig(model=name, n_agents=8, duration_s=30.0, warmup_s=10.0)
    res = run_arena(seed=0, cfg=cfg)
    assert len(res.m_series) > 0
    assert -1.0 <= res.m_bar <= 1.0


def test_compare_models_control_returns_long_frame():
    df = compare_models_control(
        ["AnticipationVelocityModel", "CollisionFreeSpeedModel"],
        seeds=range(2),
        base=ArenaConfig(n_agents=8, duration_s=30.0, warmup_s=10.0),
    )
    assert set(df.columns) == {"model", "seed", "m_bar"}
    assert len(df) == 4


def test_model_control_plot_writes_png(tmp_path):
    import pandas as pd

    from clockwise.analysis import model_control_plot
    df = pd.DataFrame(
        [
            {"model": "AVM", "seed": 0, "m_bar": 0.01},
            {"model": "AVM", "seed": 1, "m_bar": -0.01},
            {"model": "CSM", "seed": 0, "m_bar": 0.02},
        ]
    )
    out = model_control_plot(df, tmp_path / "mc.png", reference=0.185)
    assert out.exists()
