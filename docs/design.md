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

- **H1 (control):** plain JuPedSim agents roaming the arena with **symmetric** wall avoidance (no
  individual bias) do not produce CCW rotation — `M̄ ≈ 0`.
- **H2 (mechanism):** giving agents the paper's proposed individual bias — **turning left when facing
  the wall** — is sufficient to reproduce a CCW rotation with `M̄ > 0`, near the paper's `≈ 0.2` for a
  calibrated turn strength.

The deliverable is a model-based test of the paper's individual-vs-collective distinction, written up
honestly as a reproduction/showcase (a blog post), not a novelty claim.

### Where the bias lives (corrected after a calibration spike)

An earlier version of this design put the bias in *free-space curvature* (a constant CCW heading
increment) with a *symmetric* inward wall-turn. A spike showed this does **not** produce CCW
(`M̄ ≈ 0` across seeds). Re-reading the paper, its proposed mechanism is specifically *"a slight
preference … to turn **left when facing a wall**"*; a symmetric inward wall-turn erases exactly that
asymmetry. The corrected mechanism — unbiased free-space wander plus a **leftward** wall-turn — was
verified in the spike: symmetric wall-turn gave `M̄ ≈ 0`, leftward wall-turn gave a strong `M̄ > 0`.
The bias therefore lives in the **wall response**, not in free-space curvature.

### Scope and faithfulness (stated honestly)

This reproduces the **confined-arena** CCW rotation through the wall-turn mechanism the paper proposes
for that setting. The paper *also* reports CCW persisting **without boundaries** and for **lone
walkers**, which a wall-turn model cannot explain. We therefore test the paper's confined/wall
hypothesis specifically, not its full claim that an individual bias produces CCW even without walls.
The write-up will say so plainly.

## Model and methods

### Geometry

A single walkable disk of radius **R = 5 m** (matching the Spanish arena), no internal obstacles.
Agents are confined by the boundary and by the wall-response term near the rim.

### Roaming controller (the core mechanism)

Each agent carries a heading `θᵢ`. In free space it only wanders (no directional bias); the bias
appears only in how it turns away from the wall:

```
θᵢ ← θᵢ + 𝒩(0, σ²)                       # unbiased wander
if near the rim and the heading faces outward:
    control:  θᵢ ← θᵢ + g · (inward − θᵢ)  # symmetric turn toward the centre
    biased:   θᵢ ← θᵢ + β_wall             # turn LEFT (counterclockwise)
```

The agent is steered (JuPedSim **direct steering**) toward a "carrot" target a short distance `L`
ahead along `θᵢ`. The carrot is **clamped to stay inside the disk** (a robustness fix: an un-clamped
carrot can leave the walkable area and crash the simulation). The **Anticipation Velocity Model
(AVM)** provides agent–agent collision avoidance. This separates the two ingredients cleanly:

- **collective / interaction** → AVM avoidance + the symmetric wall-turn (the part the paper argues is
  *not* the cause),
- **individual** → the leftward wall bias `β_wall` (the part the paper argues *is* the cause).

`β_wall = 0` selects the symmetric control; `β_wall > 0` selects the biased (turn-left-at-wall)
condition. Larger `β_wall` turns left more sharply per step.

### Polarization metric

Per frame, each agent's velocity `v̂ᵢ` is obtained as a finite difference of successive positions; the
azimuthal unit vector at position `(x, y)` relative to the arena centre is `ê^φ = (−y, x) / r`. Then
`mᵢ = v̂ᵢ · ê^φ`, `M(t) = mean_i mᵢ`, and `M̄` is the mean of `M(t)` over the run after a warm-up.
Reported outputs: `M̄` per condition and the probability density of `M(t)` (the paper's Fig 2 style).
Sanity check (unit test): an agent moving on a CCW circle gives `m = +1`; CW gives `−1`.

### Experimental design

- **Conditions:** symmetric control (`β_wall = 0`) vs biased turn-left-at-wall (`β_wall > 0`).
- **Crowd sizes:** `N ∈ {16, 24, 32}` (the paper's group sizes); `N = 16` is the headline.
- **Replication:** ~10 seeds per condition; paired seeds across conditions where it makes sense.
- **Duration:** runs long enough for stable statistics (e.g. 120 s), discarding an initial warm-up
  (e.g. 20 s) before computing `M̄`.
- **Calibration:** `β_wall` is the single free parameter, tuned so the biased case lands near
  `M̄ ≈ 0.2`; we report the value rather than forcing an exact match. The headline result is
  qualitative: control `M̄ ≈ 0`, biased `M̄ > 0`. (The spike's `β_wall = 0.4 rad/step` gave `M̄ ≈ 0.57`,
  so the calibrated value is gentler.)

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
analysis, and CLI reuse patterns proven in the sibling `boarding` study. The wall bias `β_wall` is the
only new parameter the study needs, and it is reported, not hidden. Same spirit as `boarding`: a
careful, honest reproduction rather than a novelty claim.

## Open questions / risks

1. **Control must be ≈ 0 (load-bearing).** The symmetric wall-turn must not itself induce rotation.
   Verified in the spike: symmetric wall-turn gave `M̄ ≈ −0.02` across seeds (noise around zero). Keep
   checking it across the full seed set; a non-zero control would be a confound, not a result.
2. **Carrot must stay in bounds.** An un-clamped carrot caused an out-of-bounds crash; the carrot is
   clamped inside the disk.
3. **AVM avoidance asymmetry** — if AVM resolved conflicts with a fixed left/right preference it could
   inject a spurious bias; the near-zero control rules this out, and a Collision-Free Speed Model run
   can confirm if desired.
4. **Absolute `M̄`** — `β_wall` is calibrated, not derived; the claim is the *qualitative* contrast
   (control ≈ 0, biased > 0) and that it reproduces the paper's CCW direction, not a first-principles
   value.
5. **Scope** — confined-arena/wall mechanism only; does not address the paper's boundary-free and
   lone-walker persistence (see "Scope and faithfulness").
