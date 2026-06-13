from clockwise.config import ArenaConfig
from clockwise.experiment import ArenaResult, run_arena


def _tiny(**kw):
    return ArenaConfig(n_agents=8, duration_s=40.0, warmup_s=10.0, **kw)


def test_run_arena_returns_result_with_m_series():
    cfg = _tiny(biased_fraction=0.0)
    res = run_arena(seed=0, cfg=cfg)
    assert isinstance(res, ArenaResult)
    assert len(res.m_series) > 0
    assert -1.0 <= res.m_bar <= 1.0


def test_left_turners_produce_more_ccw_than_symmetric_control():
    control = run_arena(seed=0, cfg=_tiny(biased_fraction=0.0))
    biased = run_arena(seed=0, cfg=_tiny(biased_fraction=1.0))
    assert biased.m_bar > control.m_bar
    assert biased.m_bar > 0.0
