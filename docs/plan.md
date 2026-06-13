# Clockwise Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test, in JuPedSim, whether counterclockwise (CCW) crowd rotation emerges from collision avoidance alone (it should not) and whether a small per-agent left-turn bias reproduces it (it should), by measuring the polarization `M` for a crowd roaming a circular arena.

**Architecture:** Agents roam a 5 m disk via direct steering toward a "carrot" ahead of a per-agent heading that random-walks plus an optional constant CCW bias `β`; the Anticipation Velocity Model (AVM) supplies collision avoidance. We measure `M(t)` (azimuthal projection of each agent's finite-difference velocity, crowd-averaged) and compare a control (`β=0`) against a biased condition.

**Tech Stack:** Python ≥3.11, `jupedsim` (AVM, direct steering), Shapely, pandas, matplotlib, pytest. Verify with the shared venv `/Users/chraibi/workspace/PedestrianDynamics/jupedsim-scenarios/.venv/bin/python` and its `ruff`; run from repo root `/Users/chraibi/workspace/playground/clockwise`. The repo's `pyproject.toml` sets `pythonpath=["src"]`, so `pytest` finds the `clockwise` package; module runs (`python -m clockwise...`) need `PYTHONPATH=src`.

**Spec:** `docs/design.md`

> **DESIGN REVISION (2026-06-13, as-built):** A calibration spike during Task 8 showed the original
> mechanism (free-space CCW curvature `β` + symmetric inward wall-turn) does **not** produce CCW
> (`M̄ ≈ 0`). Per the paper's actual hypothesis, the bias is *"turn left when facing a wall."* The
> as-built code therefore differs from the task bodies below:
> - free-space motion is **unbiased wander** (no `β`);
> - the bias is a **leftward wall-turn**, parameter `left_wall_bias` (replaces `bias_beta`); when 0 the
>   wall-turn is **symmetric toward the centre** (the control);
> - the steering carrot is **clamped inside the disk** (fixes an out-of-bounds crash).
> Spike result: symmetric wall-turn `M̄ ≈ −0.02`, leftward wall-turn (`left_wall_bias = 0.4`) `M̄ ≈ 0.57`.
> The canonical description is `docs/design.md`. Tasks 1, 4, 5, 6, 7 were revised accordingly; the
> sweep/CLI/analysis column is `left_wall_bias`.

## Verified JuPedSim 1.4.2 API

- Disk geometry: `from shapely import Point; disk = Point(0,0).buffer(5.0, quad_segs=64)`.
- `jps.Simulation(model=..., geometry=disk, dt=0.05, trajectory_writer=optional)`.
- `jps.AnticipationVelocityModel(pushout_strength=0.3, rng_seed=<int>)`.
- `jps.AnticipationVelocityModelAgentParameters(position=(x,y), desired_speed=, radius=, journey_id=, stage_id=)`.
- `sim.add_direct_steering_stage()`, `sim.add_journey(jps.JourneyDescription([stage]))`, `sim.add_agent(params)->id`, `sim.agent(id)` (has `.position` tuple, settable `.target`), `sim.iterate()`.
- No `.velocity` on agents → compute velocity by finite difference of positions.

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `pyproject.toml` | Package metadata, deps, pytest `pythonpath`. |
| `src/clockwise/__init__.py` | Public exports. |
| `src/clockwise/config.py` | `ArenaConfig` dataclass (all parameters incl. `bias_beta`, `n_agents`). |
| `src/clockwise/arena.py` | `build_arena(cfg)` → disk polygon + centre; routability check. |
| `src/clockwise/polarization.py` | `azimuthal_unit`, `m_individual`, `polarization` (the `M` metric). |
| `src/clockwise/roaming.py` | `Roamer` heading controller: wander + bias + wall steering; `carrot`. |
| `src/clockwise/experiment.py` | `run_arena(seed, cfg)` → `ArenaResult`; `sweep`. |
| `src/clockwise/analysis.py` | `m_pdf_plot`, `mbar_table`, `trajectory_animation`. |
| `src/clockwise/cli.py` | CLI for a single condition / the sweep. |
| `tests/` | metric, roaming, arena, experiment smoke. |

---

### Task 1: Package skeleton + config

**Files:** Create `pyproject.toml`, `src/clockwise/__init__.py`, `src/clockwise/config.py`; Test `tests/test_config.py`.

- [ ] **Step 1: Write the failing test** (`tests/test_config.py`):

```python
from clockwise.config import ArenaConfig


def test_defaults():
    cfg = ArenaConfig()
    assert cfg.radius == 5.0
    assert cfg.n_agents == 16
    assert cfg.bias_beta == 0.0  # default is the control condition


def test_biased_config():
    cfg = ArenaConfig(bias_beta=0.02)
    assert cfg.bias_beta == 0.02
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_config.py -v`; expect `ModuleNotFoundError`.

- [ ] **Step 3: Implement** `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "clockwise"
version = "0.1.0"
description = "Does counterclockwise crowd motion emerge in JuPedSim? A test of Echeverria-Huarte et al. (2026)."
requires-python = ">=3.11"
dependencies = ["jupedsim>=1.4", "shapely>=2.0", "pandas>=2.0", "matplotlib>=3.7"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff"]

[project.scripts]
clockwise = "clockwise.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

`src/clockwise/config.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ArenaConfig:
    # arena
    radius: float = 5.0           # m
    # crowd
    n_agents: int = 16
    agent_radius: float = 0.2     # m
    v0: float = 1.2               # m/s desired speed
    # dynamics
    dt: float = 0.05              # s
    duration_s: float = 120.0     # total simulated time
    warmup_s: float = 20.0        # discarded before computing M-bar
    # roaming controller
    wander_sigma: float = 0.15    # rad, per-step random heading change (std)
    bias_beta: float = 0.0        # rad, per-step CCW heading increment (0 = control)
    carrot_distance: float = 1.0  # m, how far ahead the steering target sits
    wall_margin: float = 1.0      # m from the rim where inward steering starts
    wall_turn_gain: float = 0.3   # fraction of the inward angle applied per step
    speed_eps: float = 0.05       # m/s; agents slower than this are ignored in M
```

`src/clockwise/__init__.py`:

```python
from .config import ArenaConfig

__all__ = ["ArenaConfig"]
```

- [ ] **Step 4: Run** the test; expect 2 passing.
- [ ] **Step 5: Commit**

```bash
…/.venv/bin/ruff check src tests
git add pyproject.toml src/clockwise/__init__.py src/clockwise/config.py tests/test_config.py
git commit -m "feat: package skeleton + ArenaConfig"
```

---

### Task 2: Polarization metric

**Files:** Create `src/clockwise/polarization.py`; Test `tests/test_polarization.py`.

- [ ] **Step 1: Write the failing test** (`tests/test_polarization.py`):

```python
import math

from clockwise.polarization import azimuthal_unit, m_individual, polarization


def test_azimuthal_unit_points_ccw():
    # at (1,0) relative to centre, the CCW tangent is (0, 1)
    ex, ey = azimuthal_unit((1.0, 0.0), (0.0, 0.0))
    assert math.isclose(ex, 0.0, abs_tol=1e-9)
    assert math.isclose(ey, 1.0, abs_tol=1e-9)


def test_ccw_motion_gives_plus_one():
    # at (1,0), moving in +y (CCW) -> m = +1
    assert math.isclose(m_individual((0.0, 1.0), (1.0, 0.0), (0.0, 0.0)), 1.0, abs_tol=1e-9)


def test_cw_motion_gives_minus_one():
    assert math.isclose(m_individual((0.0, -1.0), (1.0, 0.0), (0.0, 0.0)), -1.0, abs_tol=1e-9)


def test_radial_motion_gives_zero():
    assert math.isclose(m_individual((1.0, 0.0), (1.0, 0.0), (0.0, 0.0)), 0.0, abs_tol=1e-9)


def test_polarization_ignores_zero_speed_agents():
    # one CCW agent + one stationary agent -> mean over the moving one = +1
    vels = [(0.0, 1.0), (0.0, 0.0)]
    pos = [(1.0, 0.0), (0.0, 2.0)]
    assert math.isclose(polarization(vels, pos, (0.0, 0.0), speed_eps=0.05), 1.0, abs_tol=1e-9)
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_polarization.py -v`; expect ImportError.

- [ ] **Step 3: Implement** (`src/clockwise/polarization.py`):

```python
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
```

- [ ] **Step 4: Run** the test; expect 5 passing.
- [ ] **Step 5: Commit**

```bash
…/.venv/bin/ruff check src tests
git add src/clockwise/polarization.py tests/test_polarization.py
git commit -m "feat: polarization metric M (azimuthal projection)"
```

---

### Task 3: Arena geometry

**Files:** Create `src/clockwise/arena.py`; Test `tests/test_arena.py`.

- [ ] **Step 1: Write the failing test** (`tests/test_arena.py`):

```python
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
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_arena.py -v`; expect ImportError.

- [ ] **Step 3: Implement** (`src/clockwise/arena.py`):

```python
from shapely import Point
from shapely.geometry import Polygon

from .config import ArenaConfig


def build_arena(cfg: ArenaConfig) -> tuple[Polygon, tuple[float, float]]:
    """Walkable disk of radius cfg.radius centred at the origin."""
    disk = Point(0.0, 0.0).buffer(cfg.radius, quad_segs=64)
    return disk, (0.0, 0.0)
```

- [ ] **Step 4: Run** the test; expect 2 passing.
- [ ] **Step 5: Commit**

```bash
…/.venv/bin/ruff check src tests
git add src/clockwise/arena.py tests/test_arena.py
git commit -m "feat: circular arena geometry"
```

---

### Task 4: Roaming controller

**Files:** Create `src/clockwise/roaming.py`; Test `tests/test_roaming.py`.

This is pure geometry/logic (no JuPedSim), so it is fully unit-testable.

- [ ] **Step 1: Write the failing test** (`tests/test_roaming.py`):

```python
import math
import random

from clockwise.config import ArenaConfig
from clockwise.roaming import Roamer, carrot


def test_carrot_is_ahead_along_heading():
    cx, cy = carrot((0.0, 0.0), 0.0, 1.0)
    assert math.isclose(cx, 1.0, abs_tol=1e-9)
    assert math.isclose(cy, 0.0, abs_tol=1e-9)


def test_bias_rotates_heading_ccw_on_average():
    # with no wander and a positive bias, the heading increases (CCW) each step
    cfg = ArenaConfig(wander_sigma=0.0, bias_beta=0.05)
    r = Roamer(heading=0.0)
    h0 = r.heading
    r.update(pos=(0.0, 0.0), cfg=cfg, rng=random.Random(0))  # at centre: no wall term
    assert r.heading > h0
    assert math.isclose(r.heading, 0.05, abs_tol=1e-9)


def test_control_heading_is_unbiased_on_average():
    # no bias, only wander -> mean heading change over many steps ~ 0
    cfg = ArenaConfig(wander_sigma=0.3, bias_beta=0.0)
    rng = random.Random(1)
    r = Roamer(heading=0.0)
    deltas = []
    for _ in range(5000):
        before = r.heading
        r.update(pos=(0.0, 0.0), cfg=cfg, rng=rng)
        deltas.append(r.heading - before)
    assert abs(sum(deltas) / len(deltas)) < 0.02  # close to zero


def test_wall_term_turns_inward_near_rim():
    # near the +x rim, heading pointing outward (+x, =0) should turn toward the centre (pi)
    cfg = ArenaConfig(radius=5.0, wander_sigma=0.0, bias_beta=0.0, wall_margin=1.0, wall_turn_gain=0.5)
    r = Roamer(heading=0.0)  # pointing +x, i.e. outward at (4.6, 0)
    r.update(pos=(4.6, 0.0), cfg=cfg, rng=random.Random(0))
    # inward direction is pi; heading should have moved from 0 toward pi (increased)
    assert r.heading > 0.0
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_roaming.py -v`; expect ImportError.

- [ ] **Step 3: Implement** (`src/clockwise/roaming.py`):

```python
import math
import random
from dataclasses import dataclass

from .config import ArenaConfig


def carrot(pos: tuple[float, float], heading: float, distance: float) -> tuple[float, float]:
    """A steering target `distance` metres ahead of `pos` along `heading`."""
    return (pos[0] + distance * math.cos(heading), pos[1] + distance * math.sin(heading))


@dataclass
class Roamer:
    """Per-agent heading that random-walks, drifts CCW by the bias, and steers off the wall."""

    heading: float

    def update(
        self, pos: tuple[float, float], cfg: ArenaConfig, rng: random.Random
    ) -> float:
        h = self.heading + rng.gauss(0.0, cfg.wander_sigma) + cfg.bias_beta
        r = math.hypot(pos[0], pos[1])
        if r > cfg.radius - cfg.wall_margin and r > 0.0:
            inward = math.atan2(-pos[1], -pos[0])
            diff = math.atan2(math.sin(inward - h), math.cos(inward - h))
            h += cfg.wall_turn_gain * diff
        self.heading = h
        return h
```

(Note: when `wander_sigma=0.0`, `rng.gauss(0, 0)` returns 0.0, so the bias test is exact.)

- [ ] **Step 4: Run** the test; expect 4 passing.
- [ ] **Step 5: Commit**

```bash
…/.venv/bin/ruff check src tests
git add src/clockwise/roaming.py tests/test_roaming.py
git commit -m "feat: roaming heading controller (wander + bias + wall steering)"
```

---

### Task 5: Run loop + sweep

**Files:** Create `src/clockwise/experiment.py`; Test `tests/test_experiment_smoke.py`.

- [ ] **Step 1: Write the failing test** (`tests/test_experiment_smoke.py`):

```python
from clockwise.config import ArenaConfig
from clockwise.experiment import ArenaResult, run_arena


def _tiny(**kw):
    return ArenaConfig(n_agents=8, duration_s=40.0, warmup_s=10.0, **kw)


def test_run_arena_returns_result_with_m_series():
    cfg = _tiny(bias_beta=0.0)
    res = run_arena(seed=0, cfg=cfg)
    assert isinstance(res, ArenaResult)
    assert len(res.m_series) > 0
    assert -1.0 <= res.m_bar <= 1.0


def test_bias_produces_more_ccw_than_control():
    control = run_arena(seed=0, cfg=_tiny(bias_beta=0.0))
    biased = run_arena(seed=0, cfg=_tiny(bias_beta=0.06))
    assert biased.m_bar > control.m_bar
    assert biased.m_bar > 0.0
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_experiment_smoke.py -v`; expect ImportError.

- [ ] **Step 3: Implement** (`src/clockwise/experiment.py`):

```python
import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

import jupedsim as jps
import pandas as pd

from .arena import build_arena
from .config import ArenaConfig
from .polarization import polarization
from .roaming import Roamer, carrot


@dataclass
class ArenaResult:
    seed: int
    bias_beta: float
    n_agents: int
    m_bar: float
    m_series: list[float]
    trajectory: list[list[tuple[float, float]]]  # sampled frames of agent positions (may be empty)


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
            ag.target = carrot(pos, heading, cfg.carrot_distance)
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
    return ArenaResult(seed, cfg.bias_beta, cfg.n_agents, m_bar, m_series, trajectory)


def sweep(
    biases: Sequence[float],
    sizes: Sequence[int],
    seeds: Sequence[int],
    base: ArenaConfig | None = None,
) -> pd.DataFrame:
    """Run every (bias, size, seed); returns long DataFrame of m_bar."""
    from dataclasses import replace

    cfg0 = base or ArenaConfig()
    rows = []
    for bias in biases:
        for n in sizes:
            for seed in seeds:
                res = run_arena(seed, replace(cfg0, bias_beta=bias, n_agents=n))
                rows.append(
                    {"bias_beta": bias, "n_agents": n, "seed": seed, "m_bar": res.m_bar}
                )
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run** `…/.venv/bin/python -m pytest tests/test_experiment_smoke.py -v`. Both must pass. If `test_bias_produces_more_ccw_than_control` fails (biased not clearly > control on the tiny run), increase the test's `bias_beta` (e.g. 0.06 → 0.10) and/or `duration_s`; do NOT weaken the inequality. If the control `m_bar` is itself far from 0 (a confound), STOP and report — that points to a wall/avoidance asymmetry to investigate (design risk #2/#3).

- [ ] **Step 5: Lint + commit**

```bash
…/.venv/bin/ruff check src tests
git add src/clockwise/experiment.py tests/test_experiment_smoke.py
git commit -m "feat: arena run loop (AVM + roaming) + M measurement + sweep"
```

---

### Task 6: Analysis (M-PDF, table, animation)

**Files:** Create `src/clockwise/analysis.py`; Test `tests/test_analysis.py`.

- [ ] **Step 1: Write the failing test** (`tests/test_analysis.py`):

```python
import pandas as pd

from clockwise.analysis import mbar_table


def test_mbar_table_groups_by_condition():
    df = pd.DataFrame(
        [
            {"bias_beta": 0.0, "n_agents": 16, "seed": 0, "m_bar": 0.01},
            {"bias_beta": 0.0, "n_agents": 16, "seed": 1, "m_bar": -0.01},
            {"bias_beta": 0.05, "n_agents": 16, "seed": 0, "m_bar": 0.20},
            {"bias_beta": 0.05, "n_agents": 16, "seed": 1, "m_bar": 0.22},
        ]
    )
    table = mbar_table(df)
    row = table[(table["bias_beta"] == 0.05) & (table["n_agents"] == 16)].iloc[0]
    assert abs(row["mean"] - 0.21) < 1e-9
    assert {"mean", "std", "n"} <= set(table.columns)
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_analysis.py -v`; expect ImportError.

- [ ] **Step 3: Implement** (`src/clockwise/analysis.py`):

```python
from pathlib import Path

import pandas as pd


def mbar_table(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/std of M-bar per (bias_beta, n_agents)."""
    return (
        df.groupby(["bias_beta", "n_agents"])["m_bar"]
        .agg(mean="mean", std="std", n="count")
        .reset_index()
        .fillna({"std": 0.0})
    )


def m_pdf_plot(series_by_label: dict[str, list[float]], out_path: Path) -> Path:
    """Probability density of M(t) for each labelled condition (paper Fig 2 style)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5))
    for label, series in series_by_label.items():
        ax.hist(series, bins=40, range=(-1, 1), density=True, histtype="step", label=label)
    ax.axvline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xlabel("M")
    ax.set_ylabel("pdf")
    ax.set_title("Polarization M: control vs biased")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def trajectory_animation(
    trajectory: list[list[tuple[float, float]]], radius: float, out_path: Path, fps: int = 20
) -> Path:
    """Animate agent positions inside the arena to an mp4."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation
    from matplotlib.patches import Circle

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.add_patch(Circle((0, 0), radius, fill=False, color="#5b6b88"))
    scat = ax.scatter([], [], s=40, c="#4e79a7")
    ax.set_xlim(-radius * 1.05, radius * 1.05)
    ax.set_ylim(-radius * 1.05, radius * 1.05)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    def frame(i):
        scat.set_offsets(trajectory[i])
        return [scat]

    anim = animation.FuncAnimation(fig, frame, frames=len(trajectory), interval=1000 / fps)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out_path, writer=animation.FFMpegWriter(fps=fps, bitrate=2400))
    plt.close(fig)
    return out_path
```

- [ ] **Step 4: Run** `…/.venv/bin/python -m pytest tests/test_analysis.py -v`; expect PASS.
- [ ] **Step 5: Lint + commit**

```bash
…/.venv/bin/ruff check src tests
git add src/clockwise/analysis.py tests/test_analysis.py
git commit -m "feat: analysis (M-bar table, M-pdf plot, trajectory animation)"
```

---

### Task 7: CLI

**Files:** Create `src/clockwise/cli.py`; Test `tests/test_cli.py`.

- [ ] **Step 1: Write the failing test** (`tests/test_cli.py`):

```python
from clockwise.cli import build_parser


def test_cli_defaults():
    args = build_parser().parse_args([])
    assert args.seeds == 10
    assert 0.0 in args.biases
```

- [ ] **Step 2: Run** `…/.venv/bin/python -m pytest tests/test_cli.py -v`; expect ModuleNotFoundError.

- [ ] **Step 3: Implement** (`src/clockwise/cli.py`):

```python
import argparse
from pathlib import Path

from .analysis import m_pdf_plot, mbar_table
from .config import ArenaConfig
from .experiment import run_arena, sweep


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Counterclockwise roaming study in JuPedSim.")
    p.add_argument("--biases", nargs="+", type=float, default=[0.0, 0.05])
    p.add_argument("--sizes", nargs="+", type=int, default=[16, 24, 32])
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--out", type=Path, default=Path("study-output"))
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    df = sweep(args.biases, args.sizes, list(range(args.seeds)))
    df.to_csv(args.out / "m_bar_sweep.csv", index=False)
    table = mbar_table(df)
    table.to_csv(args.out / "m_bar_table.csv", index=False)
    # headline M-pdf at the first size: control vs the largest bias
    n0 = args.sizes[0]
    control = run_arena(0, ArenaConfig(n_agents=n0, bias_beta=min(args.biases)))
    biased = run_arena(0, ArenaConfig(n_agents=n0, bias_beta=max(args.biases)))
    m_pdf_plot(
        {f"control (β={min(args.biases)})": control.m_series,
         f"biased (β={max(args.biases)})": biased.m_series},
        args.out / "m_pdf.png",
    )
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run** `…/.venv/bin/python -m pytest tests/test_cli.py -v`; expect PASS.
- [ ] **Step 5: Full suite + lint**

```bash
…/.venv/bin/python -m pytest tests -q
…/.venv/bin/ruff check src tests
```
- [ ] **Step 6: CLI smoke** (tiny):

```bash
PYTHONPATH=src …/.venv/bin/python -m clockwise --biases 0.0 0.08 --sizes 8 --seeds 2 --out /tmp/cw_smoke
ls /tmp/cw_smoke
```
Expect a printed table and files `m_bar_sweep.csv`, `m_bar_table.csv`, `m_pdf.png`. Report the printed table (control row near 0, biased row > 0).

- [ ] **Step 7: Commit**

```bash
git add src/clockwise/cli.py tests/test_cli.py
git commit -m "feat: CLI for the roaming sweep"
```

---

### Task 8: Run the study + fill README results

**Files:** Modify `README.md`; artifacts under `study-output/` (committed copies under `docs/results/`).

- [ ] **Step 1: Calibrate β.** Run a short bias sweep to find the β giving `M̄ ≈ 0.2`:

```bash
PYTHONPATH=src …/.venv/bin/python -c "
from clockwise.experiment import sweep
df = sweep([0.0,0.02,0.04,0.06,0.08,0.10],[16],[0,1,2,3,4], )
print(df.groupby('bias_beta')['m_bar'].mean())
"
```
Pick the β whose mean `M̄` is closest to 0.2; call it `β*`. Record the table.

- [ ] **Step 2: Run the main study** (control vs `β*`, all sizes, 10 seeds):

```bash
mkdir -p docs/results
PYTHONPATH=src …/.venv/bin/python -m clockwise --biases 0.0 <β*> --sizes 16 24 32 --seeds 10 --out docs/results
```
Note the printed `m_bar_table`.

- [ ] **Step 3: Make the trajectory animation** (one biased run, recorded):

```bash
PYTHONPATH=src …/.venv/bin/python -c "
from pathlib import Path
from clockwise.config import ArenaConfig
from clockwise.experiment import run_arena
from clockwise.analysis import trajectory_animation
r = run_arena(0, ArenaConfig(n_agents=24, bias_beta=<β*>, duration_s=60.0), record_traj=True)
trajectory_animation(r.trajectory, 5.0, Path('docs/results/rotation.mp4'))
print('frames', len(r.trajectory), 'm_bar', round(r.m_bar,3))
"
```
Sanity-check the mp4 by extracting a frame; confirm a visibly rotating crowd. Optionally also render a control run for side-by-side.

- [ ] **Step 4: Fill the README Results section** with: the calibrated `β*`; the `m_bar` table (control ≈ 0 vs biased > 0, across N); the `m_pdf.png` (control centred on 0, biased shifted CCW); and the `rotation.mp4`/GIF. Report the numbers actually produced. If the control `M̄` is not near 0, document it honestly and flag the confound (design risks #2/#3) rather than hiding it.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/results/m_bar_table.csv docs/results/m_bar_sweep.csv
git add -f docs/results/m_pdf.png docs/results/rotation.mp4
git commit -m "docs: clockwise study results (control vs biased) + README"
```

---

## Self-Review

**Spec coverage:**
- Disk arena radius 5 m → Task 3. ✓
- Roaming controller (wander + bias + wall) → Task 4. ✓
- AVM avoidance + direct steering + run loop → Task 5. ✓
- `M` metric (azimuthal projection, finite-diff velocity, time average) → Tasks 2, 5. ✓
- Conditions (control vs biased), N∈{16,24,32}, seeds, warm-up → Tasks 5, 7, 8. ✓
- Single calibrated β, reported → Task 8 (calibration), CLI. ✓
- Outputs: M-pdf, M̄ table, animation → Tasks 6, 8. ✓
- Confinement + metric-sign + control≈0/biased>0 tests → Tasks 2, 4, 5. ✓
- Single-agent option → not a separate task; achievable via `n_agents=1` (noted in README as optional).

**Placeholder scan:** No TBD/TODO in code steps. Task 8 uses `<β*>` as the calibrated value the runner fills in — this is a run-and-record study task, not a code stub.

**Type consistency:** `ArenaConfig` fields, `build_arena(cfg)->(disk,centre)`, `polarization(vels,positions,centre,speed_eps)`, `Roamer.update(pos,cfg,rng)`, `carrot(pos,heading,distance)`, `run_arena(seed,cfg,record_traj)->ArenaResult(... m_series, trajectory)`, `sweep(biases,sizes,seeds,base)`, `mbar_table(df)`, `m_pdf_plot(series_by_label,out)`, `trajectory_animation(trajectory,radius,out,fps)` — used consistently across tasks.

> **Validity note for the implementer:** the load-bearing result is the *control*. Before trusting the
> biased numbers, confirm the control `M̄` sits near 0 across seeds with the wall term and AVM active.
> A non-zero control means the wall steering or AVM avoidance is itself breaking symmetry (design
> risks #2/#3) — investigate before reporting, don't tune it away.
