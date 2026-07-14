"""大糖帝国：一个可视化的 Sugarscape 代理模型。

仅依赖 Python 3.12、NumPy 和 Matplotlib。
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


@dataclass(slots=True)
class Config:
    size: int = 50
    initial_agents: int = 300
    max_sugar: float = 4.0
    grow_rate: float = 1.0
    min_vision: int = 1
    max_vision: int = 6
    min_metabolism: int = 1
    max_metabolism: int = 4
    min_lifespan: int = 60
    max_lifespan: int = 100
    initial_sugar_min: float = 5.0
    initial_sugar_max: float = 25.0
    reproduction: bool = True
    reproduction_cost: float = 4.0
    seed: int | None = None

    def validate(self) -> None:
        if self.size < 5:
            raise ValueError("世界边长至少为 5")
        if not 0 <= self.initial_agents <= self.size * self.size:
            raise ValueError("初始人口必须介于 0 和格子总数之间")
        if self.max_sugar <= 0 or self.grow_rate < 0:
            raise ValueError("糖容量须为正数，生长速度不能为负")
        if not 1 <= self.min_vision <= self.max_vision:
            raise ValueError("视野范围设置无效")
        if not 1 <= self.min_metabolism <= self.max_metabolism:
            raise ValueError("代谢范围设置无效")
        if not 1 <= self.min_lifespan <= self.max_lifespan:
            raise ValueError("寿命范围设置无效")
        if not 0 <= self.initial_sugar_min <= self.initial_sugar_max:
            raise ValueError("初始财富范围设置无效")
        if self.reproduction_cost < 0:
            raise ValueError("繁殖成本不能为负")


@dataclass(slots=True)
class Agent:
    id: int
    x: int
    y: int
    sugar: float
    metabolism: int
    vision: int
    age: int
    max_age: int
    sex: int

    @property
    def fertile(self) -> bool:
        # 简化的成年和退休规则，让人口不会无限增长。
        start = 12 if self.sex == 0 else 15
        end = 50 if self.sex == 0 else 60
        return start <= self.age <= end


@dataclass(frozen=True, slots=True)
class StepStats:
    step: int
    population: int
    mean_wealth: float
    median_wealth: float
    gini: float
    total_wealth: float
    births: int
    deaths: int


def gini(values: Iterable[float]) -> float:
    """返回非负数据的基尼系数；空数据和全零数据返回 0。"""
    data = np.asarray(list(values), dtype=float)
    if data.size == 0:
        return 0.0
    data = np.clip(data, 0.0, None)
    total = float(data.sum())
    if total == 0:
        return 0.0
    data.sort()
    n = data.size
    indices = np.arange(1, n + 1, dtype=float)
    return float((2.0 * np.dot(indices, data) / total - (n + 1)) / n)


class SugarScape:
    """Sugarscape 世界及其演化规则。"""

    def __init__(self, config: Config):
        config.validate()
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.capacity = self._make_landscape()
        self.sugar = self.capacity.copy()
        self.agents: dict[int, Agent] = {}
        self.occupied: dict[tuple[int, int], int] = {}
        self.tick = 0
        self.next_id = 0
        self.history: list[StepStats] = []
        self._populate(config.initial_agents)
        self.history.append(self._collect_stats(births=0, deaths=0))

    def _make_landscape(self) -> np.ndarray:
        size = self.config.size
        yy, xx = np.mgrid[0:size, 0:size]
        # 两座圆锥形糖山，形状接近经典 Sugarscape 地图。
        peaks = ((0.25 * size, 0.25 * size), (0.75 * size, 0.75 * size))
        radius = size * 0.36
        terrain = np.zeros((size, size), dtype=float)
        for px, py in peaks:
            distance = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
            terrain = np.maximum(terrain, 1.0 - distance / radius)
        levels = np.rint(terrain * self.config.max_sugar)
        return np.clip(levels, 0.0, self.config.max_sugar)

    def _populate(self, count: int) -> None:
        cells = self.rng.choice(self.config.size**2, size=count, replace=False)
        for cell in cells:
            x, y = int(cell % self.config.size), int(cell // self.config.size)
            agent = self._new_agent(x, y)
            self.agents[agent.id] = agent
            self.occupied[(x, y)] = agent.id

    def _new_agent(self, x: int, y: int, *, sugar: float | None = None) -> Agent:
        cfg = self.config
        agent = Agent(
            id=self.next_id,
            x=x,
            y=y,
            sugar=float(
                self.rng.uniform(cfg.initial_sugar_min, cfg.initial_sugar_max)
                if sugar is None
                else sugar
            ),
            metabolism=int(self.rng.integers(cfg.min_metabolism, cfg.max_metabolism + 1)),
            vision=int(self.rng.integers(cfg.min_vision, cfg.max_vision + 1)),
            age=0,
            max_age=int(self.rng.integers(cfg.min_lifespan, cfg.max_lifespan + 1)),
            sex=int(self.rng.integers(0, 2)),
        )
        self.next_id += 1
        return agent

    def _visible_cells(self, agent: Agent) -> list[tuple[int, int, int]]:
        size = self.config.size
        cells = [(agent.x, agent.y, 0)]
        for distance in range(1, agent.vision + 1):
            for dx, dy in ((distance, 0), (-distance, 0), (0, distance), (0, -distance)):
                position = ((agent.x + dx) % size, (agent.y + dy) % size)
                if position not in self.occupied:
                    cells.append((*position, distance))
        return cells

    def _move_and_eat(self, agent: Agent) -> None:
        visible = self._visible_cells(agent)
        best_sugar = max(self.sugar[y, x] for x, y, _ in visible)
        richest = [cell for cell in visible if self.sugar[cell[1], cell[0]] == best_sugar]
        nearest_distance = min(cell[2] for cell in richest)
        nearest = [cell for cell in richest if cell[2] == nearest_distance]
        x, y, _ = nearest[int(self.rng.integers(len(nearest)))]

        del self.occupied[(agent.x, agent.y)]
        agent.x, agent.y = x, y
        self.occupied[(x, y)] = agent.id
        agent.sugar += float(self.sugar[y, x])
        self.sugar[y, x] = 0.0
        agent.sugar -= agent.metabolism
        agent.age += 1

    def _remove_dead(self) -> int:
        dead = [a.id for a in self.agents.values() if a.sugar <= 0 or a.age >= a.max_age]
        for agent_id in dead:
            agent = self.agents.pop(agent_id)
            self.occupied.pop((agent.x, agent.y), None)
        return len(dead)

    def _neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        size = self.config.size
        return [
            ((x + 1) % size, y),
            ((x - 1) % size, y),
            (x, (y + 1) % size),
            (x, (y - 1) % size),
        ]

    def _reproduce(self) -> int:
        if not self.config.reproduction:
            return 0
        births = 0
        used: set[int] = set()
        ids = list(self.agents)
        self.rng.shuffle(ids)
        cost = self.config.reproduction_cost
        for agent_id in ids:
            parent = self.agents.get(agent_id)
            if (
                parent is None
                or parent.id in used
                or not parent.fertile
                or parent.sugar < cost
            ):
                continue
            partner_ids = [
                self.occupied[pos]
                for pos in self._neighbors(parent.x, parent.y)
                if pos in self.occupied
            ]
            partners = [
                self.agents[pid]
                for pid in partner_ids
                if pid not in used
                and self.agents[pid].fertile
                and self.agents[pid].sex != parent.sex
                and self.agents[pid].sugar >= cost
            ]
            if not partners:
                continue
            partner = partners[int(self.rng.integers(len(partners)))]
            empty = [
                pos
                for pos in set(
                    self._neighbors(parent.x, parent.y)
                    + self._neighbors(partner.x, partner.y)
                )
                if pos not in self.occupied
            ]
            if not empty:
                continue
            x, y = empty[int(self.rng.integers(len(empty)))]
            parent.sugar -= cost / 2
            partner.sugar -= cost / 2
            child = self._new_agent(x, y, sugar=cost)
            self.agents[child.id] = child
            self.occupied[(x, y)] = child.id
            used.update((parent.id, partner.id))
            births += 1
        return births

    def _collect_stats(self, births: int, deaths: int) -> StepStats:
        wealth = np.fromiter((a.sugar for a in self.agents.values()), dtype=float)
        return StepStats(
            step=self.tick,
            population=len(self.agents),
            mean_wealth=float(wealth.mean()) if wealth.size else 0.0,
            median_wealth=float(np.median(wealth)) if wealth.size else 0.0,
            gini=gini(wealth),
            total_wealth=float(wealth.sum()),
            births=births,
            deaths=deaths,
        )

    def step(self) -> StepStats:
        """让世界演化一个时间步并返回统计信息。"""
        self.tick += 1
        self.sugar = np.minimum(self.capacity, self.sugar + self.config.grow_rate)
        ids = list(self.agents)
        self.rng.shuffle(ids)
        for agent_id in ids:
            agent = self.agents.get(agent_id)
            if agent is not None:
                self._move_and_eat(agent)
        deaths = self._remove_dead()
        births = self._reproduce()
        stats = self._collect_stats(births, deaths)
        self.history.append(stats)
        return stats

    def run(self, steps: int) -> StepStats:
        if steps < 0:
            raise ValueError("步数不能为负")
        stats = self.history[-1]
        for _ in range(steps):
            stats = self.step()
        return stats

    def export_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = list(StepStats.__dataclass_fields__)
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for row in self.history:
                writer.writerow({field: getattr(row, field) for field in fields})


def show_simulation(world: SugarScape, steps: int, interval: int, save: str | None) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    fig, (ax_world, ax_stats) = plt.subplots(1, 2, figsize=(13, 6))
    image = ax_world.imshow(
        world.sugar,
        cmap="YlOrBr",
        vmin=0,
        vmax=world.config.max_sugar,
        origin="lower",
        interpolation="nearest",
    )
    scatter = ax_world.scatter([], [], s=16, cmap="cool", vmin=0, vmax=40, edgecolors="none")
    title = ax_world.set_title("")
    ax_world.set_xlabel("X")
    ax_world.set_ylabel("Y")
    fig.colorbar(image, ax=ax_world, label="Sugar")

    population_line, = ax_stats.plot([], [], color="tab:blue", label="Population")
    wealth_line, = ax_stats.plot([], [], color="tab:green", label="Mean wealth")
    ax_stats.set_xlim(0, max(1, steps))
    ax_stats.set_ylim(0, max(10, world.config.initial_agents * 1.5))
    ax_stats.set_xlabel("Step")
    ax_stats.set_title("Empire statistics")
    ax_stats.grid(alpha=0.25)
    ax_stats.legend(loc="upper left")
    gini_text = ax_stats.text(0.98, 0.95, "", ha="right", va="top", transform=ax_stats.transAxes)

    def update(frame: int):
        if frame > 0:
            world.step()
        agents = list(world.agents.values())
        positions = np.array([(a.x, a.y) for a in agents], dtype=float).reshape(-1, 2)
        wealth = np.array([a.sugar for a in agents], dtype=float)
        image.set_data(world.sugar)
        scatter.set_offsets(positions)
        scatter.set_array(wealth)
        title.set_text(f"Great Sugar Empire — step {world.tick}, population {len(agents)}")
        x = [s.step for s in world.history]
        population_line.set_data(x, [s.population for s in world.history])
        wealth_line.set_data(x, [s.mean_wealth for s in world.history])
        max_y = max(
            [10.0]
            + [float(s.population) for s in world.history]
            + [s.mean_wealth for s in world.history]
        )
        ax_stats.set_ylim(0, max_y * 1.12)
        gini_text.set_text(f"Gini: {world.history[-1].gini:.3f}")
        return image, scatter, title, population_line, wealth_line, gini_text

    animation = FuncAnimation(
        fig,
        update,
        frames=steps + 1,
        interval=interval,
        repeat=False,
        blit=False,
    )
    fig.tight_layout()
    if save:
        suffix = Path(save).suffix.lower()
        if suffix == ".gif":
            animation.save(save, writer="pillow", fps=max(1, 1000 // interval))
        elif suffix == ".mp4":
            animation.save(save, writer="ffmpeg", fps=max(1, 1000 // interval))
        else:
            raise ValueError("动画文件只支持 .gif 或 .mp4")
    else:
        plt.show()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="大糖帝国（Sugarscape）代理模型")
    parser.add_argument("--size", type=int, default=50, help="地图边长（默认 50）")
    parser.add_argument("--agents", type=int, default=300, help="初始人口（默认 300）")
    parser.add_argument("--steps", type=int, default=300, help="模拟步数（默认 300）")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--interval", type=int, default=80, help="动画帧间隔，毫秒")
    parser.add_argument("--growth", type=float, default=1.0, help="每步糖生长量")
    parser.add_argument("--no-reproduction", action="store_true", help="关闭繁殖")
    parser.add_argument("--no-gui", action="store_true", help="不显示动画，直接计算")
    parser.add_argument("--save", help="将动画保存为 GIF 或 MP4")
    parser.add_argument("--csv", help="将每步统计导出到 CSV")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.steps < 0:
        raise SystemExit("错误：--steps 不能为负")
    if args.interval <= 0:
        raise SystemExit("错误：--interval 必须为正数")
    try:
        world = SugarScape(
            Config(
                size=args.size,
                initial_agents=args.agents,
                grow_rate=args.growth,
                reproduction=not args.no_reproduction,
                seed=args.seed,
            )
        )
    except ValueError as error:
        raise SystemExit(f"配置错误：{error}") from error

    if args.no_gui:
        result = world.run(args.steps)
    else:
        show_simulation(world, args.steps, args.interval, args.save)
        result = world.history[-1]
    if args.csv:
        world.export_csv(args.csv)
    print(
        f"完成：step={result.step}, population={result.population}, "
        f"mean_wealth={result.mean_wealth:.2f}, gini={result.gini:.3f}, "
        f"births={result.births}, deaths={result.deaths}"
    )


if __name__ == "__main__":
    main()
