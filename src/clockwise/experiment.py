import math
import random
from collections.abc import Sequence
from dataclasses import dataclass, field

import jupedsim as jps
import pandas as pd

from .arena import build_arena
from .config import ArenaConfig
from .models import build_agent_params, build_model
from .polarization import m_individual, polarization
from .roaming import Roamer, carrot, clamp_inside


@dataclass
class ArenaResult:
    seed: int
    biased_fraction: float
    n_agents: int
    m_bar: float
    m_series: list[float]
    trajectory: list[list[tuple[float, float]]]  # sampled frames of positions (may be empty)
    field_samples: list[tuple[float, float, float]] = field(default_factory=list)  # (x, y, m_i)


def _seed_positions(cfg: ArenaConfig, rng: random.Random) -> list[tuple[float, float]]:
    """Random non-overlapping start positions inside the disk (rejection sampling)."""
    rmax = cfg.radius - cfg.wall_margin
    min_gap = 2.5 * cfg.agent_radius
    pts: list[tuple[float, float]] = []
    attempts = 0
    while len(pts) < cfg.n_agents and attempts < 100000:
        attempts += 1
        ang = rng.uniform(0, 2 * math.pi)
        rad = rmax * math.sqrt(rng.random())
        p = (rad * math.cos(ang), rad * math.sin(ang))
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= min_gap for q in pts):
            pts.append(p)
    if len(pts) < cfg.n_agents:
        raise RuntimeError(f"could not place {cfg.n_agents} agents in r={cfg.radius}")
    return pts


def _make_roamer(cfg: ArenaConfig, rng: random.Random) -> Roamer:
    """One roamer. Intrinsic study (free_curvature > 0): every agent veers left in free space,
    walls stay symmetric. Wall-turn study (free_curvature == 0): a `biased_fraction` share
    turn left at the wall, the rest are symmetric."""
    heading = rng.uniform(0, 2 * math.pi)
    if cfg.free_curvature != 0.0:
        return Roamer(heading=heading, biased=False, free_curvature=cfg.free_curvature)
    return Roamer(heading=heading, biased=rng.random() < cfg.biased_fraction)


def run_arena(
    seed: int,
    cfg: ArenaConfig | None = None,
    record_traj: bool = False,
    record_field: bool = False,
) -> ArenaResult:
    cfg = cfg or ArenaConfig()
    rng = random.Random(seed)
    disk, centre = build_arena(cfg)
    sim = jps.Simulation(
        model=build_model(cfg.model, seed),
        geometry=disk,
        dt=cfg.dt,
    )
    direct = sim.add_direct_steering_stage()
    journey = sim.add_journey(jps.JourneyDescription([direct]))

    starts = _seed_positions(cfg, rng)
    agents: list[int] = []
    roamers: dict[int, Roamer] = {}
    prev: dict[int, tuple[float, float]] = {}
    for p in starts:
        aid = sim.add_agent(build_agent_params(cfg.model, p, cfg, journey, direct))
        agents.append(aid)
        roamers[aid] = _make_roamer(cfg, rng)
        prev[aid] = p

    n_steps = round(cfg.duration_s / cfg.dt)
    warmup_steps = round(cfg.warmup_s / cfg.dt)
    traj_stride = max(1, round(0.2 / cfg.dt))
    m_series: list[float] = []
    trajectory: list[list[tuple[float, float]]] = []
    field_samples: list[tuple[float, float, float]] = []

    for step in range(n_steps):
        positions, vels = [], []
        for aid in agents:
            ag = sim.agent(aid)
            pos = (ag.position[0], ag.position[1])
            heading = roamers[aid].update(pos, cfg, rng)
            ag.target = clamp_inside(
                carrot(pos, heading, cfg.carrot_distance), cfg.radius, cfg.carrot_margin
            )
            vx = (pos[0] - prev[aid][0]) / cfg.dt
            vy = (pos[1] - prev[aid][1]) / cfg.dt
            positions.append(pos)
            vels.append((vx, vy))
            prev[aid] = pos
        if step >= warmup_steps:
            m_series.append(polarization(vels, positions, centre, cfg.speed_eps))
            if record_traj and step % traj_stride == 0:
                trajectory.append(positions)
            if record_field:
                for p, v in zip(positions, vels, strict=True):
                    if math.hypot(v[0], v[1]) >= cfg.speed_eps:
                        field_samples.append((p[0], p[1], m_individual(v, p, centre)))
        sim.iterate()

    m_bar = sum(m_series) / len(m_series) if m_series else 0.0
    return ArenaResult(
        seed, cfg.biased_fraction, cfg.n_agents, m_bar, m_series, trajectory, field_samples
    )


def sweep(
    fractions: Sequence[float],
    sizes: Sequence[int],
    seeds: Sequence[int],
    base: ArenaConfig | None = None,
) -> pd.DataFrame:
    """Run every (biased_fraction, size, seed); returns long DataFrame of m_bar."""
    from dataclasses import replace

    cfg0 = base or ArenaConfig()
    rows = []
    for frac in fractions:
        for n in sizes:
            for seed in seeds:
                res = run_arena(seed, replace(cfg0, biased_fraction=frac, n_agents=n))
                rows.append(
                    {"biased_fraction": frac, "n_agents": n, "seed": seed, "m_bar": res.m_bar}
                )
    return pd.DataFrame(rows)


def compare_models_control(
    models: Sequence[str], seeds: Sequence[int], base: ArenaConfig | None = None
) -> pd.DataFrame:
    """Control (no bias) M-bar per operational model. Tests whether symmetric collision
    avoidance alone creates a preferred rotation — in any JuPedSim model, not just AVM."""
    from dataclasses import replace

    cfg0 = base or ArenaConfig(n_agents=24)
    rows = []
    for name in models:
        for seed in seeds:
            res = run_arena(seed, replace(cfg0, model=name, biased_fraction=0.0))
            rows.append({"model": name, "seed": seed, "m_bar": res.m_bar})
    return pd.DataFrame(rows)
