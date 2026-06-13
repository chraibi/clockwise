from clockwise.config import ArenaConfig


def test_defaults():
    cfg = ArenaConfig()
    assert cfg.radius == 5.0
    assert cfg.n_agents == 16
    assert cfg.biased_fraction == 0.0  # default: no left-turners = symmetric control


def test_biased_config():
    cfg = ArenaConfig(biased_fraction=0.45)
    assert cfg.biased_fraction == 0.45
