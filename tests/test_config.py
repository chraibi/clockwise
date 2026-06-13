from clockwise.config import ArenaConfig


def test_defaults():
    cfg = ArenaConfig()
    assert cfg.radius == 5.0
    assert cfg.n_agents == 16
    assert cfg.bias_beta == 0.0  # default is the control condition


def test_biased_config():
    cfg = ArenaConfig(bias_beta=0.02)
    assert cfg.bias_beta == 0.02
