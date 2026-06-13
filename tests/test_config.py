from clockwise.config import ArenaConfig


def test_defaults():
    cfg = ArenaConfig()
    assert cfg.radius == 5.0
    assert cfg.n_agents == 16
    assert cfg.left_wall_bias == 0.0  # default is the symmetric control condition


def test_biased_config():
    cfg = ArenaConfig(left_wall_bias=0.3)
    assert cfg.left_wall_bias == 0.3
