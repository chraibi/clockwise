# Clockwise — Design

**Date:** 2026-06-13
**Status:** Approved (design); pending implementation plan
**Repo:** `clockwise`
**Reference:** Echeverría-Huarte et al., *Individual locomotor bias drives counterclockwise motion in
pedestrian crowds*, Nature Communications 17:4869 (2026). doi:10.1038/s41467-026-73713-w. See
`materials/`.

## Background

When people roam freely inside a confined circular arena, the crowd spontaneously develops a
**collective counterclockwise (CCW) rotation**. The paper quantifies this with a polarization
parameter: for pedestrian `i` at position relative to the arena centre, `mᵢ = v̂ᵢ · êᵢ^φ`, where `v̂ᵢ`
is the unit velocity and `êᵢ^φ` is the azimuthal (CCW-tangent) unit vector at the pedestrian's
location. The crowd value is `M(t) = mean_i mᵢ(t)`; `M̄` is its time average over a free-roaming
interval. `M̄ > 0` is CCW, `M̄ < 0` is CW. Across experiments in Spain and Japan the authors find a
robust `M̄ ≈ 0.2`.

Their central claim is that this CCW bias is **not** an emergent/collective effect of
pedestrian–pedestrian interactions (it persists for people walking alone and without boundaries) but
originates from an **individual locomotor bias** — a slight per-person left-turn tendency.

## Goal and hypothesis

We test that claim with JuPedSim, whose operational models are pure *interaction* models with no
built-in turning bias. The simulator is therefore a clean testbed:

- **H1 (control):** plain JuPedSim agents roaming the arena with collision avoidance but **no
  individual bias** do not produce CCW rotation — `M̄ ≈ 0`.
- **H2 (mechanism):** adding a small per-agent left-turn bias `β` is sufficient to reproduce a CCW
  rotation with `M̄ > 0`, matching the paper's `≈ 0.2` for a calibrated `β`.

The deliverable is a model-based test of the paper's individual-vs-collective distinction, written up
honestly as a reproduction/showcase (a blog post), not a novelty claim.

## Model and methods

### Geometry

A single walkable disk of radius **R = 5 m** (matching the Spanish arena), no internal obstacles.
Agents are confined by the boundary and by an inward steering term near the rim.

### Roaming controller (the core mechanism)

Each agent carries a heading `θᵢ`, updated every control step:

```
θᵢ ← θᵢ + 𝒩(0, σ²)        # wander (random turn)
        + β               # individual CCW bias (0 in the control condition)
        + wall_turn(pos)   # inward turn if within d of the rim
```

The agent is steered (JuPedSim **direct steering**) toward a "carrot" target a short distance `L`
ahead along `θᵢ`. The **Anticipation Velocity Model (AVM)** provides agent–agent collision avoidance.
This separates the two ingredients cleanly:

- **collective / interaction** → AVM avoidance (the part the paper argues is *not* the cause),
- **individual** → the bias `β` (the part the paper argues *is* the cause).

`β = 0` is the control; `β > 0` is the biased condition. Sign convention: positive `β` rotates the
heading counterclockwise.

### Polarization metric

Per frame, each agent's velocity `v̂ᵢ` is obtained as a finite difference of successive positions; the
azimuthal unit vector at position `(x, y)` relative to the arena centre is `ê^φ = (−y, x) / r`. Then
`mᵢ = v̂ᵢ · ê^φ`, `M(t) = mean_i mᵢ`, and `M̄` is the mean of `M(t)` over the run after a warm-up.
Reported outputs: `M̄` per condition and the probability density of `M(t)` (the paper's Fig 2 style).
Sanity check (unit test): an agent moving on a CCW circle gives `m = +1`; CW gives `−1`.

### Experimental design

- **Conditions:** no-bias (`β = 0`) vs biased (`β > 0`).
- **Crowd sizes:** `N ∈ {16, 24, 32}` (the paper's group sizes); `N = 16` is the headline.
- **Replication:** ~10 seeds per condition; paired seeds across conditions where it makes sense.
- **Duration:** runs long enough for stable statistics (e.g. 120 s), discarding an initial warm-up
  (e.g. 20 s) before computing `M̄`.
- **Calibration:** `β` is the single free parameter, tuned so the biased case lands near `M̄ ≈ 0.2`;
  we report the value rather than forcing an exact match. The headline result is qualitative: control
  `M̄ ≈ 0`, biased `M̄ > 0`.
- **Optional:** a single agent (`N = 1`) with bias → still CCW (the paper's "persists alone").

## Repository structure

| Path | Responsibility |
|------|----------------|
| `src/clockwise/arena.py` | Disk geometry (radius `R`) + routability checks. |
| `src/clockwise/roaming.py` | Per-agent heading wander + bias + wall-steering controller. |
| `src/clockwise/polarization.py` | The `M` metric (azimuthal projection, time average). |
| `src/clockwise/experiment.py` | `run_arena(condition, seed, …)` + sweep over conditions/sizes. |
| `src/clockwise/analysis.py` | `M`-PDF and `M̄` plots; trajectory snapshot/animation. |
| `src/clockwise/cli.py` | Run a condition / sweep from the command line. |
| `tests/` | Metric sign (synthetic CCW/CW), confinement, tiny-run control≈0 / biased>0. |
| `materials/` | The paper and its data (see `materials/README.md`). |
| `blog/` | The write-up (added at the end). |

Depends on `jupedsim` (AVM, direct steering); verified with jupedsim 1.4.2.

## Testing

- **Metric:** a synthetic agent circling CCW yields `m = +1`, CW yields `−1`, radial motion `≈ 0`.
- **Confinement:** agents stay within the disk over a run.
- **Mechanism smoke:** on a small/short run, the control condition gives `M̄ ≈ 0` (within noise) and
  the biased condition gives `M̄ > 0`.

## Engineering assessment

Appropriately engineered: one genuinely new piece (the roaming controller); the metric, sweep,
analysis, and CLI reuse patterns proven in the sibling `boarding` study. The bias `β` is the only new
parameter the study needs, and it is reported, not hidden.

## Open questions / risks

1. **Wander vs bias separability** — `σ` (wander) must be small enough that the control condition is
   genuinely unbiased (`M̄ ≈ 0`) and large enough to look like free roaming. Tune on the smoke run.
2. **Wall artefacts** — the inward steering near the rim must not itself induce a rotation; verify the
   control `M̄ ≈ 0` holds with the wall term active (a wall-following bias would be a confound).
3. **AVM avoidance asymmetry** — if AVM resolves conflicts with a fixed left/right preference it could
   inject a spurious bias; check the control condition and, if needed, confirm with a second model
   (Collision-Free Speed Model).
4. **Absolute `M̄`** — `β` is calibrated, not derived; the claim is the *qualitative* contrast
   (control ≈ 0, biased > 0), not a first-principles value.
