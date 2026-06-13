# Does counterclockwise crowd rotation emerge in a pedestrian simulator?

*A LinkedIn article — draft. Suggested cover: `docs/results/comparison.gif`.*

---

A recent paper in Nature Communications (Echeverría-Huarte, Feliciani, Shi, Nishinari, Sánchez, Garcimartín & Zuriguel, 2026) reports a striking observation: when people roam freely inside a confined circular arena, the crowd slowly drifts **counterclockwise**. The authors measured this across experiments in Spain and Japan and found it to be robust. Their main claim is that the rotation is not a collective effect of people avoiding one another, but comes from an **individual bias** — a slight tendency, when facing a wall, to turn left.

We tried to reproduce this in [@JuPedSim](https://www.jupedsim.org/), to see whether the mechanism behaves as described.

## Why a simulator helps here

JuPedSim's models handle collision avoidance, but they have no built-in left/right turning preference — the avoidance is symmetric. That makes the simulator a clean test: if a crowd roaming a circular arena with symmetric avoidance does **not** rotate, that supports the paper's point that the bias is individual, not a by-product of interaction. And if adding the individual bias reproduces the rotation, that supports the proposed mechanism.

We model a 5 m arena, agents roaming with random headings, collision avoidance from the Anticipation Velocity Model, and we measure the same polarization quantity as the paper (`M`: each person's velocity projected onto the counterclockwise direction, averaged over the crowd; `M̄ > 0` means counterclockwise).

## What we found

**With symmetric avoidance, the crowd does not rotate.** Across crowd sizes and seeds, `M̄ ≈ 0`. So the simulator's interaction model alone produces no preferred direction.

**And this is not a quirk of one collision model.** JuPedSim ships several models of how people avoid each other — some velocity-based, some force-based — and they differ a lot in their internals. A skeptic could fairly ask whether the flat result is just a feature of the one we happened to pick. So we ran the same no-bias control through four of them: Social Force, WarpDriver, Collision-Free Speed, and Anticipation Velocity. Every one stays within a few hundredths of zero, far below the experimental value. The absence of rotation is a property of *symmetric avoidance itself*, not of any particular model — the rotation has to be put in; it does not fall out of collision handling.

**[Insert: `docs/results/model_control.png`]** — the no-bias control for the four collision models, against the experimental `M̄` (dashed). All four sit near zero.

**[Insert: `docs/results/collage_models.gif`]** — the same point as a video: one real experimental run beside the four model controls. The real crowd circulates counterclockwise; the bare models just mill.

**Adding the paper's bias — turning left when facing the wall — produces counterclockwise rotation.** We first tried placing the bias in free-space curvature; on its own it did not give the confined rotation (we come back to why below), so we used the mechanism the paper describes directly — turning left *at the wall* — and that reproduces the effect.

**The strength of the rotation depends on how common the bias is.** A single turn strength saturates, so the natural knob is the *fraction* of people who have the left-turn tendency — which matches the paper's mixed population. With nobody biased the crowd doesn't rotate; with everyone biased it rotates strongly; and a crowd where roughly a third turn left reproduces the experiment's `M̄ ≈ 0.2`.

**[Insert: `docs/results/mbar_vs_fraction.png`]** — mean polarization vs the share of left-turners. Zero with no bias, rising with the fraction; about a third reproduces the experimental value.

**[Insert: `docs/results/m_pdf.png`]** — the distribution of `M`. The control is centred on zero; with a fraction of left-turners it shifts counterclockwise, as in the paper.

**[Insert: `docs/results/comparison.gif`]** — three crowds side by side (0%, ~45%, 100% left-turners). The control mills without a net sense; with more left-turners the crowd circulates counterclockwise.

## Matching the average is not matching the mechanism

The paper's data also let us go further than the single number `M̄`. Their trajectory files include a per-agent polarization value, and recomputing it with our metric matches theirs exactly — so we can compare not just the average rotation but *where* in the arena it happens. This turned out to be the most useful test, because it is the one that can disagree with us rather than confirm us.

The experiment shows a **coherent counterclockwise rotation that fills the disk**: positive at every radius, building from a faint centre to a peak in the outer-middle, then easing at the very wall. We compared this against two minimal models — the turn-left-at-wall bias above, and an "intrinsic" version where every agent has a small constant left veer at every step (closer to the paper's reading of an individual bias present even away from walls).

Neither reproduces the experiment, and they miss in different ways. The **wall-turn** model gets the *amount* of rotation right but puts it in the wrong place — a thin spike right at the rim, with a nearly still interior, because the bias only acts at the wall. The **intrinsic veer** spreads the rotation into the interior, closer to where the experiment peaks, but it comes out **clockwise** — the wrong sign. In open space a left veer does rotate counterclockwise; we checked that directly. But once the arena is confined, our wall response flips it: the net sense is set by how the veer meets the wall, not by the veer alone.

**[Insert: `docs/results/radial_profile.png`]** — local rotation against distance from the centre, for the experiment and the two models. The experiment is positive throughout and peaks in the outer-middle; the wall-turn model spikes at the rim; the intrinsic veer turns negative.

**[Insert: `docs/results/polarization_field.png`]** — the same three as spatial maps (blue counterclockwise, red clockwise). The experiment is broadly blue across the disk; the wall-turn model is a blue ring; the intrinsic veer is a red band.

We read this as support for the paper's framing rather than against it: matching one number with a one-knob shortcut is easy, but the spatial structure of the real rotation does not casually fall out of either simple mechanism. A faithful reproduction would need more than we put in here.

## Where this leaves us

We set out to probe the mechanism behind a real phenomenon, and we learned a few concrete things. Symmetric collision avoidance produces no preferred rotation. A turn-left-at-wall bias recovers the counterclockwise motion at about the reported magnitude. And looking at *where* the rotation lives shows that getting the average right is the easy part — the spatial structure is more demanding, and it is what separates a coincidence from the actual mechanism.

There is plenty left to do. The experiment also reports counterclockwise motion **without boundaries** and for people walking **alone**, which neither of our minimal models touches yet. Reproducing the full spatial field will need a richer individual model than a single knob. So here is the question we keep coming back to: with no wall to turn at and no crowd to follow, what makes a single person drift counterclockwise? We don't have the answer yet — and that is exactly the part we find most interesting. This is a short teaser of an ongoing exploration; more to come.

Everything — model, experiments, figures, and videos — is openly available, and the results regenerate with one command:

**Code, high-quality videos & data:** https://github.com/chraibi/clockwise
**JuPedSim:** https://www.jupedsim.org/
**WebJuPedSim:** https://app.jupedsim.org

Credit for the phenomenon and the experiments belongs to Iñaki Echeverría-Huarte and colleagues.

*#PedestrianDynamics #JuPedSim #Simulation #ReproducibleResearch #CrowdDynamics*
