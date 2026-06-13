import math


def azimuthal_unit(pos: tuple[float, float], centre: tuple[float, float]) -> tuple[float, float]:
    """CCW-tangent unit vector at `pos` relative to `centre`: (-dy, dx)/r."""
    dx, dy = pos[0] - centre[0], pos[1] - centre[1]
    r = math.hypot(dx, dy)
    if r == 0.0:
        return (0.0, 0.0)
    return (-dy / r, dx / r)


def m_individual(
    vel: tuple[float, float], pos: tuple[float, float], centre: tuple[float, float]
) -> float:
    """Projection of the unit velocity onto the CCW tangent. +1 = CCW, -1 = CW, 0 = radial."""
    vx, vy = vel
    speed = math.hypot(vx, vy)
    if speed == 0.0:
        return 0.0
    ex, ey = azimuthal_unit(pos, centre)
    return (vx / speed) * ex + (vy / speed) * ey


def polarization(
    vels: list[tuple[float, float]],
    positions: list[tuple[float, float]],
    centre: tuple[float, float],
    speed_eps: float = 0.05,
) -> float:
    """Crowd polarization M = mean of m_individual over agents moving faster than speed_eps.
    Returns 0.0 if no agent is moving."""
    ms = [
        m_individual(v, p, centre)
        for v, p in zip(vels, positions, strict=True)
        if math.hypot(v[0], v[1]) >= speed_eps
    ]
    return sum(ms) / len(ms) if ms else 0.0
