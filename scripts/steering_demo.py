"""Direct-steering demo: one roaming agent and the target we feed JuPedSim each step.

Shows the API seam — every step we set the agent's target (red ring) a short way ahead of a
heading we control (dashed line); JuPedSim moves the agent (blue dot) there without collisions.
A single agent, so there is nothing to avoid; the point is the steering loop, not the crowd.

Run: PYTHONPATH=src python scripts/steering_demo.py
"""

import random
import subprocess
from pathlib import Path

import jupedsim as jps
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Circle

from clockwise.analysis import rotation_frames
from clockwise.arena import build_arena
from clockwise.config import ArenaConfig
from clockwise.models import build_agent_params, build_model
from clockwise.roaming import Roamer, carrot, clamp_inside

OUT = Path("docs/results")
FPS = 20


def run(cfg: ArenaConfig, seed: int, duration_s: float):
    """Return [(position, target), ...] for one roaming agent."""
    rng = random.Random(seed)
    disk, _ = build_arena(cfg)
    sim = jps.Simulation(model=build_model(cfg.model, seed), geometry=disk, dt=cfg.dt)
    steering = sim.add_direct_steering_stage()
    journey = sim.add_journey(jps.JourneyDescription([steering]))
    aid = sim.add_agent(build_agent_params(cfg.model, (0.0, 0.0), cfg, journey, steering))

    roamer = Roamer(heading=0.4)
    rec = []
    for _ in range(round(duration_s / cfg.dt)):
        agent = sim.agent(aid)
        pos = (agent.position[0], agent.position[1])
        heading = roamer.update(pos, cfg, rng)
        target = clamp_inside(carrot(pos, heading, cfg.carrot_distance), cfg.radius,
                              cfg.carrot_margin)
        agent.target = target
        rec.append((pos, target))
        sim.iterate()
    return rec


def animate(frames, radius: float, out_path: Path) -> None:
    """frames: list of (position, target, m) per displayed step."""
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.add_patch(Circle((0, 0), radius, fill=False, color="#5b6b88"))
    ax.set_xlim(-radius * 1.05, radius * 1.05)
    ax.set_ylim(-radius * 1.05, radius * 1.05)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    (trail,) = ax.plot([], [], color="#9fb0c8", lw=1.2, alpha=0.7, zorder=1)
    agent = ax.scatter([], [], s=90, c="#4e79a7", zorder=3, label="Agent")
    target = ax.scatter([], [], s=90, facecolors="none", edgecolors="#c0392b", zorder=3,
                        label="Target")
    ax.legend([target, agent], ["Target", "Agent"], loc="upper right", fontsize=9,
              framealpha=0.9)

    xs, ys = [], []

    def frame(i):
        (px, py), (tx, ty), m, t = frames[i]
        xs.append(px)
        ys.append(py)
        trail.set_data(xs, ys)
        agent.set_offsets([(px, py)])
        target.set_offsets([(tx, ty)])
        ax.set_title(f"t = {t:4.1f} s     M = {m:+.2f}", fontsize=12)
        return trail, agent, target

    anim = animation.FuncAnimation(fig, frame, frames=len(frames), interval=1000 / FPS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out_path, writer=animation.FFMpegWriter(fps=FPS, bitrate=2400))
    plt.close(fig)


def to_gif(mp4: Path, gif: Path) -> None:
    palette = OUT / "_palette.png"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-vf", "fps=15,scale=480:-1:flags=lanczos,palettegen",
         str(palette)], check=True, capture_output=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-i", str(palette), "-lavfi",
         "fps=15,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse", str(gif)],
        check=True, capture_output=True)
    palette.unlink(missing_ok=True)


def main() -> None:
    cfg = ArenaConfig()
    rec = run(cfg, seed=3, duration_s=40.0)
    stride = max(1, round(0.2 / cfg.dt))  # display a frame every 0.2 s
    sample_dt = stride * cfg.dt
    sampled = rec[::stride]
    positions = [[pos] for pos, _ in sampled]
    m_series = [pts[0][2] for pts in rotation_frames(positions, sample_dt, smooth_s=1.0)]
    frames = [
        (pos, tgt, m, i * sample_dt)
        for i, ((pos, tgt), m) in enumerate(zip(sampled, m_series, strict=True))
    ]
    mp4 = OUT / "steering_demo.mp4"
    animate(frames, cfg.radius, mp4)
    to_gif(mp4, OUT / "steering_demo.gif")
    print(f"wrote {mp4} and steering_demo.gif")


if __name__ == "__main__":
    main()
