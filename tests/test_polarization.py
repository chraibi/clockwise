import math

from clockwise.polarization import azimuthal_unit, m_individual, polarization


def test_azimuthal_unit_points_ccw():
    ex, ey = azimuthal_unit((1.0, 0.0), (0.0, 0.0))
    assert math.isclose(ex, 0.0, abs_tol=1e-9)
    assert math.isclose(ey, 1.0, abs_tol=1e-9)


def test_ccw_motion_gives_plus_one():
    assert math.isclose(m_individual((0.0, 1.0), (1.0, 0.0), (0.0, 0.0)), 1.0, abs_tol=1e-9)


def test_cw_motion_gives_minus_one():
    assert math.isclose(m_individual((0.0, -1.0), (1.0, 0.0), (0.0, 0.0)), -1.0, abs_tol=1e-9)


def test_radial_motion_gives_zero():
    assert math.isclose(m_individual((1.0, 0.0), (1.0, 0.0), (0.0, 0.0)), 0.0, abs_tol=1e-9)


def test_polarization_ignores_zero_speed_agents():
    vels = [(0.0, 1.0), (0.0, 0.0)]
    pos = [(1.0, 0.0), (0.0, 2.0)]
    assert math.isclose(polarization(vels, pos, (0.0, 0.0), speed_eps=0.05), 1.0, abs_tol=1e-9)
