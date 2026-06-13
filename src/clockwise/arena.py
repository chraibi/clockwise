from shapely import Point
from shapely.geometry import Polygon

from .config import ArenaConfig


def build_arena(cfg: ArenaConfig) -> tuple[Polygon, tuple[float, float]]:
    """Walkable disk of radius cfg.radius centred at the origin."""
    disk = Point(0.0, 0.0).buffer(cfg.radius, quad_segs=64)
    return disk, (0.0, 0.0)
