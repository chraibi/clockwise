import math
import random

from clockwise.config import ArenaConfig
from clockwise.roaming import Roamer, carrot, clamp_inside


def test_carrot_is_ahead_along_heading():
    cx, cy = carrot((0.0, 0.0), 0.0, 1.0)
    assert math.isclose(cx, 1.0, abs_tol=1e-9)
    assert math.isclose(cy, 0.0, abs_tol=1e-9)


def test_clamp_inside_pulls_outside_points_to_the_rim():
    # a point well outside is pulled to radius - margin, same direction
    px, py = clamp_inside((10.0, 0.0), radius=5.0, margin=0.3)
    assert math.isclose(px, 4.7, abs_tol=1e-9)
    assert math.isclose(py, 0.0, abs_tol=1e-9)
    # a point already inside is unchanged
    assert clamp_inside((1.0, 0.0), radius=5.0, margin=0.3) == (1.0, 0.0)


def test_free_space_is_unbiased_even_when_biased_condition_is_on():
    # the bias acts only at the wall; at the centre the mean heading change is ~0
    cfg = ArenaConfig(wander_sigma=0.3, left_wall_bias=0.4)
    rng = random.Random(1)
    r = Roamer(heading=0.0)
    deltas = []
    for _ in range(5000):
        before = r.heading
        r.update(pos=(0.0, 0.0), cfg=cfg, rng=rng)  # at centre: no wall term
        deltas.append(r.heading - before)
    assert abs(sum(deltas) / len(deltas)) < 0.02


def test_biased_turns_left_when_facing_the_wall():
    # at the +x rim, heading pointing outward (+x), biased condition turns LEFT (heading increases)
    cfg = ArenaConfig(radius=5.0, wander_sigma=0.0, left_wall_bias=0.2, wall_margin=1.0)
    r = Roamer(heading=0.0)
    r.update(pos=(4.6, 0.0), cfg=cfg, rng=random.Random(0))
    assert math.isclose(r.heading, 0.2, abs_tol=1e-9)


def test_control_turns_toward_centre_at_the_wall():
    # control (left_wall_bias=0): symmetric inward turn. Heading pointing tangentially (+y)
    # at the +x rim should rotate toward inward (pi), i.e. increase past pi/2.
    cfg = ArenaConfig(radius=5.0, wander_sigma=0.0, left_wall_bias=0.0,
                      wall_margin=1.0, wall_turn_gain=0.5)
    r = Roamer(heading=math.pi / 2)  # pointing +y at (4.6, 0); inward is pi
    r.update(pos=(4.6, 0.0), cfg=cfg, rng=random.Random(0))
    assert r.heading > math.pi / 2  # moved toward inward (pi)
