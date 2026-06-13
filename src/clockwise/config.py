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
    wander_sigma: float = 0.15    # rad, per-step random heading change (std); unbiased
    left_wall_bias: float = 0.0   # rad, leftward (CCW) turn per step when facing the wall.
                                  # 0 = symmetric control (turn toward centre); >0 = biased.
    carrot_distance: float = 1.0  # m, how far ahead the steering target sits
    carrot_margin: float = 0.3    # m, keep the carrot at least this far inside the rim
    wall_margin: float = 1.0      # m from the rim where the wall response starts
    wall_turn_gain: float = 0.3   # symmetric control: fraction of the inward angle per step
    speed_eps: float = 0.05       # m/s; agents slower than this are ignored in M
