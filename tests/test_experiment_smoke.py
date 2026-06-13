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


def test_symmetric_control_has_no_net_rotation():
    # load-bearing: with no left-turners, M-bar averages near zero across seeds. A
    # systematic confound (asymmetric wall-turn or AVM) would push this well past the bound.
    cfg = _tiny(biased_fraction=0.0)
    mbars = [run_arena(seed=s, cfg=cfg).m_bar for s in range(6)]
    assert abs(sum(mbars) / len(mbars)) < 0.1


def test_run_arena_accepts_custom_start_positions():
    # explicit starts override the placement count; each frame holds exactly those agents
    starts = [(0.0, 0.0), (1.0, 0.0), (-1.0, 0.5)]
    res = run_arena(seed=0, cfg=_tiny(), record_traj=True, starts=starts)
    assert res.trajectory and all(len(frame) == len(starts) for frame in res.trajectory)


def test_intrinsic_left_veer_is_ccw_in_open_space():
    # Sign check, isolated from the wall: a lone agent in a large arena (wall never fires)
    # with a constant LEFT veer rotates CCW (m_bar > 0). Confined runs invert this — the
    # wall response, not the veer, sets the confined sign — which is the study's finding.
    cfg = ArenaConfig(n_agents=1, radius=20.0, wander_sigma=0.0, warmup_s=5.0,
                      duration_s=40.0, free_curvature=0.10)
    assert run_arena(seed=0, cfg=cfg).m_bar > 0.0
