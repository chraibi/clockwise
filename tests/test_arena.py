import jupedsim as jps
from shapely import Point

from clockwise.arena import build_arena
from clockwise.config import ArenaConfig


def test_build_arena_returns_disk_and_centre():
    cfg = ArenaConfig(radius=5.0)
    disk, centre = build_arena(cfg)
    assert centre == (0.0, 0.0)
    assert disk.contains(Point(0.0, 0.0))
    assert disk.contains(Point(4.5, 0.0))
    assert not disk.contains(Point(5.5, 0.0))


def test_centre_is_routable():
    cfg = ArenaConfig(radius=5.0)
    disk, centre = build_arena(cfg)
    assert jps.RoutingEngine(disk).is_routable(centre)
