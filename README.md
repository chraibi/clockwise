# clockwise — does counterclockwise crowd motion emerge in JuPedSim?

A model-based test, using [JuPedSim](https://www.jupedsim.org/), of the claim by Echeverría-Huarte et
al. (2026) that the spontaneous **counterclockwise (CCW) rotation** of a freely roaming crowd comes
from an **individual locomotor bias**, not from pedestrian interactions.

> Status: design complete, implementation pending. Results below are placeholders to be filled in as
> the study runs. See `docs/design.md` for the full design and `materials/` for the source paper and data.

## The phenomenon

When people roam freely inside a confined circular arena, the crowd drifts counterclockwise. The paper
measures this with a polarization parameter `M`: each person's velocity projected onto the
counterclockwise (azimuthal) direction around the arena centre, averaged over the crowd. `M̄ > 0` is
CCW; the experiments find a robust `M̄ ≈ 0.2`. The authors argue this is **not** an emergent effect of
people avoiding each other — it persists even for a person walking alone — but a slight per-person
**left-turn bias**.

## The question

JuPedSim's operational models are pure *interaction* models: agents avoid collisions but have **no
built-in turning bias**. That makes the simulator a clean testbed:

- **Control** — agents roam with collision avoidance and a **symmetric** wall response (turn toward
  the centre). If the paper is right, no CCW rotation should appear (`M̄ ≈ 0`).
- **Biased** — give agents the paper's proposed individual bias: **turn left when facing the wall**. If
  the mechanism is right, a CCW rotation should appear (`M̄ > 0`, near the experimental `≈ 0.2` for a
  calibrated turn strength).

## The model and our decisions

- **Arena:** a walkable disk of radius 5 m (matching the Spanish experiment), no internal obstacles.
- **Roaming:** each agent follows a heading that random-walks (unbiased wander). Near the rim it turns
  away from the wall — **symmetrically toward the centre** in the control, or **left (CCW)** in the
  biased condition. Agents are moved by JuPedSim **direct steering** toward a point just ahead of them
  (clamped to stay inside the disk).
- **Interactions:** collision avoidance is handled by the **Anticipation Velocity Model (AVM)**,
  JuPedSim's richest lateral-avoidance model — so "no CCW from symmetric avoidance" is a strong result.
- **Where the bias lives:** the paper proposes the CCW rotation comes from *turning left when facing a
  wall*. A calibration spike confirmed this: a symmetric wall-turn gives `M̄ ≈ 0`, while a leftward
  wall-turn gives a strong `M̄ > 0`. So the individual bias is a single knob in the **wall response**,
  cleanly separated from the collective (AVM) avoidance.
- **Metric:** `M(t)` exactly as in the paper (azimuthal projection of each agent's velocity, averaged),
  with `M̄` the time average after a warm-up.
- **Conditions:** control (symmetric) vs biased (turn-left-at-wall), at crowd sizes `N ∈ {16, 24, 32}`,
  several seeds each.
- **One calibrated parameter:** the leftward wall-turn strength, tuned so the biased case lands near
  `M̄ ≈ 0.2`; we report its value. The headline result is the *qualitative* contrast, not a fitted
  number.

**Scope (honest):** this reproduces the **confined-arena** CCW via the wall-turn mechanism. The paper
also finds CCW *without* boundaries and for lone walkers, which a wall-turn model does not explain — so
we test the paper's confined/wall hypothesis specifically, not its full claim. Full rationale and risks
are in `docs/design.md`.

## Results

*To be added once the study runs:*

- [ ] `M`-distribution plot: control (centred on 0) vs biased (shifted CCW) — the headline figure.
- [ ] `M̄` table by condition and crowd size, with the calibrated wall-turn strength.
- [ ] Trajectory animation (GIF/MP4): a visibly rotating crowd in the biased condition vs a
      directionless control.
- [ ] Optional single-agent (`N=1`) check.

## Running it

*To be added with the implementation (command-line entry points for a single condition and the sweep).*

## Materials

The source paper and its data are in `materials/` (see `materials/README.md`). This repository is a
reproduction and test of that work, not original research; credit for the phenomenon and the
experiments belongs to Echeverría-Huarte, Feliciani, Shi, Nishinari, Sánchez, Garcimartín & Zuriguel.
