import math
import random

from clockwise.config import ArenaConfig
from clockwise.roaming import Roamer, carrot


def test_carrot_is_ahead_along_heading():
    cx, cy = carrot((0.0, 0.0), 0.0, 1.0)
    assert math.isclose(cx, 1.0, abs_tol=1e-9)
    assert math.isclose(cy, 0.0, abs_tol=1e-9)


def test_bias_rotates_heading_ccw_on_average():
    cfg = ArenaConfig(wander_sigma=0.0, bias_beta=0.05)
    r = Roamer(heading=0.0)
    h0 = r.heading
    r.update(pos=(0.0, 0.0), cfg=cfg, rng=random.Random(0))  # at centre: no wall term
    assert r.heading > h0
    assert math.isclose(r.heading, 0.05, abs_tol=1e-9)


def test_control_heading_is_unbiased_on_average():
    cfg = ArenaConfig(wander_sigma=0.3, bias_beta=0.0)
    rng = random.Random(1)
    r = Roamer(heading=0.0)
    deltas = []
    for _ in range(5000):
        before = r.heading
        r.update(pos=(0.0, 0.0), cfg=cfg, rng=rng)
        deltas.append(r.heading - before)
    assert abs(sum(deltas) / len(deltas)) < 0.02


def test_wall_term_turns_inward_near_rim():
    cfg = ArenaConfig(radius=5.0, wander_sigma=0.0, bias_beta=0.0, wall_margin=1.0, wall_turn_gain=0.5)
    r = Roamer(heading=0.0)  # pointing +x, i.e. outward at (4.6, 0)
    r.update(pos=(4.6, 0.0), cfg=cfg, rng=random.Random(0))
    # exact antipode: inward correction has gain*pi magnitude; sign is undefined there
    assert math.isclose(abs(r.heading), math.pi / 2, abs_tol=1e-9)
