import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

import jupedsim as jps
import pandas as pd

from .arena import build_arena
from .config import ArenaConfig
from .polarization import polarization
from .roaming import Roamer, carrot, clamp_inside


@dataclass
class ArenaResult:
    seed: int
    left_wall_bias: float
    n_agents: int
    m_bar: float
    m_series: list[float]
    trajectory: list[list[tuple[float, float]]]  # sampled frames of positions (may be empty)


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


def run_arena(seed: int, cfg: ArenaConfig | None = None, record_traj: bool = False) -> ArenaResult:
    cfg = cfg or ArenaConfig()
    rng = random.Random(seed)
    disk, centre = build_arena(cfg)
    sim = jps.Simulation(
        model=jps.AnticipationVelocityModel(rng_seed=seed),
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
        params = jps.AnticipationVelocityModelAgentParameters(
            position=p, desired_speed=cfg.v0, radius=cfg.agent_radius,
            journey_id=journey, stage_id=direct,
        )
        aid = sim.add_agent(params)
        agents.append(aid)
        roamers[aid] = Roamer(heading=rng.uniform(0, 2 * math.pi))
        prev[aid] = p

    n_steps = round(cfg.duration_s / cfg.dt)
    warmup_steps = round(cfg.warmup_s / cfg.dt)
    traj_stride = max(1, round(0.2 / cfg.dt))
    m_series: list[float] = []
    trajectory: list[list[tuple[float, float]]] = []

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
        sim.iterate()

    m_bar = sum(m_series) / len(m_series) if m_series else 0.0
    return ArenaResult(seed, cfg.left_wall_bias, cfg.n_agents, m_bar, m_series, trajectory)


def sweep(
    left_biases: Sequence[float],
    sizes: Sequence[int],
    seeds: Sequence[int],
    base: ArenaConfig | None = None,
) -> pd.DataFrame:
    """Run every (left_wall_bias, size, seed); returns long DataFrame of m_bar."""
    from dataclasses import replace

    cfg0 = base or ArenaConfig()
    rows = []
    for bias in left_biases:
        for n in sizes:
            for seed in seeds:
                res = run_arena(seed, replace(cfg0, left_wall_bias=bias, n_agents=n))
                rows.append(
                    {"left_wall_bias": bias, "n_agents": n, "seed": seed, "m_bar": res.m_bar}
                )
    return pd.DataFrame(rows)
