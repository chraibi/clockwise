"""Registry of JuPedSim operational (collision-avoidance) models.

The roaming bias lives in our own controller; the operational model only resolves
collisions. Swapping it lets us check that the control (no bias) produces no rotation in
*any* JuPedSim model, not just one — i.e. that the flat control is not a model artefact."""

import jupedsim as jps

from .config import ArenaConfig

# The four models we compare, in display order.
MODELS = (
    "SocialForceModel",
    "WarpDriverModel",
    "CollisionFreeSpeedModel",
    "AnticipationVelocityModel",
)

# Force/velocity-based models whose agent parameters take an initial orientation.
_ORIENTED = {"SocialForceModel", "WarpDriverModel"}


def build_model(name: str, seed: int):
    """Construct an operational model by name. Only AVM exposes an rng seed; the others are
    deterministic given the (seeded) initial conditions."""
    cls = getattr(jps, name)
    if name == "AnticipationVelocityModel":
        return cls(rng_seed=seed)
    return cls()


def build_agent_params(
    name: str, position: tuple[float, float], cfg: ArenaConfig, journey_id: int, stage_id: int
):
    """Agent parameters for `name`, with the same speed and radius across all models so the
    comparison is fair. Oriented models also need a (non-zero) initial heading."""
    cls = getattr(jps, name + "AgentParameters")
    common = dict(
        position=position,
        desired_speed=cfg.v0,
        radius=cfg.agent_radius,
        journey_id=journey_id,
        stage_id=stage_id,
    )
    if name in _ORIENTED:
        common["orientation"] = (1.0, 0.0)
    return cls(**common)
