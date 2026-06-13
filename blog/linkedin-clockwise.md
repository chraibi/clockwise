# Does counterclockwise crowd rotation emerge in a pedestrian simulator?

*A LinkedIn article — draft. Suggested cover: `docs/results/comparison.gif`.*

---

A recent paper in Nature Communications (Echeverría-Huarte, Feliciani, Shi, Nishinari, Sánchez, Garcimartín & Zuriguel, 2026) reports a striking observation: when people roam freely inside a confined circular arena, the crowd slowly drifts **counterclockwise**. The authors measured this across experiments in Spain and Japan and found it to be robust. Their main claim is that the rotation is not a collective effect of people avoiding one another, but comes from an **individual bias** — a slight tendency, when facing a wall, to turn left.

We tried to reproduce this in [@JuPedSim](https://www.jupedsim.org/), our open-source pedestrian simulator, to see whether the mechanism behaves as described.

## Why a simulator helps here

JuPedSim's models handle collision avoidance, but they have no built-in left/right turning preference — the avoidance is symmetric. That makes the simulator a clean test: if a crowd roaming a circular arena with symmetric avoidance does **not** rotate, that supports the paper's point that the bias is individual, not a by-product of interaction. And if adding the individual bias reproduces the rotation, that supports the proposed mechanism.

We model a 5 m arena, agents roaming with random headings, collision avoidance from the Anticipation Velocity Model, and we measure the same polarization quantity as the paper (`M`: each person's velocity projected onto the counterclockwise direction, averaged over the crowd; `M̄ > 0` means counterclockwise).

## What we found

**With symmetric avoidance, the crowd does not rotate.** Across crowd sizes and seeds, `M̄ ≈ 0`. So the simulator's interaction model alone produces no preferred direction.

**Adding the paper's bias — turning left when facing the wall — produces counterclockwise rotation.** We first tried placing the bias in free-space curvature, and it did not work; re-reading the paper, the proposed mechanism is specifically about turning left *at the wall*, and that is what reproduces the effect.

**The strength of the rotation depends on how common the bias is.** A single turn strength saturates, so the natural knob is the *fraction* of people who have the left-turn tendency — which matches the paper's mixed population. With nobody biased the crowd doesn't rotate; with everyone biased it rotates strongly; and a crowd where roughly a third turn left reproduces the experiment's `M̄ ≈ 0.2`.

**[Insert: `docs/results/mbar_vs_fraction.png`]** — mean polarization vs the share of left-turners. Zero with no bias, rising with the fraction; about a third reproduces the experimental value.

**[Insert: `docs/results/m_pdf.png`]** — the distribution of `M`. The control is centred on zero; with a fraction of left-turners it shifts counterclockwise, as in the paper.

**[Insert: `docs/results/comparison.gif`]** — three crowds side by side (0%, ~45%, 100% left-turners). The control mills without a net sense; with more left-turners the crowd circulates counterclockwise.

## What this is, and what it isn't

This is a reproduction, not new science. The phenomenon, the data, and the explanation are the authors'. What we did is check, in an independent interaction-based simulator, that symmetric avoidance produces no rotation and that the proposed turn-left-at-wall bias produces the counterclockwise motion at about the reported magnitude.

It is also limited in scope, and we want to be clear about it: we reproduce the **confined-arena** result through the wall-turn mechanism. The paper also reports counterclockwise motion **without boundaries** and for people walking **alone** — which a wall-turn model cannot explain. So we are testing the confined/wall part of their work, not the full claim that the bias acts even without walls.

Everything — model, experiments, figures, and videos — is openly available, and the results regenerate with one command:

**Code, high-quality videos & data:** https://github.com/chraibi/clockwise
**JuPedSim:** https://www.jupedsim.org/
**WebJuPedSim:** https://app.jupedsim.org

Credit for the phenomenon and the experiments belongs to Iñaki Echeverría-Huarte and colleagues.

*#PedestrianDynamics #JuPedSim #Simulation #ReproducibleResearch #CrowdDynamics*
