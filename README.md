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

- **Control** — plain agents roaming with collision avoidance but no individual bias. If the paper is
  right, no CCW rotation should appear (`M̄ ≈ 0`).
- **Biased** — add a small per-agent left-turn bias `β`. If the mechanism is right, a CCW rotation
  should appear (`M̄ > 0`, near the experimental `≈ 0.2` for a calibrated `β`).

## The model and our decisions

- **Arena:** a walkable disk of radius 5 m (matching the Spanish experiment), no internal obstacles.
- **Roaming:** each agent follows a heading that random-walks (wander) and, in the biased condition,
  receives a constant counterclockwise increment `β`; near the rim it steers inward. Agents are moved
  by JuPedSim **direct steering** toward a point just ahead of them.
- **Interactions:** collision avoidance is handled by the **Anticipation Velocity Model (AVM)**,
  JuPedSim's richest lateral-avoidance model — so "no CCW without bias" is a strong result.
- **Separation of cause:** the collective part (avoidance) lives entirely in the JuPedSim model; the
  individual part (the bias) is a single knob `β`. This mirrors the paper's individual-vs-collective
  distinction.
- **Metric:** `M(t)` exactly as in the paper (azimuthal projection of each agent's velocity, averaged),
  with `M̄` the time average after a warm-up.
- **Conditions:** control vs biased, at crowd sizes `N ∈ {16, 24, 32}`, several seeds each.
- **One calibrated parameter:** `β` is tuned so the biased case lands near `M̄ ≈ 0.2`; we report its
  value. The headline result is the *qualitative* contrast, not a fitted number.

Full rationale, parameters, and risks (wall artefacts, avoidance asymmetry) are in `docs/design.md`.

## Results

*To be added once the study runs:*

- [ ] `M`-distribution plot: control (centred on 0) vs biased (shifted CCW) — the headline figure.
- [ ] `M̄` table by condition and crowd size, with the calibrated `β`.
- [ ] Trajectory animation (GIF/MP4): a visibly rotating crowd in the biased condition vs a
      directionless control.
- [ ] Optional single-agent (`N=1`) check.

## Running it

*To be added with the implementation (command-line entry points for a single condition and the sweep).*

## Materials

The source paper and its data are in `materials/` (see `materials/README.md`). This repository is a
reproduction and test of that work, not original research; credit for the phenomenon and the
experiments belongs to Echeverría-Huarte, Feliciani, Shi, Nishinari, Sánchez, Garcimartín & Zuriguel.
